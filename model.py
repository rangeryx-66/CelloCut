import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "build"))

import numpy as np
import trimesh
import torch
import torchcumesh2sdf
import maxflow
import diso
import cppmodules as cpp
from decimate import OBJMeshDecimator
import time

class CelloCut:
  def __init__(self, voxel_res, T):
    self.voxel_res = voxel_res
    self.eps = 1 / voxel_res
    self.band = 3 / voxel_res
    self.T = T

  def thick_mesh(self, file, decimate_ratio):
    mesh = trimesh.load_mesh(file, process=False)
    V, F = mesh.vertices, mesh.faces

    bbox_min = V.min(0)
    bbox_max = V.max(0)
    self.origin_bbox_min = bbox_min
    self.origin_bbox_max = bbox_max
    V = (V - bbox_min) / (bbox_max - bbox_min) # [0, 1]
    V = V * (1 - 2*self.eps) + self.eps # [eps, 1-eps]
    tris = torch.from_numpy(V[F]).float().cuda()

    grid_udf = torchcumesh2sdf.get_udf(tris=tris, R=self.voxel_res, band=self.band)
    grid_sdf = grid_udf - self.eps

    diso_dmc = diso.DiffDMC().cuda()
    vertices, faces = diso_dmc.forward(grid_udf, isovalue=self.eps, normalize=False)

    bbox_min = torch.from_numpy(bbox_min).float().cuda()
    bbox_max = torch.from_numpy(bbox_max).float().cuda()
    bmin, _ = vertices.min(0)
    bmax, _ = vertices.max(0)
    vertices = (vertices - bmin) / (bmax - bmin)
    vertices = vertices * (bbox_max - bbox_min) + bbox_min

    decimator = OBJMeshDecimator()
    vertices, faces = decimator.decimate_mesh_ratio(vertices, faces.type(torch.int32), decimate_ratio, use_area=True, boundary_weight=5.0)

    return vertices, faces, grid_sdf

  def thin_mesh(self, vertices, faces):
    V_min = vertices.min(0)
    V_max = vertices.max(0)
    vertices = (vertices - V_min) / (V_max - V_min) # [0, 1]
    vertices = vertices * (1 - 2*self.eps) + self.eps

    tris = torch.from_numpy(vertices[faces]).float().cuda()
    udf = torchcumesh2sdf.get_udf(tris, self.voxel_res, self.band)
    diso_mc = diso.DiffDMC().cuda()
    vertices, faces = diso_mc.forward(udf, isovalue=self.eps, normalize=False) 


    vertices = vertices.cpu().numpy()
    faces = faces.cpu().numpy()

    v_min = vertices.min(0)
    v_max = vertices.max(0)
    vertices = (vertices - v_min) / (v_max - v_min)
    vertices = vertices * (V_max - V_min) + V_min

    vertices = vertices.astype(np.float32)
    faces = faces.astype(np.int32)

    mesh = trimesh.Trimesh(vertices, faces)
    components = mesh.split(only_watertight=False)
    bbox = []
    for c in components:
        bbmin = c.vertices.min(0)
        bbmax = c.vertices.max(0)
        bbox.append((bbmax - bbmin).max())
    max_component = np.argmax(bbox)
    mesh = components[max_component]

    vertices = mesh.vertices.astype(np.float32)
    faces = mesh.faces.astype(np.int32)

    return vertices, faces

  def graph_cut(self, internal_faces, labels, out_tets):
    adj = [f.tet_indices for f in internal_faces]
    area = [f.area for f in internal_faces]
    N = len(labels)
    E = len(adj)

    g = maxflow.Graph[int](N, E)
    nodes = g.add_nodes(N)
    for i in range(N):
        if labels[i] == 0:
            g.add_tedge(nodes[i], 1e18, 0)
        elif i in out_tets:
            g.add_tedge(nodes[i], 0, 1e18)
        else:
            g.add_tedge(nodes[i], 0, 0)
    for k in range(E):
        i, j = adj[k]
        a = area[k]
        pen = a if labels[i] != labels[j] else a * (1 + self.T)
        g.add_edge(nodes[i], nodes[j], int(pen), int(pen))
    g.maxflow()
    new_labels = np.array([g.get_segment(node) for node in nodes], dtype=np.int64)
    return new_labels


  def remesh(self, input_file_path, output_file_path, decimate_ratio):
    start = time.time()
    output_dir = os.path.dirname(output_file_path)
    if output_dir:
      os.makedirs(output_dir, exist_ok=True)
    thick_mesh_v, thick_mesh_f, sdf = self.thick_mesh(input_file_path, decimate_ratio)
    print("Tetrahedralizing...")
    tet_verts, tets = cpp.tetrahedralize(thick_mesh_v)
    internal_faces, outer_faces = cpp.build_adjacency_map(tet_verts, tets)
    out_tets = cpp.search_out_tet(internal_faces, tets.shape[0])
    sdf_np = sdf.detach().cpu().numpy().astype(np.float64).reshape(-1)
    initial_labels = cpp.init_labels(internal_faces, tet_verts, tets, sdf_np, self.voxel_res, self.origin_bbox_min, self.origin_bbox_max)
    print("Graph cutting...")
    new_labels = self.graph_cut(internal_faces, initial_labels, out_tets)
    gc_v, gc_f = cpp.surface_extraction(internal_faces, new_labels, tet_verts, tets, outer_faces)
    thin_mesh_v, thin_mesh_f = self.thin_mesh(gc_v, gc_f)
    repaired_mesh = trimesh.Trimesh(thin_mesh_v, thin_mesh_f)
    print("Final mesh:", repaired_mesh.is_watertight)
    print(f"Time:{time.time() - start}")
    repaired_mesh.export(output_file_path)

import torch
import cppmodules as module
import time

def mesh_decimation_(vertex_in, face_in, geometry_in, nv_in, mf_in, nv_out, useArea=True, wgtBnd=5):
    '''
    inputs:
        vertex_in:   (batch_npoints, 3+) float32 array, concatenated points with/without features
        face_in:     (batch_nfaces, 3) int32 array, concatenated triangular faces
        geometry_in: (batch_nfaces, 5) float32 array, geometrics of each face which is
                                          composed of [normal=[nx,ny,nz],intercept=d,area]
        nv_in:       (batch,) int32 vector, point/vertex number of each sample in the batch
        mf_in:       (batch,) int32 vector, face number of each sample in the batch
        nv_out:      (batch,) int32 vector, expected number of points/vertices to output of each sample
        wgtBnd:      float scalar, weight boundary quadric error, (>1) preserves boundary edges
    returns:
        vertex_out:   (batch_mpoints, 3) float32 array, concatenated points with/without features
        face_out:     (batch_mfaces, 3) int32 array, concatenated triangular faces
        geometry_out: (batch_mfaces, 5) float32 array, geometrics of each output face which is
                                           composed of [normal=[nx,ny,nz],intercept=d,area]
        nv_out:       (batch,) int32 vector, point/vertex number of each sample in the batch
        mf_out:       (batch,) int32 vector, face number of each sample in the batch
        vtReplace:   (batch_npoints,) int32 array, negative values (remove minus '-') for vertex to be
                                          contracted in each cluster; zero for vertex no change because it
                                          forms a cluster by itself; positive values recording the cluster
                                          size excluding the vertex itself
        vtMap:       (batch_npoints,) int32 array, contracted/degenerated vertices got mapping to -1,
                                          the valid vertices got mapping start from 0
    '''
    nv2Remove = nv_in - nv_out
    repIn = torch.zeros([vertex_in.shape[0]], dtype=torch.int32, device=nv_in.get_device())
    mapIn = torch.arange(repIn.shape[0], dtype=torch.int32, device=nv_in.get_device())

    useArea = torch.tensor(useArea)
    wgtBnd = torch.tensor(wgtBnd)

    while torch.any(nv2Remove>0):
        nvIn_cumsum = torch.cumsum(nv_in, dim=-1, dtype=torch.int32)
        mfIn_cumsum = torch.cumsum(mf_in, dim=-1, dtype=torch.int32)

        vertexOut, faceOut, isDegenerate, repOut, mapOut, \
        nvOut, mfOut = module.simplify(vertex_in, face_in, geometry_in, \
                                       nvIn_cumsum, mfIn_cumsum, nv2Remove, \
                                       useArea, wgtBnd)
        face_in = faceOut[~isDegenerate,:]
        vertex_in = vertexOut[mapOut>=0,:]
        geometry_in = compute_triangle_geometry_(vertex_in, face_in)
        nv2Remove = nv2Remove - (nv_in - nvOut)
        repIn, mapIn = combine_clusters_(repIn, mapIn, repOut, mapOut)
        nv_in, mf_in = nvOut, mfOut

    return vertex_in, face_in, geometry_in, nv_in, mf_in, repIn, mapIn


def combine_clusters_(repA, mapA, repB, mapB):
    '''
       inputs:
            repA: (batch_points,) int32 array, vertex clustering information of LARGE input
            mapA: (batch_points,) int32 array, vertex mappinging information of LARGE input
            repB: (batch_points,) int32 array, vertex clustering information of SMALL/decimated input
            mapB: (batch_points,) int32 array, vertex mappinging information of SMALL/decimated input
       returns:
            repComb: (batch_points,) int32 array, vertex clustering information after merging LARGE/SMALL input
            mapComb: (batch_points,) int32 array, vertex mappinging information after merging LARGE/SMALL input
    '''
    repComb, mapComb = module.combine_clusters(repA, mapA, repB, mapB)
    return repComb, mapComb


def compute_triangle_geometry_(vertex, face):
    '''
    Compute normals of the facets (0-order: no interpolation)
    '''
    vertex = vertex[:,:3]
    face = face.to(torch.long)
    vec10 = vertex[face[:,1],:] - vertex[face[:,0],:]
    vec20 = vertex[face[:,2],:] - vertex[face[:,0],:]
    raw_normal = torch.cross(vec10,vec20,-1)
    l2norm = torch.sqrt(torch.sum(raw_normal**2,dim=-1,keepdim=True))
    area = l2norm/2
    normal = raw_normal/(l2norm+1e-10)
    v1 = vertex[face[:,0],:]
    d = -torch.sum(normal*v1,dim=-1,keepdim=True)
    geometry = torch.cat([normal,d,area],dim=-1)
    return geometry


def count_vertex_adjface_(face, vtMap, vertexOut):
    '''
        Count the number of adjacent faces for output vertices, i.e. {vtMap[i] | vtMap[i]>=0},
    '''
    nfCount = module.count_vertex_adjface(face, vtMap, vertexOut[:,:3].contiguous())
    return nfCount


class OBJMeshDecimator:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")


    def decimate_single_mesh(self, vertices, faces,
                           target_vertices: int, use_area: bool = True,
                           boundary_weight: float = 5.0) -> tuple:


        start_time = time.time()
        geometry_start = time.time()
        geometry_tensor = compute_triangle_geometry_(vertices, faces)
        geometry_time = time.time() - geometry_start
        nv_in = torch.tensor([len(vertices)], dtype=torch.int32, device=self.device)
        mf_in = torch.tensor([len(faces)], dtype=torch.int32, device=self.device)
        nv_out = torch.tensor([target_vertices], dtype=torch.int32, device=self.device)

        print(f"Original: {len(vertices)} vertices, {len(faces)} faces")
        print(f"Target: {target_vertices} vertices")
        decimation_start = time.time()
        result = mesh_decimation_(
            vertices, faces, geometry_tensor,
            nv_in, mf_in, nv_out, use_area, boundary_weight
        )
        decimation_time = time.time() - decimation_start

        vertex_dec, face_dec, _, _, _, _, _ = result
        conversion_start = time.time()
        decimated_vertices = vertex_dec.cpu().numpy()
        decimated_faces = face_dec.cpu().numpy()
        conversion_time = time.time() - conversion_start

        total_time = time.time() - start_time
        print(f"Result: {len(decimated_vertices)} vertices, {len(decimated_faces)} faces")
        print(f"Timing breakdown:")
        print(f"  - Geometry computation: {geometry_time:.3f}s")
        print(f"  - Decimation algorithm: {decimation_time:.3f}s")
        print(f"  - Data conversion: {conversion_time:.3f}s")
        print(f"  - Total time: {total_time:.3f}s")
        vertices_per_sec = len(vertices) / total_time
        faces_per_sec = len(faces) / total_time

        return decimated_vertices, decimated_faces

    def decimate_mesh_ratio(self, vertices, faces,
                           reduction_ratio: float = 0.5, use_area: bool = True,
                           boundary_weight: float = 5.0) -> tuple:
        target_vertices = int(len(vertices) * (1 - reduction_ratio))
        target_vertices = max(target_vertices, 4)

        return self.decimate_single_mesh(vertices, faces, target_vertices,
                                       use_area, boundary_weight)

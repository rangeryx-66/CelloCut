#include "surfaceExtraction.h"
#include <unordered_set>
#include <unordered_map>
#include <algorithm>
#include <chrono>
#include <iostream>

double orient3d(const Vector3d& a, const Vector3d& b, const Vector3d& c, const Vector3d& d) {
    return (b - a).cross(c - a).dot(d - a);
}

std::pair<MatrixXd, MatrixXi> surface_extraction(
    const InternalFace &internal_faces,
    const std::vector<bool> &labels,
    const MatrixXd &tet_verts,
    const MatrixXi &tets,
    const OuterFace &outers)
{
  MatrixXd surf_verts;
  MatrixXi surf_faces;
  auto start = std::chrono::high_resolution_clock::now();

  std::vector<Vector3i> faces;

  // 内部面
  for (const auto &f : internal_faces)
  {
    int t0 = f.tet_indices(0);
    int t1 = f.tet_indices(1);
    
    // Only extract boundary faces
    if (labels[t0] == labels[t1])
      continue;

    // Determine which tet is "inside" (0) and which is "outside" (1)
    // We want normal to point from Inside -> Outside.
    int inside_tet_idx = (labels[t0] == 0) ? t0 : t1;
    
    // Get face vertices (currently sorted)
    Vector3i tri = f.face_nodes;
    Vector3d v0 = tet_verts.row(tri(0));
    Vector3d v1 = tet_verts.row(tri(1));
    Vector3d v2 = tet_verts.row(tri(2));

    // Find the 4th vertex of the inside tet
    int p_idx = -1;
    for(int k=0; k<4; ++k) {
        int idx = tets(inside_tet_idx, k);
        if (idx != tri(0) && idx != tri(1) && idx != tri(2)) {
            p_idx = idx;
            break;
        }
    }
    
    if (p_idx == -1) {
        // Should not happen if data is consistent
        continue; 
    }
    Vector3d p = tet_verts.row(p_idx);

    // Check orientation
    // We want normal (v1-v0)x(v2-v0) to point AWAY from p.
    // So (v1-v0)x(v2-v0) . (p-v0) should be < 0.
    double vol = orient3d(v0, v1, v2, p);
    
    if (vol < 0) {
        // Correct orientation
        faces.push_back(Vector3i(tri(0), tri(1), tri(2)));
    } else {
        // Flip orientation
        faces.push_back(Vector3i(tri(0), tri(2), tri(1)));
    }
  }

  // 外部面
  for (const auto &[face, tet_idx] : outers)
  {
    if (labels[tet_idx] == 0) // If tet is inside, this is a boundary face
    {
        // We want normal pointing OUT of the tet (which is inside).
        // So normal points away from the 4th vertex of tet_idx.
        
        Vector3i tri = face; // These might be sorted or not, let's assume sorted from build_adjacency_map
        Vector3d v0 = tet_verts.row(tri(0));
        Vector3d v1 = tet_verts.row(tri(1));
        Vector3d v2 = tet_verts.row(tri(2));

        int p_idx = -1;
        for(int k=0; k<4; ++k) {
            int idx = tets(tet_idx, k);
            if (idx != tri(0) && idx != tri(1) && idx != tri(2)) {
                p_idx = idx;
                break;
            }
        }
        
        if (p_idx == -1) continue;
        Vector3d p = tet_verts.row(p_idx);

        double vol = orient3d(v0, v1, v2, p);
        if (vol < 0) {
            faces.push_back(Vector3i(tri(0), tri(1), tri(2)));
        } else {
            faces.push_back(Vector3i(tri(0), tri(2), tri(1)));
        }
    }
  }

  std::unordered_set<int> used_set;
  for (const auto &f : faces)
    for (int k = 0; k < 3; ++k)
      used_set.insert(f(k));

  std::vector<int> used_idx(used_set.begin(), used_set.end());
  std::sort(used_idx.begin(), used_idx.end());

  std::unordered_map<int, int> remap;
  for (size_t i = 0; i < used_idx.size(); ++i)
    remap[used_idx[i]] = static_cast<int>(i);

  surf_verts.resize(used_idx.size(), 3);
  for (size_t i = 0; i < used_idx.size(); ++i)
    surf_verts.row(i) = tet_verts.row(used_idx[i]);

  surf_faces.resize(faces.size(), 3);
  for (int i = 0; i < faces.size(); ++i)
    for (int j = 0; j < 3; ++j)
      surf_faces(i, j) = remap[faces[i](j)];

  auto end = std::chrono::high_resolution_clock::now();
  return {surf_verts, surf_faces};
}

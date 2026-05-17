#include "tetrahedralize.h"
#include <unordered_map>

struct VecHash
{
  size_t operator()(const std::vector<int> &v) const noexcept
  {
    size_t seed = v.size();
    for (int x : v)
    {
      seed ^= std::hash<int>()(x) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
    }
    return seed;
  }
};

struct VecEqual
{
  bool operator()(const std::vector<int> &a, const std::vector<int> &b) const noexcept
  {
    return a.size() == b.size() && std::equal(a.begin(), a.end(), b.begin());
  }
};

std::pair<MatrixXd, MatrixXi> tetrahedralize(const MatrixXd &vertices)
{
  Delaunay dt;
  std::vector<Point3D> points;
  for (int i = 0; i < vertices.rows(); ++i)
    points.emplace_back(vertices(i, 0), vertices(i, 1), vertices(i, 2));
  dt.insert(points.begin(), points.end());

  std::map<Point3D, int> pointIndex;
  for (int i = 0; i < (int)points.size(); ++i)
    pointIndex[points[i]] = i;

  std::vector<Vector4i> tets_vec;
  for (auto cell = dt.finite_cells_begin(); cell != dt.finite_cells_end(); ++cell)
  {
    Vector4i tet;
    for (int j = 0; j < 4; ++j)
      tet(j) = pointIndex[cell->vertex(j)->point()];
    tets_vec.push_back(tet);
  }

  MatrixXi tets(tets_vec.size(), 4);
  for (int i = 0; i < tets_vec.size(); ++i)
    tets.row(i) = tets_vec[i].transpose();

  return {vertices, tets};
}

std::pair<InternalFace, OuterFace> build_adjacency_map(const MatrixXd &vertices, const MatrixXi &tets)
{
  InternalFace internal_faces;
  OuterFace outer_faces;
  std::unordered_map<std::vector<int>, int, VecHash, VecEqual>
      face_to_tet;

  for (int i = 0; i < tets.rows(); ++i)
  {
    auto faces = get_tetrahedron_faces(tets.row(i));
    for (const auto &f : faces)
    {
      std::vector<int> key = {f(0), f(1), f(2)};
      std::sort(key.begin(), key.end());

      auto it = face_to_tet.find(key);
      if (it != face_to_tet.end())
      {
        int other_tet = it->second;
        Face internal_face;
        internal_face.tet_indices = Vector2i(std::min(i, other_tet), std::max(i, other_tet));
        internal_face.face_nodes = Vector3i(key[0], key[1], key[2]);
        internal_face.area = compute_face_area(internal_face.face_nodes, vertices);
        internal_faces.push_back(internal_face);
        face_to_tet.erase(it);
      }
      else
      {
        face_to_tet[key] = i;
      }
    }
  }

  for (const auto &[key, tet_idx] : face_to_tet)
    outer_faces.emplace_back(Vector3i(key[0], key[1], key[2]), tet_idx);

  return {internal_faces, outer_faces};
}

std::vector<int> search_out_tet(const InternalFace &internal_faces, int tet_count)
{
  std::vector<int> cf(tet_count, 0);
  for (const auto &f : internal_faces)
  {
    int i = f.tet_indices(0);
    int j = f.tet_indices(1);
    cf[i]++;
    cf[j]++;
  }
  std::vector<int> out_tet;
  for (int i = 0; i < tet_count; i++)
    if (cf[i] < 4)
      out_tet.push_back(i);
  return out_tet;
}

float compute_face_area(const Vector3i &face_vertices, const MatrixXd &vertices)
{
  Vector3d v0 = vertices.row(face_vertices(0));
  Vector3d v1 = vertices.row(face_vertices(1));
  Vector3d v2 = vertices.row(face_vertices(2));
  return 1E7 * 0.5 * ((v1 - v0).cross(v2 - v0)).norm();
}

std::vector<Vector3i> get_tetrahedron_faces(const Vector4i &tet)
{
  return {
      Vector3i(tet(0), tet(1), tet(2)),
      Vector3i(tet(0), tet(1), tet(3)),
      Vector3i(tet(0), tet(2), tet(3)),
      Vector3i(tet(1), tet(2), tet(3))};
}
#pragma once
#include "args.h"
#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Delaunay_triangulation_3.h>

using K = CGAL::Exact_predicates_inexact_constructions_kernel;
using Delaunay = CGAL::Delaunay_triangulation_3<K>;
using Point3D = K::Point_3;


std::pair<MatrixXd, MatrixXi> tetrahedralize(const MatrixXd &vertices);


std::pair<InternalFace, OuterFace> build_adjacency_map(const MatrixXd &vertices, const MatrixXi &tets);


std::vector<int> search_out_tet(const InternalFace &internal_faces, int tet_count);


float compute_face_area(const Vector3i &face_vertices, const MatrixXd &vertices);

std::vector<Vector3i> get_tetrahedron_faces(const Vector4i &tet);

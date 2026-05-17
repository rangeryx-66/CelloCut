#pragma once
#include "args.h"
#include <unordered_map>
#include <unordered_set>
#include <algorithm>

std::pair<MatrixXd, MatrixXi> surface_extraction(
    const InternalFace &internal_faces,
    const std::vector<bool> &labels,
    const MatrixXd &tet_verts,
    const MatrixXi &tets,
    const OuterFace &outers);

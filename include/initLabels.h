#pragma once
#include "args.h"
#include <algorithm>
#include <cuda_runtime.h>
#include <chrono>

#define CUDA_CHECK(err)                                                                                    \
    if (err != cudaSuccess)                                                                                \
    {                                                                                                      \
        fprintf(stderr, "CUDA Error: %s at line %d of %s\n", cudaGetErrorString(err), __LINE__, __FILE__); \
        exit(EXIT_FAILURE);                                                                                \
    }

std::vector<bool> init_labels(
    const InternalFace &internal_faces,
    MatrixXd &tet_V,
    MatrixXi &tet_T,
    VectorXd &sdf,
    int voxel_res,
    const Vector3d &origin_min,
    const Vector3d &origin_max);

std::vector<double> tet_centers(const MatrixXd &V,
                                const MatrixXi &T,
                                const Vector3d &origin_min,
                                const Vector3d &origin_max);

std::vector<double> sdf_query(
    const VectorXd &sdf,
    int voxel_res,
    const std::vector<double> &points);

std::vector<int> search_out_tet(const InternalFace &internal_faces,
                                int tet_count);

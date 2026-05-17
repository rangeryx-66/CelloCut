#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <vector>
#include <string>
#include <tuple>
#include <map>
#include <array>
#include <torch/extension.h>

using Eigen::MatrixXd;
using Eigen::MatrixXi;
using Eigen::Vector2i;
using Eigen::Vector3d;
using Eigen::Vector3i;
using Eigen::Vector4i;
using Eigen::VectorXd;
using Eigen::VectorXi;

struct Face
{
  Vector2i tet_indices; 
  Vector3i face_nodes;  
  float area = 0.0;
};

using InternalFace = std::vector<Face>;
using OuterFace = std::vector<std::pair<Vector3i, int>>;

#define CHECK_CUDA(x) TORCH_CHECK(x.is_cuda(), #x " must be a CUDA tensor")
#define CHECK_CONTIGUOUS(x) TORCH_CHECK(x.is_contiguous(), #x " must be contiguous")
#define CHECK_INPUT(x) \
    CHECK_CUDA(x);     \
    CHECK_CONTIGUOUS(x)

#pragma once
#include <torch/extension.h>

torch::Tensor get_udf_grad_cu(
    const torch::Tensor df,
    const torch::Tensor points,
    const float eps);
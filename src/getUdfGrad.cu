#include "getUdfGrad.h"
#include <cmath>

template <typename scalar_t>
__device__ scalar_t ComputeSDF(
    const torch::PackedTensorAccessor<scalar_t, 3, torch::RestrictPtrTraits, size_t> df,
    const scalar_t x,
    const scalar_t y,
    const scalar_t z)
{
  const int shape_X = df.size(0);
  const int shape_Y = df.size(1);
  const int shape_Z = df.size(2);

  const scalar_t vcx = x * (shape_X - 1);
  const scalar_t vcy = y * (shape_Y - 1);
  const scalar_t vcz = z * (shape_Z - 1);

  const int ix = static_cast<int>(floor(vcx));
  const int iy = static_cast<int>(floor(vcy));
  const int iz = static_cast<int>(floor(vcz));

  const scalar_t fx = vcx - ix;
  const scalar_t fy = vcy - iy;
  const scalar_t fz = vcz - iz;

  const int dx[8] = {0, 1, 0, 1, 0, 1, 0, 1};
  const int dy[8] = {0, 0, 1, 1, 0, 0, 1, 1};
  const int dz[8] = {0, 0, 0, 0, 1, 1, 1, 1};

  const scalar_t w[8] = {
      (1 - fx) * (1 - fy) * (1 - fz),
      fx * (1 - fy) * (1 - fz),
      (1 - fx) * fy * (1 - fz),
      fx * fy * (1 - fz),
      (1 - fx) * (1 - fy) * fz,
      fx * (1 - fy) * fz,
      (1 - fx) * fy * fz,
      fx * fy * fz};

  scalar_t sum = 0;
#pragma unroll
  for (int i = 0; i < 8; ++i)
  {
    int vx = ix + dx[i];
    vx = (vx < 0) ? 0 : ((vx > shape_X - 1) ? shape_X - 1 : vx);
    int vy = iy + dy[i];
    vy = (vy < 0) ? 0 : ((vy > shape_Y - 1) ? shape_Y - 1 : vy);
    int vz = iz + dz[i];
    vz = (vz < 0) ? 0 : ((vz > shape_Z - 1) ? shape_Z - 1 : vz);

    sum += w[i] * df[vx][vy][vz];
  }

  return sum;
}

template <typename scalar_t>
__device__ __forceinline__ scalar_t ComputeGrad(
    const scalar_t fw,
    const scalar_t bw,
    const float dist)
{
  return (fw - bw) / dist;
}

template <typename scalar_t>
__global__ void grad_udf_grad_kernel(
    const torch::PackedTensorAccessor<scalar_t, 3, torch::RestrictPtrTraits, size_t> df,
    const torch::PackedTensorAccessor<scalar_t, 2, torch::RestrictPtrTraits, size_t> points,
    const float eps,
    torch::PackedTensorAccessor<scalar_t, 2, torch::RestrictPtrTraits, size_t> points_grad)
{
  const int idx = blockIdx.x * blockDim.x + threadIdx.x;

  if (idx >= points.size(0))
    return;

  const scalar_t x = points[idx][0];
  const scalar_t y = points[idx][1];
  const scalar_t z = points[idx][2];

  scalar_t x_fw = (x + eps) < 1 ? x + eps : 1;
  scalar_t x_bw = (x - eps) > 0 ? x - eps : 0;
  float dist_x = (x + eps) < 1 || (x - eps) > 0 ? 2 * eps : eps;
  scalar_t y_fw = (y + eps) < 1 ? y + eps : 1;
  scalar_t y_bw = (y - eps) > 0 ? y - eps : 0;
  float dist_y = (y + eps) < 1 || (y - eps) > 0 ? 2 * eps : eps;
  scalar_t z_fw = (z + eps) < 1 ? z + eps : 1;
  scalar_t z_bw = (z - eps) > 0 ? z - eps : 0;
  float dist_z = (z + eps) < 1 || (z - eps) > 0 ? 2 * eps : eps;

  scalar_t x_fw_sdf = ComputeSDF(df, x_fw, y, z);
  scalar_t x_bw_sdf = ComputeSDF(df, x_bw, y, z);
  scalar_t y_fw_sdf = ComputeSDF(df, x, y_fw, z);
  scalar_t y_bw_sdf = ComputeSDF(df, x, y_bw, z);
  scalar_t z_fw_sdf = ComputeSDF(df, x, y, z_fw);
  scalar_t z_bw_sdf = ComputeSDF(df, x, y, z_bw);

  scalar_t x_grad = ComputeGrad(x_fw_sdf, x_bw_sdf, dist_x);
  scalar_t y_grad = ComputeGrad(y_fw_sdf, y_bw_sdf, dist_y);
  scalar_t z_grad = ComputeGrad(z_fw_sdf, z_bw_sdf, dist_z);

  scalar_t dv = sqrt(x_grad * x_grad + y_grad * y_grad + z_grad * z_grad);
  points_grad[idx][0] = x_grad / dv;
  points_grad[idx][1] = y_grad / dv;
  points_grad[idx][2] = z_grad / dv;
}

torch::Tensor get_udf_grad_cu(
    const torch::Tensor df,
    const torch::Tensor points,
    const float eps)
{
  auto points_grad = torch::zeros({points.size(0), points.size(1)}, points.options());
  const int threads = 256;
  const int blocks = (points.size(0) + threads - 1) / threads;

  AT_DISPATCH_FLOATING_TYPES(df.scalar_type(), "grad_interpolation_cu",
                             ([&]
                              { grad_udf_grad_kernel<scalar_t><<<blocks, threads>>>(
                                    df.packed_accessor<scalar_t, 3, torch::RestrictPtrTraits, size_t>(),
                                    points.packed_accessor<scalar_t, 2, torch::RestrictPtrTraits, size_t>(),
                                    eps,
                                    points_grad.packed_accessor<scalar_t, 2, torch::RestrictPtrTraits, size_t>()); }));

  return points_grad;
}
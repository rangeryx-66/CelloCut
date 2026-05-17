#include "initLabels.h"

__global__ void trilinearInterpolation(
    const double *points,
    int Q,
    int voxel_res,
    const double *sdf,
    double *output,
    int sdf_size)
{
  int idx = blockIdx.x * blockDim.x + threadIdx.x;
  if (idx >= Q)
    return;

  double x = points[3 * idx];
  double y = points[3 * idx + 1];
  double z = points[3 * idx + 2];


  double vcx = x * (voxel_res - 1);
  double vcy = y * (voxel_res - 1);
  double vcz = z * (voxel_res - 1);

  int ix = static_cast<int>(floor(vcx));
  int iy = static_cast<int>(floor(vcy));
  int iz = static_cast<int>(floor(vcz));

  double fx = vcx - ix;
  double fy = vcy - iy;
  double fz = vcz - iz;


  int dx[8] = {0, 1, 0, 1, 0, 1, 0, 1};
  int dy[8] = {0, 0, 1, 1, 0, 0, 1, 1};
  int dz[8] = {0, 0, 0, 0, 1, 1, 1, 1};

  double w[8] = {
      (1 - fx) * (1 - fy) * (1 - fz),
      fx * (1 - fy) * (1 - fz),
      (1 - fx) * fy * (1 - fz),
      fx * fy * (1 - fz),
      (1 - fx) * (1 - fy) * fz,
      fx * (1 - fy) * fz,
      (1 - fx) * fy * fz,
      fx * fy * fz};

  double sum = 0.0;
  for (int i = 0; i < 8; ++i)
  {
    int vx = ix + dx[i];
    vx = (vx < 0) ? 0 : ((vx > voxel_res - 1) ? voxel_res - 1 : vx);
    int vy = iy + dy[i];
    vy = (vy < 0) ? 0 : ((vy > voxel_res - 1) ? voxel_res - 1 : vy);
    int vz = iz + dz[i];
    vz = (vz < 0) ? 0 : ((vz > voxel_res - 1) ? voxel_res - 1 : vz);

    int flat_idx = (vx * voxel_res + vy) * voxel_res + vz;
    double sdf_val = sdf[flat_idx];

    sum += w[i] * sdf_val;
  }

  output[idx] = sum;
}

std::vector<double> sdf_query(
    const VectorXd &sdf,
    int voxel_res,
    const std::vector<double> &points)
{
  int Q = static_cast<int>(points.size() / 3);
  int sdf_size = voxel_res * voxel_res * voxel_res;

  double *d_sdf = nullptr;
  double *d_points = nullptr;
  double *d_out = nullptr;
  CUDA_CHECK(cudaMalloc(&d_sdf, sdf_size * sizeof(double)));
  CUDA_CHECK(cudaMalloc(&d_points, points.size() * sizeof(double)));
  CUDA_CHECK(cudaMalloc(&d_out, Q * sizeof(double)));

  CUDA_CHECK(cudaMemcpy(d_sdf, sdf.data(), sdf_size * sizeof(double), cudaMemcpyHostToDevice));
  CUDA_CHECK(cudaMemcpy(d_points, points.data(), points.size() * sizeof(double), cudaMemcpyHostToDevice));

  int threads = 256;
  int blocks = (Q + threads - 1) / threads;
  trilinearInterpolation<<<blocks, threads>>>(d_points, Q, voxel_res, d_sdf, d_out, sdf_size);
  CUDA_CHECK(cudaDeviceSynchronize());

  std::vector<double> sdf_vals(Q);
  CUDA_CHECK(cudaMemcpy(sdf_vals.data(), d_out, Q * sizeof(double), cudaMemcpyDeviceToHost));

  CUDA_CHECK(cudaFree(d_sdf));
  CUDA_CHECK(cudaFree(d_points));
  CUDA_CHECK(cudaFree(d_out));

  return sdf_vals;
}

std::vector<double> tet_centers(const MatrixXd &V,
                                const MatrixXi &T,
                                const Vector3d &origin_min,
                                const Vector3d &origin_max)
{
  int Nt = static_cast<int>(T.rows());
  std::vector<double> centers(Nt * 3);

  for (int ti = 0; ti < Nt; ti++)
  {
    double cx = 0, cy = 0, cz = 0;
    for (int k = 0; k < 4; k++)
    {
      int vid = T(ti, k);
      cx += V(vid, 0);
      cy += V(vid, 1);
      cz += V(vid, 2);
    }
    cx /= 4.0;
    cy /= 4.0;
    cz /= 4.0;

    double denomx = origin_max(0) - origin_min(0);
    double denomy = origin_max(1) - origin_min(1);
    double denomz = origin_max(2) - origin_min(2);

    centers[ti * 3 + 0] = (cx - origin_min(0)) / denomx;
    centers[ti * 3 + 1] = (cy - origin_min(1)) / denomy;
    centers[ti * 3 + 2] = (cz - origin_min(2)) / denomz;
  }
  return centers;
}

std::vector<bool> init_labels(
    const InternalFace &internal_faces,
    MatrixXd &tet_V,
    MatrixXi &tet_T,
    VectorXd &sdf,
    int voxel_res,
    const Vector3d &origin_min,
    const Vector3d &origin_max)
{
  auto centers = tet_centers(tet_V, tet_T, origin_min, origin_max);

  auto dist = sdf_query(sdf, voxel_res, centers);

  int N = static_cast<int>(dist.size());
  std::vector<bool> labels(N);

  const double threshold = -1e-4;
  for (int i = 0; i < N; i++)
    labels[i] = (dist[i] <= threshold) ? 0 : 1;
  return labels;
}
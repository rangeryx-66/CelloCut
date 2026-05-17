# CelloCut

Official implementation of **CelloCut: Constructive Watertight Remeshing via Tetrahedral Cell Cuts**.

CelloCut converts defective meshes with holes, self-intersections, non-manifold elements, or ambiguous thin structures into compact watertight solids. It formulates watertight conversion as a volumetric partitioning problem over a tetrahedral cell complex and solves the resulting labeling problem with graph-cut optimization.

## Installation

The code has been tested on Linux with Python 3.10.18 and CUDA 12.4.

```bash
conda create -n CelloCut python=3.10
conda activate CelloCut
bash build.sh
```

`build.sh` installs the Python requirements, builds the CUDA UDF extension in `cumesh2sdf`, installs CGAL-related dependencies from conda-forge, and compiles the C++/CUDA extension into `build/`.

If CGAL is installed outside the active conda environment, set `CGAL_DIR` before building:

```bash
export CGAL_DIR=/path/to/lib/cmake/CGAL
bash build.sh
```

## Usage

Run CelloCut on a single mesh:

```bash
python example.py --input assets/bad_doll.obj --output results/output.obj
```

Run CelloCut on a directory of OBJ files:

```bash
python example_batch.py --input_dir path/to/input_objs --output_dir path/to/results
```

### Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--input` | `assets/bad_doll.obj` | Input mesh path for single-model inference. |
| `--output` | `results/output.obj` | Output mesh path for single-model inference. |
| `--input_dir` | `dataset/benchmark` | Input directory for batch inference. |
| `--output_dir` | `dataset/ours` | Output directory for batch inference. |
| `--voxel_res` | `512` | UDF grid resolution. The paper uses a `512^3` grid. |
| `--decimate_ratio` | `0.95` | Fraction of proxy mesh faces removed before tetrahedralization. |
| `--lamda_fill`, `--lambda_fill` | `20` | Filling regularization weight, denoted as `lambda_fill` in the paper. |

The default parameters match the paper: `voxel_res=512`, thickening offset `epsilon=1/512`, `decimate_ratio=0.95`, and `lambda_fill=20`.

## Benchmark

The CelloCut benchmark is available on Hugging Face:

[https://huggingface.co/datasets/rangeryx2005/CelloCut_Benchmark](https://huggingface.co/datasets/rangeryx2005/CelloCut_Benchmark)

## Citation

```bibtex
@article{yang2026cellocut,
  title   = {CelloCut: Constructive Watertight Remeshing via Tetrahedral Cell Cuts},
  author  = {Yang, Xuan and Zeng, Yuhang and Fang, Dinglong and Tang, Guochuan and Long, Xiao-Xiao and Lin, Cheng},
  journal = {arXiv preprint},
  year    = {2026}
}
```

The BibTeX entry will be updated after the arXiv identifier is available.

## Third-Party Components

This repository includes third-party components under their original licenses. In particular, `cumesh2sdf` is licensed under Apache-2.0, and the code under `third_party/` keeps its upstream Eigen and libigl license terms. The metric utilities in `metric.py` are adapted from PyTorch3D/Facebook code and retain the original copyright notice.

## License

The CelloCut source code is released under the Apache License 2.0. See [LICENSE](LICENSE) for details. Third-party components retain their own licenses.

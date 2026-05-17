#!/bin/bash

set -euo pipefail

PYTHON_BIN="${PYTHON:-python}"
PIP_BIN="${PIP:-pip}"

command -v "${PYTHON_BIN}" >/dev/null 2>&1 || { echo "Error: python is not found. Activate the target environment first."; exit 1; }
command -v "${PIP_BIN}" >/dev/null 2>&1 || { echo "Error: pip is not found. Activate the target environment first."; exit 1; }

"${PIP_BIN}" install -r requirements.txt
cd cumesh2sdf
"${PIP_BIN}" install . --no-build-isolation
cd ..

if command -v conda >/dev/null 2>&1; then
  conda install -y -c conda-forge gmp mpfr cgal
else
  echo "Warning: conda command is not available; assuming gmp, mpfr, and cgal are already installed in the active environment."
fi

mkdir -p build
cd build

rm -rf *
cmake ..
make -j"$(nproc)"

echo "Build Completed!"

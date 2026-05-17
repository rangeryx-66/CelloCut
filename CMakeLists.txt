cmake_minimum_required(VERSION 3.18)
project(PROJ_CPP LANGUAGES CXX CUDA)
add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0)

if(DEFINED ENV{CONDA_PREFIX})
    set(CONDA_DIR "$ENV{CONDA_PREFIX}")
    set(PYTHON_EXECUTABLE "${CONDA_DIR}/bin/python")
    
    execute_process(
        COMMAND ${PYTHON_EXECUTABLE} -m pybind11 --cmakedir
        OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    list(APPEND CMAKE_PREFIX_PATH ${PYBIND11_CMAKE_DIR} ${CONDA_DIR})

    execute_process(
        COMMAND ${PYTHON_EXECUTABLE} -c "import torch; from torch.utils.cpp_extension import include_paths; print(';'.join(include_paths()))"
        OUTPUT_VARIABLE TORCH_INCLUDE_DIRS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    execute_process(
        COMMAND ${PYTHON_EXECUTABLE} -c "import torch; import os; print(os.path.join(os.path.dirname(torch.__file__), 'lib'))"
        OUTPUT_VARIABLE TORCH_LIB_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    
    execute_process(
        COMMAND ${PYTHON_EXECUTABLE} -c "from sysconfig import get_paths; print(get_paths()['include'])"
        OUTPUT_VARIABLE PYTHON_INCLUDE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)
find_package(CUDAToolkit REQUIRED)
find_package(CGAL REQUIRED QUIET HINTS ${CONDA_DIR})

find_library(GMP_LIB NAMES gmp HINTS "${CONDA_DIR}/lib")
find_library(MPFR_LIB NAMES mpfr HINTS "${CONDA_DIR}/lib")
find_library(TORCH_PYTHON_LIB NAMES torch_python HINTS ${TORCH_LIB_DIR} NO_DEFAULT_PATH)
find_library(TORCH_LIB        NAMES torch        HINTS ${TORCH_LIB_DIR} NO_DEFAULT_PATH)
find_library(C10_LIB          NAMES c10          HINTS ${TORCH_LIB_DIR} NO_DEFAULT_PATH)


set(ALL_INCLUDES
    ${PYTHON_INCLUDE_DIR}
    ${TORCH_INCLUDE_DIRS}
    ${PROJECT_SOURCE_DIR}/include
    ${PROJECT_SOURCE_DIR}/third_party/eigen
    ${PROJECT_SOURCE_DIR}/third_party/libigl/include
    ${PROJECT_SOURCE_DIR}
    ${CONDA_DIR}/include
    ${CUDAToolkit_INCLUDE_DIRS}
)

file(GLOB SRC_CU  ${PROJECT_SOURCE_DIR}/src/*.cu)
add_library(cuda_objs OBJECT ${SRC_CU})

target_include_directories(cuda_objs PRIVATE ${ALL_INCLUDES})

set_target_properties(cuda_objs PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_compile_options(cuda_objs PRIVATE
    $<$<COMPILE_LANGUAGE:CUDA>:--expt-relaxed-constexpr -lineinfo -O3 -w>
)

file(GLOB SRC_CPP ${PROJECT_SOURCE_DIR}/src/*.cpp)
pybind11_add_module(cppmodules ${SRC_CPP})
target_sources(cppmodules PRIVATE $<TARGET_OBJECTS:cuda_objs>)

target_include_directories(cppmodules PRIVATE ${ALL_INCLUDES})

target_link_libraries(cppmodules PRIVATE
    ${CUDAToolkit_LIBRARIES}
    ${GMP_LIB}
    ${MPFR_LIB}
    ${TORCH_PYTHON_LIB}
    ${TORCH_LIB}
    ${C10_LIB}
    CGAL::CGAL
)

set_target_properties(cppmodules PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
    CUDA_RESOLVE_DEVICE_SYMBOLS ON
    CUDA_ARCHITECTURES "60;70;75;80;86"
    LIBRARY_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/build
)

target_compile_options(cppmodules PRIVATE $<$<COMPILE_LANGUAGE:CXX>:-w -O3>)
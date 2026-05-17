#pragma once
#include <vector>
#include <algorithm>
#include <cmath>
#include <cstdint>

struct Vertex {
    float x, y, z;
    uint32_t originalIndex; 
};

struct SimpleVertex {
    float x, y, z;
};

std::pair<std::vector<float>, std::vector<uint32_t>> merge_vertices(
    const std::vector<float>& inRawFloats,
    const std::vector<uint32_t>& inIndices,
    float threshold
);
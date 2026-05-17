#include "merge.h"

std::pair<std::vector<float>, std::vector<uint32_t>> merge_vertices(
    const std::vector<float>& inRawFloats,
    const std::vector<uint32_t>& inIndices,
    float threshold
) {
    std::vector<float> outVertices;
    std::vector<uint32_t> outIndices;
    
    size_t vertexCount = inRawFloats.size() / 3;
    float thresholdSq = threshold * threshold;

    std::vector<Vertex> sortedVerts;
    sortedVerts.reserve(vertexCount);
    for (size_t i = 0; i < vertexCount; ++i) {
        sortedVerts.push_back({
            inRawFloats[i * 3], 
            inRawFloats[i * 3 + 1], 
            inRawFloats[i * 3 + 2], 
            (uint32_t)i
        });
    }

    std::sort(sortedVerts.begin(), sortedVerts.end(), [](const Vertex& a, const Vertex& b) {
        if (a.x != b.x) return a.x < b.x;
        if (a.y != b.y) return a.y < b.y;
        return a.z < b.z;
    });

    std::vector<uint32_t> oldToNewMap(vertexCount);
    std::vector<SimpleVertex> uniqueVertices;
    
    std::vector<int> sortedToUniqueMap(vertexCount, -1);

    for (size_t i = 0; i < vertexCount; ++i) {
        if (sortedToUniqueMap[i] != -1) continue;

        const Vertex& v1 = sortedVerts[i];
        
        uint32_t newIndex = (uint32_t)uniqueVertices.size();
        uniqueVertices.push_back({v1.x, v1.y, v1.z});
        sortedToUniqueMap[i] = newIndex;
        
        oldToNewMap[v1.originalIndex] = newIndex;

        for (size_t j = i + 1; j < vertexCount; ++j) {
            const Vertex& v2 = sortedVerts[j];

            if (v2.x - v1.x > threshold) break;

            if (sortedToUniqueMap[j] != -1) continue;

            if (std::abs(v2.y - v1.y) > threshold) continue;
            if (std::abs(v2.z - v1.z) > threshold) continue;

            float dx = v2.x - v1.x;
            float dy = v2.y - v1.y;
            float dz = v2.z - v1.z;
            if (dx*dx + dy*dy + dz*dz <= thresholdSq) {
                sortedToUniqueMap[j] = newIndex;
                oldToNewMap[v2.originalIndex] = newIndex;
            }
        }
    }

    outVertices.clear();
    outVertices.reserve(uniqueVertices.size() * 3);
    for (const auto& v : uniqueVertices) {
        outVertices.push_back(v.x);
        outVertices.push_back(v.y);
        outVertices.push_back(v.z);
    }

    outIndices.clear();
    outIndices.reserve(inIndices.size());
    for (size_t i = 0; i < inIndices.size(); i += 3) {
        uint32_t i0 = oldToNewMap[inIndices[i]];
        uint32_t i1 = oldToNewMap[inIndices[i + 1]];
        uint32_t i2 = oldToNewMap[inIndices[i + 2]];


        if (i0 != i1 && i1 != i2 && i2 != i0) {
            outIndices.push_back(i0);
            outIndices.push_back(i1);
            outIndices.push_back(i2);
        }
    }

    return {outVertices, outIndices};
}
import json
import struct
import sys
from pathlib import Path


def parse_obj(path):
    vertices = []
    triangles = []
    for line in Path(path).read_text().splitlines():
        if line.startswith("v "):
            _, x, y, z, *rest = line.split()
            vertices.append((float(x), float(y), float(z)))
        elif line.startswith("f "):
            parts = line.split()[1:]
            face = [int(part.split("/")[0]) - 1 for part in parts]
            for i in range(1, len(face) - 1):
                triangles.append((face[0], face[i], face[i + 1]))
    return vertices, triangles


def normalize(vertices):
    mins = [min(v[i] for v in vertices) for i in range(3)]
    maxs = [max(v[i] for v in vertices) for i in range(3)]
    center = [(mins[i] + maxs[i]) * 0.5 for i in range(3)]
    scale = max(maxs[i] - mins[i] for i in range(3)) or 1.0
    return [
        (
            (v[0] - center[0]) / scale,
            (v[1] - center[1]) / scale,
            (v[2] - center[2]) / scale,
        )
        for v in vertices
    ]


def pad4(data, byte=b" "):
    return data + byte * ((4 - len(data) % 4) % 4)


def write_glb(vertices, triangles, out_path):
    vertices = normalize(vertices)
    flat_positions = [coord for vertex in vertices for coord in vertex]
    flat_indices = [index for triangle in triangles for index in triangle]

    position_bytes = struct.pack("<" + "f" * len(flat_positions), *flat_positions)
    index_bytes = struct.pack("<" + "I" * len(flat_indices), *flat_indices)
    position_bytes = pad4(position_bytes, b"\x00")
    index_offset = len(position_bytes)
    binary = position_bytes + pad4(index_bytes, b"\x00")

    mins = [min(v[i] for v in vertices) for i in range(3)]
    maxs = [max(v[i] for v in vertices) for i in range(3)]

    gltf = {
        "asset": {"version": "2.0", "generator": "CelloCut OBJ to GLB"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "materials": [
            {
                "name": "Neutral gray",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.62, 0.64, 0.66, 1.0],
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.82,
                },
                "doubleSided": True,
            }
        ],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 0},
                        "indices": 1,
                        "material": 0,
                        "mode": 4,
                    }
                ]
            }
        ],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(position_bytes),
                "target": 34962,
            },
            {
                "buffer": 0,
                "byteOffset": index_offset,
                "byteLength": len(index_bytes),
                "target": 34963,
            },
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": len(vertices),
                "type": "VEC3",
                "min": mins,
                "max": maxs,
            },
            {
                "bufferView": 1,
                "componentType": 5125,
                "count": len(flat_indices),
                "type": "SCALAR",
            },
        ],
    }

    json_chunk = pad4(json.dumps(gltf, separators=(",", ":")).encode("utf-8"))
    bin_chunk = pad4(binary, b"\x00")
    total_length = 12 + 8 + len(json_chunk) + 8 + len(bin_chunk)
    header = struct.pack("<4sII", b"glTF", 2, total_length)
    json_header = struct.pack("<I4s", len(json_chunk), b"JSON")
    bin_header = struct.pack("<I4s", len(bin_chunk), b"BIN\x00")
    Path(out_path).write_bytes(header + json_header + json_chunk + bin_header + bin_chunk)


def main():
    in_path, out_path = sys.argv[1], sys.argv[2]
    vertices, triangles = parse_obj(in_path)
    if not vertices or not triangles:
        raise SystemExit(f"No mesh data found in {in_path}")
    write_glb(vertices, triangles, out_path)


if __name__ == "__main__":
    main()

"""Converts an OBJ with triangle faces to OFF, outside the game.

The OBJ repeats a position at each texture seam (the same point once for
every (u, v)). OFF only stores positions, so vertices at the same position
are merged: the mesh becomes closed and the vertex normals come out smooth.
Faces that become degenerate after the merge are dropped.

The coordinates are written as they are in the OBJ; the game places the
model with a matrix (OffModel.fit_matrix).

Usage: python tools/obj_to_off.py input.obj output.off
"""

import sys
from pathlib import Path

import numpy as np

SAME_POSITION_DECIMALS = 6


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    positions, triangle_indices = read_obj(Path(sys.argv[1]))
    print(f"OBJ: {len(positions)} vertices, {len(triangle_indices)} faces")
    positions, triangle_indices = merge_repeated_positions(positions, triangle_indices)
    if signed_volume(positions, triangle_indices) < 0.0:
        triangle_indices = triangle_indices[:, ::-1]
        print("orientacao invertida para anti-horaria")
    write_off(Path(sys.argv[2]), positions, triangle_indices)
    print(f"OFF: {len(positions)} vertices, {len(triangle_indices)} faces")


def read_obj(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """(positions, triangle indices). Polygons are split into a fan of
    triangles; texture and normal indices are ignored."""
    positions, triangle_indices = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "v":
            positions.append([float(value) for value in fields[1:4]])
        elif fields[0] == "f":
            triangle_indices.extend(_fan_triangles(fields[1:]))
    return np.array(positions, dtype="f8"), np.array(triangle_indices, dtype="i8")


def merge_repeated_positions(
    positions: np.ndarray, triangle_indices: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    rounded = np.round(positions, SAME_POSITION_DECIMALS)
    unique_positions, new_index = np.unique(rounded, axis=0, return_inverse=True)
    triangle_indices = new_index.ravel()[triangle_indices]
    first, second, third = triangle_indices.T
    is_valid = (first != second) & (second != third) & (first != third)
    return unique_positions, triangle_indices[is_valid]


def signed_volume(positions: np.ndarray, triangle_indices: np.ndarray) -> float:
    """Positive when the faces are counterclockwise seen from outside."""
    corner_a, corner_b, corner_c = (positions[triangle_indices[:, k]] for k in range(3))
    return np.einsum("ij,ij->i", corner_a, np.cross(corner_b, corner_c)).sum() / 6.0


def write_off(path: Path, positions: np.ndarray, triangle_indices: np.ndarray) -> None:
    sides = np.full((len(triangle_indices), 1), 3)
    with open(path, "w", encoding="utf-8") as file:
        file.write("OFF\n")
        file.write(f"{len(positions)} {len(triangle_indices)} 0\n")
        np.savetxt(file, positions, fmt="%.6f")
        np.savetxt(file, np.hstack([sides, triangle_indices]), fmt="%d")


def _fan_triangles(corners: list[str]) -> list[list[int]]:
    """OBJ corners look like "position/texture/normal" and count from 1."""
    indices = [int(corner.split("/")[0]) - 1 for corner in corners]
    return [
        [indices[0], indices[index], indices[index + 1]]
        for index in range(1, len(indices) - 1)
    ]


if __name__ == "__main__":
    main()

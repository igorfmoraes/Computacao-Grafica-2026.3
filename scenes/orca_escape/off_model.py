from pathlib import Path

import glm
import numpy as np

from .mesh import Mesh

NORMALIZATION_EPSILON = 1e-12
HALF_TURN_IN_TEXTURE_U = 0.5


class OffModel:
    """Triangle mesh read from an OFF file.

    The coordinates are kept as read from the file; `fit_matrix` is what
    places the model in the scene.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.positions, self.triangle_indices = _read_off_file(self.path)
        lower_corner = self.positions.min(axis=0)
        upper_corner = self.positions.max(axis=0)
        self.center = 0.5 * (lower_corner + upper_corner)
        self.radius = float(
            np.linalg.norm(self.positions - self.center, axis=1).max()
        )
        self.vertex_normals = _area_weighted_vertex_normals(
            self.positions, self.triangle_indices
        )

    def fit_matrix(self, radius: float = 1.0) -> glm.mat4:
        """S(radius / r) T(-c): moves the bounding sphere (center c, radius r)
        to a sphere of `radius` centered at the origin."""
        return glm.scale(
            glm.mat4(1.0), glm.vec3(radius / self.radius)
        ) * glm.translate(glm.mat4(1.0), glm.vec3(*(-self.center)))

    def cylindrical_mesh(self) -> Mesh:
        """Mesh with texture coordinates from a cylindrical mapping around the
        y axis: u is the angle around the axis and v the height, from 0 at
        the lowest vertex to 1 at the highest.

        A triangle that crosses the seam would interpolate u from ~1 back to
        ~0 across the whole texture, so its vertices on the u ~ 0 side are
        duplicated with u + 1 (GL_REPEAT samples u + 1 as u).
        """
        texture_coordinates = self._cylindrical_texture_coordinates()
        texture_coordinates, triangle_indices, duplicated = _split_seam(
            texture_coordinates, self.triangle_indices
        )
        positions = np.vstack([self.positions, self.positions[duplicated]])
        normals = np.vstack([self.vertex_normals, self.vertex_normals[duplicated]])
        return Mesh(
            np.hstack([positions, normals, texture_coordinates]), triangle_indices
        )

    def summary(self) -> str:
        return (
            f"{self.path.name}: {len(self.positions)} vertices, "
            f"{len(self.triangle_indices)} faces, raio {self.radius:.4f}"
        )

    def _cylindrical_texture_coordinates(self) -> np.ndarray:
        relative = self.positions - self.center
        heights = relative[:, 1]
        u = np.arctan2(relative[:, 0], relative[:, 2]) / (2.0 * np.pi) + 0.5
        height_range = max(heights.max() - heights.min(), NORMALIZATION_EPSILON)
        v = (heights - heights.min()) / height_range
        return np.stack([u, v], axis=1)


def _read_off_file(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """(positions, triangle indices) of an OFF file whose faces are all
    triangles. Comments after `#` are ignored."""
    fields = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields.extend(line.split("#")[0].split())

    if fields[0].upper() != "OFF":
        raise ValueError(f"{path}: nao comeca com OFF")

    vertex_count, face_count = int(fields[1]), int(fields[2])
    first_vertex_field = 4
    first_face_field = first_vertex_field + 3 * vertex_count
    positions = np.array(
        fields[first_vertex_field:first_face_field], dtype="f4"
    ).reshape(vertex_count, 3)
    faces = np.array(
        fields[first_face_field : first_face_field + 4 * face_count], dtype="u4"
    ).reshape(face_count, 4)

    if not (faces[:, 0] == 3).all():
        raise ValueError(f"{path}: ha faces nao triangulares")
    return positions, np.ascontiguousarray(faces[:, 1:])


def _area_weighted_vertex_normals(
    positions: np.ndarray, triangle_indices: np.ndarray
) -> np.ndarray:
    """Sum of the normals of the faces around each vertex. The face normals
    are not normalized before the sum, so larger faces weigh more."""
    corner_a, corner_b, corner_c = (positions[triangle_indices[:, k]] for k in range(3))
    face_normals = np.cross(corner_a - corner_c, corner_b - corner_c)
    vertex_normals = np.zeros_like(positions)
    for corner in range(3):
        # np.add.at accumulates repeated indices, unlike `array[indices] +=`.
        np.add.at(vertex_normals, triangle_indices[:, corner], face_normals)
    lengths = np.linalg.norm(vertex_normals, axis=1, keepdims=True)
    return (vertex_normals / np.maximum(lengths, NORMALIZATION_EPSILON)).astype("f4")


def _split_seam(
    texture_coordinates: np.ndarray, triangle_indices: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(texture coordinates, triangle indices, indices of the duplicated
    vertices) after duplicating, with u + 1, the u ~ 0 corners of every
    triangle that crosses the seam."""
    corner_u = texture_coordinates[triangle_indices, 0]
    crosses_seam = corner_u.max(axis=1) - corner_u.min(axis=1) > HALF_TURN_IN_TEXTURE_U
    corners_to_move = crosses_seam[:, None] & (corner_u < HALF_TURN_IN_TEXTURE_U)

    duplicated = np.unique(triangle_indices[corners_to_move])
    triangle_indices = triangle_indices.astype("i8")
    triangle_indices[corners_to_move] = len(texture_coordinates) + np.searchsorted(
        duplicated, triangle_indices[corners_to_move]
    )
    copies = texture_coordinates[duplicated] + np.array([1.0, 0.0])
    return np.vstack([texture_coordinates, copies]), triangle_indices, duplicated

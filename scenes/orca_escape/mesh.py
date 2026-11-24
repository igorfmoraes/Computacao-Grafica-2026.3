import numpy as np

FLOATS_PER_VERTEX = 8
DEGENERATE_TRIANGLE_AREA = 1e-12
QUAD_CORNERS = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))


class Mesh:
    """Triangle mesh with 8 floats per vertex: position, normal and texture
    coordinates.

    The shapes are built with unit size; their size in the game comes from
    the model matrix. The triangles are reordered to be counterclockwise
    when seen from outside, the order back face culling expects.
    """

    def __init__(self, vertices: np.ndarray, triangle_indices: np.ndarray) -> None:
        self.vertices = np.asarray(vertices, dtype="f4")
        self.triangle_indices = _counterclockwise_from_outside(
            self.vertices, np.asarray(triangle_indices, dtype="i8")
        )

    @classmethod
    def cube(cls) -> "Mesh":
        """Unit cube centered at the origin. Each face has its own four
        vertices, so it keeps a flat normal and the whole texture."""
        vertices, triangle_indices = [], []
        for axis in range(3):
            for direction in (-1.0, 1.0):
                triangle_indices.extend(_quad_triangles(len(vertices)))
                vertices.extend(_cube_face_vertices(axis, direction))
        return cls(np.array(vertices), np.array(triangle_indices))

    @classmethod
    def plane(cls) -> "Mesh":
        """The square [0, 1] x [0, 1] at y = 0, facing +y."""
        vertices = [[x, 0.0, z, 0.0, 1.0, 0.0, x, z] for x, z in QUAD_CORNERS]
        return cls(np.array(vertices), np.array(_quad_triangles(0)))

    @classmethod
    def sphere(
        cls, longitude_segments: int = 48, latitude_segments: int = 24
    ) -> "Mesh":
        """Sphere of radius 1. u follows the longitude and v goes from the
        south pole (0) to the north pole (1).

        The u = 1 column repeats the u = 0 column, so no triangle
        interpolates across the seam from u ~ 1 back to u ~ 0.
        """
        polar_angles, azimuth_angles = _angle_grid(
            np.pi, latitude_segments, 2.0 * np.pi, longitude_segments
        )
        positions = np.stack(
            [
                np.sin(polar_angles) * np.cos(azimuth_angles),
                np.cos(polar_angles),
                np.sin(polar_angles) * np.sin(azimuth_angles),
            ],
            axis=-1,
        )
        texture_coordinates = np.stack(
            [azimuth_angles / (2.0 * np.pi), 1.0 - polar_angles / np.pi], axis=-1
        )
        return cls(
            _interleave(positions, positions, texture_coordinates),
            _grid_triangle_indices(longitude_segments, latitude_segments),
        )

    @classmethod
    def cone(cls, segments: int = 32) -> "Mesh":
        """Cone of height 1 and base radius 0.5, apex at y = 0.5. The side and
        the base do not share vertices because their normals differ."""
        base_radius, height = 0.5, 1.0
        side = cls._cone_side_vertices(segments, base_radius, height)
        base = cls._cone_base_vertices(segments, base_radius)
        center_index = len(side)
        base_triangles = [
            (center_index, center_index + 1 + index, center_index + 2 + index)
            for index in range(segments)
        ]
        triangle_indices = np.vstack(
            [_grid_triangle_indices(segments, 1), np.array(base_triangles)]
        )
        return cls(np.vstack([side, base]), triangle_indices)

    @classmethod
    def torus(
        cls,
        tube_radius: float = 0.25,
        ring_segments: int = 64,
        tube_segments: int = 24,
        texture_repeats_around_ring: int = 4,
    ) -> "Mesh":
        """Torus around the y axis with ring radius 1. The texture repeats
        `texture_repeats_around_ring` times along the ring (GL_REPEAT)."""
        tube_angles, ring_angles = _angle_grid(
            2.0 * np.pi, tube_segments, 2.0 * np.pi, ring_segments
        )
        distance_to_axis = 1.0 + tube_radius * np.cos(tube_angles)
        positions = np.stack(
            [
                distance_to_axis * np.cos(ring_angles),
                tube_radius * np.sin(tube_angles),
                distance_to_axis * np.sin(ring_angles),
            ],
            axis=-1,
        )
        normals = np.stack(
            [
                np.cos(tube_angles) * np.cos(ring_angles),
                np.sin(tube_angles),
                np.cos(tube_angles) * np.sin(ring_angles),
            ],
            axis=-1,
        )
        texture_coordinates = np.stack(
            [
                texture_repeats_around_ring * ring_angles / (2.0 * np.pi),
                tube_angles / (2.0 * np.pi),
            ],
            axis=-1,
        )
        return cls(
            _interleave(positions, normals, texture_coordinates),
            _grid_triangle_indices(ring_segments, tube_segments),
        )

    @staticmethod
    def _cone_side_vertices(
        segments: int, base_radius: float, height: float
    ) -> np.ndarray:
        heights, angles = _angle_grid(height, 1, 2.0 * np.pi, segments)
        radii = base_radius * (1.0 - heights / height)
        positions = np.stack(
            [radii * np.cos(angles), heights - 0.5, radii * np.sin(angles)], axis=-1
        )
        slant_length = np.hypot(height, base_radius)
        normals = np.stack(
            [
                height * np.cos(angles) / slant_length,
                np.full_like(angles, base_radius / slant_length),
                height * np.sin(angles) / slant_length,
            ],
            axis=-1,
        )
        texture_coordinates = np.stack([angles / (2.0 * np.pi), heights], axis=-1)
        return _interleave(positions, normals, texture_coordinates)

    @staticmethod
    def _cone_base_vertices(segments: int, base_radius: float) -> np.ndarray:
        angles = np.linspace(0.0, 2.0 * np.pi, segments + 1)
        cosines, sines = np.cos(angles), np.sin(angles)
        ring = np.column_stack(
            [
                base_radius * cosines,
                np.full_like(angles, -0.5),
                base_radius * sines,
                np.zeros_like(angles),
                np.full_like(angles, -1.0),
                np.zeros_like(angles),
                0.5 + 0.5 * cosines,
                0.5 + 0.5 * sines,
            ]
        )
        center = [0.0, -0.5, 0.0, 0.0, -1.0, 0.0, 0.5, 0.5]
        return np.vstack([center, ring])


def _counterclockwise_from_outside(
    vertices: np.ndarray, triangle_indices: np.ndarray
) -> np.ndarray:
    """Flips the triangles whose geometric normal, (B - A) x (C - A), points
    against the normals stored in their vertices, and drops degenerate ones."""
    positions, normals = vertices[:, :3], vertices[:, 3:6]
    corner_a, corner_b, corner_c = (positions[triangle_indices[:, k]] for k in range(3))
    geometric_normals = np.cross(corner_b - corner_a, corner_c - corner_a)
    areas = np.linalg.norm(geometric_normals, axis=1)
    is_degenerate = areas <= DEGENERATE_TRIANGLE_AREA
    triangle_indices = triangle_indices[~is_degenerate]
    geometric_normals = geometric_normals[~is_degenerate]

    stored_normals = normals[triangle_indices].sum(axis=1)
    is_clockwise = np.einsum("ij,ij->i", geometric_normals, stored_normals) < 0.0
    triangle_indices[is_clockwise] = triangle_indices[is_clockwise][:, [0, 2, 1]]
    return np.ascontiguousarray(triangle_indices, dtype="u4")


def _cube_face_vertices(axis: int, direction: float) -> list[list[float]]:
    normal = np.zeros(3)
    normal[axis] = direction
    first_tangent = np.zeros(3)
    first_tangent[(axis + 1) % 3] = 1.0
    second_tangent = np.cross(normal, first_tangent)
    return [
        [
            *(0.5 * normal + (u - 0.5) * first_tangent + (v - 0.5) * second_tangent),
            *normal,
            u,
            v,
        ]
        for u, v in QUAD_CORNERS
    ]


def _quad_triangles(first_index: int) -> list[tuple[int, int, int]]:
    return [
        (first_index, first_index + 1, first_index + 2),
        (first_index, first_index + 2, first_index + 3),
    ]


def _angle_grid(
    row_range: float, row_count: int, column_range: float, column_count: int
) -> tuple[np.ndarray, np.ndarray]:
    """(row values, column values) of a grid with (row_count + 1) x
    (column_count + 1) vertices."""
    rows = np.linspace(0.0, row_range, row_count + 1)
    columns = np.linspace(0.0, column_range, column_count + 1)
    return np.meshgrid(rows, columns, indexing="ij")


def _grid_triangle_indices(column_count: int, row_count: int) -> np.ndarray:
    """Two triangles for each square of a grid built by `_angle_grid`."""
    rows, columns = np.meshgrid(
        np.arange(row_count), np.arange(column_count), indexing="ij"
    )
    top_left = (rows * (column_count + 1) + columns).ravel()
    bottom_left = top_left + column_count + 1
    first_half = np.stack([top_left, bottom_left, bottom_left + 1], axis=1)
    second_half = np.stack([top_left, bottom_left + 1, top_left + 1], axis=1)
    return np.vstack([first_half, second_half])


def _interleave(
    positions: np.ndarray, normals: np.ndarray, texture_coordinates: np.ndarray
) -> np.ndarray:
    return np.concatenate([positions, normals, texture_coordinates], axis=-1).reshape(
        -1, FLOATS_PER_VERTEX
    )

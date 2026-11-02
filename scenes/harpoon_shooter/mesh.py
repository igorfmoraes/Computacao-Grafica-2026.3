import moderngl
import numpy as np


class Mesh:
    def __init__(
        self, vertices: np.ndarray, draw_mode: int = moderngl.TRIANGLES
    ) -> None:
        self.vertices = np.asarray(vertices, dtype="f4")
        self.triangle_indices = np.array(
            self._triangulate_between_last_two_vertices(), dtype="i4"
        )
        self.draw_mode = draw_mode

    @classmethod
    def closed_outline(cls, vertices: np.ndarray) -> "Mesh":
        return cls(vertices, moderngl.TRIANGLES)

    def _triangulate_between_last_two_vertices(self) -> list[int]:
        outline_vertex_count = len(self.vertices) - 2
        midpoint_index = outline_vertex_count // 2
        second_half_anchor_index = outline_vertex_count
        first_half_anchor_index = outline_vertex_count + 1

        return (
            self._triangles_around_anchor(first_half_anchor_index, 0, midpoint_index)
            + self._triangles_around_anchor(
                second_half_anchor_index, midpoint_index, outline_vertex_count - 1
            )
            + [first_half_anchor_index, midpoint_index, second_half_anchor_index]
        )

    @staticmethod
    def _triangles_around_anchor(
        anchor_index: int, first_vertex_index: int, end_vertex_index: int
    ) -> list[int]:
        triangle_indices = []
        for vertex_index in range(first_vertex_index, end_vertex_index):
            triangle_indices.extend([anchor_index, vertex_index, vertex_index + 1])
        return triangle_indices

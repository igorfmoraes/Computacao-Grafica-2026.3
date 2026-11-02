import moderngl
import numpy as np

from .shader_program import ShaderProgram
from .mesh import Mesh

VERTEX_POSITION_ATTRIBUTE = "vertex_position"
TWO_FLOATS_PER_VERTEX = "2f"


class DrawableMesh:
    def __init__(
        self, context: moderngl.Context, mesh: Mesh, shader_program: ShaderProgram
    ) -> None:
        self._vertex_buffer = context.buffer(mesh.vertices.tobytes())
        self._index_buffer = context.buffer(mesh.triangle_indices.tobytes())
        self._vertex_array = context.vertex_array(
            shader_program.program,
            [(self._vertex_buffer, TWO_FLOATS_PER_VERTEX, VERTEX_POSITION_ATTRIBUTE)],
            index_buffer=self._index_buffer,
        )
        self._shader_program = shader_program
        self._draw_mode = mesh.draw_mode

    def draw(
        self, transform: np.ndarray, color: tuple[float, float, float, float]
    ) -> None:
        self._shader_program.set_uniforms(
            {
                # GLSL reads matrices column-major; NumPy stores them row-major.
                "shape_transform": transform.T,
                "shape_color": np.array(color, dtype=np.float32),
            }
        )
        self._vertex_array.render(self._draw_mode)

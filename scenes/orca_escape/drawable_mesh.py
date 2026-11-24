import moderngl

from .mesh import Mesh
from .shader_program import ShaderProgram

VERTEX_LAYOUT = "3f 3f 2f"
VERTEX_ATTRIBUTES = ("vertex_position", "vertex_normal", "vertex_texture_coordinates")


class DrawableMesh:
    """The GPU copy of a `Mesh`: its buffers are created once and the same
    mesh is drawn many times with different model matrices."""

    def __init__(
        self, context: moderngl.Context, mesh: Mesh, shader_program: ShaderProgram
    ) -> None:
        self._vertex_buffer = context.buffer(mesh.vertices.tobytes())
        self._index_buffer = context.buffer(mesh.triangle_indices.tobytes())
        self._vertex_array = context.vertex_array(
            shader_program.program,
            [(self._vertex_buffer, VERTEX_LAYOUT, *VERTEX_ATTRIBUTES)],
            index_buffer=self._index_buffer,
        )

    def draw(self) -> None:
        self._vertex_array.render(moderngl.TRIANGLES)

    def release(self) -> None:
        self._vertex_array.release()
        self._vertex_buffer.release()
        self._index_buffer.release()

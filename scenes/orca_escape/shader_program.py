from pathlib import Path

import glm
import moderngl

SHADERS_DIRECTORY = Path(__file__).parent / "shaders"
GLM_MATRIX_TYPES = (glm.mat3, glm.mat4)
GLM_VECTOR_TYPES = (glm.vec2, glm.vec3, glm.vec4)


class ShaderProgram:
    def __init__(
        self,
        context: moderngl.Context,
        vertex_shader_path: Path,
        fragment_shader_path: Path,
    ) -> None:
        self._program = context.program(
            vertex_shader=vertex_shader_path.read_text(encoding="utf-8"),
            fragment_shader=fragment_shader_path.read_text(encoding="utf-8"),
        )

    @classmethod
    def named(cls, context: moderngl.Context, name: str) -> "ShaderProgram":
        """Loads `shaders/<name>.vert` and `shaders/<name>.frag`."""
        return cls(
            context,
            SHADERS_DIRECTORY / f"{name}.vert",
            SHADERS_DIRECTORY / f"{name}.frag",
        )

    @property
    def program(self) -> moderngl.Program:
        return self._program

    def set_uniform(self, name: str, value) -> None:
        """Sends `value` to the uniform `name`.

        Uniforms the shader does not declare, or that the compiler removed
        because they are unused, are ignored.
        """
        uniform = self._program.get(name, None)
        if uniform is None:
            return
        if isinstance(value, GLM_MATRIX_TYPES):
            uniform.write(value.to_bytes())
        elif isinstance(value, GLM_VECTOR_TYPES):
            uniform.value = tuple(value)
        else:
            uniform.value = value

    def set_uniforms(self, values: dict) -> None:
        for name, value in values.items():
            self.set_uniform(name, value)

    def release(self) -> None:
        self._program.release()

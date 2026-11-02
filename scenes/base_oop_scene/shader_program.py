from pathlib import Path

import moderngl
import numpy as np


class ShaderProgram:
    def __init__(
        self,
        context: moderngl.Context,
        vertex_shader_path: Path,
        fragment_shader_path: Path,
    ) -> None:
        self._program = context.program(
            vertex_shader_path.read_text(encoding="utf-8"),
            fragment_shader_path.read_text(encoding="utf-8"),
        )

    @property
    def program(self) -> moderngl.Program:
        return self._program

    def set_uniform(self, name: str, value) -> None:
        uniform = self._program.get(name, None)
        if uniform is None:
            return
        if isinstance(value, np.ndarray):
            uniform.write(value.astype(np.float32).tobytes())
        else:
            uniform.value = value

    def set_uniforms(self, values):
        for name, value in values.items():
            self.set_uniform(name, value)

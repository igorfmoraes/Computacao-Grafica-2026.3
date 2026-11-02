from pathlib import Path

from .drawable_mesh import DrawableMesh
from .shader_program import ShaderProgram
from .mesh import Mesh

import moderngl
import numpy as np

SHADERS_DIRECTORY = Path(__file__).parent / "shaders"


class Player:
    SCALE = 0.3
    POSITION = (0.0, 0.0)
    COLOR = (1.0, 0.75, 0.0, 1.0)

    def __init__(self, context: moderngl.Context) -> None:
        self._context = context
        self._shader_program = ShaderProgram(
            context,
            SHADERS_DIRECTORY / "body.vert",
            SHADERS_DIRECTORY / "color.frag",
        )

        angles_radians = np.linspace(0.0, 2.0 * np.pi, 128, endpoint=False)
        x_coordinates = np.cos(angles_radians)
        y_coordinates = np.sin(angles_radians)
        outline_mesh = Mesh.closed_outline(np.vstack((x_coordinates, y_coordinates)).T)

        self._drawable_mesh = DrawableMesh(context, outline_mesh, self._shader_program)

    def draw(self, elapsed_time_seconds: float) -> None:
        self._drawable_mesh.draw(self.SCALE, self.POSITION, self.COLOR)
        pass

from pathlib import Path

import moderngl
import numpy as np

from .drawable_mesh import DrawableMesh
from .mesh import Mesh
from .shader_program import ShaderProgram
from .transform import transformation_matrix

SHADERS_DIRECTORY = Path(__file__).parent / "shaders"
ELLIPSE_POINT_COUNT = 48

COAT_COLOR = (1.0, 0.75, 0.0, 1.0)
SLEEVE_COLOR = (0.9, 0.65, 0.0, 1.0)
HOOD_COLOR = (0.8, 0.55, 0.0, 1.0)
HOOD_OPENING_COLOR = (0.2, 0.12, 0.05, 1.0)


def _ellipse_outline(
    center: tuple[float, float],
    radii: tuple[float, float],
    rotation_radians: float = 0.0,
) -> np.ndarray:
    angles = np.linspace(0.0, 2.0 * np.pi, ELLIPSE_POINT_COUNT, endpoint=False)
    points = np.column_stack((radii[0] * np.cos(angles), radii[1] * np.sin(angles)))
    cosine, sine = np.cos(rotation_radians), np.sin(rotation_radians)
    rotation = np.array([[cosine, -sine], [sine, cosine]])
    return points @ rotation.T + np.array(center)


FISHERMAN_PARTS = [
    (_ellipse_outline((0.0, -0.1), (0.9, 0.5)), COAT_COLOR),  # shoulders / body
    (_ellipse_outline((0.8, 0.25), (0.17, 0.45), 0.3), SLEEVE_COLOR),  # right arm
    (_ellipse_outline((-0.8, 0.25), (0.17, 0.45), -0.3), SLEEVE_COLOR),  # left arm
    (_ellipse_outline((0.0, -0.05), (0.4, 0.4)), HOOD_COLOR),  # hood
    (_ellipse_outline((0.0, 0.15), (0.2, 0.14)), HOOD_OPENING_COLOR),  # hood opening
]


class Player:
    SCALE = 0.1

    def __init__(self, context: moderngl.Context) -> None:
        shader_program = ShaderProgram(
            context,
            SHADERS_DIRECTORY / "body.vert",
            SHADERS_DIRECTORY / "color.frag",
        )
        self._parts = [
            (DrawableMesh(context, Mesh.closed_outline(outline), shader_program), color)
            for outline, color in FISHERMAN_PARTS
        ]
        self.position = (0.0, -0.7)
        self.rotation_radians = 0.0

    def draw(self, elapsed_time_seconds: float) -> None:
        transform = transformation_matrix(
            self.SCALE, self.rotation_radians, self.position
        )
        for drawable_mesh, color in self._parts:
            drawable_mesh.draw(transform, color)

from pathlib import Path

import moderngl
import numpy as np

from .drawable_mesh import DrawableMesh
from .mesh import Mesh
from .shader_program import ShaderProgram
from .transform import transformation_matrix

SHADERS_DIRECTORY = Path(__file__).parent / "shaders"

SHAFT_COLOR = (0.45, 0.3, 0.15, 1.0)
HEAD_COLOR = (0.75, 0.78, 0.8, 1.0)

SHAFT_OUTLINE = np.array([(-0.04, 0.0), (0.04, 0.0), (0.04, 1.6), (-0.04, 1.6)])
HEAD_OUTLINE = np.array([(-0.16, 1.5), (0.16, 1.5), (0.0, 2.0)])
TIP_OFFSET = 2.0


class Harpoon:
    SCALE = 0.1
    SPEED_UNITS_PER_SECOND = 2.0
    SCREEN_LIMIT = 1.0

    def __init__(self, context: moderngl.Context) -> None:
        shader_program = ShaderProgram(
            context,
            SHADERS_DIRECTORY / "body.vert",
            SHADERS_DIRECTORY / "color.frag",
        )
        self._parts = [
            (DrawableMesh(context, Mesh.closed_outline(outline), shader_program), color)
            for outline, color in (
                (SHAFT_OUTLINE, SHAFT_COLOR),
                (HEAD_OUTLINE, HEAD_COLOR),
            )
        ]
        self._is_flying = False
        self._position = np.zeros(2)
        self._direction = np.array([0.0, 1.0])
        self._rotation_radians = 0.0

    @property
    def is_flying(self) -> bool:
        return self._is_flying

    @property
    def tip_position(self) -> np.ndarray:
        """Leading point of the harpoon; intended for collision tests."""
        return self._position + self._direction * TIP_OFFSET * self.SCALE

    def fire(self, origin: tuple[float, float], rotation_radians: float) -> None:
        if self._is_flying:
            return
        self._position = np.array(origin, dtype=float)
        self._rotation_radians = rotation_radians
        self._direction = np.array(
            [-np.sin(rotation_radians), np.cos(rotation_radians)]
        )
        self._is_flying = True

    def stop(self) -> None:
        """Ends the flight (called on a hit or when leaving the screen)."""
        self._is_flying = False

    def update(self, delta_time_seconds: float) -> None:
        if not self._is_flying:
            return
        self._position += (
            self._direction * self.SPEED_UNITS_PER_SECOND * delta_time_seconds
        )
        if np.any(np.abs(self._position) > self.SCREEN_LIMIT):
            self.stop()

    def draw(self) -> None:
        if not self._is_flying:
            return
        transform = transformation_matrix(
            self.SCALE, self._rotation_radians, self._position
        )
        for drawable_mesh, color in self._parts:
            drawable_mesh.draw(transform, color)

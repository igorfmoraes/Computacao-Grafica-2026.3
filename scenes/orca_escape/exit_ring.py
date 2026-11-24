import math

import glm

from .collision import Sphere
from .maze import Maze

UP = glm.vec3(0.0, 1.0, 0.0)
HEIGHT = 1.6
SCALE = 1.2
SPIN_RADIANS_PER_SECOND = 0.8
CLOSED_PULSES_RADIANS_PER_SECOND = 1.5
OPEN_PULSES_RADIANS_PER_SECOND = 4.0


class ExitRing:
    """The maze exit: a spinning ring that opens once every fish was
    collected."""

    COLLISION_RADIUS = 1.3

    def __init__(self, maze: Maze) -> None:
        self.position = maze.cell_center(maze.exit_cell, HEIGHT)
        self.reset()

    def reset(self) -> None:
        self.is_open = False
        self._elapsed_seconds = 0.0

    def update(self, elapsed_seconds: float) -> None:
        self._elapsed_seconds += elapsed_seconds

    @property
    def collision_sphere(self) -> Sphere:
        return Sphere(self.position, self.COLLISION_RADIUS)

    @property
    def glow(self) -> float:
        """Brightness between 0.2 and 1, pulsing faster when open."""
        pulses = (
            OPEN_PULSES_RADIANS_PER_SECOND
            if self.is_open
            else CLOSED_PULSES_RADIANS_PER_SECOND
        )
        return 0.6 + 0.4 * math.sin(self._elapsed_seconds * pulses)

    def model_matrix(self) -> glm.mat4:
        """The torus is built around y; it stands up by a quarter turn
        around x."""
        matrix = glm.translate(glm.mat4(1.0), self.position)
        matrix = glm.rotate(matrix, self._elapsed_seconds * SPIN_RADIANS_PER_SECOND, UP)
        matrix = glm.rotate(matrix, glm.radians(90.0), glm.vec3(1.0, 0.0, 0.0))
        return glm.scale(matrix, glm.vec3(SCALE))

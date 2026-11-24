import math

import glm

from .collision import Sphere
from .maze import Maze


class Jellyfish:
    """Swims back and forth along one axis, bouncing off the walls, while
    its bell pulses and it drifts up and down."""

    COLLISION_RADIUS = 0.75
    SPEED_UNITS_PER_SECOND = 3.0
    SWIM_HEIGHT = 1.7
    BELL_RADII = glm.vec3(0.8, 0.55, 0.8)

    def __init__(
        self,
        maze: Maze,
        spawn_cell: tuple[int, int],
        spawn_direction: glm.vec3,
        phase_radians: float,
    ) -> None:
        self._maze = maze
        self._spawn_cell = spawn_cell
        self._spawn_direction = glm.vec3(spawn_direction)
        self.phase_radians = phase_radians
        self.reset()

    def reset(self) -> None:
        self._body = Sphere(
            self._maze.cell_center(self._spawn_cell, self.SWIM_HEIGHT),
            self.COLLISION_RADIUS,
        )
        self.direction = glm.vec3(self._spawn_direction)
        self.elapsed_seconds = 0.0

    def update(self, elapsed_seconds: float) -> None:
        self.elapsed_seconds += elapsed_seconds
        displacement = self.direction * (self.SPEED_UNITS_PER_SECOND * elapsed_seconds)
        if self._maze.move_sphere(self._body, displacement):
            self.turn_back()

    def turn_back(self) -> None:
        self.direction = -self.direction

    @property
    def center(self) -> glm.vec3:
        drift = 0.25 * math.sin(self.elapsed_seconds * 1.3 + self.phase_radians)
        return self._body.center + glm.vec3(0.0, drift, 0.0)

    @property
    def collision_sphere(self) -> Sphere:
        return Sphere(self.center, self.COLLISION_RADIUS)

    def bell_matrix(self) -> glm.mat4:
        """An ellipsoid squashed and stretched over time: a non uniform scale
        that changes every frame."""
        pulse = math.sin(self.elapsed_seconds * 3.0 + self.phase_radians)
        squash = glm.vec3(1.0 + 0.12 * pulse, 1.0 - 0.18 * pulse, 1.0 + 0.12 * pulse)
        return glm.scale(
            glm.translate(glm.mat4(1.0), self.center), self.BELL_RADII * squash
        )

    def tentacles_matrix(self) -> glm.mat4:
        return glm.translate(glm.mat4(1.0), self.center)

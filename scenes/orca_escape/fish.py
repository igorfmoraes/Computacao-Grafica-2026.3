import math

import glm

from .collision import Sphere
from .maze import Maze

UP = glm.vec3(0.0, 1.0, 0.0)
SWIM_HEIGHT = 1.4
CIRCLE_RADIUS = 0.6
BODY_RADII = glm.vec3(0.7, 0.42, 0.22)
TAIL_JOINT_OFFSET = glm.vec3(-0.62, 0.0, 0.0)
TAIL_CENTER_OFFSET = glm.vec3(-0.25, 0.0, 0.0)
TAIL_SIZE = glm.vec3(0.9, 0.5, 0.12)


class Fish:
    """A collectible fish swimming in circles inside its cell."""

    COLLISION_RADIUS = 0.6

    def __init__(self, maze: Maze, cell: tuple[int, int], phase_radians: float) -> None:
        self._home = maze.cell_center(cell, SWIM_HEIGHT)
        self._phase_radians = phase_radians
        self.reset()

    def reset(self) -> None:
        self.is_collected = False
        self._elapsed_seconds = 0.0

    def update(self, elapsed_seconds: float) -> None:
        self._elapsed_seconds += elapsed_seconds

    @property
    def position(self) -> glm.vec3:
        bobbing = 0.3 * math.sin(self._elapsed_seconds * 2.2 + self._phase_radians)
        return self._home + glm.vec3(0.0, bobbing, 0.0)

    @property
    def collision_sphere(self) -> Sphere:
        return Sphere(self.position, self.COLLISION_RADIUS)

    def body_and_tail_matrices(self) -> tuple[glm.mat4, glm.mat4]:
        """Model matrices of the body (a scaled sphere) and of the tail (a
        flattened cone whose apex points to the body and wags around the
        joint)."""
        circling_radians = self._elapsed_seconds * 1.6 + self._phase_radians
        swimmer = glm.translate(glm.mat4(1.0), self.position)
        swimmer = glm.rotate(swimmer, circling_radians, UP)
        swimmer = glm.translate(swimmer, glm.vec3(0.0, 0.0, CIRCLE_RADIUS))
        body = glm.scale(swimmer, BODY_RADII)

        wag_radians = 0.4 * math.sin(self._elapsed_seconds * 10.0 + self._phase_radians)
        tail = glm.translate(swimmer, TAIL_JOINT_OFFSET)
        tail = glm.rotate(tail, wag_radians, UP)
        tail = glm.translate(tail, TAIL_CENTER_OFFSET)
        tail = glm.rotate(tail, glm.radians(-90.0), glm.vec3(0.0, 0.0, 1.0))
        return body, glm.scale(tail, TAIL_SIZE)

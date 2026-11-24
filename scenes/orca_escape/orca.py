import math
from dataclasses import dataclass

import glm

from .collision import Sphere
from .maze import Maze

UP = glm.vec3(0.0, 1.0, 0.0)
IDENTITY = glm.mat4(1.0)
# The OFF file has the head towards -y and the back towards +z. A -90 degree
# turn around x takes -y to +z (the game's forward) and +z to +y.
FILE_TO_GAME_ORIENTATION = glm.rotate(IDENTITY, glm.radians(-90.0), glm.vec3(1, 0, 0))
FIRST_OPEN_NEIGHBOR_HEADINGS = (
    (0.0, (0, 1)),
    (math.pi / 2, (1, 0)),
    (math.pi, (0, -1)),
    (-math.pi / 2, (-1, 0)),
)


@dataclass
class SwimInput:
    """What the player is asking for in this frame.

    `forward_amount` is 1 to swim forward and -1 backwards; `turn_amount` is
    1 to turn left and -1 right.
    """

    forward_amount: float = 0.0
    turn_amount: float = 0.0
    turbo: bool = False


def heading_direction(heading_radians: float) -> glm.vec3:
    """Horizontal direction of a heading: 0 is +z, and turning by the heading
    around y takes +z to this direction."""
    return glm.vec3(math.sin(heading_radians), 0.0, math.cos(heading_radians))


class Orca:
    COLLISION_RADIUS = 0.8
    SWIM_HEIGHT = 1.3
    SCALE = 1.2
    SPEED_UNITS_PER_SECOND = 6.0
    TURBO_SPEED_UNITS_PER_SECOND = 14.0
    TURN_SPEED_RADIANS_PER_SECOND = math.radians(140.0)
    INVULNERABLE_SECONDS = 1.5
    KNOCKBACK_SPEED_UNITS_PER_SECOND = 10.0
    KNOCKBACK_DECAY_PER_SECOND = 4.0
    BANK_RADIANS = 0.35
    BANK_RESPONSE_PER_SECOND = 6.0
    BLINKS_PER_SECOND = 12

    def __init__(self, maze: Maze, model_fit_matrix: glm.mat4) -> None:
        self._maze = maze
        self._model_fit_matrix = model_fit_matrix
        self.reset()

    def reset(self) -> None:
        self.body = Sphere(
            self._maze.cell_center(self._maze.start_cell, self.SWIM_HEIGHT),
            self.COLLISION_RADIUS,
        )
        self.heading_radians = self._heading_to_first_open_neighbor()
        self.elapsed_seconds = 0.0
        self.invulnerable_seconds = 0.0
        self._knockback_velocity = glm.vec3(0.0)
        self._forward_speed = 0.0
        self._bank_radians = 0.0

    @property
    def position(self) -> glm.vec3:
        return self.body.center

    @property
    def forward(self) -> glm.vec3:
        return heading_direction(self.heading_radians)

    @property
    def is_visible(self) -> bool:
        """Blinks while invulnerable. Uses the game time, which stops during
        the pause."""
        if self.invulnerable_seconds <= 0.0:
            return True
        return int(self.elapsed_seconds * self.BLINKS_PER_SECOND) % 2 == 0

    def update(self, elapsed_seconds: float, swim_input: SwimInput) -> None:
        self.elapsed_seconds += elapsed_seconds
        self.invulnerable_seconds = max(
            0.0, self.invulnerable_seconds - elapsed_seconds
        )
        turn_speed = swim_input.turn_amount * self.TURN_SPEED_RADIANS_PER_SECOND
        self.heading_radians += turn_speed * elapsed_seconds
        self._update_bank(elapsed_seconds, swim_input)
        self._swim(elapsed_seconds, swim_input)

    def take_hit(self, source_position: glm.vec3) -> bool:
        """Pushes the orca away from `source_position` and makes it
        invulnerable for a while. Returns False, doing nothing, if it is
        already invulnerable."""
        if self.invulnerable_seconds > 0.0:
            return False
        away = self.position - source_position
        away.y = 0.0
        if glm.length(away) > 0.0:
            self._knockback_velocity = (
                glm.normalize(away) * self.KNOCKBACK_SPEED_UNITS_PER_SECOND
            )
        self.invulnerable_seconds = self.INVULNERABLE_SECONDS
        return True

    def model_matrix(self) -> glm.mat4:
        bobbing_height = 0.12 * math.sin(self.elapsed_seconds * 2.0)
        swim_effort = min(1.0, abs(self._forward_speed) / self.SPEED_UNITS_PER_SECOND)
        body_sway_radians = 0.06 * math.sin(self.elapsed_seconds * 9.0) * swim_effort
        matrix = glm.translate(IDENTITY, self.position + glm.vec3(0, bobbing_height, 0))
        matrix = glm.rotate(matrix, self.heading_radians + body_sway_radians, UP)
        matrix = glm.rotate(matrix, self._bank_radians, glm.vec3(0, 0, 1))
        matrix = glm.scale(matrix, glm.vec3(self.SCALE))
        return matrix * FILE_TO_GAME_ORIENTATION * self._model_fit_matrix

    def headlight_pose(self) -> tuple[glm.vec3, glm.vec3]:
        """(position, direction) of the spot light on the orca's head."""
        position = self.position + self.forward * 1.1 + glm.vec3(0, 0.25, 0)
        direction = glm.normalize(self.forward + glm.vec3(0, -0.18, 0))
        return position, direction

    def _update_bank(self, elapsed_seconds: float, swim_input: SwimInput) -> None:
        """Leans into the turns. The lean decays exponentially towards its
        target, which looks the same at any frame rate."""
        swimming_direction = 1.0 if swim_input.forward_amount >= 0 else -1.0
        target_radians = (
            -self.BANK_RADIANS * swim_input.turn_amount * swimming_direction
        )
        response = 1.0 - math.exp(-self.BANK_RESPONSE_PER_SECOND * elapsed_seconds)
        self._bank_radians += (target_radians - self._bank_radians) * response

    def _swim(self, elapsed_seconds: float, swim_input: SwimInput) -> None:
        top_speed = (
            self.TURBO_SPEED_UNITS_PER_SECOND
            if swim_input.turbo
            else self.SPEED_UNITS_PER_SECOND
        )
        self._forward_speed = swim_input.forward_amount * top_speed
        velocity = self.forward * self._forward_speed + self._knockback_velocity
        self._knockback_velocity *= math.exp(
            -self.KNOCKBACK_DECAY_PER_SECOND * elapsed_seconds
        )
        self._maze.move_sphere(self.body, velocity * elapsed_seconds)

    def _heading_to_first_open_neighbor(self) -> float:
        column, row = self._maze.start_cell
        for heading_radians, offset in FIRST_OPEN_NEIGHBOR_HEADINGS:
            column_offset, row_offset = offset
            if self._maze.is_open(column + column_offset, row + row_offset):
                return heading_radians
        return 0.0

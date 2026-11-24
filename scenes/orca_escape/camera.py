import math
from dataclasses import dataclass
from enum import Enum

import glm

from .maze import Maze
from .orca import Orca

FIELD_OF_VIEW_RADIANS = math.radians(50.0)
ORBIT_RADIANS_PER_PIXEL = 0.005
ZOOM_FRACTION_PER_SCROLL_STEP = 0.1
MIN_ELEVATION_RADIANS = math.radians(5.0)
MAX_ELEVATION_RADIANS = math.radians(85.0)
FOLLOW_TURN_RESPONSE_PER_SECOND = 5.0
OVERVIEW_HEADING_RADIANS = math.pi
FOLLOW_TARGET_HEIGHT = 0.6


class CameraMode(Enum):
    FOLLOW = "seguir"
    OVERVIEW = "geral"


@dataclass
class Orbit:
    """Where the camera sits around its target in one mode, and the depth
    range and fog density that go with that distance.

    Follow: near 0.1 because the camera gets ~3 units from the orca and the
    walls; far 90 is past the point where the fog already hides everything
    (exp(-(0.035 d)^2) < 0.01 beyond d = 61), so nothing pops out of view.
    Overview: the camera is ~70 units from the center of a 60 x 60 maze;
    near 1 and far 220 enclose it with margin and keep more depth buffer
    precision than a 0.1 near would.
    """

    distance: float
    elevation_radians: float
    min_distance: float
    max_distance: float
    near: float
    far: float
    fog_density: float
    heading_offset_radians: float = 0.0

    def __post_init__(self) -> None:
        self._default_placement = (self.distance, self.elevation_radians)

    def reset(self) -> None:
        self.distance, self.elevation_radians = self._default_placement
        self.heading_offset_radians = 0.0


class Camera:
    """LookAt camera that either follows the orca from behind or shows the
    whole maze from above. Dragging orbits it around its target and the
    scroll wheel changes its distance."""

    def __init__(self, maze: Maze) -> None:
        self._maze = maze
        overview_distance = (
            0.6 * max(maze.width, maze.depth) / math.tan(FIELD_OF_VIEW_RADIANS / 2)
        )
        self._orbits = {
            CameraMode.FOLLOW: Orbit(
                7.0, math.radians(28.0), 3.0, 16.0, 0.1, 90.0, 0.035
            ),
            CameraMode.OVERVIEW: Orbit(
                overview_distance,
                math.radians(70.0),
                0.3 * overview_distance,
                1.5 * overview_distance,
                1.0,
                220.0,
                0.004,
            ),
        }
        self.mode = CameraMode.FOLLOW
        self.aspect_ratio = 1.0
        self.is_perspective = True
        self.position = glm.vec3(0.0, 10.0, 0.0)
        self._target = glm.vec3(0.0)
        self._smoothed_heading_radians = None

    @property
    def fog_density(self) -> float:
        return self._orbit.fog_density

    @property
    def _orbit(self) -> Orbit:
        return self._orbits[self.mode]

    def toggle_mode(self) -> None:
        self.mode = (
            CameraMode.OVERVIEW if self.mode is CameraMode.FOLLOW else CameraMode.FOLLOW
        )

    def toggle_projection(self) -> None:
        self.is_perspective = not self.is_perspective

    def orbit(self, horizontal_pixels: float, vertical_pixels: float) -> None:
        orbit = self._orbit
        orbit.heading_offset_radians -= horizontal_pixels * ORBIT_RADIANS_PER_PIXEL
        orbit.elevation_radians = _clamp(
            orbit.elevation_radians + vertical_pixels * ORBIT_RADIANS_PER_PIXEL,
            MIN_ELEVATION_RADIANS,
            MAX_ELEVATION_RADIANS,
        )

    def zoom(self, scroll_steps: float) -> None:
        orbit = self._orbit
        orbit.distance = _clamp(
            orbit.distance * (1.0 - ZOOM_FRACTION_PER_SCROLL_STEP * scroll_steps),
            orbit.min_distance,
            orbit.max_distance,
        )

    def reset(self) -> None:
        for orbit in self._orbits.values():
            orbit.reset()
        self._smoothed_heading_radians = None

    def update(self, elapsed_seconds: float, orca: Orca) -> None:
        if self.mode is CameraMode.FOLLOW:
            self._target = orca.position + glm.vec3(0.0, FOLLOW_TARGET_HEIGHT, 0.0)
            heading_radians = self._follow_heading(elapsed_seconds, orca)
        else:
            self._target = glm.vec3(self._maze.center)
            heading_radians = OVERVIEW_HEADING_RADIANS
        self.position = self._target + self._offset_from_target(heading_radians)

    def view_matrix(self) -> glm.mat4:
        return glm.lookAt(self.position, self._target, glm.vec3(0.0, 1.0, 0.0))

    def projection_matrix(self) -> glm.mat4:
        orbit = self._orbit
        if self.is_perspective:
            return glm.perspective(
                FIELD_OF_VIEW_RADIANS, self.aspect_ratio, orbit.near, orbit.far
            )
        # Same half height as the perspective has at the target's distance,
        # so the scene keeps its size when the projection changes.
        half_height = orbit.distance * math.tan(FIELD_OF_VIEW_RADIANS / 2)
        half_width = half_height * self.aspect_ratio
        return glm.ortho(
            -half_width, half_width, -half_height, half_height, orbit.near, orbit.far
        )

    def _follow_heading(self, elapsed_seconds: float, orca: Orca) -> float:
        """The camera heading chases the orca's with an exponential decay,
        which looks the same at any frame rate."""
        if self._smoothed_heading_radians is None:
            self._smoothed_heading_radians = orca.heading_radians
        difference_radians = math.remainder(
            orca.heading_radians - self._smoothed_heading_radians, 2.0 * math.pi
        )
        response = 1.0 - math.exp(-FOLLOW_TURN_RESPONSE_PER_SECOND * elapsed_seconds)
        self._smoothed_heading_radians += difference_radians * response
        return self._smoothed_heading_radians

    def _offset_from_target(self, heading_radians: float) -> glm.vec3:
        orbit = self._orbit
        total_heading_radians = heading_radians + orbit.heading_offset_radians
        horizontal_distance = orbit.distance * math.cos(orbit.elevation_radians)
        return glm.vec3(
            -math.sin(total_heading_radians) * horizontal_distance,
            orbit.distance * math.sin(orbit.elevation_radians),
            -math.cos(total_heading_radians) * horizontal_distance,
        )


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))

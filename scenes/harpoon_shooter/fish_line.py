"""Line of fish swimming across the top of the screen."""

from pathlib import Path

import numpy as np

from .difficulty import Difficulty, difficulty_for_score
from .fish_model import create_fish_drawables
from .geometry import segment_intersects_circle
from .shader_program import ShaderProgram
from .transform import transformation_matrix

SHADERS_DIRECTORY = Path(__file__).parent / "shaders"
TWO_PI = 2.0 * np.pi

FISH_COUNT = 6
BASE_SPACING = 0.4
LINE_Y = 0.75
EDGE_X = 1.15
FISH_SCALE = 0.06
FISH_HIT_RADIUS_MODEL = (
    1.06 
)
TAIL_WAVE_AMPLITUDE = 0.3
TAIL_WAVE_FREQUENCY_HZ = 6.0


class FishLine:
    def __init__(self, context, rng: np.random.Generator) -> None:
        self._shader_program = ShaderProgram(
            context,
            SHADERS_DIRECTORY / "body.vert",
            SHADERS_DIRECTORY / "color.frag",
        )
        self._drawables = create_fish_drawables(context, self._shader_program)
        self._rng = rng
        self._difficulty: Difficulty = difficulty_for_score(0)
        self._direction = 1
        self._progress = np.zeros(FISH_COUNT)
        self._phases = np.zeros(FISH_COUNT)
        self.reset()

    def reset(self) -> None:
        self._direction = int(self._rng.choice((-1, 1)))
        self._progress = (EDGE_X - 0.1) - BASE_SPACING * np.arange(FISH_COUNT)
        self._phases = self._rng.uniform(0.0, TWO_PI, FISH_COUNT)

    def update(self, delta_time_seconds: float, difficulty: Difficulty) -> None:
        self._difficulty = difficulty
        self._progress += difficulty.fish_speed * delta_time_seconds
        for index in np.flatnonzero(self._progress > EDGE_X):
            self._send_to_back(index)

    def catch_along(
        self,
        segment_start: np.ndarray,
        segment_end: np.ndarray,
        game_time_seconds: float,
    ) -> bool:
        """Removes the first fish touched by the segment and returns True if any was hit."""
        radius = FISH_SCALE * FISH_HIT_RADIUS_MODEL
        for index in range(FISH_COUNT):
            center = self._position(index, game_time_seconds)
            if segment_intersects_circle(segment_start, segment_end, center, radius):
                self._send_to_back(index)
                return True
        return False

    def draw(self, game_time_seconds: float) -> None:
        rotation = (
            0.0 if self._direction > 0 else np.pi
        )  # nose faces the swim direction
        for index in range(FISH_COUNT):
            transform = transformation_matrix(
                FISH_SCALE, rotation, self._position(index, game_time_seconds)
            )
            uniforms = {
                "wave_amplitude": TAIL_WAVE_AMPLITUDE,
                "wave_phase": float(
                    TWO_PI * TAIL_WAVE_FREQUENCY_HZ * game_time_seconds
                    + self._phases[index]
                ),
            }
            for drawable, color in self._drawables:
                drawable.draw(transform, color, uniforms)

    def _position(self, index: int, game_time_seconds: float) -> np.ndarray:
        x = self._direction * self._progress[index]
        bob = self._difficulty.bob_amplitude * np.sin(
            TWO_PI * self._difficulty.bob_frequency_hz * game_time_seconds
            + self._phases[index]
        )
        return np.array((x, LINE_Y + bob))

    def _send_to_back(self, index: int) -> None:
        """Moves a fish to the trailing end of the line, off screen, with a random gap."""
        others = np.delete(self._progress, index)
        rear = min(float(others.min()), -EDGE_X)
        gap = BASE_SPACING + self._rng.uniform(0.0, self._difficulty.extra_spacing_max)
        self._progress[index] = rear - gap
        self._phases[index] = self._rng.uniform(0.0, TWO_PI)

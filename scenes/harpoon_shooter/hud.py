"""Score marks, lives and state overlays, all drawn with geometry."""

from enum import Enum, auto
from pathlib import Path

import moderngl
import numpy as np

from .drawable_mesh import DrawableMesh
from .fish_model import create_fish_drawables
from .mesh import Mesh
from .shader_program import ShaderProgram
from .transform import transformation_matrix

SHADERS_DIRECTORY = Path(__file__).parent / "shaders"
STILL = {"wave_amplitude": 0.0, "wave_phase": 0.0}
IDENTITY = transformation_matrix(1.0, 0.0, (0.0, 0.0))
CIRCLE_SEGMENTS = 20
RECTANGLE_INDICES = [0, 1, 2, 0, 2, 3]

SCORE_MARK_SCALE = 0.02
SCORE_MARK_COLUMNS = 16
SCORE_MARK_SPACING = 0.1
SCORE_MARK_ROWS_Y = (-0.85, -0.92, -0.99)
MAX_SCORE_MARKS = SCORE_MARK_COLUMNS * len(
    SCORE_MARK_ROWS_Y
)

LIFE_RADIUS = 0.03
LIFE_ORIGIN = (-0.9, 0.9)
LIFE_SPACING = 0.1
LIFE_SLOTS = 3
LIFE_COLOR = (0.9, 0.2, 0.2, 1.0)

DIM_COLOR = (0.0, 0.0, 0.0, 0.45)
PLAY_COLOR = (1.0, 1.0, 1.0, 1.0)
PAUSE_COLOR = (1.0, 1.0, 1.0, 1.0)
GAME_OVER_COLOR = (0.9, 0.1, 0.1, 1.0)


class Overlay(Enum):
    START = auto()
    PAUSED = auto()
    GAME_OVER = auto()


def _rectangle(center, width: float, height: float, angle_radians: float) -> np.ndarray:
    corners = np.array(
        [
            (-width / 2, -height / 2),
            (width / 2, -height / 2),
            (width / 2, height / 2),
            (-width / 2, height / 2),
        ]
    )
    cosine, sine = np.cos(angle_radians), np.sin(angle_radians)
    rotation = np.array([[cosine, -sine], [sine, cosine]])
    return corners @ rotation.T + np.asarray(center, dtype=float)


def _circle_ring(radius: float) -> np.ndarray:
    angles = np.linspace(0.0, 2.0 * np.pi, CIRCLE_SEGMENTS, endpoint=False)
    return np.column_stack((radius * np.cos(angles), radius * np.sin(angles)))


class Hud:
    def __init__(self, context: moderngl.Context) -> None:
        program = ShaderProgram(
            context,
            SHADERS_DIRECTORY / "body.vert",
            SHADERS_DIRECTORY / "color.frag",
        )
        self._score_fish = create_fish_drawables(context, program)

        ring = _circle_ring(LIFE_RADIUS)
        filled_vertices = np.vstack(((0.0, 0.0), ring))
        filled_indices = list(range(CIRCLE_SEGMENTS + 1)) + [1]
        self._life_filled = DrawableMesh(
            context,
            Mesh(
                filled_vertices, moderngl.TRIANGLE_FAN, triangle_indices=filled_indices
            ),
            program,
        )
        self._life_lost = DrawableMesh(
            context,
            Mesh(
                ring, moderngl.LINE_LOOP, triangle_indices=list(range(CIRCLE_SEGMENTS))
            ),
            program,
        )

        self._overlays = self._build_overlays(context, program)

    @staticmethod
    def _build_overlays(context, program) -> dict:
        def part(vertices, indices, color):
            mesh = Mesh(
                np.asarray(vertices, dtype=float),
                moderngl.TRIANGLES,
                triangle_indices=indices,
            )
            return DrawableMesh(context, mesh, program), color

        dim = part(_rectangle((0.0, 0.0), 2.0, 2.0, 0.0), RECTANGLE_INDICES, DIM_COLOR)
        play = part([(-0.08, -0.12), (-0.08, 0.12), (0.12, 0.0)], [0, 1, 2], PLAY_COLOR)
        pause_left = part(
            _rectangle((-0.05, 0.0), 0.04, 0.25, 0.0), RECTANGLE_INDICES, PAUSE_COLOR
        )
        pause_right = part(
            _rectangle((0.05, 0.0), 0.04, 0.25, 0.0), RECTANGLE_INDICES, PAUSE_COLOR
        )
        cross_a = part(
            _rectangle((0.0, 0.0), 0.04, 0.5, np.pi / 4),
            RECTANGLE_INDICES,
            GAME_OVER_COLOR,
        )
        cross_b = part(
            _rectangle((0.0, 0.0), 0.04, 0.5, -np.pi / 4),
            RECTANGLE_INDICES,
            GAME_OVER_COLOR,
        )

        return {
            Overlay.START: [dim, play],
            Overlay.PAUSED: [dim, pause_left, pause_right],
            Overlay.GAME_OVER: [dim, cross_a, cross_b],
        }

    def draw(self, caught_count: int, lives_left: int, overlay: Overlay | None) -> None:
        for index in range(min(caught_count, MAX_SCORE_MARKS)):
            column = index % SCORE_MARK_COLUMNS
            row = index // SCORE_MARK_COLUMNS
            position = (-0.75 + column * SCORE_MARK_SPACING, SCORE_MARK_ROWS_Y[row])
            transform = transformation_matrix(SCORE_MARK_SCALE, 0.0, position)
            for drawable, color in self._score_fish:
                drawable.draw(transform, color, STILL)

        for slot in range(LIFE_SLOTS):
            center = (LIFE_ORIGIN[0] + slot * LIFE_SPACING, LIFE_ORIGIN[1])
            transform = transformation_matrix(1.0, 0.0, center)
            drawable = self._life_filled if slot < lives_left else self._life_lost
            drawable.draw(transform, LIFE_COLOR, STILL)

        if overlay is not None:
            for drawable, color in self._overlays[overlay]:
                drawable.draw(IDENTITY, color, STILL)

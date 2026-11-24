import math
from enum import Enum, auto

import moderngl

from .shape_brush import ShapeBrush

REFERENCE_HEIGHT_PIXELS = 720.0
SCORE_DIGITS = 5
PANEL_MARGIN = 20.0
PANEL_HEIGHT = 60.0
DIGIT_SPACING = 32.0
LIFE_SPACING = 40.0
FISH_SPACING = 30.0
OVERLAY_SIZE = 90.0
PULSE_PIXELS = 6.0

WHITE = (0.95, 0.97, 1.0, 1.0)
PANEL_COLOR = (0.02, 0.06, 0.12, 0.65)
BORDER_COLOR = (0.45, 0.75, 0.95, 1.0)
LIFE_COLOR = (0.95, 0.3, 0.35, 1.0)
FISH_COLOR = (1.0, 0.65, 0.15, 1.0)
EMPTY_COLOR = (0.5, 0.55, 0.6, 1.0)
DIM_COLOR = (0.0, 0.02, 0.05, 0.5)
VICTORY_COLOR = (0.35, 0.95, 0.5, 1.0)
GOLD_COLOR = (1.0, 0.85, 0.3, 1.0)


class Overlay(Enum):
    START = auto()
    PAUSED = auto()
    DEFEAT = auto()
    VICTORY = auto()


class Hud:
    """Score, lives and collected fish, plus a symbol for each game state,
    drawn with geometry in a second pass over the 3D scene: orthographic
    projection in pixels and no depth test. Sizes are given for a 720 pixel
    tall window and scale with its height."""

    def __init__(self, context: moderngl.Context) -> None:
        self._context = context
        self._brush = ShapeBrush(context)
        self._width_pixels = self._height_pixels = 1

    def resize(self, width_pixels: int, height_pixels: int) -> None:
        self._width_pixels = max(1, width_pixels)
        self._height_pixels = max(1, height_pixels)

    def draw(
        self,
        score_points: int,
        lives: int,
        max_lives: int,
        collected_fish: int,
        total_fish: int,
        overlay: Overlay | None,
        pulse: float,
    ) -> None:
        """`pulse`, between 0 and 1, makes the overlay rings breathe."""
        self._context.disable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        self._context.enable(moderngl.BLEND)
        self._context.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self._brush.begin(self._width_pixels, self._height_pixels)

        self._draw_score(score_points)
        self._draw_lives(lives, max_lives)
        self._draw_fish_counter(collected_fish, total_fish)
        if overlay is not None:
            self._draw_overlay(overlay, pulse)
        self._context.disable(moderngl.BLEND)

    def release(self) -> None:
        self._brush.release()

    @property
    def _scale(self) -> float:
        return self._height_pixels / REFERENCE_HEIGHT_PIXELS

    @property
    def _panel_bottom(self) -> float:
        return self._height_pixels - (PANEL_MARGIN + PANEL_HEIGHT) * self._scale

    def _draw_panel(self, left: float, width: float) -> None:
        corner = (left, self._panel_bottom)
        size = (width, PANEL_HEIGHT * self._scale)
        self._brush.rectangle(corner, size, PANEL_COLOR)
        self._brush.rectangle_outline(corner, size, BORDER_COLOR)

    def _draw_score(self, score_points: int) -> None:
        scale = self._scale
        left = PANEL_MARGIN * scale
        self._draw_panel(left, (SCORE_DIGITS * DIGIT_SPACING + 18) * scale)
        shown_points = min(score_points, 10**SCORE_DIGITS - 1)
        for index, character in enumerate(f"{shown_points:0{SCORE_DIGITS}d}"):
            corner = (
                left + (14 + index * DIGIT_SPACING) * scale,
                self._panel_bottom + 10 * scale,
            )
            self._brush.digit(
                int(character), corner, (22 * scale, 40 * scale), 5 * scale, WHITE
            )

    def _draw_lives(self, lives: int, max_lives: int) -> None:
        scale = self._scale
        width = (max_lives * LIFE_SPACING + 16) * scale
        left = self._width_pixels - PANEL_MARGIN * scale - width
        self._draw_panel(left, width)
        center_height = self._panel_bottom + PANEL_HEIGHT * scale / 2
        for index in range(max_lives):
            is_alive = index < lives
            center = (left + (28 + index * LIFE_SPACING) * scale, center_height)
            color = LIFE_COLOR if is_alive else EMPTY_COLOR
            self._brush.circle(center, 14 * scale, color, is_filled=is_alive)

    def _draw_fish_counter(self, collected_fish: int, total_fish: int) -> None:
        scale = self._scale
        width = (total_fish * FISH_SPACING + 20) * scale
        left = (self._width_pixels - width) / 2
        self._draw_panel(left, width)
        center_height = self._panel_bottom + PANEL_HEIGHT * scale / 2
        for index in range(total_fish):
            is_collected = index < collected_fish
            center = (left + (25 + index * FISH_SPACING) * scale, center_height)
            color = FISH_COLOR if is_collected else EMPTY_COLOR
            self._brush.diamond(center, 13 * scale, color, is_filled=is_collected)

    def _draw_overlay(self, overlay: Overlay, pulse: float) -> None:
        self._brush.rectangle(
            (0.0, 0.0), (self._width_pixels, self._height_pixels), DIM_COLOR
        )
        center = (self._width_pixels / 2, self._height_pixels / 2)
        size = OVERLAY_SIZE * self._scale
        ring_growth = PULSE_PIXELS * pulse
        if overlay is Overlay.START:
            self._draw_play_symbol(center, size, ring_growth)
        elif overlay is Overlay.PAUSED:
            self._draw_pause_symbol(center, size)
        elif overlay is Overlay.DEFEAT:
            self._draw_defeat_symbol(center, size)
        elif overlay is Overlay.VICTORY:
            self._draw_victory_symbol(center, size, ring_growth)

    def _draw_play_symbol(self, center, size: float, ring_growth: float) -> None:
        self._brush.play_triangle(center, size * 1.3, WHITE)
        self._brush.circle(center, size * 1.2 + ring_growth, BORDER_COLOR, False)

    def _draw_pause_symbol(self, center, size: float) -> None:
        center_x, center_y = center
        for horizontal_offset in (-0.45, 0.45):
            bar_center = (center_x + horizontal_offset * size, center_y)
            self._brush.rotated_bar(bar_center, (0.4 * size, 1.6 * size), 0.0, WHITE)

    def _draw_defeat_symbol(self, center, size: float) -> None:
        for angle_radians in (math.pi / 4, -math.pi / 4):
            self._brush.rotated_bar(
                center, (2.2 * size, 0.35 * size), angle_radians, LIFE_COLOR
            )
        self._brush.circle(center, size * 1.3, LIFE_COLOR, False)

    def _draw_victory_symbol(self, center, size: float, ring_growth: float) -> None:
        center_x, center_y = center
        short_stroke_center = (center_x - 0.45 * size, center_y - 0.25 * size)
        long_stroke_center = (center_x + 0.3 * size, center_y + 0.05 * size)
        self._brush.rotated_bar(
            short_stroke_center, (0.85 * size, 0.3 * size), -math.pi / 4, VICTORY_COLOR
        )
        self._brush.rotated_bar(
            long_stroke_center,
            (1.6 * size, 0.3 * size),
            math.radians(48.0),
            VICTORY_COLOR,
        )
        self._brush.circle(center, size * 1.3 + ring_growth, GOLD_COLOR, False)

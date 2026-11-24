import math

import glm
import moderngl
import numpy as np

from .shader_program import ShaderProgram

CIRCLE_SEGMENTS = 32
Z_AXIS = glm.vec3(0.0, 0.0, 1.0)
Color = tuple[float, float, float, float]

DIGIT_SEGMENTS = {
    0: "abcdef",
    1: "bc",
    2: "abdeg",
    3: "abcdg",
    4: "bcfg",
    5: "acdfg",
    6: "acdefg",
    7: "abc",
    8: "abcdefg",
    9: "abcdfg",
}


class ShapeBrush:
    """Draws flat 2D shapes in pixel coordinates with the `hud` shader.

    Five buffers are created once and placed by a transform, using four
    primitives: TRIANGLES (square, triangle), LINE_LOOP (square outline,
    circle outline) and TRIANGLE_FAN (filled circle).
    """

    def __init__(self, context: moderngl.Context) -> None:
        self._shader_program = ShaderProgram.named(context, "hud")
        circle_border = self._circle_border()
        shapes = {
            "square": [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1],
            "square_outline": [0, 0, 1, 0, 1, 1, 0, 1],
            "filled_circle": np.vstack([[0.0, 0.0], circle_border]),
            "circle_outline": circle_border[:-1],
            "triangle": [-0.4, -0.5, 0.6, 0.0, -0.4, 0.5],
        }
        self._buffers = {
            name: context.buffer(np.asarray(points, dtype="f4").tobytes())
            for name, points in shapes.items()
        }
        self._vertex_arrays = {
            name: context.vertex_array(
                self._shader_program.program, [(buffer, "2f", "vertex_position")]
            )
            for name, buffer in self._buffers.items()
        }

    def begin(self, width_pixels: int, height_pixels: int) -> None:
        """Sets a projection where (0, 0) is the bottom left pixel."""
        self._shader_program.set_uniform(
            "projection_matrix", glm.ortho(0, width_pixels, 0, height_pixels, -1, 1)
        )

    def rectangle(
        self,
        corner: tuple[float, float],
        size: tuple[float, float],
        color: Color,
    ) -> None:
        """Rectangle with its bottom left corner at `corner`."""
        transform = glm.scale(_translation(corner), glm.vec3(*size, 1.0))
        self._draw("square", moderngl.TRIANGLES, transform, color)

    def rotated_bar(
        self,
        center: tuple[float, float],
        size: tuple[float, float],
        angle_radians: float,
        color: Color,
    ) -> None:
        width, height = size
        transform = glm.rotate(_translation(center), angle_radians, Z_AXIS)
        transform = glm.translate(transform, glm.vec3(-width / 2, -height / 2, 0.0))
        transform = glm.scale(transform, glm.vec3(width, height, 1.0))
        self._draw("square", moderngl.TRIANGLES, transform, color)

    def rectangle_outline(
        self,
        corner: tuple[float, float],
        size: tuple[float, float],
        color: Color,
    ) -> None:
        transform = glm.scale(_translation(corner), glm.vec3(*size, 1.0))
        self._draw("square_outline", moderngl.LINE_LOOP, transform, color)

    def circle(
        self,
        center: tuple[float, float],
        radius: float,
        color: Color,
        is_filled: bool = True,
    ) -> None:
        transform = glm.scale(_translation(center), glm.vec3(radius, radius, 1.0))
        if is_filled:
            self._draw("filled_circle", moderngl.TRIANGLE_FAN, transform, color)
        else:
            self._draw("circle_outline", moderngl.LINE_LOOP, transform, color)

    def diamond(
        self,
        center: tuple[float, float],
        side: float,
        color: Color,
        is_filled: bool = True,
    ) -> None:
        transform = glm.rotate(_translation(center), math.pi / 4, Z_AXIS)
        transform = glm.translate(transform, glm.vec3(-side / 2, -side / 2, 0.0))
        transform = glm.scale(transform, glm.vec3(side, side, 1.0))
        if is_filled:
            self._draw("square", moderngl.TRIANGLES, transform, color)
        else:
            self._draw("square_outline", moderngl.LINE_LOOP, transform, color)

    def play_triangle(
        self, center: tuple[float, float], size: float, color: Color
    ) -> None:
        transform = glm.scale(_translation(center), glm.vec3(size, size, 1.0))
        self._draw("triangle", moderngl.TRIANGLES, transform, color)

    def digit(
        self,
        value: int,
        corner: tuple[float, float],
        size: tuple[float, float],
        thickness: float,
        color: Color,
    ) -> None:
        """Seven segment digit with its bottom left corner at `corner`. The
        segments are named like this::

              a
            f   b
              g
            e   c
              d
        """
        segments = _digit_segment_rectangles(corner, size, thickness)
        for segment in DIGIT_SEGMENTS[value]:
            self.rectangle(*segments[segment], color)

    def release(self) -> None:
        for vertex_array in self._vertex_arrays.values():
            vertex_array.release()
        for buffer in self._buffers.values():
            buffer.release()
        self._shader_program.release()

    def _draw(
        self, shape: str, primitive: int, transform: glm.mat4, color: Color
    ) -> None:
        self._shader_program.set_uniforms(
            {"shape_transform": transform, "shape_color": color}
        )
        self._vertex_arrays[shape].render(primitive)

    @staticmethod
    def _circle_border() -> np.ndarray:
        angles_radians = np.linspace(0.0, 2.0 * np.pi, CIRCLE_SEGMENTS + 1)
        return np.column_stack([np.cos(angles_radians), np.sin(angles_radians)])


def _translation(position: tuple[float, float]) -> glm.mat4:
    return glm.translate(glm.mat4(1.0), glm.vec3(*position, 0.0))


def _digit_segment_rectangles(
    corner: tuple[float, float], size: tuple[float, float], thickness: float
) -> dict[str, tuple[tuple[float, float], tuple[float, float]]]:
    left, bottom = corner
    width, height = size
    right = left + width - thickness
    middle = bottom + height / 2 - thickness / 2
    horizontal = (width, thickness)
    upper_vertical = (thickness, height / 2 + thickness / 2)
    lower_vertical = (thickness, height / 2)
    return {
        "a": ((left, bottom + height - thickness), horizontal),
        "g": ((left, middle), horizontal),
        "d": ((left, bottom), horizontal),
        "f": ((left, middle), upper_vertical),
        "b": ((right, middle), upper_vertical),
        "e": ((left, bottom), lower_vertical),
        "c": ((right, bottom), lower_vertical),
    }

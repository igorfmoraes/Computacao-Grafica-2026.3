import math

import glm
import moderngl
import numpy as np

from .camera import Camera
from .shader_program import ShaderProgram

TENTACLE_COUNT = 8
SEGMENTS_PER_TENTACLE = 10
RING_RADIUS = 0.45
TENTACLE_LENGTH = 1.4
TIP_NARROWING = 0.3
COLOR = glm.vec3(0.8, 0.3, 0.7)


class Tentacles:
    """Jellyfish tentacles: line segments (GL_LINES) hanging from a ring.

    Each vertex stores its position and how far along the tentacle it is,
    which the vertex shader uses to wave the tip more than the root.
    """

    def __init__(self, context: moderngl.Context) -> None:
        self._shader_program = ShaderProgram.named(context, "tentacles")
        self._vertex_buffer = context.buffer(self._line_vertices().tobytes())
        self._vertex_array = context.vertex_array(
            self._shader_program.program,
            [
                (
                    self._vertex_buffer,
                    "3f 1f",
                    "vertex_position",
                    "vertex_length_fraction",
                )
            ],
        )

    def begin_frame(self, camera: Camera, fog_color: glm.vec3) -> None:
        self._shader_program.set_uniforms(
            {
                "view_matrix": camera.view_matrix(),
                "projection_matrix": camera.projection_matrix(),
                "camera_position": camera.position,
                "tentacle_color": COLOR,
                "fog_color": fog_color,
                "fog_density": camera.fog_density,
            }
        )

    def draw(
        self, model_matrix: glm.mat4, elapsed_time_seconds: float, phase_radians: float
    ) -> None:
        self._shader_program.set_uniforms(
            {
                "model_matrix": model_matrix,
                "elapsed_time_seconds": elapsed_time_seconds,
                "phase_radians": phase_radians,
            }
        )
        self._vertex_array.render(moderngl.LINES)

    def release(self) -> None:
        self._vertex_array.release()
        self._vertex_buffer.release()
        self._shader_program.release()

    @staticmethod
    def _line_vertices() -> np.ndarray:
        fractions = np.linspace(0.0, 1.0, SEGMENTS_PER_TENTACLE + 1)
        segment_ends = np.repeat(fractions, 2)[1:-1]
        vertices = [
            Tentacles._tentacle_vertex(tentacle_index, fraction)
            for tentacle_index in range(TENTACLE_COUNT)
            for fraction in segment_ends
        ]
        return np.array(vertices, dtype="f4")

    @staticmethod
    def _tentacle_vertex(tentacle_index: int, fraction: float) -> list[float]:
        angle_radians = 2.0 * math.pi * tentacle_index / TENTACLE_COUNT
        radius = RING_RADIUS * (1.0 - TIP_NARROWING * fraction)
        return [
            radius * math.cos(angle_radians),
            -TENTACLE_LENGTH * fraction,
            radius * math.sin(angle_radians),
            fraction,
        ]

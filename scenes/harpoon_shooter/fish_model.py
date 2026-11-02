from pathlib import Path

import moderngl
import numpy as np

from .drawable_mesh import DrawableMesh
from .mesh import Mesh
from .triangulation import ear_clip

FISH_BODY_COLOR = (1.0, 0.45, 0.2, 1.0)
FISH_EYE_COLOR = (0.05, 0.05, 0.1, 1.0)
CURVE_SAMPLES_PER_LOOP = 36
EYE_CENTER = (0.6, 0.12)
EYE_RADIUS = 0.07
EYE_SEGMENTS = 16


def fish_curve(angles: np.ndarray) -> np.ndarray:
    x = np.cos(angles) - np.sin(angles) ** 2 / np.sqrt(2.0)
    y = np.cos(angles) * np.sin(angles)
    return np.column_stack((x, y))


def _body_and_tail_mesh() -> Mesh:
    body_angles = np.linspace(-np.pi / 2, np.pi / 2, CURVE_SAMPLES_PER_LOOP)[:-1]
    tail_angles = np.linspace(np.pi / 2, 3 * np.pi / 2, CURVE_SAMPLES_PER_LOOP)[:-1]
    body = fish_curve(body_angles)
    tail = fish_curve(tail_angles)

    vertices = np.vstack((body, tail))
    body_indices = ear_clip(body)
    tail_indices = [index + len(body) for index in ear_clip(tail)]
    return Mesh(
        vertices, moderngl.TRIANGLES, triangle_indices=body_indices + tail_indices
    )


def _eye_mesh() -> Mesh:
    angles = np.linspace(0.0, 2.0 * np.pi, EYE_SEGMENTS, endpoint=False)
    ring = np.column_stack((EYE_RADIUS * np.cos(angles), EYE_RADIUS * np.sin(angles)))
    ring += np.array(EYE_CENTER)
    vertices = np.vstack((np.array(EYE_CENTER), ring))  # index 0 is the center
    indices = list(range(EYE_SEGMENTS + 1)) + [1]  # closes the fan
    return Mesh(vertices, moderngl.TRIANGLE_FAN, triangle_indices=indices)


def create_fish_drawables(context: moderngl.Context, shader_program) -> list:
    """Creates the fish VBOs once. Returns (DrawableMesh, color) pairs."""
    return [
        (DrawableMesh(context, _body_and_tail_mesh(), shader_program), FISH_BODY_COLOR),
        (DrawableMesh(context, _eye_mesh(), shader_program), FISH_EYE_COLOR),
    ]

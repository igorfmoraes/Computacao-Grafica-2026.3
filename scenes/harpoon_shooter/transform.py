import numpy as np


def transformation_matrix(
    scale: float,
    rotation_radians: float,
    translation: tuple[float, float],
) -> np.ndarray:
    """Builds a 4x4 matrix (column-vector convention) that scales, then rotates, then translates."""
    cosine = np.cos(rotation_radians)
    sine = np.sin(rotation_radians)
    translation_x, translation_y = translation

    return np.array(
        [
            [scale * cosine, -scale * sine, 0.0, translation_x],
            [scale * sine, scale * cosine, 0.0, translation_y],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )

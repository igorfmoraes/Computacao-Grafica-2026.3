"""Images generated with numpy when the game starts.

The colors are written as seen on screen (sRGB). Every pattern is periodic
(the noise grid wraps around and the sines have integer frequencies), so the
images tile without visible seams under GL_REPEAT.
"""

import numpy as np

RANDOM_SEED = 2026
OPAQUE_ALPHA = 255


def sand_image(side_pixels: int = 512) -> np.ndarray:
    generator = np.random.default_rng(RANDOM_SEED)
    noise = _fractal_noise(side_pixels, generator, base_cells=8, octaves=5)
    rows, columns = _normalized_pixel_grid(side_pixels)
    ripples = 0.5 + 0.5 * np.sin(2.0 * np.pi * (3 * columns + 2 * rows) + 5.0 * noise)
    grains = generator.random((side_pixels, side_pixels))
    brightness = 0.55 * noise + 0.3 * ripples + 0.15 * grains
    return _opaque(_blend((120, 108, 78), (215, 196, 150), brightness))


def stone_blocks_image(
    side_pixels: int = 512, block_rows: int = 8, block_columns: int = 4
) -> np.ndarray:
    """Stone blocks laid in a running bond, with algae where the noise is
    high."""
    generator = np.random.default_rng(RANDOM_SEED + 1)
    block_height = side_pixels // block_rows
    block_width = side_pixels // block_columns
    rows, columns = np.mgrid[0:side_pixels, 0:side_pixels]
    block_row = rows // block_height
    shifted_columns = (columns + (block_row % 2) * (block_width // 2)) % side_pixels
    block_column = shifted_columns // block_width
    row_in_block = rows % block_height
    column_in_block = shifted_columns % block_width

    block_tone = generator.uniform(0.75, 1.15, (block_rows, block_columns))
    noise = _fractal_noise(side_pixels, generator, base_cells=8, octaves=4)
    color = np.array((88, 100, 110)) * (
        block_tone[block_row, block_column] * (0.8 + 0.4 * noise)
    )[..., None]
    distance_to_block_edge = np.minimum(
        np.minimum(row_in_block, block_height - row_in_block),
        np.minimum(column_in_block, block_width - column_in_block),
    )
    color *= np.clip(0.75 + distance_to_block_edge / 30.0, 0.0, 1.0)[..., None]

    algae = np.clip((_fractal_noise(side_pixels, generator, 4) - 0.55) * 5.0, 0.0, 1.0)
    color = _blend_arrays(color, np.array((40, 95, 50)), algae * 0.7)
    mortar_width_pixels = 5
    is_mortar = (row_in_block < mortar_width_pixels) | (
        column_in_block < mortar_width_pixels
    )
    color[is_mortar] = (32, 40, 46)
    return _opaque(color)


def orca_skin_image(side_pixels: int = 512) -> np.ndarray:
    """Made for the cylindrical mapping around the orca's length: u is the
    angle (0.5 on the back, 0 and 1 on the belly) and v goes from the head
    (0) to the tail (1). Black on top, white below, with the white patch
    behind the eye and the gray saddle behind the dorsal fin."""
    generator = np.random.default_rng(RANDOM_SEED + 2)
    v, u = _texture_coordinate_grid(side_pixels)
    distance_from_back = np.abs(u - 0.5)

    is_white = distance_from_back > _belly_boundary(v)
    is_eye_patch = (
        ((distance_from_back - 0.17) / 0.045) ** 2 + ((v - 0.2) / 0.06) ** 2 < 1.0
    )
    is_saddle = (distance_from_back < 0.07) & (np.abs(v - 0.52) < 0.06)

    color = np.empty((side_pixels, side_pixels, 3))
    color[:] = (18, 20, 26)
    color[is_saddle] = (95, 98, 108)
    color[is_white | is_eye_patch] = (236, 236, 230)
    noise = _fractal_noise(side_pixels, generator, base_cells=8, octaves=3)
    return _opaque(color * (0.9 + 0.2 * noise)[..., None])


def fish_scales_image(side_pixels: int = 256, scales_per_side: int = 16) -> np.ndarray:
    """Golden scales that darken towards their border. The color goes from
    the light belly (v = 0) to the orange back (v = 1)."""
    v, _ = _texture_coordinate_grid(side_pixels)
    rows, columns = np.mgrid[0:side_pixels, 0:side_pixels]
    scale_size_pixels = side_pixels / scales_per_side
    scale_row = np.floor(rows / scale_size_pixels)
    row_in_scale = (rows / scale_size_pixels) % 1.0
    column_in_scale = (columns / scale_size_pixels + 0.5 * (scale_row % 2)) % 1.0
    distance_to_center = np.hypot(column_in_scale - 0.5, row_in_scale - 0.2)
    shading = np.clip(1.15 - distance_to_center * 1.1, 0.55, 1.0)
    color = _blend((250, 225, 150), (235, 110, 25), np.clip(v * 1.6, 0.0, 1.0))
    return _opaque(color * shading[..., None])


def white_image() -> np.ndarray:
    return np.full((4, 4, 4), 255, dtype="u1")


def _belly_boundary(v: np.ndarray) -> np.ndarray:
    """Distance from the back where the white belly starts: it rises under
    the chin and vanishes towards the tail."""
    boundary = 0.30 + 0.03 * np.sin(v * 18.0)
    boundary = np.where(v < 0.3, 0.30 - 0.1 * (0.3 - v) / 0.3, boundary)
    return np.where(v > 0.75, 0.30 + (v - 0.75) * 1.2, boundary)


def _periodic_value_noise(
    side_pixels: int, cells: int, generator: np.random.Generator
) -> np.ndarray:
    """Random values on a cells x cells grid that wraps around, interpolated
    with the smooth curve 3f^2 - 2f^3."""
    grid = generator.random((cells, cells))
    position = np.arange(side_pixels) * cells / side_pixels
    lower_cell = np.floor(position).astype(int)
    upper_cell = (lower_cell + 1) % cells
    fraction = position - lower_cell
    fraction = fraction * fraction * (3.0 - 2.0 * fraction)
    row_fraction, column_fraction = fraction[:, None], fraction[None, :]
    top = (
        grid[np.ix_(lower_cell, lower_cell)] * (1 - column_fraction)
        + grid[np.ix_(lower_cell, upper_cell)] * column_fraction
    )
    bottom = (
        grid[np.ix_(upper_cell, lower_cell)] * (1 - column_fraction)
        + grid[np.ix_(upper_cell, upper_cell)] * column_fraction
    )
    return top * (1 - row_fraction) + bottom * row_fraction


def _fractal_noise(
    side_pixels: int,
    generator: np.random.Generator,
    base_cells: int = 4,
    octaves: int = 4,
) -> np.ndarray:
    """Sum of noise octaves, each with twice the cells and half the weight of
    the previous one, normalized to [0, 1]."""
    weights = [0.5**octave for octave in range(octaves)]
    layers = [
        weight * _periodic_value_noise(side_pixels, base_cells * 2**octave, generator)
        for octave, weight in enumerate(weights)
    ]
    return sum(layers) / sum(weights)


def _normalized_pixel_grid(side_pixels: int) -> tuple[np.ndarray, np.ndarray]:
    rows, columns = np.mgrid[0:side_pixels, 0:side_pixels]
    return rows / side_pixels, columns / side_pixels


def _texture_coordinate_grid(side_pixels: int) -> tuple[np.ndarray, np.ndarray]:
    """(v, u) at each pixel center. Image row 0 is v = 1, because the texture
    upload flips the image so the bottom row is t = 0."""
    rows, columns = np.mgrid[0:side_pixels, 0:side_pixels]
    return 1.0 - (rows + 0.5) / side_pixels, (columns + 0.5) / side_pixels


def _blend(first_color, second_color, amount: np.ndarray) -> np.ndarray:
    amount = np.clip(amount, 0.0, 1.0)[..., None]
    return np.array(first_color) * (1 - amount) + np.array(second_color) * amount


def _blend_arrays(colors: np.ndarray, tint, amount: np.ndarray) -> np.ndarray:
    return colors * (1 - amount[..., None]) + tint * amount[..., None]


def _opaque(colors: np.ndarray) -> np.ndarray:
    rgb = np.clip(colors, 0, 255).astype("u1")
    alpha = np.full(rgb.shape[:2] + (1,), OPAQUE_ALPHA, dtype="u1")
    return np.concatenate([rgb, alpha], axis=2)

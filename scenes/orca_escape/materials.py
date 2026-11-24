from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    """Phong coefficients, in linear light.

    `diffuse` multiplies the texture color, so a white diffuse shows the
    texture as it is. `shininess` is the specular exponent.
    """

    ambient: tuple[float, float, float]
    diffuse: tuple[float, float, float]
    specular: tuple[float, float, float]
    shininess: float


STONE = Material((0.35, 0.35, 0.35), (0.9, 0.9, 0.9), (0.04, 0.04, 0.04), 8.0)
SAND = Material((0.4, 0.4, 0.4), (1.0, 1.0, 1.0), (0.02, 0.02, 0.02), 4.0)
ORCA_SKIN = Material((0.3, 0.3, 0.3), (1.0, 1.0, 1.0), (0.6, 0.6, 0.6), 64.0)
FISH_SCALES = Material((0.4, 0.4, 0.4), (1.0, 1.0, 1.0), (0.9, 0.8, 0.5), 96.0)
JELLYFISH_BELL = Material((0.3, 0.3, 0.3), (0.7, 0.25, 0.6), (0.9, 0.9, 0.9), 128.0)
EXIT_RING = Material((0.2, 0.2, 0.2), (0.5, 0.5, 0.55), (1.0, 1.0, 1.0), 200.0)

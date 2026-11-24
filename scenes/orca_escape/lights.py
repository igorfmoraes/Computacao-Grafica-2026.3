import math
from dataclasses import dataclass, field

import glm


@dataclass
class DirectionalLight:
    """Light from the surface, coming from above and a bit to the side."""

    direction: glm.vec3 = field(
        default_factory=lambda: glm.normalize(glm.vec3(0.35, -1.0, 0.25))
    )
    color: glm.vec3 = field(default_factory=lambda: glm.vec3(0.35, 0.55, 0.65))
    is_enabled: bool = True

    def uniforms(self) -> dict:
        return {
            "directional_light_enabled": self.is_enabled,
            "directional_light_direction": self.direction,
            "directional_light_color": self.color,
        }


@dataclass
class SpotLight:
    """The orca's headlight. The intensity fades smoothly between the inner
    and the outer cone and is zero outside the outer one. `attenuation` holds
    the constant, linear and quadratic terms of 1 / (c + l d + q d^2)."""

    position: glm.vec3 = field(default_factory=glm.vec3)
    direction: glm.vec3 = field(default_factory=lambda: glm.vec3(0.0, 0.0, 1.0))
    color: glm.vec3 = field(default_factory=lambda: glm.vec3(2.4, 2.3, 2.0))
    inner_cone_cosine: float = math.cos(math.radians(14.0))
    outer_cone_cosine: float = math.cos(math.radians(26.0))
    attenuation: glm.vec3 = field(default_factory=lambda: glm.vec3(1.0, 0.06, 0.012))
    is_enabled: bool = True

    def uniforms(self) -> dict:
        return {
            "spot_light_enabled": self.is_enabled,
            "spot_light_position": self.position,
            "spot_light_direction": self.direction,
            "spot_light_color": self.color,
            "spot_light_inner_cone_cosine": self.inner_cone_cosine,
            "spot_light_outer_cone_cosine": self.outer_cone_cosine,
            "spot_light_attenuation": self.attenuation,
        }


@dataclass
class PointLight:
    """The exit's light: red while closed, green once open."""

    CLOSED_COLOR = glm.vec3(1.6, 0.25, 0.15)
    OPEN_COLOR = glm.vec3(0.3, 2.2, 0.8)

    position: glm.vec3 = field(default_factory=glm.vec3)
    color: glm.vec3 = field(default_factory=lambda: glm.vec3(1.6, 0.25, 0.15))
    attenuation: glm.vec3 = field(default_factory=lambda: glm.vec3(1.0, 0.12, 0.04))
    is_enabled: bool = True

    def uniforms(self) -> dict:
        return {
            "point_light_enabled": self.is_enabled,
            "point_light_position": self.position,
            "point_light_color": self.color,
            "point_light_attenuation": self.attenuation,
        }

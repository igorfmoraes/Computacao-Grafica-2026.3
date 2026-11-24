import math
from dataclasses import dataclass

import glm

TOUCHING_DISTANCE_SQUARED = 1e-9


@dataclass
class Sphere:
    center: glm.vec3
    radius: float

    def overlaps(self, other: "Sphere") -> bool:
        """Two spheres touch when the distance between the centers is less
        than the sum of the radii (compared squared, without a square root)."""
        offset = self.center - other.center
        return glm.dot(offset, offset) < (self.radius + other.radius) ** 2


class Box:
    """Axis aligned box given by its lower and upper corners."""

    def __init__(self, lower_corner, upper_corner) -> None:
        self.lower_corner = glm.vec3(lower_corner)
        self.upper_corner = glm.vec3(upper_corner)

    def push_out(self, sphere: Sphere) -> glm.vec3 | None:
        """The shortest translation that takes `sphere` out of the box, or
        None when they do not touch.

        The point of the box closest to the center is the center clamped to
        the box; if it is closer than one radius, the sphere leaves in its
        direction.
        """
        closest_point = glm.clamp(sphere.center, self.lower_corner, self.upper_corner)
        offset = sphere.center - closest_point
        distance_squared = glm.dot(offset, offset)
        if distance_squared >= sphere.radius**2:
            return None
        if distance_squared <= TOUCHING_DISTANCE_SQUARED:
            return self._exit_through_nearest_face(sphere)
        distance = math.sqrt(distance_squared)
        return offset * ((sphere.radius - distance) / distance)

    def _exit_through_nearest_face(self, sphere: Sphere) -> glm.vec3:
        """For a center inside the box, where the offset to the closest point
        has no direction."""
        exits = []
        for axis in range(3):
            below = sphere.center[axis] - self.lower_corner[axis] + sphere.radius
            above = self.upper_corner[axis] - sphere.center[axis] + sphere.radius
            exits += [(below, axis, -below), (above, axis, above)]
        _, axis, signed_distance = min(exits)
        translation = glm.vec3(0.0)
        translation[axis] = signed_distance
        return translation

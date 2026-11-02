"""Ear-clipping triangulation for simple polygons (no self-intersections)."""

import numpy as np


def signed_area(points: np.ndarray) -> float:
    x, y = points[:, 0], points[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


def _cross(origin, a, b) -> float:
    """Positive when b is counterclockwise from a, seen from origin."""
    return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (
        b[0] - origin[0]
    )


def _point_in_counterclockwise_triangle(p, a, b, c) -> bool:
    return _cross(a, b, p) >= 0 and _cross(b, c, p) >= 0 and _cross(c, a, p) >= 0


def ear_clip(points) -> list[int]:
    """Returns triangle indices (into `points`) covering a simple polygon."""
    points = np.asarray(points, dtype=float)
    remaining = list(range(len(points)))
    if signed_area(points) < 0:
        remaining.reverse()

    triangles: list[int] = []
    while len(remaining) > 3:
        for k in range(len(remaining)):
            previous_index = remaining[k - 1]
            current_index = remaining[k]
            next_index = remaining[(k + 1) % len(remaining)]
            a, b, c = points[previous_index], points[current_index], points[next_index]

            if _cross(a, b, c) <= 0:  # reflex or flat vertex, not an ear
                continue
            others = (
                points[j]
                for j in remaining
                if j not in (previous_index, current_index, next_index)
            )
            if any(_point_in_counterclockwise_triangle(p, a, b, c) for p in others):
                continue

            triangles += [previous_index, current_index, next_index]
            del remaining[k]
            break
        else:
            raise ValueError("ear clipping failed: polygon is not simple")

    triangles += remaining
    return triangles

import numpy as np


def segment_intersects_circle(
    segment_start: np.ndarray,
    segment_end: np.ndarray,
    circle_center: np.ndarray,
    circle_radius: float,
) -> bool:
    """True if the segment passes within `circle_radius` of `circle_center`."""
    segment_vector = segment_end - segment_start
    segment_length_squared = float(np.dot(segment_vector, segment_vector))

    if segment_length_squared == 0.0:
        closest_point = segment_start
    else:
        fraction_along_segment = np.clip(
            np.dot(circle_center - segment_start, segment_vector) / segment_length_squared,
            0.0,
            1.0,
        )
        closest_point = segment_start + fraction_along_segment * segment_vector

    offset_to_center = closest_point - circle_center
    return float(np.dot(offset_to_center, offset_to_center)) <= circle_radius * circle_radius

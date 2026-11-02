from dataclasses import dataclass


@dataclass(frozen=True)
class Difficulty:
    fish_speed: float  # units per second
    extra_spacing_max: float  # random extra gap added when a fish re-enters the line
    bob_amplitude: float  # vertical bobbing amplitude (NDC)
    bob_frequency_hz: float


def difficulty_for_score(score: int) -> Difficulty:
    return Difficulty(
        fish_speed=min(0.25 + 0.03 * score, 1.2),
        extra_spacing_max=min(0.1 + 0.04 * score, 0.8),
        bob_amplitude=min(0.02 + 0.005 * score, 0.1),
        bob_frequency_hz=min(0.8 + 0.1 * score, 3.0),
    )

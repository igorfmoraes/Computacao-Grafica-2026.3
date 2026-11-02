import moderngl
import numpy as np

from .background import Background
from .difficulty import difficulty_for_score
from .fish_line import FishLine
from .harpoon import Harpoon
from .hud import Hud, Overlay
from .player import Player


class Scene:
    MAX_MISSED_HARPOONS = 3

    def __init__(
        self,
        background: Background,
        player: Player,
        harpoon: Harpoon,
        fish_line: FishLine,
        hud: Hud,
    ) -> None:
        self._background = background
        self._player = player
        self._harpoon = harpoon
        self._fish_line = fish_line
        self._hud = hud
        self._game_time_seconds = 0.0
        self._caught_count = 0
        self._missed_count = 0

    @classmethod
    def build(cls, context: moderngl.Context) -> "Scene":
        rng = np.random.default_rng()
        return cls(
            Background(context),
            Player(context),
            Harpoon(context),
            FishLine(context, rng),
            Hud(context),
        )

    @property
    def player(self) -> Player:
        return self._player

    @property
    def lives_left(self) -> int:
        return max(self.MAX_MISSED_HARPOONS - self._missed_count, 0)

    @property
    def is_game_over(self) -> bool:
        return self._missed_count >= self.MAX_MISSED_HARPOONS

    def reset(self) -> None:
        self._game_time_seconds = 0.0
        self._caught_count = 0
        self._missed_count = 0
        self._harpoon.stop()
        self._player.rotation_radians = 0.0
        self._fish_line.reset()

    def fire_harpoon(self) -> None:
        self._harpoon.fire(self._player.position, self._player.rotation_radians)

    def update(self, delta_time_seconds: float) -> None:
        """Only called while the game is running, so pauses do not advance game time."""
        self._game_time_seconds += delta_time_seconds
        self._fish_line.update(
            delta_time_seconds, difficulty_for_score(self._caught_count)
        )

        if not self._harpoon.is_flying:
            return

        self._harpoon.advance(delta_time_seconds)
        if self._fish_line.catch_along(
            self._harpoon.previous_tip_position,
            self._harpoon.tip_position,
            self._game_time_seconds,
        ):
            self._harpoon.stop()
            self._caught_count += 1
        elif self._harpoon.has_left_screen():
            self._harpoon.stop()
            self._missed_count += 1

    def render(self, elapsed_time_seconds: float, overlay: Overlay | None) -> None:
        self._background.clear(elapsed_time_seconds)
        self._fish_line.draw(self._game_time_seconds)
        self._harpoon.draw()
        self._player.draw(elapsed_time_seconds)
        self._hud.draw(self._caught_count, self.lives_left, overlay)

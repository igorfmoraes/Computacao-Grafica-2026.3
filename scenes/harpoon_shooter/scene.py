import moderngl

from .background import Background
from .player import Player

import moderngl

from .background import Background
from .harpoon import Harpoon
from .player import Player


class Scene:
    def __init__(
        self, background: Background, player: Player, harpoon: Harpoon
    ) -> None:
        self._background = background
        self._player = player
        self._harpoon = harpoon

    @classmethod
    def build(cls, context: moderngl.Context) -> "Scene":
        return cls(Background(context), Player(context), Harpoon(context))

    @property
    def player(self) -> Player:
        return self._player

    def fire_harpoon(self) -> None:
        self._harpoon.fire(self._player.position, self._player.rotation_radians)

    def update(self, delta_time_seconds: float) -> None:
        self._harpoon.update(delta_time_seconds)

    def render(self, elapsed_time_seconds: float) -> None:
        self._background.clear(elapsed_time_seconds)
        self._harpoon.draw()
        self._player.draw(elapsed_time_seconds)

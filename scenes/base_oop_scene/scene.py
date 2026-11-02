import moderngl

from .background import Background
from .player import Player


class Scene:
    def __init__(self, background: Background, player: Player) -> None:
        self._background = background
        self._player = player

    @classmethod
    def build(cls, context: moderngl.Context) -> "Scene":
        return cls(Background(context), Player(context))

    def render(self, elapsed_time_seconds: float) -> None:
        self._background.clear(elapsed_time_seconds)
        self._player.draw(elapsed_time_seconds)

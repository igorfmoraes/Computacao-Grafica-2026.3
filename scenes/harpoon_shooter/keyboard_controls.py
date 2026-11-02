import glfw
import numpy as np
from .window import Window
from .player import Player

ROTATION_SPEED_RADIANS_PER_SECOND = np.radians(90.0)


class KeyboardControls:
    """Maps keyboard keys to actions on the window and on the scene settings.

    Args:
        window: Window that closes when Escape is pressed.
        settings: Settings changed by the A, F and D keys.

    Register `handle_key_press` with `Window.add_key_press_listener` to activate it.
    """

    HELP_TEXT = (
        "ESC - Fecha o Jogo\n"
        "SETAS ESQUERDA/DIREITA - Giram o Jogador\n"
        "ESPACO - Atira o Arpao\n"
    )

    def __init__(self, window: Window, player: Player, on_fire) -> None:
        self._window = window
        self._player = player
        self._actions = {
            glfw.KEY_ESCAPE: window.request_close,
            glfw.KEY_SPACE: on_fire,
        }

    def handle_key_press(self, key: int) -> None:
        """Runs the action bound to `key`; keys without an action are ignored."""
        action = self._actions.get(key)
        if action is None:
            return
        action()

    def update(self, delta_time_seconds: float) -> None:
        """Applies continuous input (held keys) for one frame."""
        direction = 0
        if self._window.is_key_down(glfw.KEY_LEFT):
            direction += 1
        if self._window.is_key_down(glfw.KEY_RIGHT):
            direction -= 1
        if direction != 0:
            self._player.rotate(
                direction * ROTATION_SPEED_RADIANS_PER_SECOND * delta_time_seconds
            )

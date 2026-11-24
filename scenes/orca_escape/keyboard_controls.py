from typing import Callable

import glfw

from .orca import SwimInput
from .window import Window

FORWARD_KEYS = (glfw.KEY_W, glfw.KEY_UP)
BACKWARD_KEYS = (glfw.KEY_S, glfw.KEY_DOWN)
LEFT_KEYS = (glfw.KEY_A, glfw.KEY_LEFT)
RIGHT_KEYS = (glfw.KEY_D, glfw.KEY_RIGHT)
TURBO_KEYS = (glfw.KEY_LEFT_SHIFT, glfw.KEY_RIGHT_SHIFT)


class KeyboardControls:
    """Discrete actions arrive through the key callback; continuous swimming
    is polled each frame with glfw.get_key.

    Args:
        window: Window whose keys are read.
        actions: Action to run when each key is pressed.

    Register `handle_key_press` with `Window.add_key_press_listener` to
    activate the actions.
    """

    HELP_TEXT = (
        "W/S ou setas - nada para frente/tras | A/D ou setas - gira | SHIFT - turbo\n"
        "ENTER - inicia | P - pausa | R - reinicia | C - camera | O - projecao\n"
        "L - luz direcional | F - lanterna | K - luz da saida | V - vsync\n"
        "Z - camera padrao | mouse: arrastar gira, roda aproxima | ESC - sai\n"
    )

    def __init__(self, window: Window, actions: dict[int, Callable[[], None]]) -> None:
        self._window = window
        self._actions = actions

    def handle_key_press(self, key: int) -> None:
        """Runs the action bound to `key`; keys without an action are
        ignored."""
        action = self._actions.get(key)
        if action is None:
            return
        action()

    def read_swim_input(self) -> SwimInput:
        is_down = self._window.is_key_down
        forward_amount = float(is_down(*FORWARD_KEYS)) - float(is_down(*BACKWARD_KEYS))
        turn_amount = float(is_down(*LEFT_KEYS)) - float(is_down(*RIGHT_KEYS))
        return SwimInput(forward_amount, turn_amount, is_down(*TURBO_KEYS))

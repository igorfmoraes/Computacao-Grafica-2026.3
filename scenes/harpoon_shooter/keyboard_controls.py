"""Continuous input is polled with glfw.get_key. Discrete actions arrive through the key callback."""

from typing import Callable

import glfw
import numpy as np

from .player import Player
from .window import Window

ROTATION_SPEED_RADIANS_PER_SECOND = np.radians(90.0)


class KeyboardControls:
    def __init__(
        self,
        window: Window,
        player: Player,
        discrete_actions: dict[int, Callable[[], None]],
    ) -> None:
        self._window = window
        self._player = player
        self._actions = discrete_actions
        window.add_key_press_listener(self.handle_key_press)

    def handle_key_press(self, key: int) -> None:
        action = self._actions.get(key)
        if action is not None:
            action()

    def update(self, delta_time_seconds: float) -> None:
        """Applies held keys for one frame. Called only while the game is running."""
        direction = 0
        if self._window.is_key_down(glfw.KEY_LEFT):
            direction += 1
        if self._window.is_key_down(glfw.KEY_RIGHT):
            direction -= 1
        if direction != 0:
            self._player.rotate(
                direction * ROTATION_SPEED_RADIANS_PER_SECOND * delta_time_seconds
            )

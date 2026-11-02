import glfw

from .window import Window


class KeyboardControls:
    """Maps keyboard keys to actions on the window and on the scene settings.

    Args:
        window: Window that closes when Escape is pressed.
        settings: Settings changed by the A, F and D keys.

    Register `handle_key_press` with `Window.add_key_press_listener` to activate it.
    """

    HELP_TEXT = "ESC - Fecha o Jogo\n"

    def __init__(self, window: Window) -> None:
        self._actions = {
            glfw.KEY_ESCAPE: window.request_close,
        }

    def handle_key_press(self, key: int) -> None:
        """Runs the action bound to `key`; keys without an action are ignored."""
        action = self._actions.get(key)
        if action is None:
            return
        action()

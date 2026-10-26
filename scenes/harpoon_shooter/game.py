from .window import Window


class Game:
    def __init__(self, window: Window) -> None:
        self._window = window

    def run(self) -> None:
        while not self._window.should_close():
            self._window.swap_buffers()
            self._window.poll_events()

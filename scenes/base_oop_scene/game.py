from .scene import Scene
from .window import Window


class Game:
    def __init__(self, window: Window, scene: Scene) -> None:
        self._window = window
        self._scene = scene

    def run(self) -> None:
        while not self._window.should_close():
            self._scene.render(self._window.elapsed_time_seconds)
            self._window.swap_buffers()
            self._window.poll_events()

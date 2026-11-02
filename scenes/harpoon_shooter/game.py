from .scene import Scene
from .window import Window
from .keyboard_controls import KeyboardControls

MAX_DELTA_TIME_SECONDS = 1.0 / 20.0


class Game:
    def __init__(
        self, window: Window, scene: Scene, keyboard_controls: KeyboardControls
    ) -> None:
        self._window = window
        self._scene = scene
        self._keyboard_controls = keyboard_controls

    def run(self) -> None:
        previous_time_seconds = self._window.elapsed_time_seconds
        while not self._window.should_close():
            current_time_seconds = self._window.elapsed_time_seconds
            delta_time_seconds = min(
                current_time_seconds - previous_time_seconds, MAX_DELTA_TIME_SECONDS
            )
            previous_time_seconds = current_time_seconds

            self._keyboard_controls.update(delta_time_seconds)
            self._scene.update(delta_time_seconds)
            self._scene.render(current_time_seconds)
            self._window.swap_buffers()
            self._window.poll_events()

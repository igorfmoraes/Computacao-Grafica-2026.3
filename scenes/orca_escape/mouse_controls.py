from typing import Callable

from .camera import Camera


class MouseControls:
    """Dragging orbits the camera and the scroll wheel zooms it.

    Args:
        camera: Camera moved by the mouse.
        is_enabled: Tells whether the mouse may move the camera now (it
            must not during the pause).

    Register `handle_drag` and `handle_scroll` with the window listeners.
    """

    def __init__(self, camera: Camera, is_enabled: Callable[[], bool]) -> None:
        self._camera = camera
        self._is_enabled = is_enabled

    def handle_drag(self, horizontal_pixels: float, vertical_pixels: float) -> None:
        if not self._is_enabled():
            return
        self._camera.orbit(horizontal_pixels, vertical_pixels)

    def handle_scroll(self, scroll_steps: float) -> None:
        if not self._is_enabled():
            return
        self._camera.zoom(scroll_steps)

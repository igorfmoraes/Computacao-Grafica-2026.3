import sys
from typing import Callable

import glfw
import moderngl

OPENGL_MAJOR_VERSION = 4
OPENGL_MINOR_VERSION = 0
MULTISAMPLE_COUNT = 4
SWAP_INTERVAL_FRAMES = 1
DRAG_BUTTONS = (glfw.MOUSE_BUTTON_LEFT, glfw.MOUSE_BUTTON_RIGHT)


class WindowCreationError(RuntimeError):
    """Raised when GLFW cannot be initialized or cannot create the window."""


class Window:
    """GLFW window with an OpenGL 4.0 Core context.

    The GLFW callbacks are forwarded to listeners: register them with the
    `add_*_listener` methods.
    """

    def __init__(
        self,
        width_pixels: int = 1280,
        height_pixels: int = 720,
        title: str = "GLFW Window",
    ) -> None:
        self._native_window = self._create_native_window(
            width_pixels, height_pixels, title
        )
        self.graphics_context = self._create_graphics_context()

        self._key_press_listeners = []
        self._drag_listeners = []
        self._scroll_listeners = []
        self._resize_listeners = []
        self._is_dragging = False
        self._last_cursor_position = (0.0, 0.0)
        self._register_callbacks()

    @property
    def elapsed_time_seconds(self) -> float:
        return glfw.get_time()

    @property
    def framebuffer_size_pixels(self) -> tuple[int, int]:
        return glfw.get_framebuffer_size(self._native_window)

    def should_close(self) -> bool:
        return bool(glfw.window_should_close(self._native_window))

    def request_close(self) -> None:
        glfw.set_window_should_close(self._native_window, True)

    def swap_buffers(self) -> None:
        glfw.swap_buffers(self._native_window)

    def poll_events(self) -> None:
        glfw.poll_events()

    def is_key_down(self, *keys: int) -> bool:
        """Whether any of `keys` is held, read directly with glfw.get_key."""
        return any(glfw.get_key(self._native_window, key) == glfw.PRESS for key in keys)

    def set_vsync(self, is_enabled: bool) -> None:
        glfw.swap_interval(1 if is_enabled else 0)

    def set_title(self, title: str) -> None:
        glfw.set_window_title(self._native_window, title)

    def terminate(self) -> None:
        glfw.terminate()

    def add_key_press_listener(self, listener: Callable[[int], None]) -> None:
        self._key_press_listeners.append(listener)

    def add_drag_listener(self, listener: Callable[[float, float], None]) -> None:
        """`listener(horizontal_pixels, vertical_pixels)` is called while the
        cursor moves with the left or right button held."""
        self._drag_listeners.append(listener)

    def add_scroll_listener(self, listener: Callable[[float], None]) -> None:
        self._scroll_listeners.append(listener)

    def add_resize_listener(self, listener: Callable[[int, int], None]) -> None:
        """`listener(width_pixels, height_pixels)` receives the new
        framebuffer size."""
        self._resize_listeners.append(listener)

    @staticmethod
    def _create_native_window(width_pixels: int, height_pixels: int, title: str):
        glfw.set_error_callback(Window._report_glfw_error)
        if not glfw.init():
            raise WindowCreationError("Erro: GLFW Não Conseguiu Iniciar")

        Window._apply_window_hints()
        native_window = glfw.create_window(
            width_pixels, height_pixels, title, None, None
        )

        if not native_window:
            glfw.terminate()
            raise WindowCreationError("Erro: Não Foi Possível Criar A Janela")

        return native_window

    @staticmethod
    def _apply_window_hints() -> None:
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, OPENGL_MAJOR_VERSION)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, OPENGL_MINOR_VERSION)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.SAMPLES, MULTISAMPLE_COUNT)
        glfw.window_hint(glfw.SRGB_CAPABLE, glfw.TRUE)
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)

    @staticmethod
    def _report_glfw_error(code: int, description: str) -> None:
        print(f"GLFW [{code}]: {description}", file=sys.stderr)

    def _create_graphics_context(self) -> moderngl.Context:
        glfw.make_context_current(self._native_window)
        glfw.swap_interval(SWAP_INTERVAL_FRAMES)
        return moderngl.create_context(require=400)

    def _register_callbacks(self) -> None:
        glfw.set_key_callback(self._native_window, self._dispatch_key_event)
        glfw.set_mouse_button_callback(self._native_window, self._dispatch_mouse_button)
        glfw.set_cursor_pos_callback(self._native_window, self._dispatch_cursor_motion)
        glfw.set_scroll_callback(self._native_window, self._dispatch_scroll)
        glfw.set_framebuffer_size_callback(
            self._native_window, self._dispatch_framebuffer_size
        )

    def _dispatch_key_event(self, native_window, key, scancode, action, modifiers):
        if action != glfw.PRESS:
            return
        for listener in self._key_press_listeners:
            listener(key)

    def _dispatch_mouse_button(self, native_window, button, action, modifiers):
        if button not in DRAG_BUTTONS:
            return
        self._is_dragging = action == glfw.PRESS
        self._last_cursor_position = glfw.get_cursor_pos(native_window)

    def _dispatch_cursor_motion(self, native_window, x_pixels, y_pixels):
        last_x_pixels, last_y_pixels = self._last_cursor_position
        self._last_cursor_position = (x_pixels, y_pixels)
        if not self._is_dragging:
            return
        for listener in self._drag_listeners:
            listener(x_pixels - last_x_pixels, y_pixels - last_y_pixels)

    def _dispatch_scroll(self, native_window, horizontal_steps, vertical_steps):
        for listener in self._scroll_listeners:
            listener(vertical_steps)

    def _dispatch_framebuffer_size(self, native_window, width_pixels, height_pixels):
        for listener in self._resize_listeners:
            listener(width_pixels, height_pixels)

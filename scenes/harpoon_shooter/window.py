import moderngl
import glfw

OPENGL_MAJOR_VERSION = 4
OPENGL_MINOR_VERSION = 0
MULTISAMPLE_COUNT = 4
SWAP_INTERVAL_FRAMES = 1


class Window:
    def __init__(
        self,
        width_pixels: int = 640,
        height_pixels: int = 640,
        title: str = "GLFW Window",
    ) -> None:
        self._native_window = self._create_native_window(
            width_pixels, height_pixels, title
        )
        self.graphics_context = self._create_graphics_context()

        self._set_aspect_ratio(width_pixels, height_pixels)

    def should_close(self) -> bool:
        return glfw.window_should_close(self._native_window)

    def request_close(self) -> None:
        glfw.set_window_should_close(self._native_window, True)

    def swap_buffers(self) -> None:
        glfw.swap_buffers(self._native_window)

    def poll_events(self) -> None:
        glfw.poll_events()

    @staticmethod
    def _create_native_window(
        width_pixels: int = 640,
        height_pixels: int = 640,
        title: str = "GLFW Window",
    ):
        if not glfw.init():
            pass

        Window._apply_window_hints()
        native_window = glfw.create_window(
            width_pixels, height_pixels, title, None, None
        )

        if not native_window:
            glfw.terminate()

        return native_window

    @staticmethod
    def _apply_window_hints() -> None:
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, OPENGL_MAJOR_VERSION)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, OPENGL_MINOR_VERSION)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.SAMPLES, MULTISAMPLE_COUNT)
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)

    def _create_graphics_context(self) -> moderngl.Context:
        glfw.make_context_current(self._native_window)
        glfw.swap_interval(SWAP_INTERVAL_FRAMES)
        context = moderngl.create_context()
        context.enable(moderngl.BLEND)

        return context

    def _set_aspect_ratio(self, width_pixels, height_pixels) -> None:
        glfw.set_window_aspect_ratio(self._native_window, width_pixels, height_pixels)
        glfw.set_framebuffer_size_callback(
            self._native_window, self._framebuffer_size_callback
        )

    def _framebuffer_size_callback(self, window, width, height) -> None:
        self.graphics_context.viewport = (0, 0, width, height)

import sys
import glfw
import moderngl
import numpy as np
from pathlib import Path

SHADERS = Path(__file__).parent / "shaders"


def main():
    window = create_window()
    current_context = create_context(window)

    while not glfw.window_should_close(window):
        current_context.clear(1.0, 1.0, 1.0, 1.0)
        glfw.swap_buffers(window)
        glfw.poll_events()


def create_window(width=640, height=640, title="GLFW Window"):
    glfw.set_error_callback(
        lambda code, description: print(
            f"GLFW [{code}]: {description}", file=sys.stderr
        )
    )

    if not glfw.init():
        sys.exit("Erro: GLFW Não Conseguiu Iniciar")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
    glfw.window_hint(glfw.SAMPLES, 4)
    glfw.window_hint(glfw.RESIZABLE, False)

    window = glfw.create_window(width, height, title, None, None)

    if not window:
        glfw.terminate()
        sys.exit("Erro: Não Foi Possível Criar A Janela")

    glfw.set_key_callback(window, process_key)

    return window


def create_context(window):
    glfw.make_context_current(window)
    glfw.swap_interval(1)
    context = moderngl.create_context()
    context.enable(moderngl.BLEND)

    return context


def process_key(window, key, scancode, action, mods):
    global amplitude, frequency, attenuation, dark_mode
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)


if __name__ == "__main__":
    main()

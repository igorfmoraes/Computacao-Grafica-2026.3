import sys
import glfw
import moderngl
import numpy as np
from pathlib import Path

SHADERS = Path(__file__).parent / ""

frequency = 3
possible_frequencies = [6, 4.5, 3, 1.5]
amplitude = 16
possible_amplitudes = [8, 12, 16, 20]
attenuation = 1.0
dark_mode = False


def main():
    window = create_window()
    current_context = create_context(window)

    water_shader = current_context.program(
        vertex_shader=(SHADERS / "water.vert").read_text(encoding="utf-8"),
        fragment_shader=(SHADERS / "color.frag").read_text(encoding="utf-8"),
    )

    water = construct_water()
    water_raw_data, water_data_organization = construct_vertex_data_and_organization(
        water, current_context, water_shader
    )

    while not glfw.window_should_close(window):
        elapsed_time = glfw.get_time()
        current_context.clear(1.0, 1.0, 1.0, 1.0)

        set_uniform_value("u_frequency", frequency, water_shader)
        set_uniform_value("u_amplitude", amplitude, water_shader)
        set_uniform_value("u_attenuation", attenuation, water_shader)
        set_uniform_value("u_time", elapsed_time, water_shader)

        draw_shape(
            water_data_organization,
            1.0,
            (0.0, 0.0),
            (0.0, 1.0, 1.0, 1.0),
            water_shader,
        )

        glfw.swap_buffers(window)
        glfw.poll_events()


def construct_water(steps=128):
    x_coordinates = np.linspace(-0.9, 0.9, steps)
    y_coordinates = 0.7 + np.zeros(steps)

    return np.vstack(
        (
            np.append(x_coordinates, [0.9, -0.9]),
            np.append(y_coordinates, [-0.9, -0.9]),
        )
    ).T


def construct_vertex_data_and_organization(vertices, context, shaders_program):
    # Vertex Buffer Object, stores the raw data (position) to be sent to the GPU
    vertex_data = context.buffer(np.asarray(vertices, dtype="f4").tobytes())

    vertices_indices = convert_shape_to_triangle_fan(vertices)
    vertices_indices_bytes = context.buffer(
        np.array(vertices_indices, dtype="i4").tobytes()
    )

    # Vertex Array Objet, defines the organization/structure of the data (where to split, how to map)
    # 2 floats to be stores in vPosition (x, y)
    vertex_data_organization = context.vertex_array(
        shaders_program,
        [(vertex_data, "2f", "vPosition")],
        index_buffer=vertices_indices_bytes,
    )

    return vertex_data, vertex_data_organization


def convert_shape_to_triangle_fan(vertices):
    number_of_vertices = len(vertices) - 2
    midpoint_index = number_of_vertices // 2

    bottom_right_index = number_of_vertices
    bottom_left_index = number_of_vertices + 1

    vertices_indices = []

    for vertex_index in range(midpoint_index):
        vertices_indices.extend([bottom_left_index, vertex_index, vertex_index + 1])

    for vertex_index in range(midpoint_index, number_of_vertices - 1):
        vertices_indices.extend([bottom_right_index, vertex_index, vertex_index + 1])

    vertices_indices.extend([bottom_left_index, midpoint_index, bottom_right_index])

    return vertices_indices


def draw_shape(
    vertex_data_organization,
    scale,
    offset,
    color,
    shaders_program,
    mode=moderngl.TRIANGLES,
):
    set_uniform_value("u_scale", scale, shaders_program)
    set_uniform_value("u_offset", offset, shaders_program)
    set_uniform_value("u_color", np.array(color, dtype=np.float32), shaders_program)
    vertex_data_organization.render(mode)


def set_uniform_value(name, value, shaders_program):
    uniform = shaders_program.get(name, None)
    if uniform is not None:
        uniform.value = value


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
    elif key == glfw.KEY_A:
        amplitude = possible_amplitudes[possible_amplitudes.index(amplitude) - 1]
    elif key == glfw.KEY_F:
        frequency = possible_frequencies[possible_frequencies.index(frequency) - 1]
    elif key == glfw.KEY_D:
        dark_mode = not dark_mode
        attenuation = 0.6 if dark_mode else 1.0


if __name__ == "__main__":
    main()

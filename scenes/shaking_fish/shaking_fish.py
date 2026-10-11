import sys
import glfw
import moderngl
import numpy as np
from pathlib import Path

SHADERS = Path(__file__).parent / ""

wave_frequency_multiplier = 3
possible_frequencies = [6, 4.5, 3, 1.5]
wave_amplitude_divisor = 16
possible_wave_amplitude_divisors = [8, 12, 16, 20]
brightness_multiplier = 1.0
dark_mode = False


def main():
    window = create_window(900, 900, "Chacoalha Esse Peixe!")
    context = create_context(window)

    print(
        "A - Muda Amplitude das Ondas\nF - Muda Frequência das Ondas\nD - Alterna Modo Dia/Noite"
    )

    water_shader = context.program(
        vertex_shader=(SHADERS / "water.vert").read_text(encoding="utf-8"),
        fragment_shader=(SHADERS / "color.frag").read_text(encoding="utf-8"),
    )
    body_shader = context.program(
        vertex_shader=(SHADERS / "body.vert").read_text(encoding="utf-8"),
        fragment_shader=(SHADERS / "color.frag").read_text(encoding="utf-8"),
    )

    water = construct_water()
    water_raw_data, water_data_organization = construct_vertex_buffer_and_organization(
        water, context, water_shader
    )

    fish = construct_fish()
    fish_raw_data, fish_data_organization = construct_vertex_buffer_and_organization(
        fish, context, body_shader
    )

    circle = construct_circle()
    circle_raw_data, circle_data_organization = (
        construct_vertex_buffer_and_organization(circle, context, body_shader)
    )

    while not glfw.window_should_close(window):
        elapsed_time_seconds = glfw.get_time()
        context.clear(
            np.sqrt(wave_frequency_multiplier / wave_amplitude_divisor)
            / 1.5
            * brightness_multiplier,
            (0.45 + np.cos(elapsed_time_seconds) / 16) * brightness_multiplier,
            (0.92 + np.sin(elapsed_time_seconds) / 16) * brightness_multiplier,
            1.0,
        )

        set_uniform_value(
            "u_wave_frequency_multiplier", wave_frequency_multiplier, water_shader
        )
        set_uniform_value(
            "u_wave_amplitude_divisor", wave_amplitude_divisor, water_shader
        )
        set_uniform_value(
            "u_brightness_multiplier", brightness_multiplier, water_shader
        )
        set_uniform_value("u_time", elapsed_time_seconds, water_shader)

        set_uniform_value(
            "u_wave_frequency_multiplier", wave_frequency_multiplier, body_shader
        )
        set_uniform_value(
            "u_wave_amplitude_divisor", wave_amplitude_divisor, body_shader
        )
        set_uniform_value("u_brightness_multiplier", brightness_multiplier, body_shader)
        set_uniform_value("u_time", elapsed_time_seconds, body_shader)

        draw_shape(
            water_data_organization,
            1.0,
            (0.0, 0.0),
            (0.0, 1.0, 1.0, 1.0),
            water_shader,
        )

        draw_shape(
            fish_data_organization,
            0.3,
            (0.0, -0.2),
            (1.0, 0.44, 0.2, 1.0),
            body_shader,
        )

        draw_shape(
            circle_data_organization,
            0.05,
            (
                0.12
                + np.cos(elapsed_time_seconds * 0.5 * wave_frequency_multiplier)
                / wave_amplitude_divisor
                / 2,
                -0.1,
            ),
            (0.85, 0.85, 1.0, 1.0),
            body_shader,
        )
        draw_shape(
            circle_data_organization,
            0.05,
            (
                0.22
                + np.cos(elapsed_time_seconds * 0.5 * wave_frequency_multiplier)
                / wave_amplitude_divisor
                / 2,
                -0.1,
            ),
            (0.85, 0.85, 1.0, 1.0),
            body_shader,
        )

        draw_shape(
            circle_data_organization,
            0.02,
            (
                0.14
                + np.cos(elapsed_time_seconds * 0.5 * wave_frequency_multiplier)
                / wave_amplitude_divisor
                / 1.8,
                -0.1,
            ),
            (0.15, 0.15, 0.25, 1.0),
            body_shader,
        )
        draw_shape(
            circle_data_organization,
            0.02,
            (
                0.24
                + np.cos(elapsed_time_seconds * 0.5 * wave_frequency_multiplier)
                / wave_amplitude_divisor
                / 1.8,
                -0.1,
            ),
            (0.15, 0.15, 0.25, 1.0),
            body_shader,
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


def construct_fish(steps=64):
    angle_radians = np.linspace(0.0, 2.0 * np.pi, steps, endpoint=False)
    x_coordinates = np.cos(angle_radians) - np.sin(angle_radians) ** 2 / np.sqrt(2)
    y_coordinates = np.cos(angle_radians) * np.sin(angle_radians)

    return np.vstack((x_coordinates, y_coordinates)).T


def construct_circle(steps=32):
    angles_radian = np.linspace(0.0, 2.0 * np.pi, steps, endpoint=False)
    x_coordinates = np.cos(angles_radian)
    y_coordinates = np.sin(angles_radian)

    return np.vstack((x_coordinates, y_coordinates)).T


def construct_vertex_buffer_and_organization(vertices, context, shaders_program):
    # Vertex Buffer Object, stores the raw data (position) to be sent to the GPU
    vertex_buffer = context.buffer(np.asarray(vertices, dtype="f4").tobytes())

    vertices_indices = triangulate_surface_between_two_corners(vertices)
    index_buffer = context.buffer(np.array(vertices_indices, dtype="i4").tobytes())

    # Vertex Array Objet, defines the organization/structure of the data (where to split, how to map)
    # 2 floats to be stores in vPosition (x, y)
    vertex_array = context.vertex_array(
        shaders_program,
        [(vertex_buffer, "2f", "vPosition")],
        index_buffer=index_buffer,
    )

    return vertex_buffer, vertex_array


def triangulate_surface_between_two_corners(vertices):
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
    vertex_array,
    scale,
    offset,
    color,
    shaders_program,
    mode=moderngl.TRIANGLES,
):
    set_uniform_value("u_scale", scale, shaders_program)
    set_uniform_value("u_offset", offset, shaders_program)
    set_uniform_value("u_color", np.array(color, dtype=np.float32), shaders_program)
    vertex_array.render(mode)


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
    global wave_amplitude_divisor, wave_frequency_multiplier, brightness_multiplier, dark_mode
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_A:
        wave_amplitude_divisor = possible_wave_amplitude_divisors[
            possible_wave_amplitude_divisors.index(wave_amplitude_divisor) - 1
        ]
    elif key == glfw.KEY_F:
        wave_frequency_multiplier = possible_frequencies[
            possible_frequencies.index(wave_frequency_multiplier) - 1
        ]
    elif key == glfw.KEY_D:
        dark_mode = not dark_mode
        brightness_multiplier = 0.6 if dark_mode else 1.0


if __name__ == "__main__":
    main()

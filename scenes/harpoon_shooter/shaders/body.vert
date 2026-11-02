#version 400 core

layout(location = 0) in vec2 vertex_position;

uniform mat4 shape_transform;
uniform vec4 shape_color;

uniform float wave_amplitude;
uniform float wave_phase;

out vec4 vertex_color;

void main() {
    vec2 position = vertex_position;
    float tail_factor = smoothstep(0.7, 1.0, -position.x);
    position.y += wave_amplitude * tail_factor * sin(wave_phase);

    gl_Position = shape_transform * vec4(position, 0.0, 1.0);
    vertex_color = shape_color;
}

#version 400 core

// The line buffer never changes; the waving is computed here from the time
// and from how far along the tentacle the vertex is (0 at the root).

layout(location = 0) in vec3 vertex_position;
layout(location = 1) in float vertex_length_fraction;

uniform mat4 model_matrix;
uniform mat4 view_matrix;
uniform mat4 projection_matrix;
uniform float elapsed_time_seconds;
uniform float phase_radians;

out vec3 world_position;

void main() {
    vec3 position = vertex_position;
    float wave = elapsed_time_seconds * 3.0 + vertex_length_fraction * 6.0 + phase_radians;
    position.x += 0.18 * vertex_length_fraction * sin(wave);
    position.z += 0.12 * vertex_length_fraction * cos(wave * 0.8);
    vec4 world = model_matrix * vec4(position, 1.0);
    gl_Position = projection_matrix * view_matrix * world;
    world_position = world.xyz;
}

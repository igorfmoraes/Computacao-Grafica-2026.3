#version 400 core

// Position and normal go to WORLD space, where the lights and the camera
// are; the lighting is evaluated per fragment, in lit.frag.

layout(location = 0) in vec3 vertex_position;
layout(location = 1) in vec3 vertex_normal;
layout(location = 2) in vec2 vertex_texture_coordinates;

uniform mat4 model_matrix;
uniform mat4 view_matrix;
uniform mat4 projection_matrix;
uniform mat3 normal_matrix;

out vec3 world_position;
out vec3 world_normal;
out vec2 texture_coordinates;

void main() {
    vec4 position = model_matrix * vec4(vertex_position, 1.0);
    gl_Position = projection_matrix * view_matrix * position;
    world_position = position.xyz;
    world_normal = normal_matrix * vertex_normal;
    texture_coordinates = vertex_texture_coordinates;
}

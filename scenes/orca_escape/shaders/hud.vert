#version 400 core

layout(location = 0) in vec2 vertex_position;

uniform mat4 projection_matrix;
uniform mat4 shape_transform;

void main() {
    gl_Position = projection_matrix * shape_transform * vec4(vertex_position, 0.0, 1.0);
}

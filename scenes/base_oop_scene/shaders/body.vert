#version 400 core

layout(location = 0) in vec2 vertex_position;

uniform mat4 shape_transform;
uniform vec4 shape_color;

out vec4 vertex_color;

void main() {
    gl_Position = shape_transform * vec4(vertex_position, 0.0, 1.0);
    vertex_color = shape_color;
}

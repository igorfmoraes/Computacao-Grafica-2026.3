#version 400 core

layout(location = 0) in vec4 vertex_position;

uniform float shape_scale;
uniform vec2  shape_offset;
uniform vec4  shape_color;

out vec4 vertex_color;

void main() {
    vec2 original_position = vertex_position.xy;
    vec2 displaced_position = vec2(original_position.x,original_position.y);

    gl_Position = vec4(displaced_position * shape_scale + shape_offset, 0.0, 1.0);   
    vertex_color = shape_color;
}

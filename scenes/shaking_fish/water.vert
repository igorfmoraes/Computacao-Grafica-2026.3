#version 400 core

layout(location = 0) in vec4 vPosition;

uniform float u_scale;
uniform vec2  u_offset;
uniform vec4  u_color;

out vec4 v2fcolor;

void main() {
    float y = vPosition.y + sin(vPosition.x * 3 * 3.14) / 24;
    float x = vPosition.x;
    gl_Position = vec4(x * u_scale + u_offset.x, y * u_scale + u_offset.y, 0.0, 1.0);

    v2fcolor = u_color;
}

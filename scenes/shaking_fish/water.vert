#version 400 core

layout(location = 0) in vec4 vPosition;

uniform float u_scale;
uniform vec2  u_offset;
uniform vec4  u_color;
uniform float u_frequency;
uniform int u_amplitude;
uniform float u_time;

out vec4 v2fcolor;

void main() {
    float y = vPosition.y + (sin(-u_time * u_frequency + (vPosition.x + vPosition.y) *  3.14 * u_frequency) / u_amplitude) + cos(u_time * u_frequency + vPosition.x)/20;
    float x = vPosition.x + cos(u_time * u_frequency/2 + (vPosition.x + vPosition.y) / 4) / 24;
    gl_Position = vec4(x * u_scale + u_offset.x, y * u_scale + u_offset.y, 0.0, 1.0);

    v2fcolor = vec4(u_color.r, u_color.g + sin(vPosition.x * vPosition.y + u_time) / 8, u_color.b+ cos(vPosition.x * vPosition.y + u_time) / 8, u_color.a);
}

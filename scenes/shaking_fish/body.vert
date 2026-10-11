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
    float x = vPosition.x + cos(u_time * u_frequency/2 + (vPosition.x + vPosition.y) / 2) / 6;
    float y = vPosition.y + sin(u_time * u_frequency + vPosition.x)/u_amplitude/2;
    vec2 position = vec2(x,y);
    gl_Position = vec4(position.xy * u_scale + u_offset, 0.0, 1.0);
    v2fcolor = u_color;
}

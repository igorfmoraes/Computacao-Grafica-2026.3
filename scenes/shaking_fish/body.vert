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
    float x = vPosition.x;
    float y = vPosition.y;
    vec2 position = vec2(x,y);
    gl_Position = vec4(position.xy * u_scale + u_offset, 0.0, 1.0);
    v2fcolor = u_color;
}

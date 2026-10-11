#version 400 core

layout(location = 0) in vec4 vPosition;

uniform float u_scale;
uniform vec2  u_offset;
uniform vec4  u_color;
uniform float u_wave_frequency_multiplier;
uniform int u_wave_amplitude_divisor;
uniform float u_time;

out vec4 v2fcolor;

void main() {
    float x = vPosition.x + cos(u_time * u_wave_frequency_multiplier/2 + (vPosition.x + vPosition.y) / 2) / 6;
    float y = vPosition.y + sin(u_time * u_wave_frequency_multiplier + vPosition.x)/u_wave_amplitude_divisor/2;
    vec2 position = vec2(x,y);
    gl_Position = vec4(position.xy * u_scale + u_offset, 0.0, 1.0);
    v2fcolor = u_color;
}

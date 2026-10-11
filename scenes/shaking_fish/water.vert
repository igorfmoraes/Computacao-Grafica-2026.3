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
    float y = vPosition.y + (sin(-u_time * u_wave_frequency_multiplier + (vPosition.x + vPosition.y) *  3.14 * u_wave_frequency_multiplier) / u_wave_amplitude_divisor) + cos(u_time * u_wave_frequency_multiplier + vPosition.x)/20;
    float x = vPosition.x + cos(u_time * u_wave_frequency_multiplier/2 + (vPosition.x + vPosition.y) / 4) / 24;
    gl_Position = vec4(x * u_scale + u_offset.x, y * u_scale + u_offset.y, 0.0, 1.0);

    v2fcolor = vec4(u_color.r, u_color.g + sin(vPosition.x * vPosition.y + u_time) / 8, u_color.b+ cos(vPosition.x * vPosition.y + u_time) / 8, u_color.a);
}

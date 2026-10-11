#version 400 core
in vec4 v2fcolor;
out vec4 outfragcolor;

uniform float u_brightness_multiplier;

void main() {
    outfragcolor = vec4(v2fcolor.rgb * u_brightness_multiplier, v2fcolor.a);
}

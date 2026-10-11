#version 400 core
in vec4 v2fcolor;
out vec4 outfragcolor;

uniform float u_attenuation;

void main() {
    outfragcolor = vec4(v2fcolor.rgb, v2fcolor.a);
}

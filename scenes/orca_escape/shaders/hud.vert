#version 400 core

// Placar: geometria 2D em pixels, com projecao ortografica.

layout(location = 0) in vec2 vPosition;

uniform mat4 u_projecao;
uniform mat4 u_modelo;

void main() {
    gl_Position = u_projecao * u_modelo * vec4(vPosition, 0.0, 1.0);
}

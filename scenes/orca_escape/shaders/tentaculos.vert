#version 400 core

// Tentaculos das aguas-vivas (GL_LINES). O VBO e fixo; a ondulacao
// e calculada aqui, em funcao do tempo e de s (0 na raiz, 1 na ponta).

layout(location = 0) in vec3 vPosition;
layout(location = 1) in float vS;

uniform mat4 u_modelo, u_visao, u_projecao;
uniform float u_tempo;
uniform float u_fase;

out vec3 fP;

void main() {
    vec3 p = vPosition;
    float onda = u_tempo * 3.0 + vS * 6.0 + u_fase;
    p.x += 0.18 * vS * sin(onda);
    p.z += 0.12 * vS * cos(onda * 0.8);
    vec4 mundo = u_modelo * vec4(p, 1.0);
    gl_Position = u_projecao * u_visao * mundo;
    fP = mundo.xyz;
}

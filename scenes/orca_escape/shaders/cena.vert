#version 400 core

// Leva posicao e normal para o espaco do MUNDO, onde estao as luzes
// e a camera (u_olho). O rasterizador interpola as tres saidas, e a
// iluminacao e avaliada por fragmento, em cena.frag.

layout(location = 0) in vec3 vPosition;
layout(location = 1) in vec3 vNormal;
layout(location = 2) in vec2 vTexCoord;

uniform mat4 u_modelo, u_visao, u_projecao;
uniform mat3 u_normal;     // inversa transposta do bloco 3x3 de u_modelo

out vec3 fP;    // posicao no mundo
out vec3 fN;    // normal no mundo, sem normalizar
out vec2 fUV;

void main() {
    vec4 mundo = u_modelo * vec4(vPosition, 1.0);
    gl_Position = u_projecao * u_visao * mundo;
    fP = mundo.xyz;
    fN = u_normal * vNormal;
    fUV = vTexCoord;
}

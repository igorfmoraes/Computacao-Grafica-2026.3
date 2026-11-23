#version 400 core

in vec3 fP;

uniform vec3  u_cor;             // em luz linear, sem iluminacao
uniform vec3  u_olho;
uniform vec3  u_neblina_cor;
uniform float u_neblina_dens;

out vec4 cor_saida;

void main() {
    float d = length(u_olho - fP) * u_neblina_dens;
    cor_saida = vec4(mix(u_neblina_cor, u_cor, exp(-d * d)), 0.8);
}

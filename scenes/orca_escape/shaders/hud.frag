#version 400 core

// O placar e desenhado com GL_FRAMEBUFFER_SRGB desligado: u_cor ja
// e a cor que aparece na tela.

uniform vec4 u_cor;
out vec4 cor_saida;

void main() {
    cor_saida = u_cor;
}

#version 400 core

// Sombreamento de Phong com o modelo de Blinn-Phong, no espaco do
// mundo, com tres fontes de luz:
//   direcional  a luz que vem da superficie, com causticas animadas
//   conica      a lanterna presa a cabeca da orca
//   pontual     a luz da saida, com atenuacao
// A textura (GL_SRGB8_ALPHA8) ja chega decodificada em luz linear e
// faz o papel do albedo; a saida e luz linear, codificada em sRGB uma
// unica vez pelo OpenGL (GL_FRAMEBUFFER_SRGB).

in vec3 fP;
in vec3 fN;
in vec2 fUV;

uniform sampler2D u_textura;
uniform vec2  u_uv_escala;       // > 1 repete a textura (GL_REPEAT)

uniform vec3  u_ka, u_kd, u_ks;  // material
uniform float u_alfa;
uniform vec3  u_emissao;
uniform float u_opacidade;

uniform vec3  u_olho;            // camera no mundo
uniform vec3  u_luz_ambiente;
uniform float u_tempo;

uniform bool  u_dir_ligada;
uniform vec3  u_dir_direcao;     // para onde a luz caminha
uniform vec3  u_dir_cor;

uniform bool  u_cone_ligada;
uniform vec3  u_cone_pos, u_cone_dir, u_cone_cor;
uniform float u_cone_cos_int, u_cone_cos_ext;
uniform vec3  u_cone_aten;       // (kc, kl, kq)

uniform bool  u_pont_ligada;
uniform vec3  u_pont_pos, u_pont_cor;
uniform vec3  u_pont_aten;

uniform vec3  u_neblina_cor;     // em luz linear
uniform float u_neblina_dens;

out vec4 cor_saida;

// Difusa + especular de uma fonte; L aponta do ponto para a luz.
vec3 blinn_phong(vec3 N, vec3 V, vec3 L, vec3 cor_luz, vec3 kd) {
    float NdotL = max(dot(N, L), 0.0);
    float brilho = 0.0;
    if (NdotL > 0.0) {
        vec3 H = normalize(L + V);
        brilho = pow(max(dot(N, H), 0.0), u_alfa);
    }
    return cor_luz * (kd * NdotL + u_ks * brilho);
}

float atenuacao(vec3 k, float d) {
    return 1.0 / (k.x + k.y * d + k.z * d * d);
}

// Manchas de luz que a superficie ondulada da agua projeta no fundo:
// uma soma de senoides que se deslocam com o tempo.
float causticas(vec2 p, float t) {
    float a = sin(p.x * 1.1 + t * 1.3) * sin(p.y * 0.9 - t * 1.1);
    float b = sin((p.x + p.y) * 0.6 + t * 0.7);
    float c = 0.5 + 0.5 * (a + 0.5 * b) / 1.5;
    return 0.55 + 0.9 * pow(c, 3.0);
}

void main() {
    vec3 N = normalize(fN);
    vec3 V = normalize(u_olho - fP);

    vec3 base = texture(u_textura, fUV * u_uv_escala).rgb;
    vec3 kd = u_kd * base;
    vec3 cor = u_ka * base * u_luz_ambiente + u_emissao;

    if (u_dir_ligada) {
        vec3 c = u_dir_cor * causticas(fP.xz, u_tempo);
        cor += blinn_phong(N, V, normalize(-u_dir_direcao), c, kd);
    }

    if (u_cone_ligada) {
        vec3 para_luz = u_cone_pos - fP;
        float d = length(para_luz);
        vec3 L = para_luz / d;
        float cos_t = dot(-L, normalize(u_cone_dir));
        // transicao suave entre o cone interno e o externo
        float cone = smoothstep(u_cone_cos_ext, u_cone_cos_int, cos_t);
        if (cone > 0.0)
            cor += cone * atenuacao(u_cone_aten, d)
                 * blinn_phong(N, V, L, u_cone_cor, kd);
    }

    if (u_pont_ligada) {
        vec3 para_luz = u_pont_pos - fP;
        float d = length(para_luz);
        cor += atenuacao(u_pont_aten, d)
             * blinn_phong(N, V, para_luz / d, u_pont_cor, kd);
    }

    // Neblina exponencial quadratica: a agua engole o que esta longe.
    float d_olho = length(u_olho - fP) * u_neblina_dens;
    float visivel = exp(-d_olho * d_olho);
    cor = mix(u_neblina_cor, cor, visivel);

    cor_saida = vec4(cor, u_opacidade);
}

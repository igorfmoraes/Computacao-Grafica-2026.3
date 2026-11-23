"""Placar e telas de estado, desenhados com geometria numa segunda
passada: projecao ortografica em pixels, sem teste de profundidade.

Quatro VBOs, criados uma vez, desenhados com matrizes de modelo
diferentes e quatro primitivas:
  quadrado  (TRIANGLES)       paineis, segmentos dos digitos, barras
  contorno  (LINE_LOOP)       bordas dos paineis
  circulo   (TRIANGLE_FAN)    vidas
  anel      (LINE_LOOP)       vidas perdidas, moldura das telas
  triangulo (TRIANGLES)       tela de inicio
"""
import math
from enum import Enum, auto

import glm
import moderngl
import numpy as np

LADOS_CIRCULO = 32

# Segmentos de um digito de 7 segmentos: a b c d e f g.
#    a
#  f   b
#    g
#  e   c
#    d
SEGMENTOS = {
    0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg",
    5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg",
}

BRANCO = (0.95, 0.97, 1.0, 1.0)
PAINEL = (0.02, 0.06, 0.12, 0.65)
BORDA = (0.45, 0.75, 0.95, 1.0)
VIDA = (0.95, 0.3, 0.35, 1.0)
PEIXE = (1.0, 0.65, 0.15, 1.0)
APAGADO = (0.5, 0.55, 0.6, 1.0)


class Sobreposicao(Enum):
    INICIO = auto()
    PAUSA = auto()
    DERROTA = auto()
    VITORIA = auto()


class Hud:
    def __init__(self, ctx, programa):
        self.ctx, self.prog = ctx, programa
        quadrado = np.array([0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1], dtype='f4')
        contorno = np.array([0, 0, 1, 0, 1, 1, 0, 1], dtype='f4')
        ang = np.linspace(0, 2 * np.pi, LADOS_CIRCULO + 1)
        borda = np.stack([np.cos(ang), np.sin(ang)], axis=1)
        circulo = np.vstack([[0, 0], borda]).astype('f4')
        anel = borda[:-1].astype('f4')
        triangulo = np.array([-0.4, -0.5, 0.6, 0.0, -0.4, 0.5], dtype='f4')
        self.buffers, self.vaos = [], {}
        for nome, dados in (("quadrado", quadrado), ("contorno", contorno),
                            ("circulo", circulo), ("anel", anel),
                            ("triangulo", triangulo)):
            vbo = ctx.buffer(dados.tobytes())
            self.buffers.append(vbo)
            self.vaos[nome] = ctx.vertex_array(
                programa, [(vbo, '2f', 'vPosition')])
        self.largura = self.altura = 1

    def redimensionar(self, largura, altura):
        self.largura, self.altura = max(1, largura), max(1, altura)

    # --- primitivas posicionadas por matriz de modelo ---

    def _desenhar(self, nome, modo, modelo, cor):
        self.prog['u_modelo'].write(modelo.to_bytes())
        self.prog['u_cor'].value = cor
        self.vaos[nome].render(modo)

    def retangulo(self, x, y, l, a, cor, angulo=0.0, centrado=False):
        m = glm.translate(glm.mat4(1.0), glm.vec3(x, y, 0))
        m = glm.rotate(m, angulo, glm.vec3(0, 0, 1))
        if centrado:
            m = glm.translate(m, glm.vec3(-l / 2, -a / 2, 0))
        self._desenhar("quadrado", moderngl.TRIANGLES,
                       glm.scale(m, glm.vec3(l, a, 1)), cor)

    def contorno(self, x, y, l, a, cor):
        m = glm.scale(glm.translate(glm.mat4(1.0), glm.vec3(x, y, 0)),
                      glm.vec3(l, a, 1))
        self._desenhar("contorno", moderngl.LINE_LOOP, m, cor)

    def circulo(self, x, y, r, cor, cheio=True):
        m = glm.scale(glm.translate(glm.mat4(1.0), glm.vec3(x, y, 0)),
                      glm.vec3(r, r, 1))
        if cheio:
            self._desenhar("circulo", moderngl.TRIANGLE_FAN, m, cor)
        else:
            self._desenhar("anel", moderngl.LINE_LOOP, m, cor)

    def losango(self, x, y, lado, cor, cheio=True):
        m = glm.translate(glm.mat4(1.0), glm.vec3(x, y, 0))
        m = glm.rotate(m, math.pi / 4, glm.vec3(0, 0, 1))
        m = glm.scale(glm.translate(m, glm.vec3(-lado / 2, -lado / 2, 0)),
                      glm.vec3(lado, lado, 1))
        if cheio:
            self._desenhar("quadrado", moderngl.TRIANGLES, m, cor)
        else:
            self._desenhar("contorno", moderngl.LINE_LOOP, m, cor)

    def digito(self, valor, x, y, l, a, e, cor):
        """Digito de 7 segmentos com canto inferior esquerdo em (x, y),
        largura l, altura a e espessura e."""
        meio = y + a / 2 - e / 2
        segs = {
            "a": (x, y + a - e, l, e), "g": (x, meio, l, e), "d": (x, y, l, e),
            "f": (x, meio, e, a / 2 + e / 2), "b": (x + l - e, meio, e, a / 2 + e / 2),
            "e": (x, y, e, a / 2), "c": (x + l - e, y, e, a / 2),
        }
        for s in SEGMENTOS[valor]:
            self.retangulo(*segs[s], cor)

    # --- o placar ---

    def desenhar(self, pontos, vidas, vidas_max, peixes, peixes_total,
                 sobreposicao, piscar):
        ctx = self.ctx
        ctx.disable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        L, A = self.largura, self.altura
        projecao = glm.ortho(0, L, 0, A, -1, 1)
        self.prog['u_projecao'].write(projecao.to_bytes())
        u = A / 720.0                          # escala com a altura

        # pontuacao, 5 digitos
        n_dig, dl, da, esp = 5, 22 * u, 40 * u, 5 * u
        px, py = 20 * u, A - 20 * u - 60 * u
        pl, pa = n_dig * 32 * u + 18 * u, 60 * u
        self.retangulo(px, py, pl, pa, PAINEL)
        self.contorno(px, py, pl, pa, BORDA)
        texto = f"{min(pontos, 10 ** n_dig - 1):0{n_dig}d}"
        for k, c in enumerate(texto):
            self.digito(int(c), px + 14 * u + k * 32 * u, py + 10 * u,
                        dl, da, esp, BRANCO)

        # vidas, a direita
        vl = vidas_max * 40 * u + 16 * u
        vx = L - 20 * u - vl
        self.retangulo(vx, py, vl, pa, PAINEL)
        self.contorno(vx, py, vl, pa, BORDA)
        for k in range(vidas_max):
            cx = vx + 28 * u + k * 40 * u
            self.circulo(cx, py + pa / 2, 14 * u, VIDA if k < vidas
                         else APAGADO, cheio=k < vidas)

        # peixes coletados, no centro
        fl = peixes_total * 30 * u + 20 * u
        fx = (L - fl) / 2
        self.retangulo(fx, py, fl, pa, PAINEL)
        self.contorno(fx, py, fl, pa, BORDA)
        for k in range(peixes_total):
            self.losango(fx + 25 * u + k * 30 * u, py + pa / 2, 13 * u,
                         PEIXE if k < peixes else APAGADO, cheio=k < peixes)

        if sobreposicao is not None:
            self._tela(sobreposicao, L / 2, A / 2, 90 * u, piscar)
        ctx.disable(moderngl.BLEND)

    def _tela(self, tipo, cx, cy, s, piscar):
        self.retangulo(0, 0, self.largura, self.altura, (0, 0.02, 0.05, 0.5))
        if tipo is Sobreposicao.INICIO:
            m = glm.scale(glm.translate(glm.mat4(1.0), glm.vec3(cx, cy, 0)),
                          glm.vec3(s * 1.3, s * 1.3, 1))
            self._desenhar("triangulo", moderngl.TRIANGLES, m, BRANCO)
            self.circulo(cx, cy, s * 1.2 + (6 * piscar), BORDA, cheio=False)
        elif tipo is Sobreposicao.PAUSA:
            for dx in (-0.45, 0.45):
                self.retangulo(cx + dx * s, cy, 0.4 * s, 1.6 * s, BRANCO,
                               centrado=True)
        elif tipo is Sobreposicao.DERROTA:
            for ang in (math.pi / 4, -math.pi / 4):
                self.retangulo(cx, cy, 2.2 * s, 0.35 * s, VIDA, ang,
                               centrado=True)
            self.circulo(cx, cy, s * 1.3, VIDA, cheio=False)
        elif tipo is Sobreposicao.VITORIA:
            verde = (0.35, 0.95, 0.5, 1.0)
            # o "visto": um traco curto descendo e um longo subindo
            self.retangulo(cx - 0.45 * s, cy - 0.25 * s, 0.85 * s, 0.3 * s,
                           verde, -math.pi / 4, centrado=True)
            self.retangulo(cx + 0.3 * s, cy + 0.05 * s, 1.6 * s, 0.3 * s,
                           verde, math.radians(48.0), centrado=True)
            self.circulo(cx, cy, s * 1.3 + 6 * piscar, (1.0, 0.85, 0.3, 1.0),
                         cheio=False)

    def liberar(self):
        for v in self.vaos.values():
            v.release()
        for b in self.buffers:
            b.release()

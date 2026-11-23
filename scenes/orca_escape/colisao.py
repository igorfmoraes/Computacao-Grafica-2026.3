"""Colisao em 3D: esfera contra caixa alinhada aos eixos (AABB) e
esfera contra esfera, e o movimento em subpassos que evita o
tunelamento."""
import math

import glm

EPS = 1e-9
# Cada subpasso anda no maximo esta fracao do raio. Com ela menor que
# 1, a esfera nunca salta por cima de uma parede de espessura >= raio.
FRACAO_DO_RAIO = 0.5


class Caixa:
    """Caixa alinhada aos eixos, dada pelos cantos minimo e maximo."""

    def __init__(self, minimo, maximo):
        self.minimo = glm.vec3(minimo)
        self.maximo = glm.vec3(maximo)


def esfera_caixa(centro, raio, caixa):
    """Vetor que tira a esfera de dentro da caixa, ou None se nao ha
    colisao.

    O ponto da caixa mais proximo do centro e o centro com cada
    coordenada limitada ao intervalo da caixa. Se esse ponto esta a
    menos de um raio, ha colisao, e a esfera sai na direcao dele.
    """
    q = glm.clamp(centro, caixa.minimo, caixa.maximo)
    d = centro - q
    dist2 = glm.dot(d, d)
    if dist2 >= raio * raio:
        return None
    if dist2 > EPS:
        dist = math.sqrt(dist2)
        return d * ((raio - dist) / dist)
    # O centro esta dentro da caixa: sai pela face mais proxima.
    melhor, saida = math.inf, glm.vec3(0.0)
    for eixo in range(3):
        para_baixo = centro[eixo] - caixa.minimo[eixo] + raio
        para_cima = caixa.maximo[eixo] - centro[eixo] + raio
        if para_baixo < melhor:
            melhor, saida = para_baixo, glm.vec3(0.0)
            saida[eixo] = -para_baixo
        if para_cima < melhor:
            melhor, saida = para_cima, glm.vec3(0.0)
            saida[eixo] = para_cima
    return saida


def esferas(c1, r1, c2, r2):
    """As esferas se tocam se a distancia dos centros e menor que a
    soma dos raios (comparada ao quadrado, sem raiz)."""
    d = c1 - c2
    return glm.dot(d, d) < (r1 + r2) ** 2


def mover(centro, raio, deslocamento, caixas_perto):
    """Anda o deslocamento em subpassos, resolvendo as colisoes com as
    caixas devolvidas por caixas_perto(centro) a cada subpasso.

    Devolve (novo centro, houve colisao). Como a resolucao empurra a
    esfera so para fora da parede, o movimento ao longo dela continua:
    a esfera desliza.
    """
    distancia = glm.length(deslocamento)
    n = max(1, math.ceil(distancia / (FRACAO_DO_RAIO * raio)))
    passo = deslocamento / n
    centro = glm.vec3(centro)
    colidiu = False
    for _ in range(n):
        centro += passo
        for caixa in caixas_perto(centro):
            saida = esfera_caixa(centro, raio, caixa)
            if saida is not None:
                centro += saida
                colidiu = True
    return centro, colidiu

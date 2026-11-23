"""Geometrias geradas no codigo, cada uma com posicao, normal e
coordenada de textura (8 floats por vertice) e indices.

Todas sao criadas em tamanho unitario; o tamanho no jogo vem da
matriz de modelo. As coordenadas de textura sao geradas junto com a
geometria; na esfera e no toro, a coluna da costura (u = 1) e
duplicada, para que nenhum triangulo interpole de u ~ 1 para u ~ 0.
"""
import math

import numpy as np

EPS = 1e-12


def orientar(dados, indices):
    """Garante faces anti-horarias vistas de fora (a ordem que o
    descarte de faces traseiras espera) e tira as degeneradas.

    A normal geometrica de cada triangulo, (B - A) x (C - A), e
    comparada com a soma das normais dos seus vertices; se apontam
    para lados opostos, dois indices sao trocados.
    """
    pos, nor = dados[:, :3], dados[:, 3:6]
    a, b, c = (pos[indices[:, i]] for i in range(3))
    geom = np.cross(b - a, c - a)
    area = np.linalg.norm(geom, axis=1)
    indices = indices[area > EPS]
    geom = geom[area > EPS]
    soma = nor[indices].sum(axis=1)
    invertidas = np.einsum('ij,ij->i', geom, soma) < 0.0
    indices[invertidas] = indices[invertidas][:, [0, 2, 1]]
    return dados.astype('f4'), np.ascontiguousarray(indices, dtype='u4')


def _grade(n_u, n_v):
    """Indices de uma grade de (n_u + 1) x (n_v + 1) vertices, dois
    triangulos por quadrado."""
    tris = []
    for i in range(n_v):
        for j in range(n_u):
            a = i * (n_u + 1) + j
            b, c, d = a + n_u + 1, a + n_u + 2, a + 1
            tris += [(a, b, c), (a, c, d)]
    return np.array(tris, dtype='i8')


def cubo():
    """Cubo de lado 1 centrado na origem: 24 vertices, para que cada
    face tenha a sua normal e o seu (u, v) de 0 a 1."""
    dados, indices = [], []
    for eixo in range(3):
        for sinal in (-1.0, 1.0):
            n = np.zeros(3)
            n[eixo] = sinal
            t1 = np.zeros(3)
            t1[(eixo + 1) % 3] = 1.0
            t2 = np.cross(n, t1)
            base = len(dados)
            for u, v in ((0, 0), (1, 0), (1, 1), (0, 1)):
                p = 0.5 * n + (u - 0.5) * t1 + (v - 0.5) * t2
                dados.append([*p, *n, u, v])
            indices += [(base, base + 1, base + 2),
                        (base, base + 2, base + 3)]
    return orientar(np.array(dados), np.array(indices))


def plano():
    """Quadrado de [0, 1] x [0, 1] em y = 0, virado para +y."""
    dados = np.array([[x, 0, z, 0, 1, 0, x, z]
                      for x, z in ((0, 0), (1, 0), (1, 1), (0, 1))],
                     dtype='f8')
    return orientar(dados, np.array([(0, 1, 2), (0, 2, 3)]))


def esfera(n_lon=48, n_lat=24):
    """Esfera de raio 1: u e a longitude e v a latitude, de 0 no polo
    sul a 1 no polo norte."""
    dados = []
    for i in range(n_lat + 1):
        theta = math.pi * i / n_lat               # 0 no polo norte
        for j in range(n_lon + 1):                # j = n_lon: costura
            phi = 2.0 * math.pi * j / n_lon
            p = (math.sin(theta) * math.cos(phi), math.cos(theta),
                 math.sin(theta) * math.sin(phi))
            dados.append([*p, *p, j / n_lon, 1.0 - i / n_lat])
    return orientar(np.array(dados), _grade(n_lon, n_lat))


def cone(n=32):
    """Cone de altura 1 e raio da base 0,5, com o vertice em y = 0,5:
    a lateral e a base, que nao compartilham vertices porque as
    normais sao diferentes."""
    r, h = 0.5, 1.0
    inclinacao = math.hypot(h, r)
    dados = []
    for k in range(2):                       # anel da base e vertice
        for j in range(n + 1):
            phi = 2.0 * math.pi * j / n
            normal = (h * math.cos(phi) / inclinacao, r / inclinacao,
                      h * math.sin(phi) / inclinacao)
            raio = r * (1 - k)
            p = (raio * math.cos(phi), -0.5 + k * h, raio * math.sin(phi))
            dados.append([*p, *normal, j / n, float(k)])
    indices = list(_grade(n, 1))
    centro = len(dados)
    dados.append([0, -0.5, 0, 0, -1, 0, 0.5, 0.5])
    for j in range(n + 1):
        phi = 2.0 * math.pi * j / n
        c, s = math.cos(phi), math.sin(phi)
        dados.append([r * c, -0.5, r * s, 0, -1, 0,
                      0.5 + 0.5 * c, 0.5 + 0.5 * s])
    for j in range(n):
        indices.append((centro, centro + 1 + j, centro + 2 + j))
    return orientar(np.array(dados), np.array(indices))


def toro(r_tubo=0.25, n_u=64, n_v=24, voltas_u=4):
    """Toro em torno do eixo y, com raio do anel 1. A textura se
    repete voltas_u vezes ao longo do anel (GL_REPEAT)."""
    dados = []
    for i in range(n_v + 1):
        v = 2.0 * math.pi * i / n_v
        for j in range(n_u + 1):
            u = 2.0 * math.pi * j / n_u
            n = (math.cos(v) * math.cos(u), math.sin(v),
                 math.cos(v) * math.sin(u))
            raio = 1.0 + r_tubo * math.cos(v)
            p = (raio * math.cos(u), r_tubo * math.sin(v),
                 raio * math.sin(u))
            dados.append([*p, *n, voltas_u * j / n_u, i / n_v])
    return orientar(np.array(dados), _grade(n_u, n_v))


def tentaculos(n=8, segmentos=10, raio=0.45, comprimento=1.4):
    """Segmentos de reta (GL_LINES) pendurados de um anel: posicao (3)
    e s (1), a fracao do comprimento, que o vertex shader usa para
    ondular a ponta mais que a raiz."""
    dados = []
    for k in range(n):
        phi = 2.0 * math.pi * k / n
        x, z = raio * math.cos(phi), raio * math.sin(phi)
        for s in range(segmentos):
            for t in (s, s + 1):
                f = t / segmentos
                dados.append([x * (1 - 0.3 * f), -comprimento * f,
                              z * (1 - 0.3 * f), f])
    return np.array(dados, dtype='f4')

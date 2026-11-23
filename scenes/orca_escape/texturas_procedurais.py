"""Texturas geradas com numpy na inicializacao.

As cores sao escritas como cores de tela (sRGB), e as imagens vao
para a GPU como GL_SRGB8_ALPHA8 (texturas.carregar com srgb=True):
o amostrador as decodifica para luz linear antes da iluminacao.

Todos os padroes sao periodicos (o ruido usa uma grade que da a
volta e as senoides tem frequencias inteiras), para que a textura
se repita sem emenda com GL_REPEAT.
"""
import numpy as np

SEMENTE = 2026


def _ruido(lado, celulas, rng):
    """Ruido de valor periodico: valores aleatorios numa grade de
    celulas x celulas, interpolados com a curva suave 3f^2 - 2f^3."""
    grade = rng.random((celulas, celulas))
    t = np.arange(lado) * celulas / lado
    i0 = np.floor(t).astype(int)
    f = t - i0
    f = f * f * (3.0 - 2.0 * f)
    i1 = (i0 + 1) % celulas
    fy, fx = f[:, None], f[None, :]
    a, b = grade[np.ix_(i0, i0)], grade[np.ix_(i0, i1)]
    c, d = grade[np.ix_(i1, i0)], grade[np.ix_(i1, i1)]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def _fbm(lado, rng, base=4, oitavas=4):
    """Soma de oitavas de ruido, normalizada em [0, 1]."""
    soma, peso, total = 0.0, 1.0, 0.0
    for k in range(oitavas):
        soma = soma + peso * _ruido(lado, base * 2 ** k, rng)
        total += peso
        peso *= 0.5
    return soma / total


def _misturar(c0, c1, t):
    t = np.clip(t, 0.0, 1.0)[..., None]
    return np.array(c0) * (1 - t) + np.array(c1) * t


def _rgba(rgb):
    rgb = np.clip(rgb, 0, 255).astype('u1')
    alfa = np.full(rgb.shape[:2] + (1,), 255, dtype='u1')
    return np.concatenate([rgb, alfa], axis=2)


def areia(lado=512):
    rng = np.random.default_rng(SEMENTE)
    n = _fbm(lado, rng, base=8, oitavas=5)
    y, x = np.mgrid[0:lado, 0:lado] / lado
    # ondulacoes da areia, entortadas pelo ruido
    ondas = 0.5 + 0.5 * np.sin(2 * np.pi * (3 * x + 2 * y) + 5.0 * n)
    graos = rng.random((lado, lado))
    t = 0.55 * n + 0.3 * ondas + 0.15 * graos
    return _rgba(_misturar((120, 108, 78), (215, 196, 150), t))


def pedra(lado=512, linhas=8, colunas=4):
    """Blocos de pedra assentados com junta desencontrada, com algas
    onde o ruido e alto."""
    rng = np.random.default_rng(SEMENTE + 1)
    alt, larg = lado // linhas, lado // colunas
    y, x = np.mgrid[0:lado, 0:lado]
    linha = y // alt
    xd = (x + (linha % 2) * (larg // 2)) % lado
    coluna = xd // larg
    ly, lx = y % alt, xd % larg
    junta = 5
    eh_junta = (ly < junta) | (lx < junta)

    tom = rng.uniform(0.75, 1.15, (linhas, colunas))[linha, coluna]
    n = _fbm(lado, rng, base=8, oitavas=4)
    base = np.array((88, 100, 110)) * (tom * (0.8 + 0.4 * n))[..., None]
    # canto dos blocos mais escuro: um pouco de relevo
    borda = np.minimum(np.minimum(ly, alt - ly), np.minimum(lx, larg - lx))
    base *= np.clip(0.75 + borda / 30.0, 0.0, 1.0)[..., None]

    algas = np.clip((_fbm(lado, rng, base=4) - 0.55) * 5.0, 0.0, 1.0)
    cor = base * (1 - algas[..., None] * 0.7) \
        + np.array((40, 95, 50)) * (algas[..., None] * 0.7)
    cor[eh_junta] = (32, 40, 46)
    return _rgba(cor)


def orca(lado=512):
    """Para o mapeamento cilindrico em torno do comprimento da orca:
    u e o angulo (0,5 no dorso, 0 e 1 na barriga) e v vai da cabeca
    (0) a cauda (1). Preta em cima, branca embaixo, com a mancha
    branca atras do olho e a sela cinza atras da nadadeira."""
    rng = np.random.default_rng(SEMENTE + 2)
    lin, col = np.mgrid[0:lado, 0:lado]
    u = (col + 0.5) / lado
    v = 1.0 - (lin + 0.5) / lado        # linha 0 da imagem e v = 1
    d = np.abs(u - 0.5)                 # 0 no dorso, 0,5 na barriga

    # A fronteira da barriga sobe no queixo e some na cauda.
    limite = 0.30 + 0.03 * np.sin(v * 18.0)
    limite = np.where(v < 0.3, 0.30 - 0.1 * (0.3 - v) / 0.3, limite)
    limite = np.where(v > 0.75, 0.30 + (v - 0.75) * 1.2, limite)
    branco = d > limite

    olho = ((d - 0.17) / 0.045) ** 2 + ((v - 0.2) / 0.06) ** 2 < 1.0
    sela = (d < 0.07) & (np.abs(v - 0.52) < 0.06)

    n = _fbm(lado, rng, base=8, oitavas=3)[..., None]
    cor = np.empty((lado, lado, 3))
    cor[:] = (18, 20, 26)
    cor[sela] = (95, 98, 108)
    cor[branco | olho] = (236, 236, 230)
    return _rgba(cor * (0.9 + 0.2 * n))


def escamas(lado=256, n=16):
    """Escamas douradas: cada celula escurece para a borda. A cor vai
    da barriga clara (v = 0) ao dorso alaranjado (v = 1)."""
    lin, col = np.mgrid[0:lado, 0:lado]
    v = 1.0 - (lin + 0.5) / lado
    tam = lado / n
    fy = (lin / tam) % 1.0
    fx = ((col / tam) + 0.5 * (np.floor(lin / tam) % 2)) % 1.0
    dist = np.hypot(fx - 0.5, fy - 0.2)
    sombra = np.clip(1.15 - dist * 1.1, 0.55, 1.0)
    cor = _misturar((250, 225, 150), (235, 110, 25), np.clip(v * 1.6, 0, 1))
    return _rgba(cor * sombra[..., None])


def branca():
    return np.full((4, 4, 4), 255, dtype='u1')

"""As fontes de luz, no espaco do mundo. As cores estao em luz
linear."""
import math

import glm


class LuzDirecional:
    """A luz que vem da superficie, de cima e um pouco de lado."""

    def __init__(self):
        self.direcao = glm.normalize(glm.vec3(0.35, -1.0, 0.25))
        self.cor = glm.vec3(0.35, 0.55, 0.65)
        self.ligada = True


class LuzConica:
    """A lanterna da orca. Entre os dois cones a intensidade cai
    suavemente; fora do externo, zero. A atenuacao 1/(kc + kl d + kq
    d^2) e a mesma da luz pontual."""

    def __init__(self):
        self.pos = glm.vec3(0.0)
        self.direcao = glm.vec3(0, 0, 1)
        self.cor = glm.vec3(2.4, 2.3, 2.0)
        self.cos_interno = math.cos(math.radians(14.0))
        self.cos_externo = math.cos(math.radians(26.0))
        self.atenuacao = glm.vec3(1.0, 0.06, 0.012)
        self.ligada = True


class LuzPontual:
    """A luz da saida: vermelha enquanto fechada, verde quando aberta."""

    FECHADA = glm.vec3(1.6, 0.25, 0.15)
    ABERTA = glm.vec3(0.3, 2.2, 0.8)

    def __init__(self):
        self.pos = glm.vec3(0.0)
        self.cor = glm.vec3(self.FECHADA)
        self.atenuacao = glm.vec3(1.0, 0.12, 0.04)
        self.ligada = True

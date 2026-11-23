"""Os elementos do jogo. Cada um guarda o seu estado (posicao,
direcao, tempo proprio) e monta a sua matriz de modelo; nenhum mexe
nos VBOs. Todas as velocidades estao em unidades por segundo."""
import math

import glm

from . import colisao

EIXO_Y = glm.vec3(0, 1, 0)
IDENTIDADE = glm.mat4(1.0)

# O OFF da orca tem a cabeca em -y e o dorso em +z. Esta rotacao de
# -90 graus em x leva -y para +z (a frente do jogo) e +z para +y.
ORIENTACAO_ORCA = glm.rotate(IDENTIDADE, glm.radians(-90.0),
                             glm.vec3(1, 0, 0))


def frente_de(rumo):
    """Direcao horizontal para um rumo, em radianos: rumo 0 e +z, e a
    rotacao de rumo em torno de y leva +z para esta direcao."""
    return glm.vec3(math.sin(rumo), 0.0, math.cos(rumo))


class Orca:
    RAIO = 0.8                  # esfera de colisao
    ALTURA = 1.3                # do centro ao fundo
    ESCALA = 1.2                # sobre a esfera de raio 1 do enquadramento
    VELOCIDADE = 6.0
    VELOCIDADE_TURBO = 14.0
    GIRO = math.radians(140.0)  # rad/s
    INVULNERAVEL = 1.5          # segundos depois de uma batida
    EMPURRAO = 5.0              # recuo depois de bater numa agua-viva

    def __init__(self, labirinto, enquadramento):
        self.lab = labirinto
        self.enquadramento = enquadramento
        self.reiniciar()

    def reiniciar(self):
        self.pos = self.lab.centro_celula(self.lab.inicio, self.ALTURA)
        col, lin = self.lab.inicio
        # comeca virada para a primeira celula livre vizinha
        self.rumo = 0.0
        for rumo, (dc, dl) in ((0.0, (0, 1)), (math.pi / 2, (1, 0)),
                               (math.pi, (0, -1)), (-math.pi / 2, (-1, 0))):
            if self.lab.livre(col + dc, lin + dl):
                self.rumo = rumo
                break
        self.tempo = 0.0
        self.invulneravel = 0.0
        self.recuo = glm.vec3(0.0)
        self.velocidade_atual = 0.0
        self.inclinacao = 0.0

    @property
    def frente(self):
        return frente_de(self.rumo)

    @property
    def visivel(self):
        """Pisca enquanto esta invulneravel (pelo tempo do jogo, que
        para na pausa)."""
        return self.invulneravel <= 0.0 or int(self.tempo * 12) % 2 == 0

    def atualizar(self, dt, avancar, girar, turbo):
        self.tempo += dt
        self.invulneravel = max(0.0, self.invulneravel - dt)
        self.rumo += girar * self.GIRO * dt
        vel = self.VELOCIDADE_TURBO if turbo else self.VELOCIDADE
        self.velocidade_atual = avancar * vel
        # A orca se inclina na curva; a inclinacao segue o alvo com
        # um decaimento exponencial, independente da taxa de quadros.
        alvo = -0.35 * girar * (1.0 if avancar >= 0 else -1.0)
        self.inclinacao += (alvo - self.inclinacao) * (1 - math.exp(-6 * dt))

        deslocamento = self.frente * (self.velocidade_atual * dt) \
            + self.recuo * dt
        self.recuo *= math.exp(-4.0 * dt)
        self.pos, _ = colisao.mover(self.pos, self.RAIO, deslocamento,
                                    self.lab.caixas_perto)

    def bater(self, origem):
        """Perde vida, se nao esta invulneravel. Devolve True se perdeu."""
        if self.invulneravel > 0.0:
            return False
        direcao = self.pos - origem
        direcao.y = 0.0
        if glm.length(direcao) > 1e-6:
            self.recuo = glm.normalize(direcao) * self.EMPURRAO * 2
        self.invulneravel = self.INVULNERAVEL
        return True

    def matriz(self):
        # Animacao propria: sobe e desce e abana o corpo ao nadar.
        flutua = 0.12 * math.sin(self.tempo * 2.0)
        abano = 0.06 * math.sin(self.tempo * 9.0) \
            * min(1.0, abs(self.velocidade_atual) / self.VELOCIDADE)
        m = glm.translate(IDENTIDADE, self.pos + glm.vec3(0, flutua, 0))
        m = glm.rotate(m, self.rumo + abano, EIXO_Y)
        m = glm.rotate(m, self.inclinacao, glm.vec3(0, 0, 1))
        m = glm.scale(m, glm.vec3(self.ESCALA))
        return m * ORIENTACAO_ORCA * self.enquadramento

    def lanterna(self):
        """Posicao e direcao da luz conica, na cabeca da orca."""
        pos = self.pos + self.frente * 1.1 + glm.vec3(0, 0.25, 0)
        return pos, glm.normalize(self.frente + glm.vec3(0, -0.18, 0))


class AguaViva:
    RAIO = 0.75
    VELOCIDADE = 3.0
    ALTURA = 1.7

    def __init__(self, labirinto, celula, direcao, fase):
        self.lab = labirinto
        self.celula, self.direcao_inicial = celula, glm.vec3(direcao)
        self.fase = fase
        self.reiniciar()

    def reiniciar(self):
        self.pos = self.lab.centro_celula(self.celula, self.ALTURA)
        self.direcao = glm.vec3(self.direcao_inicial)
        self.tempo = 0.0

    def atualizar(self, dt):
        self.tempo += dt
        self.pos, bateu = colisao.mover(
            self.pos, self.RAIO, self.direcao * (self.VELOCIDADE * dt),
            self.lab.caixas_perto)
        if bateu:
            self.direcao = -self.direcao       # ricochete na parede

    @property
    def pulso(self):
        return math.sin(self.tempo * 3.0 + self.fase)

    @property
    def centro(self):
        return self.pos + glm.vec3(0, 0.25 * math.sin(self.tempo * 1.3
                                                      + self.fase), 0)

    def matriz_sino(self):
        """Elipsoide que pulsa: escala nao uniforme que muda com o
        tempo (a matriz normal corrige as normais)."""
        p = self.pulso
        m = glm.translate(IDENTIDADE, self.centro)
        return glm.scale(m, glm.vec3(0.8 * (1 + 0.12 * p), 0.55 * (1 - 0.18 * p),
                                     0.8 * (1 + 0.12 * p)))

    def matriz_tentaculos(self):
        return glm.translate(IDENTIDADE, self.centro)


class Peixe:
    RAIO = 0.6

    def __init__(self, labirinto, celula, fase):
        self.base = labirinto.centro_celula(celula, 1.4)
        self.fase = fase
        self.reiniciar()

    def reiniciar(self):
        self.vivo = True
        self.tempo = 0.0

    def atualizar(self, dt):
        self.tempo += dt

    @property
    def pos(self):
        return self.base + glm.vec3(0, 0.3 * math.sin(self.tempo * 2.2
                                                      + self.fase), 0)

    def matrizes(self):
        """(corpo, cauda). O peixe nada em circulos: gira em torno de y
        e anda um pouco para fora do centro da celula."""
        angulo = self.tempo * 1.6 + self.fase
        m = glm.translate(IDENTIDADE, self.pos)
        m = glm.rotate(m, angulo, EIXO_Y)
        m = glm.translate(m, glm.vec3(0, 0, 0.6))
        corpo = glm.scale(m, glm.vec3(0.7, 0.42, 0.22))
        abano = 0.4 * math.sin(self.tempo * 10.0 + self.fase)
        c = glm.translate(m, glm.vec3(-0.62, 0, 0))
        c = glm.rotate(c, abano, EIXO_Y)
        c = glm.translate(c, glm.vec3(-0.25, 0, 0))
        c = glm.rotate(c, glm.radians(-90.0), glm.vec3(0, 0, 1))
        cauda = glm.scale(c, glm.vec3(0.9, 0.5, 0.12))
        return corpo, cauda


class Saida:
    RAIO = 1.3

    def __init__(self, labirinto):
        self.pos = labirinto.centro_celula(labirinto.saida, 1.6)
        self.tempo = 0.0
        self.aberta = False

    def reiniciar(self):
        self.tempo = 0.0
        self.aberta = False

    def atualizar(self, dt):
        self.tempo += dt

    def matriz(self):
        m = glm.translate(IDENTIDADE, self.pos)
        m = glm.rotate(m, self.tempo * 0.8, EIXO_Y)
        m = glm.rotate(m, glm.radians(90.0), glm.vec3(1, 0, 0))
        return glm.scale(m, glm.vec3(1.2))

    @property
    def brilho(self):
        """Pulsa mais rapido quando aberta."""
        freq = 4.0 if self.aberta else 1.5
        return 0.6 + 0.4 * math.sin(self.tempo * freq)

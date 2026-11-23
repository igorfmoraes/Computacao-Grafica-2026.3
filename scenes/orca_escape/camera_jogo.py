"""Camera LookAt com dois modos: seguindo a orca e a visao geral do
labirinto. Arrastar o mouse gira a camera em torno do alvo e a roda
muda a distancia.

near e far: o near e pequeno (0,1) na camera que segue, que chega a
~3 unidades da orca e das paredes; o far (90) passa do ponto em que
a neblina ja cobriu tudo (exp(-(0,035 d)^2) < 0,01 para d > 61), entao
nada some de repente. Na visao geral, a camera fica a ~70 do centro e
o labirinto tem 60 x 60: near 1 e far 220 envolvem a cena com folga
e dao mais precisao ao buffer de profundidade que um near de 0,1.
"""
import math

import glm

FOVY = math.radians(50.0)
SENSIBILIDADE = 0.005          # radianos por pixel arrastado
PASSO_ZOOM = 0.1               # fracao da distancia por clique da roda

SEGUIR, GERAL = 0, 1
NOMES = {SEGUIR: "seguir", GERAL: "geral"}


class Orbita:
    """Parametros de um modo: distancia ao alvo, elevacao e um desvio
    de rumo controlado pelo mouse."""

    def __init__(self, distancia, elevacao, dist_min, dist_max,
                 near, far, neblina):
        self.distancia, self.elevacao = distancia, elevacao
        self.desvio = 0.0
        self.dist_min, self.dist_max = dist_min, dist_max
        self.near, self.far = near, far
        self.neblina = neblina
        self.padrao = (distancia, elevacao)

    def zerar(self):
        self.distancia, self.elevacao = self.padrao
        self.desvio = 0.0


class CameraJogo:
    def __init__(self, labirinto):
        self.lab = labirinto
        tam = max(labirinto.largura, labirinto.profundidade)
        dist_geral = 0.6 * tam / math.tan(FOVY / 2)
        self.orbitas = {
            SEGUIR: Orbita(7.0, math.radians(28.0), 3.0, 16.0,
                           0.1, 90.0, 0.035),
            GERAL: Orbita(dist_geral, math.radians(70.0), 0.3 * dist_geral,
                          1.5 * dist_geral, 1.0, 220.0, 0.004),
        }
        self.modo = SEGUIR
        self.aspecto = 1.0
        self.perspectiva = True
        self.olho = glm.vec3(0, 10, 0)
        self.alvo = glm.vec3(0)
        self.rumo_suave = None

    @property
    def orbita(self):
        return self.orbitas[self.modo]

    @property
    def neblina(self):
        return self.orbita.neblina

    def alternar_modo(self):
        self.modo = GERAL if self.modo == SEGUIR else SEGUIR

    def girar(self, dx, dy):
        o = self.orbita
        o.desvio -= dx * SENSIBILIDADE
        o.elevacao = min(math.radians(85.0),
                         max(math.radians(5.0), o.elevacao + dy * SENSIBILIDADE))

    def aproximar(self, cliques):
        o = self.orbita
        o.distancia = min(o.dist_max, max(o.dist_min,
                          o.distancia * (1.0 - PASSO_ZOOM * cliques)))

    def zerar(self):
        for o in self.orbitas.values():
            o.zerar()
        self.rumo_suave = None

    def atualizar(self, dt, orca):
        if self.modo == SEGUIR:
            # O rumo da camera persegue o da orca com decaimento
            # exponencial: suave e igual em qualquer taxa de quadros.
            if self.rumo_suave is None:
                self.rumo_suave = orca.rumo
            diferenca = math.remainder(orca.rumo - self.rumo_suave, 2 * math.pi)
            self.rumo_suave += diferenca * (1.0 - math.exp(-5.0 * dt))
            self.alvo = orca.pos + glm.vec3(0, 0.6, 0)
            rumo = self.rumo_suave
        else:
            self.alvo = glm.vec3(self.lab.centro)
            rumo = math.pi            # norte do mapa no alto da tela
        o = self.orbita
        r = rumo + o.desvio
        horizontal = o.distancia * math.cos(o.elevacao)
        self.olho = self.alvo + glm.vec3(-math.sin(r) * horizontal,
                                         o.distancia * math.sin(o.elevacao),
                                         -math.cos(r) * horizontal)

    def visao(self):
        return glm.lookAt(self.olho, self.alvo, glm.vec3(0, 1, 0))

    def projecao(self):
        o = self.orbita
        if self.perspectiva:
            return glm.perspective(FOVY, self.aspecto, o.near, o.far)
        # Ortografica com a mesma meia-altura que a perspectiva tem no
        # plano do alvo: a cena nao muda de tamanho ao alternar.
        t = o.distancia * math.tan(FOVY / 2)
        r = t * self.aspecto
        return glm.ortho(-r, r, -t, t, o.near, o.far)

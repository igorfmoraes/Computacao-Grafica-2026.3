"""Laco de jogo e maquina de estados.

  INICIO --ENTER--> JOGANDO <--P--> PAUSADO
  JOGANDO --> DERROTA | VITORIA --ENTER--> JOGANDO (partida nova)
  R reinicia a partida a qualquer momento.

Adaptado do Game do jogo 2D (harpoon_shooter).
"""
from enum import Enum, auto

import glfw

from . import camera_jogo
from .hud import Sobreposicao

TITULO = "Orca Escape"
DT_MAXIMO = 1.0 / 20.0           # passo maximo, em segundos
INTERVALO_FPS = 0.5              # atualizacao do FPS no titulo


class Estado(Enum):
    INICIO = auto()
    JOGANDO = auto()
    PAUSADO = auto()
    DERROTA = auto()
    VITORIA = auto()


ROTULOS = {Estado.INICIO: "INICIO (ENTER)", Estado.JOGANDO: "JOGANDO",
           Estado.PAUSADO: "PAUSADO", Estado.DERROTA: "DERROTA (ENTER)",
           Estado.VITORIA: "VITORIA (ENTER)"}
SOBREPOSICOES = {Estado.INICIO: Sobreposicao.INICIO,
                 Estado.PAUSADO: Sobreposicao.PAUSA,
                 Estado.DERROTA: Sobreposicao.DERROTA,
                 Estado.VITORIA: Sobreposicao.VITORIA}


class Jogo:
    def __init__(self, janela, cena):
        self.janela, self.cena = janela, cena
        self.estado = Estado.INICIO
        self.vsync = True
        self.fps = 0.0
        self._quadros = 0
        self._inicio_fps = janela.tempo()
        self.acoes = {
            glfw.KEY_ESCAPE: janela.fechar,
            glfw.KEY_ENTER: self._iniciar,
            glfw.KEY_KP_ENTER: self._iniciar,
            glfw.KEY_P: self._pausar,
            glfw.KEY_R: self._reiniciar,
            glfw.KEY_V: self._alternar_vsync,
            glfw.KEY_C: self._alternar_camera,
            glfw.KEY_O: self._alternar_projecao,
            glfw.KEY_L: self._alternar(lambda: cena.luz_dir),
            glfw.KEY_F: self._alternar(lambda: cena.lanterna),
            glfw.KEY_K: self._alternar(lambda: cena.luz_saida),
            glfw.KEY_Z: cena.camera.zerar,
        }
        janela.ao_teclar.append(self._tecla)
        janela.ao_arrastar.append(self._arrastar)
        janela.ao_rolar.append(self._rolar)
        janela.ao_redimensionar.append(self._redimensionar)
        cena.redimensionar(*janela.tamanho_framebuffer())
        self._atualizar_titulo()

    def executar(self):
        anterior = self.janela.tempo()
        while not self.janela.deve_fechar():
            agora = self.janela.tempo()
            # Passo maximo: janela arrastada ou programa parado nao
            # viram um salto na simulacao.
            dt = min(agora - anterior, DT_MAXIMO)
            # anterior avanca mesmo na pausa: o tempo pausado nunca
            # entra no dt.
            anterior = agora

            if self.estado is Estado.JOGANDO:
                resultado = self.cena.atualizar(dt, *self._ler_controles())
                if resultado == "derrota":
                    self._mudar(Estado.DERROTA)
                elif resultado == "vitoria":
                    self._mudar(Estado.VITORIA)
            # Na pausa a camera tambem fica parada (dt = 0).
            dt_camera = 0.0 if self.estado is Estado.PAUSADO else dt
            self.cena.camera.atualizar(dt_camera, self.cena.orca)

            self.cena.desenhar(SOBREPOSICOES.get(self.estado), agora)
            self.janela.trocar_buffers()
            self.janela.processar_eventos()
            self._contar_quadro(agora)

    def _ler_controles(self):
        """Movimento continuo: consulta direta com glfw.get_key."""
        j = self.janela
        avancar = float(j.tecla_apertada(glfw.KEY_W, glfw.KEY_UP)) \
            - float(j.tecla_apertada(glfw.KEY_S, glfw.KEY_DOWN))
        girar = float(j.tecla_apertada(glfw.KEY_A, glfw.KEY_LEFT)) \
            - float(j.tecla_apertada(glfw.KEY_D, glfw.KEY_RIGHT))
        turbo = j.tecla_apertada(glfw.KEY_LEFT_SHIFT, glfw.KEY_RIGHT_SHIFT)
        return avancar, girar, turbo

    # --- acoes discretas (callback de teclado) ---

    def _tecla(self, tecla):
        acao = self.acoes.get(tecla)
        if acao is not None:
            acao()

    def _mudar(self, estado):
        self.estado = estado
        self._atualizar_titulo()

    def _iniciar(self):
        if self.estado in (Estado.DERROTA, Estado.VITORIA):
            self.cena.reiniciar()
        if self.estado in (Estado.INICIO, Estado.DERROTA, Estado.VITORIA):
            self._mudar(Estado.JOGANDO)

    def _reiniciar(self):
        self.cena.reiniciar()
        self._mudar(Estado.INICIO)

    def _pausar(self):
        if self.estado is Estado.JOGANDO:
            self._mudar(Estado.PAUSADO)
        elif self.estado is Estado.PAUSADO:
            self._mudar(Estado.JOGANDO)

    def _alternar_vsync(self):
        self.vsync = not self.vsync
        self.janela.definir_vsync(self.vsync)
        self._atualizar_titulo()

    def _alternar_camera(self):
        self.cena.camera.alternar_modo()
        self._atualizar_titulo()

    def _alternar_projecao(self):
        cam = self.cena.camera
        cam.perspectiva = not cam.perspectiva
        self._atualizar_titulo()

    def _alternar(self, luz):
        def alternar():
            fonte = luz()
            fonte.ligada = not fonte.ligada
            self._atualizar_titulo()
        return alternar

    # --- mouse (callbacks) ---

    def _arrastar(self, dx, dy):
        if self.estado is not Estado.PAUSADO:
            self.cena.camera.girar(dx, dy)

    def _rolar(self, cliques):
        if self.estado is not Estado.PAUSADO:
            self.cena.camera.aproximar(cliques)

    def _redimensionar(self, largura, altura):
        self.cena.redimensionar(largura, altura)

    # --- titulo ---

    def _contar_quadro(self, agora):
        self._quadros += 1
        if agora - self._inicio_fps >= INTERVALO_FPS:
            self.fps = self._quadros / (agora - self._inicio_fps)
            self._quadros, self._inicio_fps = 0, agora
            self._atualizar_titulo()

    def _atualizar_titulo(self):
        c = self.cena
        liga = lambda fonte: "on" if fonte.ligada else "off"  # noqa: E731
        cam = c.camera
        proj = "persp" if cam.perspectiva else "orto"
        self.janela.definir_titulo(
            f"{TITULO} | {ROTULOS[self.estado]} | FPS {self.fps:.0f} | "
            f"VSync {'ON' if self.vsync else 'OFF'} | "
            f"camera {camera_jogo.NOMES[cam.modo]} ({proj}) | "
            f"luz dir {liga(c.luz_dir)} | lanterna {liga(c.lanterna)} | "
            f"saida {liga(c.luz_saida)}")

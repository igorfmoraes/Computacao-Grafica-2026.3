"""Janela GLFW com contexto OpenGL 4.0 Core e os callbacks de
teclado, mouse e redimensionamento repassados a quem se inscrever.
Adaptada da Window do jogo 2D (harpoon_shooter)."""
import sys

import glfw
import moderngl

VERSAO_GL = (4, 0)
AMOSTRAS = 4


class ErroJanela(RuntimeError):
    pass


class Janela:
    def __init__(self, largura, altura, titulo):
        glfw.set_error_callback(self._erro_glfw)
        if not glfw.init():
            raise ErroJanela("FALHA: o GLFW nao inicializou")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, VERSAO_GL[0])
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, VERSAO_GL[1])
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.SAMPLES, AMOSTRAS)
        glfw.window_hint(glfw.SRGB_CAPABLE, glfw.TRUE)
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)
        self._janela = glfw.create_window(largura, altura, titulo, None, None)
        if not self._janela:
            glfw.terminate()
            raise ErroJanela("FALHA: nao foi possivel criar a janela")
        glfw.make_context_current(self._janela)
        glfw.swap_interval(1)
        self.ctx = moderngl.create_context(require=400)

        self.ao_teclar, self.ao_arrastar, self.ao_rolar = [], [], []
        self.ao_redimensionar = []
        self._arrastando = False
        self._ultimo = (0.0, 0.0)
        glfw.set_key_callback(self._janela, self._tecla)
        glfw.set_mouse_button_callback(self._janela, self._botao)
        glfw.set_cursor_pos_callback(self._janela, self._cursor)
        glfw.set_scroll_callback(self._janela, self._roda)
        glfw.set_framebuffer_size_callback(self._janela, self._tamanho)

    # --- consultas ---

    @staticmethod
    def tempo():
        return glfw.get_time()

    def tecla_apertada(self, *teclas):
        """Consulta direta, para os movimentos continuos."""
        return any(glfw.get_key(self._janela, k) == glfw.PRESS for k in teclas)

    def tamanho_framebuffer(self):
        return glfw.get_framebuffer_size(self._janela)

    def deve_fechar(self):
        return bool(glfw.window_should_close(self._janela))

    def fechar(self):
        glfw.set_window_should_close(self._janela, True)

    def trocar_buffers(self):
        glfw.swap_buffers(self._janela)

    @staticmethod
    def processar_eventos():
        glfw.poll_events()

    @staticmethod
    def definir_vsync(ligado):
        glfw.swap_interval(1 if ligado else 0)

    def definir_titulo(self, titulo):
        glfw.set_window_title(self._janela, titulo)

    @staticmethod
    def encerrar():
        glfw.terminate()

    # --- callbacks ---

    def _tecla(self, janela, tecla, scancode, acao, mods):
        if acao == glfw.PRESS:
            for f in self.ao_teclar:
                f(tecla)

    def _botao(self, janela, botao, acao, mods):
        if botao in (glfw.MOUSE_BUTTON_LEFT, glfw.MOUSE_BUTTON_RIGHT):
            self._arrastando = acao == glfw.PRESS
            self._ultimo = glfw.get_cursor_pos(janela)

    def _cursor(self, janela, x, y):
        if self._arrastando:
            dx, dy = x - self._ultimo[0], y - self._ultimo[1]
            for f in self.ao_arrastar:
                f(dx, dy)
        self._ultimo = (x, y)

    def _roda(self, janela, dx, dy):
        for f in self.ao_rolar:
            f(dy)

    def _tamanho(self, janela, largura, altura):
        for f in self.ao_redimensionar:
            f(largura, altura)

    @staticmethod
    def _erro_glfw(codigo, descricao):
        print(f"GLFW [{codigo}]: {descricao}", file=sys.stderr)

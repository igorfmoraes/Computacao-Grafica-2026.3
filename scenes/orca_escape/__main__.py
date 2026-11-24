"""Orca Escape - jogo 3D de labirinto.

MCCC007-23 Computacao Grafica - UFABC - Atividade 05

A orca precisa coletar todos os peixes do labirinto e chegar a saida (o
anel luminoso, que fica verde quando todos os peixes foram pegos), sem
encostar nas aguas-vivas: cada toque custa uma vida.

Execucao (a partir de scenes/, com o ambiente virtual ativo):
    python -m orca_escape

Teclado - movimento continuo (consulta direta com glfw.get_key):
    W / seta cima       nada para frente
    S / seta baixo      nada para tras
    A / seta esquerda   gira a esquerda
    D / seta direita    gira a direita
    SHIFT               turbo

Teclado - acoes (callback):
    ENTER   inicia / nova partida apos o fim de jogo
    P       pausa / retoma
    R       reinicia (volta a tela de inicio)
    C       camera: seguir a orca / visao geral
    O       projecao perspectiva / ortografica
    L       liga / desliga a luz direcional (superficie)
    F       liga / desliga a lanterna (luz conica da orca)
    K       liga / desliga a luz pontual da saida
    V       liga / desliga o vsync (FPS na barra de titulo)
    Z       volta a camera a posicao padrao
    ESC     sai

Mouse (callbacks):
    arrastar com o botao esquerdo ou direito   gira a camera
    roda                                        aproxima / afasta
"""

import os
import sys

# GLFW needs X11 on Linux with Wayland, and it reads this when imported.
os.environ["XDG_SESSION_TYPE"] = "x11"

from .game import BASE_TITLE, Game  # noqa: E402
from .keyboard_controls import KeyboardControls  # noqa: E402
from .scene import Scene  # noqa: E402
from .window import Window, WindowCreationError  # noqa: E402

WINDOW_WIDTH_PIXELS = 1280
WINDOW_HEIGHT_PIXELS = 720


def main() -> None:
    try:
        window = Window(WINDOW_WIDTH_PIXELS, WINDOW_HEIGHT_PIXELS, BASE_TITLE)
    except WindowCreationError as error:
        sys.exit(str(error))

    scene = Scene.build(window.graphics_context)
    print(KeyboardControls.HELP_TEXT)
    try:
        Game(window, scene).run()
    finally:
        scene.release()
        window.terminate()


if __name__ == "__main__":
    main()

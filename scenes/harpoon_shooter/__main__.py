"""Harpoon Shooter

Execução (a partir do diretório que contém o pacote):
    python -m harpoon_shooter

Teclas:
    ENTER          Inicia a partida ou reinicia após o fim de jogo
    SETA ESQUERDA  Gira o pescador no sentido anti-horário (limite de 30°)
    SETA DIREITA   Gira o pescador no sentido horário (limite de 30°)
    ESPAÇO         Atira o arpão na direção em que o pescador está virado
    P              Pausa / retoma
    V              Liga / desliga o VSync (a taxa de quadros aparece na barra de título)
    ESC            Fecha o jogo

Regra: a cada 3 arpões que saem da tela sem acertar um peixe, o jogo termina.
"""

import sys
import os

os.environ["XDG_SESSION_TYPE"] = "x11"
from .game import Game
from .scene import Scene
from .window import Window, WindowCreationError

WINDOW_WIDTH_PIXELS = 800
WINDOW_HEIGHT_PIXELS = 800
WINDOW_TITLE = "Harpoon Shooter"


def main() -> None:
    try:
        window = Window(WINDOW_WIDTH_PIXELS, WINDOW_HEIGHT_PIXELS, WINDOW_TITLE)
    except WindowCreationError as error:
        sys.exit(str(error))

    scene = Scene.build(window.graphics_context)
    print(__doc__)
    Game(window, scene).run()


if __name__ == "__main__":
    main()

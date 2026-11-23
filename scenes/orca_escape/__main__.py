"""Orca Escape - jogo 3D de labirinto.

MCCC007-23 Computacao Grafica - UFABC - Atividade 05

Uma orca precisa coletar todos os peixes do labirinto e chegar a
saida (o anel luminoso, que fica verde quando todos os peixes foram
pegos), sem encostar nas aguas-vivas: cada toque custa uma vida.

Execucao (a partir de scenes/, com o ambiente virtual ativo):
    python -m orca_escape
No Linux com Wayland, o GLFW precisa de XDG_SESSION_TYPE=x11 (ja
definido abaixo).

Teclado - movimento continuo (consulta direta):
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

os.environ["XDG_SESSION_TYPE"] = "x11"

from .cena import Cena                   # noqa: E402
from .janela import ErroJanela, Janela   # noqa: E402
from .jogo import TITULO, Jogo           # noqa: E402


def main():
    try:
        janela = Janela(1280, 720, TITULO)
    except ErroJanela as erro:
        sys.exit(str(erro))
    cena = Cena(janela.ctx)
    print(__doc__)
    try:
        Jogo(janela, cena).executar()
    finally:
        cena.liberar()
        janela.encerrar()


if __name__ == "__main__":
    main()

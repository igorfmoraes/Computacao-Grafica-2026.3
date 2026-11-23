"""O labirinto: uma grade de celulas lida de um mapa em texto.

  #  parede        S  inicio da orca     E  saida
  o  peixe         H  agua-viva que nada em x   V  agua-viva em z
  .  agua livre
"""
import glm

from .colisao import Caixa

CELULA = 4.0          # lado de uma celula, em unidades do mundo
ALTURA_PAREDE = 2.6

MAPA = [
    "###############",
    "#S..#.....#..o#",
    "#.#.#.###.#.#.#",
    "#.#...#o..#.#.#",
    "#.#####.###.#.#",
    "#o..H.#...#...#",
    "###.#.###.###.#",
    "#...#...#.....#",
    "#.#####.#.###.#",
    "#.#o..#...#o#.#",
    "#.#.#.#####.#.#",
    "#..V#...o...#.#",
    "#.###.#####.#.#",
    "#o....#..H...E#",
    "###############",
]


class Labirinto:
    def __init__(self, mapa=MAPA):
        self.linhas, self.colunas = len(mapa), len(mapa[0])
        self.paredes = {}               # (coluna, linha) -> Caixa
        self.peixes, self.aguas_vivas = [], []
        self.inicio = self.saida = None
        for lin, texto in enumerate(mapa):
            if len(texto) != self.colunas:
                raise ValueError(f"linha {lin} do mapa com tamanho errado")
            for col, c in enumerate(texto):
                if c == "#":
                    x0, z0 = col * CELULA, lin * CELULA
                    self.paredes[(col, lin)] = Caixa(
                        (x0, 0.0, z0),
                        (x0 + CELULA, ALTURA_PAREDE, z0 + CELULA))
                elif c == "S":
                    self.inicio = (col, lin)
                elif c == "E":
                    self.saida = (col, lin)
                elif c == "o":
                    self.peixes.append((col, lin))
                elif c in "HV":
                    direcao = glm.vec3(1, 0, 0) if c == "H" \
                        else glm.vec3(0, 0, 1)
                    self.aguas_vivas.append(((col, lin), direcao))
        if self.inicio is None or self.saida is None:
            raise ValueError("o mapa precisa de S e de E")

    @property
    def largura(self):
        return self.colunas * CELULA

    @property
    def profundidade(self):
        return self.linhas * CELULA

    @property
    def centro(self):
        return glm.vec3(self.largura / 2, 0.0, self.profundidade / 2)

    def centro_celula(self, celula, y=0.0):
        col, lin = celula
        return glm.vec3((col + 0.5) * CELULA, y, (lin + 0.5) * CELULA)

    def livre(self, col, lin):
        return (col, lin) not in self.paredes and \
            0 <= col < self.colunas and 0 <= lin < self.linhas

    def caixas_perto(self, p):
        """As paredes das 3 x 3 celulas em torno do ponto: com raios
        menores que uma celula, nenhuma outra pode tocar a esfera."""
        col, lin = int(p.x // CELULA), int(p.z // CELULA)
        for dl in (-1, 0, 1):
            for dc in (-1, 0, 1):
                caixa = self.paredes.get((col + dc, lin + dl))
                if caixa is not None:
                    yield caixa

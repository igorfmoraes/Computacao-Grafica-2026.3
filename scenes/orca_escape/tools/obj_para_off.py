"""Converte um OBJ de faces triangulares para OFF, fora do jogo.

O OBJ repete posicoes nas costuras das coordenadas de textura (o
mesmo ponto aparece uma vez para cada (u, v)). O OFF guarda so
posicoes, entao os vertices de mesma posicao sao fundidos: assim a
malha fica fechada e as normais de vertice saem suaves. Faces que
ficam degeneradas depois da fusao sao descartadas.

As coordenadas sao gravadas como estao no OBJ; o jogo enquadra a
malha por uma matriz (Malha.matriz_enquadramento).

Uso: python tools/obj_para_off.py entrada.obj saida.off
"""
import sys
from pathlib import Path

import numpy as np

CASAS = 6      # precisao usada para decidir que duas posicoes sao iguais


def ler_obj(caminho):
    vertices, faces = [], []
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        campos = linha.split()
        if not campos:
            continue
        if campos[0] == "v":
            vertices.append([float(c) for c in campos[1:4]])
        elif campos[0] == "f":
            # "i/t/n" -> i; indices do OBJ comecam em 1
            idx = [int(c.split("/")[0]) - 1 for c in campos[1:]]
            for k in range(1, len(idx) - 1):          # leque
                faces.append([idx[0], idx[k], idx[k + 1]])
    return np.array(vertices, dtype='f8'), np.array(faces, dtype='i8')


def fundir(vertices, faces):
    chave = np.round(vertices, CASAS)
    unicos, inverso = np.unique(chave, axis=0, return_inverse=True)
    faces = inverso.ravel()[faces]
    a, b, c = faces[:, 0], faces[:, 1], faces[:, 2]
    validas = (a != b) & (b != c) & (a != c)
    return unicos, faces[validas]


def volume_com_sinal(vertices, faces):
    a, b, c = (vertices[faces[:, i]] for i in range(3))
    return np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6.0


def gravar_off(caminho, vertices, faces):
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("OFF\n")
        f.write(f"{len(vertices)} {len(faces)} 0\n")
        np.savetxt(f, vertices, fmt="%.6f")
        np.savetxt(f, np.hstack([np.full((len(faces), 1), 3), faces]),
                   fmt="%d")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    vertices, faces = ler_obj(sys.argv[1])
    print(f"OBJ: {len(vertices)} vertices, {len(faces)} faces")
    vertices, faces = fundir(vertices, faces)
    # Volume positivo: faces anti-horarias vistas de fora.
    if volume_com_sinal(vertices, faces) < 0.0:
        faces = faces[:, ::-1]
        print("orientacao invertida para anti-horaria")
    gravar_off(sys.argv[2], vertices, faces)
    print(f"OFF: {len(vertices)} vertices, {len(faces)} faces")


if __name__ == "__main__":
    main()

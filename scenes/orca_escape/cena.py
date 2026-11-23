"""A cena: cria uma vez os programas, VBOs e texturas, guarda os
elementos do jogo, atualiza a simulacao e desenha cada quadro.

Cada geometria tem um so VBO, desenhado quantas vezes for preciso
com matrizes de modelo diferentes (as ~120 paredes sao o mesmo cubo).
"""
from pathlib import Path

import glm
import moderngl

from . import colisao, geometria
from . import texturas as tx
from . import texturas_procedurais as tp
from .camera_jogo import CameraJogo
from .entidades import AguaViva, Orca, Peixe, Saida
from .hud import Hud
from .labirinto import ALTURA_PAREDE, CELULA, Labirinto
from .luzes import LuzConica, LuzDirecional, LuzPontual
from .malha import Malha
from .material import Material

AQUI = Path(__file__).parent
ARQUIVO_ORCA = AQUI / "models" / "orca.off"

# O moderngl nao tem nome para este estado do OpenGL.
GL_FRAMEBUFFER_SRGB = 0x8DB9

VIDAS = 3
PONTOS_PEIXE = 100
PONTOS_VIDA_RESTANTE = 500

# Cor da agua em luz linear: e a cor de limpeza e a da neblina, para
# que o que some na neblina se funda com o fundo.
AGUA = glm.vec3(0.004, 0.035, 0.07)
LUZ_AMBIENTE = glm.vec3(0.25, 0.35, 0.45)

# Materiais (ka, kd, ks, alfa), em luz linear. kd multiplica a textura.
MATERIAIS = {
    "pedra": Material("pedra", (0.35,) * 3, (0.9, 0.9, 0.9), (0.04,) * 3, 8.0),
    "areia": Material("areia", (0.4,) * 3, (1.0, 1.0, 1.0), (0.02,) * 3, 4.0),
    "orca": Material("orca", (0.3,) * 3, (1.0, 1.0, 1.0), (0.6,) * 3, 64.0),
    "peixe": Material("peixe", (0.4,) * 3, (1.0, 1.0, 1.0), (0.9, 0.8, 0.5), 96.0),
    "agua_viva": Material("agua-viva", (0.3,) * 3, (0.7, 0.25, 0.6),
                          (0.9,) * 3, 128.0),
    "portal": Material("portal", (0.2,) * 3, (0.5, 0.5, 0.55), (1.0,) * 3, 200.0),
}
COR_TENTACULOS = glm.vec3(0.8, 0.3, 0.7)

FORMATO = '3f 3f 2f'
ATRIBUTOS = ('vPosition', 'vNormal', 'vTexCoord')


def matriz_normal(modelo):
    """Inversa transposta do bloco 3x3 da matriz de modelo: leva as
    normais corretamente mesmo com escala nao uniforme."""
    return glm.transpose(glm.inverse(glm.mat3(modelo)))


def enviar(prog, **uniformes):
    """Envia so os uniformes que o programa declara."""
    for nome, valor in uniformes.items():
        if nome not in prog:
            continue
        if isinstance(valor, (glm.mat3, glm.mat4)):
            prog[nome].write(valor.to_bytes())
        elif isinstance(valor, (glm.vec2, glm.vec3, glm.vec4)):
            prog[nome].value = tuple(valor)
        else:
            prog[nome].value = valor


def carregar_programa(ctx, nome):
    pasta = AQUI / "shaders"
    return ctx.program(
        vertex_shader=(pasta / f"{nome}.vert").read_text(encoding="utf-8"),
        fragment_shader=(pasta / f"{nome}.frag").read_text(encoding="utf-8"))


class Geometria:
    """Um VAO com VBO e EBO, criados uma vez."""

    def __init__(self, ctx, prog, dados, indices, formato=FORMATO):
        self.vbo = ctx.buffer(dados.tobytes())
        self.ebo = ctx.buffer(indices.tobytes())
        self.vao = ctx.vertex_array(prog, [(self.vbo, formato, *ATRIBUTOS)],
                                    index_buffer=self.ebo)

    def desenhar(self):
        self.vao.render(moderngl.TRIANGLES)

    def liberar(self):
        for r in (self.vao, self.vbo, self.ebo):
            r.release()


class Cena:
    def __init__(self, ctx):
        self.ctx = ctx
        ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        ctx.front_face = 'ccw'
        ctx.cull_face = 'back'

        self.prog = carregar_programa(ctx, "cena")
        self.prog_tentaculos = carregar_programa(ctx, "tentaculos")
        self.prog_hud = carregar_programa(ctx, "hud")
        enviar(self.prog, u_textura=0)

        # --- geometrias ---
        p = self.prog
        self.malha_orca = Malha(ARQUIVO_ORCA)
        print(self.malha_orca.resumo())
        # Mapeamento cilindrico em torno do comprimento (y do arquivo),
        # com a costura (na barriga) corrigida. 12 floats por vertice;
        # a tangente (ultimos 16 bytes) nao e usada.
        dados, indices = self.malha_orca.texturada("cilindrico", "y")
        self.geo = {
            "orca": Geometria(ctx, p, dados, indices, '3f 3f 2f 16x'),
            "cubo": Geometria(ctx, p, *geometria.cubo()),
            "plano": Geometria(ctx, p, *geometria.plano()),
            "esfera": Geometria(ctx, p, *geometria.esfera()),
            "cone": Geometria(ctx, p, *geometria.cone()),
            "toro": Geometria(ctx, p, *geometria.toro()),
        }
        tent = geometria.tentaculos()
        self.vbo_tentaculos = ctx.buffer(tent.tobytes())
        self.vao_tentaculos = ctx.vertex_array(
            self.prog_tentaculos,
            [(self.vbo_tentaculos, '3f 1f', 'vPosition', 'vS')])

        # --- texturas: cor, em sRGB, com mipmaps e filtro trilinear ---
        self.tex = {
            nome: tx.carregar(ctx, img, srgb=True)
            for nome, img in (("pedra", tp.pedra()), ("areia", tp.areia()),
                              ("orca", tp.orca()), ("escamas", tp.escamas()),
                              ("branca", tp.branca()))
        }

        self.hud = Hud(ctx, self.prog_hud)

        # --- jogo ---
        self.lab = Labirinto()
        self.orca = Orca(self.lab, self.malha_orca.matriz_enquadramento())
        self.aguas_vivas = [AguaViva(self.lab, cel, d, 1.7 * k)
                            for k, (cel, d) in enumerate(self.lab.aguas_vivas)]
        self.peixes = [Peixe(self.lab, cel, 0.9 * k)
                       for k, cel in enumerate(self.lab.peixes)]
        self.saida = Saida(self.lab)
        self.camera = CameraJogo(self.lab)
        self.luz_dir = LuzDirecional()
        self.lanterna = LuzConica()
        self.luz_saida = LuzPontual()
        self.luz_saida.pos = self.saida.pos
        self.tempo = 0.0
        self.paredes = [self._matriz_parede(c) for c in self.lab.paredes]
        self.reiniciar()

    def _matriz_parede(self, celula):
        """Cubo unitario levado a celula: escala nao uniforme
        (CELULA x ALTURA_PAREDE x CELULA)."""
        col, lin = celula
        centro = glm.vec3((col + 0.5) * CELULA, ALTURA_PAREDE / 2,
                          (lin + 0.5) * CELULA)
        return glm.scale(glm.translate(glm.mat4(1.0), centro),
                         glm.vec3(CELULA, ALTURA_PAREDE, CELULA))

    # --- estado da partida ---

    def reiniciar(self):
        self.pontos = 0
        self.vidas = VIDAS
        self.tempo = 0.0
        self.orca.reiniciar()
        for e in self.aguas_vivas + self.peixes:
            e.reiniciar()
        self.saida.reiniciar()
        self.camera.zerar()
        self.camera.atualizar(0.0, self.orca)

    @property
    def peixes_coletados(self):
        return sum(not p.vivo for p in self.peixes)

    def atualizar(self, dt, avancar, girar, turbo):
        """Um passo da simulacao. Devolve "derrota", "vitoria" ou None."""
        self.tempo += dt
        self.orca.atualizar(dt, avancar, girar, turbo)
        for e in self.aguas_vivas + self.peixes:
            e.atualizar(dt)
        self.saida.atualizar(dt)

        for peixe in self.peixes:
            if peixe.vivo and colisao.esferas(self.orca.pos, Orca.RAIO,
                                              peixe.pos, Peixe.RAIO):
                peixe.vivo = False
                self.pontos += PONTOS_PEIXE

        for agua in self.aguas_vivas:
            if colisao.esferas(self.orca.pos, Orca.RAIO,
                               agua.centro, AguaViva.RAIO):
                if self.orca.bater(agua.centro):
                    self.vidas -= 1
                    agua.direcao = -agua.direcao
                    if self.vidas <= 0:
                        return "derrota"

        self.saida.aberta = self.peixes_coletados == len(self.peixes)
        if self.saida.aberta and colisao.esferas(
                self.orca.pos, Orca.RAIO, self.saida.pos, Saida.RAIO):
            self.pontos += self.vidas * PONTOS_VIDA_RESTANTE
            return "vitoria"
        return None

    # --- desenho ---

    def redimensionar(self, largura, altura):
        largura, altura = max(1, largura), max(1, altura)
        self.ctx.viewport = (0, 0, largura, altura)
        self.camera.aspecto = largura / altura
        self.hud.redimensionar(largura, altura)

    def _objeto(self, geo, modelo, material, textura, uv_escala=(1.0, 1.0),
                emissao=(0.0, 0.0, 0.0), opacidade=1.0):
        m = MATERIAIS[material]
        enviar(self.prog, u_modelo=modelo, u_normal=matriz_normal(modelo),
               u_ka=m.ka, u_kd=m.kd, u_ks=m.ks, u_alfa=m.alfa,
               u_emissao=emissao, u_opacidade=opacidade, u_uv_escala=uv_escala)
        self.tex[textura].use(0)
        self.geo[geo].desenhar()

    def desenhar(self, sobreposicao, tempo_real):
        ctx = self.ctx
        # A limpeza e a cena saem em luz linear; o OpenGL codifica em
        # sRGB ao escrever no framebuffer.
        ctx.enable_direct(GL_FRAMEBUFFER_SRGB)
        ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        ctx.clear(*AGUA, depth=1.0)

        cam = self.camera
        visao, projecao = cam.visao(), cam.projecao()
        pos_lanterna, dir_lanterna = self.orca.lanterna()
        self.lanterna.pos, self.lanterna.direcao = pos_lanterna, dir_lanterna
        brilho = self.saida.brilho
        cor_saida = LuzPontual.ABERTA if self.saida.aberta else LuzPontual.FECHADA
        self.luz_saida.cor = cor_saida * brilho

        ld, lc, lp = self.luz_dir, self.lanterna, self.luz_saida
        enviar(self.prog, u_visao=visao, u_projecao=projecao, u_olho=cam.olho,
               u_luz_ambiente=LUZ_AMBIENTE, u_tempo=self.tempo,
               u_dir_ligada=ld.ligada, u_dir_direcao=ld.direcao, u_dir_cor=ld.cor,
               u_cone_ligada=lc.ligada, u_cone_pos=lc.pos, u_cone_dir=lc.direcao,
               u_cone_cor=lc.cor, u_cone_cos_int=lc.cos_interno,
               u_cone_cos_ext=lc.cos_externo, u_cone_aten=lc.atenuacao,
               u_pont_ligada=lp.ligada, u_pont_pos=lp.pos, u_pont_cor=lp.cor,
               u_pont_aten=lp.atenuacao,
               u_neblina_cor=AGUA, u_neblina_dens=cam.neblina)

        # chao: o plano unitario esticado sobre o labirinto, com a
        # textura repetida uma vez por celula (coordenadas > 1)
        lab = self.lab
        chao = glm.scale(glm.mat4(1.0), glm.vec3(lab.largura, 1.0, lab.profundidade))
        self._objeto("plano", chao, "areia", "areia",
                     (float(lab.colunas), float(lab.linhas)))
        for m in self.paredes:
            self._objeto("cubo", m, "pedra", "pedra", (2.0, 1.3))

        for peixe in self.peixes:
            if peixe.vivo:
                corpo, cauda = peixe.matrizes()
                self._objeto("esfera", corpo, "peixe", "escamas", (2.0, 1.0))
                self._objeto("cone", cauda, "peixe", "escamas")

        if self.orca.visivel:
            self._objeto("orca", self.orca.matriz(), "orca", "orca")

        emissao = (cor_saida * (0.25 * brilho))
        self._objeto("toro", self.saida.matriz(), "portal", "branca",
                     emissao=tuple(emissao))

        # Transparentes por ultimo, com mistura.
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        pt = self.prog_tentaculos
        enviar(pt, u_visao=visao, u_projecao=projecao, u_olho=cam.olho,
               u_cor=COR_TENTACULOS, u_neblina_cor=AGUA,
               u_neblina_dens=cam.neblina)
        for agua in self.aguas_vivas:
            enviar(pt, u_modelo=agua.matriz_tentaculos(), u_tempo=agua.tempo,
                   u_fase=agua.fase)
            self.vao_tentaculos.render(moderngl.LINES)
        for agua in self.aguas_vivas:
            self._objeto("esfera", agua.matriz_sino(), "agua_viva", "branca",
                         emissao=(0.12, 0.02, 0.1), opacidade=0.75)
        ctx.disable(moderngl.BLEND)

        # Segunda passada: o placar, em cores de tela.
        ctx.disable_direct(GL_FRAMEBUFFER_SRGB)
        piscar = 0.5 + 0.5 * glm.sin(tempo_real * 4.0)
        self.hud.desenhar(self.pontos, self.vidas, VIDAS,
                          self.peixes_coletados, len(self.peixes),
                          sobreposicao, piscar)

    def liberar(self):
        for g in self.geo.values():
            g.liberar()
        for t in self.tex.values():
            t.release()
        self.vao_tentaculos.release()
        self.vbo_tentaculos.release()
        self.hud.liberar()
        for p in (self.prog, self.prog_tentaculos, self.prog_hud):
            p.release()

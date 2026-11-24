from enum import Enum, auto
from pathlib import Path

import glm
import moderngl

from . import materials
from . import procedural_textures
from .camera import Camera
from .drawable_mesh import DrawableMesh
from .exit_ring import ExitRing
from .fish import Fish
from .hud import Hud, Overlay
from .jellyfish import Jellyfish
from .lighting_pass import LightingPass
from .lights import DirectionalLight, PointLight, SpotLight
from .maze import CELL_SIZE, WALL_HEIGHT, Maze
from .mesh import Mesh
from .off_model import OffModel
from .orca import Orca, SwimInput
from .tentacles import Tentacles
from .textures import upload_color_texture

ORCA_MODEL_PATH = Path(__file__).parent / "models" / "orca.off"
# moderngl has no name for this OpenGL state.
GL_FRAMEBUFFER_SRGB = 0x8DB9

MAX_LIVES = 3
POINTS_PER_FISH = 100
POINTS_PER_REMAINING_LIFE = 500
JELLYFISH_PHASE_STEP_RADIANS = 1.7
FISH_PHASE_STEP_RADIANS = 0.9
HUD_PULSES_RADIANS_PER_SECOND = 4.0

# The clear color and the fog color are the same, so whatever fades into the
# fog blends with the background.
WATER_COLOR = glm.vec3(0.004, 0.035, 0.07)
AMBIENT_LIGHT_COLOR = glm.vec3(0.25, 0.35, 0.45)
WALL_TEXTURE_REPEATS = (2.0, 1.3)
FISH_BODY_TEXTURE_REPEATS = (2.0, 1.0)
JELLYFISH_EMISSION = (0.12, 0.02, 0.1)
JELLYFISH_OPACITY = 0.75
EXIT_RING_EMISSION_FRACTION = 0.25


class RoundOutcome(Enum):
    DEFEAT = auto()
    VICTORY = auto()


class Scene:
    """Everything in the game world: creates the GPU resources once, advances
    the simulation and draws each frame."""

    def __init__(self, context: moderngl.Context) -> None:
        self._context = context
        self._lighting_pass = LightingPass(context)
        self._tentacles = Tentacles(context)
        self._hud = Hud(context)
        orca_model = OffModel(ORCA_MODEL_PATH)
        print(orca_model.summary())
        self._drawables = self._create_drawables(orca_model)
        self._textures = self._create_textures()

        self.maze = Maze()
        self.orca = Orca(self.maze, orca_model.fit_matrix())
        self._jellyfishes = self._create_jellyfishes()
        self._fishes = self._create_fishes()
        self._exit_ring = ExitRing(self.maze)
        self.camera = Camera(self.maze)
        self.directional_light = DirectionalLight()
        self.spot_light = SpotLight()
        self.point_light = PointLight(position=self._exit_ring.position)
        self._wall_matrices = [self._wall_matrix(cell) for cell in self.maze.walls]
        self.reset()

    @classmethod
    def build(cls, context: moderngl.Context) -> "Scene":
        context.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        context.front_face = "ccw"
        context.cull_face = "back"
        return cls(context)

    def reset(self) -> None:
        self.score_points = 0
        self.lives = MAX_LIVES
        self._elapsed_seconds = 0.0
        self.orca.reset()
        for element in self._moving_elements:
            element.reset()
        self.camera.reset()
        self.camera.update(0.0, self.orca)

    @property
    def collected_fish(self) -> int:
        return sum(fish.is_collected for fish in self._fishes)

    def update(
        self, elapsed_seconds: float, swim_input: SwimInput
    ) -> RoundOutcome | None:
        """Advances the game by `elapsed_seconds` and tells whether the round
        just ended."""
        self._elapsed_seconds += elapsed_seconds
        self.orca.update(elapsed_seconds, swim_input)
        for element in self._moving_elements:
            element.update(elapsed_seconds)

        self._collect_touched_fish()
        if self._hit_by_jellyfish() and self.lives <= 0:
            return RoundOutcome.DEFEAT
        if self._reached_open_exit():
            self.score_points += self.lives * POINTS_PER_REMAINING_LIFE
            return RoundOutcome.VICTORY
        return None

    def resize(self, width_pixels: int, height_pixels: int) -> None:
        width_pixels, height_pixels = max(1, width_pixels), max(1, height_pixels)
        self._context.viewport = (0, 0, width_pixels, height_pixels)
        self.camera.aspect_ratio = width_pixels / height_pixels
        self._hud.resize(width_pixels, height_pixels)

    def render(self, overlay: Overlay | None, elapsed_time_seconds: float) -> None:
        self._begin_frame()
        self._draw_maze()
        self._draw_fishes()
        self._draw_orca()
        self._draw_exit_ring()
        self._draw_jellyfishes()
        self._draw_hud(overlay, elapsed_time_seconds)

    def release(self) -> None:
        for drawable in self._drawables.values():
            drawable.release()
        for texture in self._textures.values():
            texture.release()
        self._lighting_pass.release()
        self._tentacles.release()
        self._hud.release()

    @property
    def _moving_elements(self) -> list:
        return [*self._jellyfishes, *self._fishes, self._exit_ring]

    def _create_drawables(self, orca_model: OffModel) -> dict[str, DrawableMesh]:
        shader_program = self._lighting_pass.shader_program
        meshes = {
            "orca": orca_model.cylindrical_mesh(),
            "cube": Mesh.cube(),
            "plane": Mesh.plane(),
            "sphere": Mesh.sphere(),
            "cone": Mesh.cone(),
            "torus": Mesh.torus(),
        }
        return {
            name: DrawableMesh(self._context, mesh, shader_program)
            for name, mesh in meshes.items()
        }

    def _create_textures(self) -> dict[str, moderngl.Texture]:
        images = {
            "stone": procedural_textures.stone_blocks_image(),
            "sand": procedural_textures.sand_image(),
            "orca": procedural_textures.orca_skin_image(),
            "scales": procedural_textures.fish_scales_image(),
            "white": procedural_textures.white_image(),
        }
        return {
            name: upload_color_texture(self._context, image)
            for name, image in images.items()
        }

    def _create_jellyfishes(self) -> list[Jellyfish]:
        return [
            Jellyfish(self.maze, cell, direction, index * JELLYFISH_PHASE_STEP_RADIANS)
            for index, (cell, direction) in enumerate(self.maze.jellyfish_spawns)
        ]

    def _create_fishes(self) -> list[Fish]:
        return [
            Fish(self.maze, cell, index * FISH_PHASE_STEP_RADIANS)
            for index, cell in enumerate(self.maze.fish_cells)
        ]

    @staticmethod
    def _wall_matrix(cell: tuple[int, int]) -> glm.mat4:
        """The unit cube stretched over a wall cell: a non uniform scale."""
        column, row = cell
        center = glm.vec3(
            (column + 0.5) * CELL_SIZE, WALL_HEIGHT / 2, (row + 0.5) * CELL_SIZE
        )
        return glm.scale(
            glm.translate(glm.mat4(1.0), center),
            glm.vec3(CELL_SIZE, WALL_HEIGHT, CELL_SIZE),
        )

    def _collect_touched_fish(self) -> None:
        for fish in self._fishes:
            if fish.is_collected or not self.orca.body.overlaps(fish.collision_sphere):
                continue
            fish.is_collected = True
            self.score_points += POINTS_PER_FISH

    def _hit_by_jellyfish(self) -> bool:
        for jellyfish in self._jellyfishes:
            if not self.orca.body.overlaps(jellyfish.collision_sphere):
                continue
            if self.orca.take_hit(jellyfish.center):
                self.lives -= 1
                jellyfish.turn_back()
                return True
        return False

    def _reached_open_exit(self) -> bool:
        self._exit_ring.is_open = self.collected_fish == len(self._fishes)
        return self._exit_ring.is_open and self.orca.body.overlaps(
            self._exit_ring.collision_sphere
        )

    def _begin_frame(self) -> None:
        """Clears and lights in linear light; OpenGL encodes to sRGB when
        writing to the framebuffer."""
        self._context.enable_direct(GL_FRAMEBUFFER_SRGB)
        self._context.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        self._context.clear(*WATER_COLOR, depth=1.0)

        self.spot_light.position, self.spot_light.direction = self.orca.headlight_pose()
        exit_color = (
            PointLight.OPEN_COLOR
            if self._exit_ring.is_open
            else PointLight.CLOSED_COLOR
        )
        self.point_light.color = exit_color * self._exit_ring.glow
        self._lighting_pass.begin_frame(
            self.camera,
            (self.directional_light, self.spot_light, self.point_light),
            AMBIENT_LIGHT_COLOR,
            WATER_COLOR,
            self._elapsed_seconds,
        )

    def _draw_maze(self) -> None:
        floor_matrix = glm.scale(
            glm.mat4(1.0), glm.vec3(self.maze.width, 1.0, self.maze.depth)
        )
        one_tile_per_cell = (float(self.maze.column_count), float(self.maze.row_count))
        self._lighting_pass.draw(
            self._drawables["plane"],
            floor_matrix,
            materials.SAND,
            self._textures["sand"],
            one_tile_per_cell,
        )
        for wall_matrix in self._wall_matrices:
            self._lighting_pass.draw(
                self._drawables["cube"],
                wall_matrix,
                materials.STONE,
                self._textures["stone"],
                WALL_TEXTURE_REPEATS,
            )

    def _draw_fishes(self) -> None:
        for fish in self._fishes:
            if fish.is_collected:
                continue
            body_matrix, tail_matrix = fish.body_and_tail_matrices()
            self._lighting_pass.draw(
                self._drawables["sphere"],
                body_matrix,
                materials.FISH_SCALES,
                self._textures["scales"],
                FISH_BODY_TEXTURE_REPEATS,
            )
            self._lighting_pass.draw(
                self._drawables["cone"],
                tail_matrix,
                materials.FISH_SCALES,
                self._textures["scales"],
            )

    def _draw_orca(self) -> None:
        if not self.orca.is_visible:
            return
        self._lighting_pass.draw(
            self._drawables["orca"],
            self.orca.model_matrix(),
            materials.ORCA_SKIN,
            self._textures["orca"],
        )

    def _draw_exit_ring(self) -> None:
        emission = self.point_light.color * EXIT_RING_EMISSION_FRACTION
        self._lighting_pass.draw(
            self._drawables["torus"],
            self._exit_ring.model_matrix(),
            materials.EXIT_RING,
            self._textures["white"],
            emission_color=tuple(emission),
        )

    def _draw_jellyfishes(self) -> None:
        """Translucent, so drawn after every opaque object."""
        self._context.enable(moderngl.BLEND)
        self._context.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self._tentacles.begin_frame(self.camera, WATER_COLOR)
        for jellyfish in self._jellyfishes:
            self._tentacles.draw(
                jellyfish.tentacles_matrix(),
                jellyfish.elapsed_seconds,
                jellyfish.phase_radians,
            )
        for jellyfish in self._jellyfishes:
            self._lighting_pass.draw(
                self._drawables["sphere"],
                jellyfish.bell_matrix(),
                materials.JELLYFISH_BELL,
                self._textures["white"],
                emission_color=JELLYFISH_EMISSION,
                opacity=JELLYFISH_OPACITY,
            )
        self._context.disable(moderngl.BLEND)

    def _draw_hud(self, overlay: Overlay | None, elapsed_time_seconds: float) -> None:
        """The HUD colors are screen colors, so the sRGB encoding is off."""
        self._context.disable_direct(GL_FRAMEBUFFER_SRGB)
        pulse_radians = elapsed_time_seconds * HUD_PULSES_RADIANS_PER_SECOND
        pulse = 0.5 + 0.5 * glm.sin(pulse_radians)
        self._hud.draw(
            self.score_points,
            self.lives,
            MAX_LIVES,
            self.collected_fish,
            len(self._fishes),
            overlay,
            pulse,
        )

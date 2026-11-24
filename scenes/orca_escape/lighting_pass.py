import glm
import moderngl

from .camera import Camera
from .drawable_mesh import DrawableMesh
from .lights import DirectionalLight, PointLight, SpotLight
from .materials import Material
from .shader_program import ShaderProgram

TEXTURE_UNIT = 0
NO_EMISSION = (0.0, 0.0, 0.0)
NO_REPEAT = (1.0, 1.0)


def normal_matrix(model_matrix: glm.mat4) -> glm.mat3:
    """Inverse transpose of the linear part of the model matrix: keeps the
    normals perpendicular to the surface even under non uniform scale."""
    return glm.transpose(glm.inverse(glm.mat3(model_matrix)))


class LightingPass:
    """Draws lit and textured meshes with the `lit` shader.

    Call `begin_frame` once per frame, then `draw` for each object.
    """

    def __init__(self, context: moderngl.Context) -> None:
        self.shader_program = ShaderProgram.named(context, "lit")
        self.shader_program.set_uniform("surface_texture", TEXTURE_UNIT)

    def begin_frame(
        self,
        camera: Camera,
        lights: tuple[DirectionalLight, SpotLight, PointLight],
        ambient_light_color: glm.vec3,
        fog_color: glm.vec3,
        elapsed_time_seconds: float,
    ) -> None:
        self.shader_program.set_uniforms(
            {
                "view_matrix": camera.view_matrix(),
                "projection_matrix": camera.projection_matrix(),
                "camera_position": camera.position,
                "ambient_light_color": ambient_light_color,
                "fog_color": fog_color,
                "fog_density": camera.fog_density,
                "elapsed_time_seconds": elapsed_time_seconds,
            }
        )
        for light in lights:
            self.shader_program.set_uniforms(light.uniforms())

    def draw(
        self,
        drawable: DrawableMesh,
        model_matrix: glm.mat4,
        material: Material,
        texture: moderngl.Texture,
        texture_repeats: tuple[float, float] = NO_REPEAT,
        emission_color: tuple[float, float, float] = NO_EMISSION,
        opacity: float = 1.0,
    ) -> None:
        """Draws `drawable` placed by `model_matrix`. `texture_repeats` above
        1 tile the texture across the surface."""
        self.shader_program.set_uniforms(
            {
                "model_matrix": model_matrix,
                "normal_matrix": normal_matrix(model_matrix),
                "material_ambient": material.ambient,
                "material_diffuse": material.diffuse,
                "material_specular": material.specular,
                "material_shininess": material.shininess,
                "emission_color": emission_color,
                "opacity": opacity,
                "texture_repeats": texture_repeats,
            }
        )
        texture.use(TEXTURE_UNIT)
        drawable.draw()

    def release(self) -> None:
        self.shader_program.release()

import moderngl
import numpy as np

# moderngl has no name for this OpenGL constant.
GL_SRGB8_ALPHA8 = 0x8C43
MAX_ANISOTROPY_SAMPLES = 8.0


def upload_color_texture(
    context: moderngl.Context, image: np.ndarray
) -> moderngl.Texture:
    """Uploads an RGBA image (height, width, 4), row 0 on top, holding colors
    as seen on screen (sRGB).

    The texture is stored as GL_SRGB8_ALPHA8, so the sampler decodes the
    texels to linear light before the lighting uses them. It repeats outside
    [0, 1] (GL_REPEAT) and has mipmaps with trilinear filtering.
    """
    height, width = image.shape[:2]
    # OpenGL expects the first row sent to be the bottom one (t = 0).
    bottom_row_first = np.ascontiguousarray(image[::-1])
    texture = context.texture(
        (width, height), 4, bottom_row_first.tobytes(), internal_format=GL_SRGB8_ALPHA8
    )
    texture.repeat_x = texture.repeat_y = True
    texture.build_mipmaps()
    texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
    texture.anisotropy = min(MAX_ANISOTROPY_SAMPLES, context.max_anisotropy)
    return texture

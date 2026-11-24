#version 400 core

// Phong shading with the Blinn-Phong model, in world space, lit by a
// directional light, a spot light and a point light. The texture is stored
// as GL_SRGB8_ALPHA8, so it arrives already in linear light; the output is
// linear too and OpenGL encodes it to sRGB once (GL_FRAMEBUFFER_SRGB).

in vec3 world_position;
in vec3 world_normal;
in vec2 texture_coordinates;

uniform sampler2D surface_texture;
uniform vec2 texture_repeats;

uniform vec3 material_ambient;
uniform vec3 material_diffuse;
uniform vec3 material_specular;
uniform float material_shininess;
uniform vec3 emission_color;
uniform float opacity;

uniform vec3 camera_position;
uniform vec3 ambient_light_color;
uniform float elapsed_time_seconds;

uniform bool directional_light_enabled;
uniform vec3 directional_light_direction;
uniform vec3 directional_light_color;

uniform bool spot_light_enabled;
uniform vec3 spot_light_position;
uniform vec3 spot_light_direction;
uniform vec3 spot_light_color;
uniform float spot_light_inner_cone_cosine;
uniform float spot_light_outer_cone_cosine;
uniform vec3 spot_light_attenuation;

uniform bool point_light_enabled;
uniform vec3 point_light_position;
uniform vec3 point_light_color;
uniform vec3 point_light_attenuation;

uniform vec3 fog_color;
uniform float fog_density;

out vec4 fragment_color;

vec3 blinn_phong(vec3 normal, vec3 to_camera, vec3 to_light, vec3 light_color, vec3 diffuse) {
    float diffuse_factor = max(dot(normal, to_light), 0.0);
    float specular_factor = 0.0;
    if (diffuse_factor > 0.0) {
        vec3 halfway = normalize(to_light + to_camera);
        specular_factor = pow(max(dot(normal, halfway), 0.0), material_shininess);
    }
    return light_color * (diffuse * diffuse_factor + material_specular * specular_factor);
}

float attenuation(vec3 coefficients, float distance_to_light) {
    return 1.0 / (coefficients.x
                  + coefficients.y * distance_to_light
                  + coefficients.z * distance_to_light * distance_to_light);
}

// Moving patches of light that the wavy water surface casts on the bottom.
float caustics(vec2 point, float time_seconds) {
    float crossing = sin(point.x * 1.1 + time_seconds * 1.3) * sin(point.y * 0.9 - time_seconds * 1.1);
    float diagonal = sin((point.x + point.y) * 0.6 + time_seconds * 0.7);
    float pattern = 0.5 + 0.5 * (crossing + 0.5 * diagonal) / 1.5;
    return 0.55 + 0.9 * pow(pattern, 3.0);
}

vec3 directional_light(vec3 normal, vec3 to_camera, vec3 diffuse) {
    vec3 color = directional_light_color * caustics(world_position.xz, elapsed_time_seconds);
    return blinn_phong(normal, to_camera, normalize(-directional_light_direction), color, diffuse);
}

vec3 spot_light(vec3 normal, vec3 to_camera, vec3 diffuse) {
    vec3 to_light = spot_light_position - world_position;
    float distance_to_light = length(to_light);
    to_light /= distance_to_light;
    float angle_cosine = dot(-to_light, normalize(spot_light_direction));
    float cone = smoothstep(spot_light_outer_cone_cosine, spot_light_inner_cone_cosine, angle_cosine);
    return cone * attenuation(spot_light_attenuation, distance_to_light)
         * blinn_phong(normal, to_camera, to_light, spot_light_color, diffuse);
}

vec3 point_light(vec3 normal, vec3 to_camera, vec3 diffuse) {
    vec3 to_light = point_light_position - world_position;
    float distance_to_light = length(to_light);
    return attenuation(point_light_attenuation, distance_to_light)
         * blinn_phong(normal, to_camera, to_light / distance_to_light, point_light_color, diffuse);
}

void main() {
    vec3 normal = normalize(world_normal);
    vec3 to_camera = normalize(camera_position - world_position);
    vec3 albedo = texture(surface_texture, texture_coordinates * texture_repeats).rgb;
    vec3 diffuse = material_diffuse * albedo;

    vec3 color = material_ambient * albedo * ambient_light_color + emission_color;
    if (directional_light_enabled) color += directional_light(normal, to_camera, diffuse);
    if (spot_light_enabled) color += spot_light(normal, to_camera, diffuse);
    if (point_light_enabled) color += point_light(normal, to_camera, diffuse);

    float fog_depth = length(camera_position - world_position) * fog_density;
    float visibility = exp(-fog_depth * fog_depth);
    fragment_color = vec4(mix(fog_color, color, visibility), opacity);
}

#version 400 core

in vec3 world_position;

uniform vec3 tentacle_color;
uniform vec3 camera_position;
uniform vec3 fog_color;
uniform float fog_density;

out vec4 fragment_color;

void main() {
    float fog_depth = length(camera_position - world_position) * fog_density;
    vec3 color = mix(fog_color, tentacle_color, exp(-fog_depth * fog_depth));
    fragment_color = vec4(color, 0.8);
}

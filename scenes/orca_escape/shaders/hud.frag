#version 400 core

// Drawn with GL_FRAMEBUFFER_SRGB disabled: shape_color is already the color
// shown on screen.

uniform vec4 shape_color;

out vec4 fragment_color;

void main() {
    fragment_color = shape_color;
}

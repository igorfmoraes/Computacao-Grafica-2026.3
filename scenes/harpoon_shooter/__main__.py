from .window import Window
from .scene import Scene
from .game import Game

WINDOW_WIDTH_PIXELS = 800
WINDOW_HEIGHT_PIXELS = 800
WINDOW_TITLE = "Harpoon Shooter"


def main() -> None:
    window = Window(WINDOW_WIDTH_PIXELS, WINDOW_HEIGHT_PIXELS, WINDOW_TITLE)
    context = window.graphics_context

    scene = Scene.build(context)

    Game(window, scene).run()


if __name__ == "__main__":
    main()

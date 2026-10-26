from .window import Window
from .game import Game

WINDOW_WIDTH_PIXELS = 800
WINDOW_HEIGHT_PIXELS = 450
WINDOW_TITLE = "Harpoon Shooter"


def main() -> None:
    window = Window(WINDOW_WIDTH_PIXELS, WINDOW_HEIGHT_PIXELS, WINDOW_TITLE)
    context = window.graphics_context

    Game(window).run()


if __name__ == "__main__":
    main()

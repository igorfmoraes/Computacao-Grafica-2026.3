import sys
from .window import Window, WindowCreationError
from .keyboard_controls import KeyboardControls
from .scene import Scene
from .game import Game

WINDOW_WIDTH_PIXELS = 800
WINDOW_HEIGHT_PIXELS = 800
WINDOW_TITLE = "Harpoon Shooter"


def main() -> None:
    try:
        window = Window(WINDOW_WIDTH_PIXELS, WINDOW_HEIGHT_PIXELS, WINDOW_TITLE)
    except WindowCreationError as error:
        sys.exit(str(error))

    context = window.graphics_context
    scene = Scene.build(context)
    keyboard_controls = KeyboardControls(window)
    window.add_key_press_listener(keyboard_controls.handle_key_press)
    print(KeyboardControls.HELP_TEXT)

    Game(window, scene).run()


if __name__ == "__main__":
    main()

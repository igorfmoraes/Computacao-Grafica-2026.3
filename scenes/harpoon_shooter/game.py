"""Game loop and state machine.

READY -> RUNNING <-> PAUSED
RUNNING -> GAME_OVER -> RUNNING (restart with ENTER)
"""

from enum import Enum, auto

import glfw

from .hud import Overlay
from .keyboard_controls import KeyboardControls
from .scene import Scene
from .window import Window

BASE_TITLE = "Harpoon Shooter"
MAX_DELTA_TIME_SECONDS = 1.0 / 20.0
FPS_REFRESH_INTERVAL_SECONDS = 0.5


class GameState(Enum):
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


STATE_LABELS = {
    GameState.READY: "INICIO",
    GameState.RUNNING: "JOGANDO",
    GameState.PAUSED: "PAUSADO",
    GameState.GAME_OVER: "FIM DE JOGO",
}

OVERLAY_BY_STATE = {
    GameState.READY: Overlay.START,
    GameState.PAUSED: Overlay.PAUSED,
    GameState.GAME_OVER: Overlay.GAME_OVER,
}


class Game:
    def __init__(self, window: Window, scene: Scene) -> None:
        self._window = window
        self._scene = scene
        self._state = GameState.READY
        self._vsync_enabled = True
        self._frames_since_refresh = 0
        self._refresh_started_at = window.elapsed_time_seconds
        self._fps = 0.0
        self._controls = KeyboardControls(
            window,
            scene.player,
            {
                glfw.KEY_ESCAPE: window.request_close,
                glfw.KEY_ENTER: self._start_or_restart,
                glfw.KEY_KP_ENTER: self._start_or_restart,
                glfw.KEY_P: self._toggle_pause,
                glfw.KEY_V: self._toggle_vsync,
                glfw.KEY_SPACE: self._fire_harpoon,
            },
        )
        self._update_title()

    def run(self) -> None:
        previous_time = self._window.elapsed_time_seconds
        while not self._window.should_close():
            current_time = self._window.elapsed_time_seconds
            delta_time = min(current_time - previous_time, MAX_DELTA_TIME_SECONDS)
            previous_time = current_time

            # While paused, previous_time still advances every frame,
            # so the paused interval never reaches delta_time.
            if self._state is GameState.RUNNING:
                self._controls.update(delta_time)
                self._scene.update(delta_time)
                if self._scene.is_game_over:
                    self._set_state(GameState.GAME_OVER)

            self._scene.render(current_time, OVERLAY_BY_STATE.get(self._state))
            self._window.swap_buffers()
            self._window.poll_events()
            self._update_fps(current_time)

    def _set_state(self, state: GameState) -> None:
        self._state = state
        self._update_title()

    def _start_or_restart(self) -> None:
        if self._state in (GameState.READY, GameState.GAME_OVER):
            self._scene.reset()
            self._set_state(GameState.RUNNING)

    def _toggle_pause(self) -> None:
        if self._state is GameState.RUNNING:
            self._set_state(GameState.PAUSED)
        elif self._state is GameState.PAUSED:
            self._set_state(GameState.RUNNING)

    def _fire_harpoon(self) -> None:
        if self._state is GameState.RUNNING:
            self._scene.fire_harpoon()

    def _toggle_vsync(self) -> None:
        self._vsync_enabled = not self._vsync_enabled
        self._window.set_vsync(self._vsync_enabled)
        self._update_title()

    def _update_fps(self, now: float) -> None:
        self._frames_since_refresh += 1
        elapsed = now - self._refresh_started_at
        if elapsed >= FPS_REFRESH_INTERVAL_SECONDS:
            self._fps = self._frames_since_refresh / elapsed
            self._frames_since_refresh = 0
            self._refresh_started_at = now
            self._update_title()

    def _update_title(self) -> None:
        vsync = "ON" if self._vsync_enabled else "OFF"
        self._window.set_title(
            f"{BASE_TITLE} | {STATE_LABELS[self._state]} | FPS: {self._fps:.0f} | VSync: {vsync}"
        )

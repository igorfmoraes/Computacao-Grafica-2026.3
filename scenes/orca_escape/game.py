"""Game loop and state machine.

START -> RUNNING <-> PAUSED
RUNNING -> DEFEAT | VICTORY -> RUNNING (new round with ENTER)
R goes back to START from any state.
"""

from enum import Enum, auto

import glfw

from .hud import Overlay
from .keyboard_controls import KeyboardControls
from .mouse_controls import MouseControls
from .scene import RoundOutcome, Scene
from .window import Window

BASE_TITLE = "Orca Escape"
MAX_DELTA_TIME_SECONDS = 1.0 / 20.0
FPS_REFRESH_INTERVAL_SECONDS = 0.5


class GameState(Enum):
    START = auto()
    RUNNING = auto()
    PAUSED = auto()
    DEFEAT = auto()
    VICTORY = auto()


STATE_LABELS = {
    GameState.START: "INICIO (ENTER)",
    GameState.RUNNING: "JOGANDO",
    GameState.PAUSED: "PAUSADO",
    GameState.DEFEAT: "DERROTA (ENTER)",
    GameState.VICTORY: "VITORIA (ENTER)",
}

OVERLAY_BY_STATE = {
    GameState.START: Overlay.START,
    GameState.PAUSED: Overlay.PAUSED,
    GameState.DEFEAT: Overlay.DEFEAT,
    GameState.VICTORY: Overlay.VICTORY,
}

STATE_BY_OUTCOME = {
    RoundOutcome.DEFEAT: GameState.DEFEAT,
    RoundOutcome.VICTORY: GameState.VICTORY,
}


class Game:
    def __init__(self, window: Window, scene: Scene) -> None:
        self._window = window
        self._scene = scene
        self._state = GameState.START
        self._vsync_enabled = True
        self._frames_since_refresh = 0
        self._refresh_started_at = window.elapsed_time_seconds
        self._fps = 0.0
        self._keyboard_controls = KeyboardControls(window, self._key_actions())
        self._mouse_controls = MouseControls(
            scene.camera, lambda: self._state is not GameState.PAUSED
        )
        self._register_listeners()
        scene.resize(*window.framebuffer_size_pixels)
        self._update_title()

    def run(self) -> None:
        previous_time = self._window.elapsed_time_seconds
        while not self._window.should_close():
            current_time = self._window.elapsed_time_seconds
            delta_time = min(current_time - previous_time, MAX_DELTA_TIME_SECONDS)
            # previous_time advances even while paused, so the paused
            # interval never reaches delta_time.
            previous_time = current_time

            if self._state is GameState.RUNNING:
                self._advance(delta_time)
            camera_delta_time = 0.0 if self._state is GameState.PAUSED else delta_time
            self._scene.camera.update(camera_delta_time, self._scene.orca)

            self._scene.render(OVERLAY_BY_STATE.get(self._state), current_time)
            self._window.swap_buffers()
            self._window.poll_events()
            self._update_fps(current_time)

    def _advance(self, delta_time: float) -> None:
        swim_input = self._keyboard_controls.read_swim_input()
        outcome = self._scene.update(delta_time, swim_input)
        if outcome is not None:
            self._set_state(STATE_BY_OUTCOME[outcome])

    def _key_actions(self) -> dict:
        return {
            glfw.KEY_ESCAPE: self._window.request_close,
            glfw.KEY_ENTER: self._start_round,
            glfw.KEY_KP_ENTER: self._start_round,
            glfw.KEY_P: self._toggle_pause,
            glfw.KEY_R: self._restart,
            glfw.KEY_V: self._toggle_vsync,
            glfw.KEY_C: self._toggle_camera_mode,
            glfw.KEY_O: self._toggle_projection,
            glfw.KEY_L: lambda: self._toggle_light(self._scene.directional_light),
            glfw.KEY_F: lambda: self._toggle_light(self._scene.spot_light),
            glfw.KEY_K: lambda: self._toggle_light(self._scene.point_light),
            glfw.KEY_Z: self._scene.camera.reset,
        }

    def _register_listeners(self) -> None:
        self._window.add_key_press_listener(self._keyboard_controls.handle_key_press)
        self._window.add_drag_listener(self._mouse_controls.handle_drag)
        self._window.add_scroll_listener(self._mouse_controls.handle_scroll)
        self._window.add_resize_listener(self._scene.resize)

    def _set_state(self, state: GameState) -> None:
        self._state = state
        self._update_title()

    def _start_round(self) -> None:
        if self._state in (GameState.DEFEAT, GameState.VICTORY):
            self._scene.reset()
        if self._state in (GameState.START, GameState.DEFEAT, GameState.VICTORY):
            self._set_state(GameState.RUNNING)

    def _restart(self) -> None:
        self._scene.reset()
        self._set_state(GameState.START)

    def _toggle_pause(self) -> None:
        if self._state is GameState.RUNNING:
            self._set_state(GameState.PAUSED)
        elif self._state is GameState.PAUSED:
            self._set_state(GameState.RUNNING)

    def _toggle_vsync(self) -> None:
        self._vsync_enabled = not self._vsync_enabled
        self._window.set_vsync(self._vsync_enabled)
        self._update_title()

    def _toggle_camera_mode(self) -> None:
        self._scene.camera.toggle_mode()
        self._update_title()

    def _toggle_projection(self) -> None:
        self._scene.camera.toggle_projection()
        self._update_title()

    def _toggle_light(self, light) -> None:
        light.is_enabled = not light.is_enabled
        self._update_title()

    def _update_fps(self, now_seconds: float) -> None:
        self._frames_since_refresh += 1
        elapsed_seconds = now_seconds - self._refresh_started_at
        if elapsed_seconds < FPS_REFRESH_INTERVAL_SECONDS:
            return
        self._fps = self._frames_since_refresh / elapsed_seconds
        self._frames_since_refresh = 0
        self._refresh_started_at = now_seconds
        self._update_title()

    def _update_title(self) -> None:
        scene = self._scene
        camera = scene.camera
        projection = "persp" if camera.is_perspective else "orto"
        self._window.set_title(
            f"{BASE_TITLE} | {STATE_LABELS[self._state]} | FPS: {self._fps:.0f} | "
            f"VSync: {_on_off(self._vsync_enabled)} | "
            f"Camera: {camera.mode.value} ({projection}) | "
            f"Luz dir: {_on_off(scene.directional_light.is_enabled)} | "
            f"Lanterna: {_on_off(scene.spot_light.is_enabled)} | "
            f"Saida: {_on_off(scene.point_light.is_enabled)}"
        )


def _on_off(is_enabled: bool) -> str:
    return "ON" if is_enabled else "OFF"

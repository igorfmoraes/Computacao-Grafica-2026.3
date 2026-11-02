import moderngl
import numpy as np


class Background:
    def __init__(self, context: moderngl.Context) -> None:
        self._context = context

    def clear(self, elapsed_time_seconds: float) -> None:
        self._context.clear(0.0, 0.9, 1.0, 1.0)

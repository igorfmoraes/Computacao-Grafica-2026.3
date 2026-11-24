import math

import glm

from .collision import Box, Sphere

CELL_SIZE = 4.0
WALL_HEIGHT = 2.6
# Below one radius per substep, a sphere never jumps over a wall at least
# one radius thick, however fast it moves.
SUBSTEP_FRACTION_OF_RADIUS = 0.5

WALL = "#"
START = "S"
EXIT = "E"
FISH = "o"
JELLYFISH_ALONG_X = "H"
JELLYFISH_ALONG_Z = "V"

LAYOUT = [
    "###############",
    "#S..#.....#..o#",
    "#.#.#.###.#.#.#",
    "#.#...#o..#.#.#",
    "#.#####.###.#.#",
    "#o..H.#...#...#",
    "###.#.###.###.#",
    "#...#...#.....#",
    "#.#####.#.###.#",
    "#.#o..#...#o#.#",
    "#.#.#.#####.#.#",
    "#..V#...o...#.#",
    "#.###.#####.#.#",
    "#o....#..H...E#",
    "###############",
]


class Maze:
    """Grid of cells read from a text layout, where each character is a cell:
    `#` wall, `.` open water, `S` orca start, `E` exit, `o` fish and `H`/`V`
    a jellyfish swimming along x/z."""

    def __init__(self, layout: list[str] = LAYOUT) -> None:
        self.row_count = len(layout)
        self.column_count = len(layout[0])
        self.walls: dict[tuple[int, int], Box] = {}
        self.fish_cells: list[tuple[int, int]] = []
        self.jellyfish_spawns: list[tuple[tuple[int, int], glm.vec3]] = []
        self.start_cell = self.exit_cell = None
        for row, line in enumerate(layout):
            self._read_line(row, line)
        if self.start_cell is None or self.exit_cell is None:
            raise ValueError("o mapa precisa de S e de E")

    @property
    def width(self) -> float:
        return self.column_count * CELL_SIZE

    @property
    def depth(self) -> float:
        return self.row_count * CELL_SIZE

    @property
    def center(self) -> glm.vec3:
        return glm.vec3(self.width / 2, 0.0, self.depth / 2)

    def cell_center(self, cell: tuple[int, int], height: float = 0.0) -> glm.vec3:
        column, row = cell
        return glm.vec3((column + 0.5) * CELL_SIZE, height, (row + 0.5) * CELL_SIZE)

    def is_open(self, column: int, row: int) -> bool:
        is_inside = 0 <= column < self.column_count and 0 <= row < self.row_count
        return is_inside and (column, row) not in self.walls

    def move_sphere(self, sphere: Sphere, displacement: glm.vec3) -> bool:
        """Moves `sphere` by `displacement`, in substeps, pushing it out of
        every wall it touches. Returns whether it touched any.

        Since the push only removes the part of the motion into the wall,
        the sphere keeps sliding along it.
        """
        substep_length = SUBSTEP_FRACTION_OF_RADIUS * sphere.radius
        substep_count = max(1, math.ceil(glm.length(displacement) / substep_length))
        substep = displacement / substep_count
        collided = False
        for _ in range(substep_count):
            sphere.center += substep
            collided = self._push_out_of_walls(sphere) or collided
        return collided

    def _push_out_of_walls(self, sphere: Sphere) -> bool:
        collided = False
        for wall in self._walls_near(sphere.center):
            translation = wall.push_out(sphere)
            if translation is None:
                continue
            sphere.center += translation
            collided = True
        return collided

    def _walls_near(self, point: glm.vec3) -> list[Box]:
        """Walls of the 3 x 3 cells around `point`: with radii smaller than a
        cell, no other wall can touch a sphere centered there."""
        column, row = int(point.x // CELL_SIZE), int(point.z // CELL_SIZE)
        neighbors = [
            (column + column_offset, row + row_offset)
            for row_offset in (-1, 0, 1)
            for column_offset in (-1, 0, 1)
        ]
        return [self.walls[cell] for cell in neighbors if cell in self.walls]

    def _read_line(self, row: int, line: str) -> None:
        if len(line) != self.column_count:
            raise ValueError(f"linha {row} do mapa com tamanho errado")
        for column, symbol in enumerate(line):
            self._read_cell((column, row), symbol)

    def _read_cell(self, cell: tuple[int, int], symbol: str) -> None:
        if symbol == WALL:
            self.walls[cell] = self._wall_box(cell)
        elif symbol == START:
            self.start_cell = cell
        elif symbol == EXIT:
            self.exit_cell = cell
        elif symbol == FISH:
            self.fish_cells.append(cell)
        elif symbol == JELLYFISH_ALONG_X:
            self.jellyfish_spawns.append((cell, glm.vec3(1.0, 0.0, 0.0)))
        elif symbol == JELLYFISH_ALONG_Z:
            self.jellyfish_spawns.append((cell, glm.vec3(0.0, 0.0, 1.0)))

    @staticmethod
    def _wall_box(cell: tuple[int, int]) -> Box:
        column, row = cell
        lower_x, lower_z = column * CELL_SIZE, row * CELL_SIZE
        return Box(
            (lower_x, 0.0, lower_z),
            (lower_x + CELL_SIZE, WALL_HEIGHT, lower_z + CELL_SIZE),
        )

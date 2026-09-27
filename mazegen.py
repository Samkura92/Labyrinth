"""mazegen - a small, reusable maze generator.

This single-file module can be imported in any Python project to
generate a maze (either a "perfect" maze with a unique path between
two points, or a "playable" maze with a few loops, similar to a
Pac-Man board).

Quick start
-----------
    from mazegen import MazeGenerator

    generator = MazeGenerator(
        width=20,
        height=15,
        entry=(0, 0),
        exit_=(19, 14),
        perfect=True,
        seed=42,
    )
    generator.generate()

    # Access the raw wall data (one integer bitmask per cell).
    walls = generator.grid  # walls[y][x] -> int

    # Access a solution (list of "N"/"E"/"S"/"W" moves).
    solution = generator.solve()

Wall encoding
-------------
Each cell is encoded as an integer between 0 and 15. Each bit tells
whether a wall is CLOSED (1) or OPEN (0):

    bit 0 (value 1) -> North wall
    bit 1 (value 2) -> East wall
    bit 2 (value 4) -> South wall
    bit 3 (value 8) -> West wall

Custom parameters
------------------
- ``width`` / ``height``: size of the maze, in number of cells.
- ``entry`` / ``exit_``: (x, y) coordinates, inside the maze bounds.
- ``perfect``: True for a maze with a single path (no loop at all),
  False for a maze with a few loops and (almost) no dead end.
- ``seed``: any hashable value used to make the maze reproducible.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Set, Tuple

# --- wall bit values (see module docstring) --------------------------------
NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8

# For a given direction, the opposite direction and the (dx, dy) move.
_OPPOSITE: Dict[int, int] = {
    NORTH: SOUTH, SOUTH: NORTH, EAST: WEST, WEST: EAST,
}
_DELTA: Dict[int, Tuple[int, int]] = {
    NORTH: (0, -1),
    SOUTH: (0, 1),
    EAST: (1, 0),
    WEST: (-1, 0),
}
_LETTER: Dict[int, str] = {NORTH: "N", SOUTH: "S", EAST: "E", WEST: "W"}

Cell = Tuple[int, int]

# --- a small 5x7 "pixel font" used to draw the "42" pattern ----------------
# '#' cells will be fully closed (all 4 walls), forming the shape.
_DIGIT_4 = [
    "#...#",
    "#...#",
    "#...#",
    "#####",
    "....#",
    "....#",
    "....#",
]
_DIGIT_2 = [
    "#####",
    "....#",
    "....#",
    "#####",
    "#....",
    "#....",
    "#####",
]


class MazeError(Exception):
    """Raised when the requested maze cannot be generated."""


class MazeGenerator:
    """Generate a rectangular maze made of cells with N/E/S/W walls.

    Attributes:
        width: Number of cells on the horizontal axis.
        height: Number of cells on the vertical axis.
        entry: (x, y) coordinates of the entry cell.
        exit_: (x, y) coordinates of the exit cell.
        perfect: True for a single-path maze, False for a looped one.
        grid: The generated maze, grid[y][x] is a wall bitmask.
              Populated only after calling generate().
        pattern_cells: Set of (x, y) cells forming the "42" pattern.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: Cell,
        exit_: Cell,
        perfect: bool = True,
        seed: Optional[int] = None,
    ) -> None:
        """Create a maze generator.

        Args:
            width: Maze width in number of cells (must be >= 2).
            height: Maze height in number of cells (must be >= 2).
            entry: Entry coordinates (x, y), inside the maze.
            exit_: Exit coordinates (x, y), inside the maze, different
                from the entry.
            perfect: If True, build a perfect maze (one unique path,
                no loop). If False, build a maze with a few loops and
                almost no dead end (useful for a Pac-Man-like board).
            seed: Optional seed for reproducible generation.

        Raises:
            MazeError: If the given parameters are not usable.
        """
        if width < 2 or height < 2:
            raise MazeError("width and height must be at least 2")
        if not self._inside(entry, width, height):
            raise MazeError(f"entry {entry} is outside the maze")
        if not self._inside(exit_, width, height):
            raise MazeError(f"exit {exit_} is outside the maze")
        if entry == exit_:
            raise MazeError("entry and exit must be different cells")

        self.width = width
        self.height = height
        self.entry = entry
        self.exit_ = exit_
        self.perfect = perfect
        self._rng = random.Random(seed)

        # grid[y][x] -> wall bitmask, all walls closed by default.
        self.grid: List[List[int]] = [
            [NORTH | EAST | SOUTH | WEST for _ in range(width)]
            for _ in range(height)
        ]
        self.pattern_cells: Set[Cell] = set()

    @staticmethod
    def _inside(cell: Cell, width: int, height: int) -> bool:
        """Return True if cell (x, y) is inside a width x height grid."""
        x, y = cell
        return 0 <= x < width and 0 <= y < height

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def generate(self) -> "MazeGenerator":
        """Generate the maze in place and return self (for chaining)."""
        self.pattern_cells = self._place_pattern()
        self._carve_spanning_tree()
        if not self.perfect:
            self._add_loops_and_remove_dead_ends()
        return self

    def solve(self) -> List[str]:
        """Return the shortest path from entry to exit.

        Returns:
            A list of single-letter moves ("N", "E", "S" or "W").

        Raises:
            MazeError: If no path exists (should not happen on a
                maze produced by generate()).
        """
        path_cells = self._shortest_path_cells()
        moves: List[str] = []
        for (x1, y1), (x2, y2) in zip(path_cells, path_cells[1:]):
            dx, dy = x2 - x1, y2 - y1
            for direction, (ddx, ddy) in _DELTA.items():
                if (ddx, ddy) == (dx, dy):
                    moves.append(_LETTER[direction])
                    break
        return moves

    def to_hex_rows(self) -> List[str]:
        """Return the maze as a list of hexadecimal-digit strings.

        One string per row, one hexadecimal digit per cell, following
        the wall encoding described in the module docstring.
        """
        rows: List[str] = []
        for y in range(self.height):
            row = "".join(f"{self.grid[y][x]:X}" for x in range(self.width))
            rows.append(row)
        return rows

    # ------------------------------------------------------------------ #
    # Internal helpers - graph exploration                               #
    # ------------------------------------------------------------------ #
    def _neighbors(self, cell: Cell) -> List[Tuple[int, Cell]]:
        """Return the (direction, neighbor_cell) pairs inside the grid."""
        x, y = cell
        result: List[Tuple[int, Cell]] = []
        for direction, (dx, dy) in _DELTA.items():
            neighbor = (x + dx, y + dy)
            if self._inside(neighbor, self.width, self.height):
                result.append((direction, neighbor))
        return result

    def is_open(self, cell: Cell, direction: int) -> bool:
        """Return True if the wall of a cell in a direction is open.

        This is part of the public API: it lets another project ask
        the generator whether two cells are connected, without having
        to decode the ``grid`` bitmask by hand.
        """
        x, y = cell
        return not (self.grid[y][x] & direction)

    def _open_wall(self, cell: Cell, direction: int) -> None:
        """Open the wall between cell and its neighbor in that direction."""
        x, y = cell
        nx, ny = x + _DELTA[direction][0], y + _DELTA[direction][1]
        self.grid[y][x] &= ~direction
        self.grid[ny][nx] &= ~_OPPOSITE[direction]

    def _close_wall(self, cell: Cell, direction: int) -> None:
        """Close the wall between cell and its neighbor (used to undo)."""
        x, y = cell
        nx, ny = x + _DELTA[direction][0], y + _DELTA[direction][1]
        self.grid[y][x] |= direction
        self.grid[ny][nx] |= _OPPOSITE[direction]

    # ------------------------------------------------------------------ #
    # Internal helpers - the "42" pattern                                #
    # ------------------------------------------------------------------ #
    def _place_pattern(self) -> Set[Cell]:
        """Compute the set of cells forming the "42" pattern, if it fits.

        The pattern is centered in the maze. If the maze is too small
        to contain it, an error message is printed and no pattern is
        used, as allowed by the subject.
        """
        pattern_width = len(_DIGIT_4[0]) + 1 + len(_DIGIT_2[0])
        pattern_height = len(_DIGIT_4)
        # Keep at least a 1-cell margin all around the pattern.
        if self.width < pattern_width + 2 or self.height < pattern_height + 2:
            print(
                "Warning: maze is too small to display the '42' pattern, "
                "skipping it."
            )
            return set()

        left = (self.width - pattern_width) // 2
        top = (self.height - pattern_height) // 2
        cells: Set[Cell] = set()
        combined = [
            row4 + "." + row2 for row4, row2 in zip(_DIGIT_4, _DIGIT_2)
        ]
        for row_index, row in enumerate(combined):
            for col_index, char in enumerate(row):
                if char == "#":
                    cells.add((left + col_index, top + row_index))

        # Never block the entry, the exit, or (in playable mode) the
        # center cell, which must stay a usable corridor.
        cells.discard(self.entry)
        cells.discard(self.exit_)
        if not self.perfect:
            center = (self.width // 2, self.height // 2)
            cells.discard(center)
            for corner in self._corners():
                cells.discard(corner)
        return cells

    def _corners(self) -> Tuple[Cell, Cell, Cell, Cell]:
        """Return the four corner cells of the maze."""
        return (
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
        )

    # ------------------------------------------------------------------ #
    # Internal helpers - maze carving                                    #
    # ------------------------------------------------------------------ #
    def _carve_spanning_tree(self) -> None:
        """Carve a perfect maze (a spanning tree) using a randomized DFS.

        Cells belonging to the "42" pattern are treated as obstacles:
        they stay fully closed and are not part of the connectivity
        graph, as explicitly allowed by the subject.
        """
        start = self.entry if self.entry not in self.pattern_cells else (
            self._first_free_cell()
        )
        visited: Set[Cell] = {start}
        stack: List[Cell] = [start]

        while stack:
            current = stack[-1]
            candidates = [
                (direction, neighbor)
                for direction, neighbor in self._neighbors(current)
                if neighbor not in visited
                and neighbor not in self.pattern_cells
            ]
            if not candidates:
                stack.pop()
                continue
            direction, neighbor = self._rng.choice(candidates)
            self._open_wall(current, direction)
            visited.add(neighbor)
            stack.append(neighbor)

    def _first_free_cell(self) -> Cell:
        """Return the first cell that is not part of the "42" pattern."""
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.pattern_cells:
                    return (x, y)
        raise MazeError("the maze has no free cell to start from")

    def _free_cells(self) -> List[Cell]:
        """Return every cell that is not part of the "42" pattern."""
        return [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in self.pattern_cells
        ]

    def _would_create_big_open_area(self, cell: Cell, direction: int) -> bool:
        """Return True if opening this wall would create a 3x3 open area.

        A corridor must never be wider than 2 cells, so no 3x3 block
        of cells may end up fully interconnected.
        """
        self._open_wall(cell, direction)
        found = self._has_3x3_open_area()
        self._close_wall(cell, direction)
        return found

    def _has_3x3_open_area(self) -> bool:
        """Return True if any 3x3 block of cells is fully open inside."""
        for top in range(self.height - 2):
            for left in range(self.width - 2):
                if self._block_is_fully_open(left, top):
                    return True
        return False

    def _block_is_fully_open(self, left: int, top: int) -> bool:
        """Return True if the 3x3 block starting at (left, top) is open.

        "Open" means every pair of horizontally or vertically adjacent
        cells inside the block has no wall between them.
        """
        for y in range(top, top + 3):
            for x in range(left, left + 2):
                if (x, y) in self.pattern_cells:
                    return False
                if (x + 1, y) in self.pattern_cells:
                    return False
                if not self.is_open((x, y), EAST):
                    return False
        for y in range(top, top + 2):
            for x in range(left, left + 3):
                if (x, y) in self.pattern_cells:
                    return False
                if (x, y + 1) in self.pattern_cells:
                    return False
                if not self.is_open((x, y), SOUTH):
                    return False
        return True

    def _dead_ends(self) -> List[Cell]:
        """Return cells that have exactly one open wall (dead ends)."""
        dead_ends: List[Cell] = []
        for cell in self._free_cells():
            open_count = sum(
                1 for direction, _ in self._neighbors(cell)
                if self.is_open(cell, direction)
            )
            if open_count == 1:
                dead_ends.append(cell)
        return dead_ends

    def _add_loops_and_remove_dead_ends(self) -> None:
        """Add extra passages so the maze has loops and few dead ends.

        Used for the "playable" (non-perfect) mode. This repeatedly
        opens a closed wall next to a dead end (when it does not
        create a too-wide corridor), until dead ends become rare or
        no more progress can be made. It also makes sure the maze
        ends up with at least two independent extra routes (loops).
        """
        max_passes = self.width * self.height * 2
        extra_edges_opened = 0

        for _ in range(max_passes):
            dead_ends = self._dead_ends()
            if not dead_ends and extra_edges_opened >= 2:
                break
            progressed = False
            self._rng.shuffle(dead_ends)
            for cell in dead_ends:
                closed_neighbors = [
                    (direction, neighbor)
                    for direction, neighbor in self._neighbors(cell)
                    if neighbor not in self.pattern_cells
                    and not self.is_open(cell, direction)
                ]
                self._rng.shuffle(closed_neighbors)
                for direction, _neighbor in closed_neighbors:
                    if not self._would_create_big_open_area(cell, direction):
                        self._open_wall(cell, direction)
                        extra_edges_opened += 1
                        progressed = True
                        break
            if not progressed:
                break

        # Guarantee at least two independent extra routes even if the
        # maze already had no dead end to begin with.
        self._ensure_minimum_loops(
            minimum=2, already_opened=extra_edges_opened,
        )

    def _ensure_minimum_loops(self, minimum: int, already_opened: int) -> None:
        """Open extra random walls until at least `minimum` loops exist."""
        if already_opened >= minimum:
            return
        candidates = self._free_cells()
        self._rng.shuffle(candidates)
        opened = already_opened
        for cell in candidates:
            if opened >= minimum:
                return
            closed_neighbors = [
                (direction, neighbor)
                for direction, neighbor in self._neighbors(cell)
                if neighbor not in self.pattern_cells
                and not self.is_open(cell, direction)
            ]
            self._rng.shuffle(closed_neighbors)
            for direction, _neighbor in closed_neighbors:
                if not self._would_create_big_open_area(cell, direction):
                    self._open_wall(cell, direction)
                    opened += 1
                    break

    # ------------------------------------------------------------------ #
    # Internal helpers - shortest path (breadth-first search)            #
    # ------------------------------------------------------------------ #
    def _shortest_path_cells(self) -> List[Cell]:
        """Return the list of cells forming the shortest entry-exit path."""
        came_from: Dict[Cell, Cell] = {}
        visited: Set[Cell] = {self.entry}
        queue: List[Cell] = [self.entry]
        head = 0

        while head < len(queue):
            current = queue[head]
            head += 1
            if current == self.exit_:
                break
            for direction, neighbor in self._neighbors(current):
                if neighbor in visited:
                    continue
                if not self.is_open(current, direction):
                    continue
                visited.add(neighbor)
                came_from[neighbor] = current
                queue.append(neighbor)

        if self.exit_ not in visited:
            raise MazeError("no path exists between entry and exit")

        path = [self.exit_]
        while path[-1] != self.entry:
            path.append(came_from[path[-1]])
        path.reverse()
        return path

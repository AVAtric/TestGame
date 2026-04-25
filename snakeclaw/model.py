"""Game models and logic for Snake game."""

import random
import time
from collections import deque
from enum import Enum
from typing import Iterable, List, Set, Tuple, Optional


class Direction(Enum):
    """Movement direction for the snake."""
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)


class Action(Enum):
    """Input actions beyond movement."""
    QUIT = "quit"
    RESET = "reset"
    PAUSE = "pause"
    START = "start"
    MENU = "menu"
    HIGH_SCORES = "high_scores"
    HELP = "help"
    SELECT = "select"
    MENU_UP = "menu_up"
    MENU_DOWN = "menu_down"


class GameState(Enum):
    """Game state machine states."""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    ENTER_INITIALS = "enter_initials"
    HIGH_SCORES = "high_scores"
    HELP = "help"
    QUIT = "quit"


class WallMode(Enum):
    """Whether walls wrap (toroidal) or kill on contact."""
    WRAP = "wrap"
    SOLID = "solid"


OPPOSITE: dict[Direction, Direction] = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}


class Snake:
    """Snake representation with movement and collision detection."""

    def __init__(self, start_pos: Tuple[int, int], length: int = 3,
                 direction: Direction = Direction.UP):
        self.direction: Direction = direction
        self._last_moved_direction: Direction = direction
        self.body: List[Tuple[int, int]] = [start_pos]
        dx, dy = direction.value
        current_pos = start_pos
        for _ in range(1, length):
            current_pos = (current_pos[0] - dx, current_pos[1] - dy)
            self.body.append(current_pos)
        self.grow: bool = False

    def move(self, new_head: Optional[Tuple[int, int]] = None) -> None:
        """Move the snake one step. Pass `new_head` to override the computed
        position (e.g. when the engine has applied wall-wrap)."""
        if new_head is None:
            head = self.body[0]
            new_head = (head[0] + self.direction.value[0],
                        head[1] + self.direction.value[1])
        self.body.insert(0, new_head)
        if self.grow:
            self.grow = False
        else:
            self.body.pop()
        self._last_moved_direction = self.direction

    def set_direction(self, direction: Direction) -> None:
        """Change direction, preventing 180-degree turns.

        Validate against the last *moved* direction, not the pending one — otherwise
        two perpendicular inputs within a single tick (e.g. RIGHT → UP → LEFT)
        can stack into a 180° turn that drives the head into its own neck.
        """
        if direction == OPPOSITE.get(self._last_moved_direction):
            return
        self.direction = direction

    def get_head(self) -> Tuple[int, int]:
        return self.body[0]

    def get_tail(self) -> Tuple[int, int]:
        return self.body[-1]

    def get_body(self) -> List[Tuple[int, int]]:
        return self.body.copy()

    @staticmethod
    def _out_of_bounds(pos: Tuple[int, int], width: int, height: int) -> bool:
        r, c = pos
        return r < 0 or r >= height or c < 0 or c >= width

    def check_collision(self, width: int, height: int) -> bool:
        """Check if the snake has collided with walls or itself."""
        head = self.get_head()
        return self._out_of_bounds(head, width, height) or head in self.body[1:]

    def compute_next_head(self, width: int, height: int,
                          wrap: bool = False) -> Tuple[int, int]:
        """Where the head will land on the next move, applying wrap if enabled.

        With wrap=False, the result may be out of bounds — callers must check.
        """
        head = self.body[0]
        raw = (head[0] + self.direction.value[0],
               head[1] + self.direction.value[1])
        if wrap:
            return (raw[0] % height, raw[1] % width)
        return raw

    def check_next_move(self, width: int, height: int,
                        wrap: bool = False) -> bool:
        """Check if the next move would cause a collision.

        With wrap=True, walls are toroidal; only self-collision is fatal.
        """
        new_head = self.compute_next_head(width, height, wrap=wrap)
        if not wrap and self._out_of_bounds(new_head, width, height):
            return True
        body_to_check = self.body if self.grow else self.body[:-1]
        return new_head in body_to_check

    def grow_snake(self) -> None:
        """Mark the snake to grow by one segment."""
        self.grow = True


class Food:
    """Food position in the playfield."""

    def __init__(self, width: int, height: int,
                 initial_position: Optional[Tuple[int, int]] = None,
                 food_chars: Optional[List[str]] = None):
        self.width = width
        self.height = height
        self.position: Tuple[int, int] = (0, 0)
        self.food_chars = food_chars or ['🟩']
        self.current_char: str = random.choice(self.food_chars)
        if initial_position is not None:
            self.position = initial_position
        else:
            self.place()

    def place(self, pos: Optional[Tuple[int, int]] = None,
              snake_body: Optional[List[Tuple[int, int]]] = None) -> None:
        self.current_char = random.choice(self.food_chars)
        if pos is not None:
            self.position = pos
            return
        while True:
            p = (random.randint(0, self.height - 1),
                 random.randint(0, self.width - 1))
            if snake_body is None or p not in snake_body:
                self.position = p
                break

    def get_position(self) -> Tuple[int, int]:
        return self.position
    
    def get_char(self) -> str:
        return self.current_char

    def check_eaten(self, snake_head: Tuple[int, int]) -> bool:
        return self.get_position() == snake_head


class BonusFood:
    """Rare golden bonus food that appears temporarily for extra points."""

    def __init__(self, width: int, height: int, char: str = '★★',
                 duration: float = 5.0):
        self.width = width
        self.height = height
        self.char = char
        self.duration = duration
        self.position: Optional[Tuple[int, int]] = None
        self.spawn_time: float = 0.0

    @property
    def active(self) -> bool:
        return self.position is not None

    def spawn_at(self, pos: Tuple[int, int]) -> None:
        """Place bonus food at an explicit position and start its timer.

        Placement strategy (reachability, avoiding the snake / normal food)
        lives in the engine; this method is the model-level primitive that
        records *where* and *when* a spawn happened.
        """
        self.position = pos
        self.spawn_time = time.time()

    def despawn(self) -> None:
        self.position = None

    def is_expired(self) -> bool:
        if not self.active:
            return False
        return time.time() - self.spawn_time >= self.duration

    def is_blinking(self, threshold: float = 2.0) -> bool:
        """True whenever the bonus is on screen — bonus food blinks the whole time
        it's visible so it stands out against the regular food."""
        return self.active

    def check_eaten(self, snake_head: Tuple[int, int]) -> bool:
        return self.active and self.position == snake_head


# ---------------------------------------------------------------------------
# Reachability (BFS) — used by the engine to ensure food is always placeable
# on a cell the snake can actually reach from its current head.
# ---------------------------------------------------------------------------

def reachable_cells(snake_body: Iterable[Tuple[int, int]],
                    head: Tuple[int, int],
                    width: int, height: int,
                    wrap: bool) -> Set[Tuple[int, int]]:
    """Cells reachable from `head` without crossing the snake's body.

    Treats every body segment except the head as a wall. Honors `wrap` so
    toroidal walls don't artificially partition the grid. Returns the set of
    reachable empty cells (excludes the head itself).
    """
    obstacles = set(snake_body)
    obstacles.discard(head)
    visited: Set[Tuple[int, int]] = {head}
    queue: deque = deque([head])
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    while queue:
        r, c = queue.popleft()
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if wrap:
                nr %= height
                nc %= width
            elif not (0 <= nr < height and 0 <= nc < width):
                continue
            cell = (nr, nc)
            if cell in visited or cell in obstacles:
                continue
            visited.add(cell)
            queue.append(cell)
    visited.discard(head)
    return visited

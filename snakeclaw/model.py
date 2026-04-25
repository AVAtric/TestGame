"""Game models and logic for Snake game."""

import random
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


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
    YES = "yes"   # Y key — used in confirmation dialogs
    NO = "no"     # N key — used in confirmation dialogs


class GameState(Enum):
    """Game state machine states."""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    ENTER_INITIALS = "enter_initials"
    HIGH_SCORES = "high_scores"
    HELP = "help"
    CONFIRM_QUIT = "confirm_quit"  # "Are you sure?" overlay before QUIT
    QUIT = "quit"


class WallMode(Enum):
    """Whether walls wrap (toroidal) or kill on contact."""
    WRAP = "wrap"
    SOLID = "solid"


class GameMode(Enum):
    """Top-level game mode picked from the menu.

    MODERN  = the full feature set (fruit variety, power-ups, popups, buffs,
              wrap walls). The "Start Game" entry.
    CLASSIC = pure Nokia-3310-style snake: small grid, solid walls, apples
              only, no power-ups, no popups. The "Classic Game" entry.
    """
    MODERN = "modern"
    CLASSIC = "classic"


class Effect(Enum):
    """Power-up effects applied when eaten."""
    NONE = "none"
    SPEED_UP = "speed_up"
    SLOW_DOWN = "slow_down"
    SHRINK = "shrink"


OPPOSITE: Dict[Direction, Direction] = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}


# ---------------------------------------------------------------------------
# Fruit / power-up descriptors
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FruitKind:
    """Static description of a fruit or power-up.

    `weight` drives weighted random selection across a kind list.
    `lifetime` of None means the fruit stays until eaten (regular food);
    a number means it auto-despawns after that many seconds (power-ups).
    """
    name: str
    char: str
    points: int
    color: int
    weight: float = 1.0
    effect: Effect = Effect.NONE
    lifetime: Optional[float] = None


def pick_kind(kinds: Sequence[FruitKind]) -> FruitKind:
    """Weighted random pick among kinds."""
    weights = [k.weight for k in kinds]
    return random.choices(list(kinds), weights=weights, k=1)[0]


@dataclass
class ScorePopup:
    """Floating `+N` text shown briefly where a fruit was eaten."""
    position: Tuple[int, int]
    text: str
    color: int
    expires_at: float

    def is_expired(self, now: Optional[float] = None) -> bool:
        return (now if now is not None else time.time()) >= self.expires_at


# ---------------------------------------------------------------------------
# Snake
# ---------------------------------------------------------------------------

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

    def shrink(self, amount: int = 1) -> int:
        """Remove up to `amount` tail segments. Returns the actual number removed.

        Always preserves a single head segment so the snake can keep moving.
        """
        removed = 0
        while removed < amount and len(self.body) > 1:
            self.body.pop()
            removed += 1
        return removed


# ---------------------------------------------------------------------------
# Fruit (the regular, always-on-screen fruit) and PowerUp (rare, timed)
# ---------------------------------------------------------------------------

class Fruit:
    """Regular fruit on the playfield. One on screen at a time, picks a
    weighted kind on each placement."""

    def __init__(self, width: int, height: int,
                 kinds: Sequence[FruitKind],
                 initial_position: Optional[Tuple[int, int]] = None):
        if not kinds:
            raise ValueError("Fruit requires at least one FruitKind")
        self.width = width
        self.height = height
        self.kinds: Sequence[FruitKind] = tuple(kinds)
        self.kind: FruitKind = pick_kind(self.kinds)
        self.position: Tuple[int, int] = initial_position or (0, 0)

    # -- placement ----------------------------------------------------------

    def place(self, pos: Optional[Tuple[int, int]] = None,
              snake_body: Optional[List[Tuple[int, int]]] = None,
              kind: Optional[FruitKind] = None) -> None:
        """Place the fruit. `kind` overrides the random pick if given.

        With `pos`, places exactly there; otherwise picks a random cell not
        on the snake. The kind is re-rolled (or set to `kind`) on every place.
        """
        self.kind = kind or pick_kind(self.kinds)
        if pos is not None:
            self.position = pos
            return
        while True:
            p = (random.randint(0, self.height - 1),
                 random.randint(0, self.width - 1))
            if snake_body is None or p not in snake_body:
                self.position = p
                return

    # -- queries ------------------------------------------------------------

    def get_position(self) -> Tuple[int, int]:
        return self.position

    def get_char(self) -> str:
        return self.kind.char

    def get_points(self) -> int:
        return self.kind.points

    def get_color(self) -> int:
        return self.kind.color

    def check_eaten(self, snake_head: Tuple[int, int]) -> bool:
        return self.position == snake_head


class PowerUp:
    """Timed power-up. Picks a weighted kind on spawn, applies effects when eaten.

    Off-screen by default; the engine spawns one occasionally on a reachable
    cell and despawns it on expiry.
    """

    def __init__(self, width: int, height: int,
                 kinds: Sequence[FruitKind],
                 default_duration: float = 6.0):
        if not kinds:
            raise ValueError("PowerUp requires at least one FruitKind")
        self.width = width
        self.height = height
        self.kinds: Sequence[FruitKind] = tuple(kinds)
        self.default_duration: float = default_duration
        self.kind: FruitKind = self.kinds[0]
        self.position: Optional[Tuple[int, int]] = None
        self.spawn_time: float = 0.0

    @property
    def active(self) -> bool:
        return self.position is not None

    @property
    def duration(self) -> float:
        return self.kind.lifetime if self.kind.lifetime is not None else self.default_duration

    def spawn_at(self, pos: Tuple[int, int],
                 kind: Optional[FruitKind] = None) -> None:
        """Place the power-up at an explicit position and start its timer."""
        self.kind = kind or pick_kind(self.kinds)
        self.position = pos
        self.spawn_time = time.time()

    def despawn(self) -> None:
        self.position = None

    def is_expired(self) -> bool:
        if not self.active:
            return False
        return time.time() - self.spawn_time >= self.duration

    def remaining(self) -> float:
        """Seconds remaining before this power-up despawns. 0 when inactive."""
        if not self.active:
            return 0.0
        return max(0.0, self.duration - (time.time() - self.spawn_time))

    def is_blinking(self) -> bool:
        """Power-ups blink the whole time they're visible."""
        return self.active

    def get_char(self) -> str:
        return self.kind.char

    def get_points(self) -> int:
        return self.kind.points

    def get_color(self) -> int:
        return self.kind.color

    def get_effect(self) -> Effect:
        return self.kind.effect

    def check_eaten(self, snake_head: Tuple[int, int]) -> bool:
        return self.active and self.position == snake_head


# ---------------------------------------------------------------------------
# Pathfinder — BFS reachability with optional distance map
# ---------------------------------------------------------------------------

def bfs_distances(snake_body: Iterable[Tuple[int, int]],
                  head: Tuple[int, int],
                  width: int, height: int,
                  wrap: bool) -> Dict[Tuple[int, int], int]:
    """BFS from `head` through empty cells; returns {cell: distance}.

    Treats every body segment except `head` as a wall. Honors `wrap` so
    toroidal walls don't partition the grid. The head itself is not in the
    returned map.
    """
    obstacles = set(snake_body)
    obstacles.discard(head)
    distances: Dict[Tuple[int, int], int] = {head: 0}
    queue: deque = deque([head])
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    while queue:
        r, c = queue.popleft()
        d = distances[(r, c)]
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if wrap:
                nr %= height
                nc %= width
            elif not (0 <= nr < height and 0 <= nc < width):
                continue
            cell = (nr, nc)
            if cell in distances or cell in obstacles:
                continue
            distances[cell] = d + 1
            queue.append(cell)
    distances.pop(head, None)
    return distances


def reachable_cells(snake_body: Iterable[Tuple[int, int]],
                    head: Tuple[int, int],
                    width: int, height: int,
                    wrap: bool) -> Set[Tuple[int, int]]:
    """Set of cells reachable from `head` (excluding head)."""
    return set(bfs_distances(snake_body, head, width, height, wrap).keys())

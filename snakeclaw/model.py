"""Game models and logic for Snake game."""

import random
import time
from enum import Enum
from typing import List, Tuple, Optional


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

    def move(self) -> None:
        """Move the snake one step in its current direction."""
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

    def check_next_move(self, width: int, height: int) -> bool:
        """Check if the next move would cause a collision."""
        head = self.get_head()
        new_head = (head[0] + self.direction.value[0],
                    head[1] + self.direction.value[1])
        if self._out_of_bounds(new_head, width, height):
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

    def spawn(self, snake_body: List[Tuple[int, int]],
              food_pos: Tuple[int, int]) -> None:
        """Place bonus food avoiding snake and normal food."""
        for _ in range(100):
            p = (random.randint(0, self.height - 1),
                 random.randint(0, self.width - 1))
            if p not in snake_body and p != food_pos:
                self.position = p
                self.spawn_time = time.time()
                return

    def despawn(self) -> None:
        self.position = None

    def is_expired(self) -> bool:
        if not self.active:
            return False
        return time.time() - self.spawn_time >= self.duration

    def is_blinking(self, threshold: float = 2.0) -> bool:
        """True when fewer than `threshold` seconds remain — for blink rendering."""
        if not self.active:
            return False
        return time.time() - self.spawn_time > self.duration - threshold

    def check_eaten(self, snake_head: Tuple[int, int]) -> bool:
        return self.active and self.position == snake_head

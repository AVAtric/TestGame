"""Game models and logic for Snake game."""

import random
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


# Keep backward compat aliases used by old tests
class GameStatus(Enum):
    PLAYING = "playing"
    GAME_OVER = "game_over"
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
        if not self.grow:
            self.body.pop()
        else:
            self.grow = False  # Reset grow flag after growing

    def set_direction(self, direction: Direction) -> None:
        """Change direction, preventing 180-degree turns."""
        if direction == OPPOSITE.get(self.direction):
            return
        self.direction = direction

    def get_head(self) -> Tuple[int, int]:
        return self.body[0]

    def get_tail(self) -> Tuple[int, int]:
        return self.body[-1]

    def get_body(self) -> List[Tuple[int, int]]:
        return self.body.copy()

    def check_collision(self, width: int, height: int) -> bool:
        """Check if the snake has collided with walls or itself."""
        head = self.get_head()
        if head[0] < 0 or head[0] >= height or head[1] < 0 or head[1] >= width:
            return True
        if head in self.body[1:]:
            return True
        return False

    def check_next_move(self, width: int, height: int) -> bool:
        """Check if the next move would cause a collision."""
        head = self.get_head()
        new_head = (head[0] + self.direction.value[0],
                    head[1] + self.direction.value[1])
        if new_head[0] < 0 or new_head[0] >= height or \
           new_head[1] < 0 or new_head[1] >= width:
            return True
        body_to_check = self.body if self.grow else self.body[:-1]
        if new_head in body_to_check:
            return True
        return False

    def grow_snake(self) -> None:
        """Mark the snake to grow by one segment."""
        self.grow = True


class Food:
    """Food position in the playfield."""

    def __init__(self, width: int, height: int,
                 initial_position: Optional[Tuple[int, int]] = None):
        self.width = width
        self.height = height
        self.position: Tuple[int, int] = (0, 0)
        if initial_position is not None:
            self.position = initial_position
        else:
            self.place()

    def place(self, pos: Optional[Tuple[int, int]] = None,
              snake_body: Optional[List[Tuple[int, int]]] = None) -> None:
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

    def check_eaten(self, snake_head: Tuple[int, int]) -> bool:
        return self.get_position() == snake_head

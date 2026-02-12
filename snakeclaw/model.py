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
    RESET = (0, 0)
    QUIT = (-1, -1)


class GameStatus(Enum):
    """Game status enum."""
    PLAYING = "playing"
    GAME_OVER = "game_over"
    QUIT = "quit"


class Snake:
    """Snake representation with movement and collision detection."""

    def __init__(self, start_pos: Tuple[int, int], length: int = 3, direction: Direction = Direction.RIGHT):
        """
        Initialize the snake.

        Args:
            start_pos: Starting position (row, col)
            length: Initial length of the snake
            direction: Initial direction of movement
        """
        self.direction: Direction = direction
        # Build body with head at start_pos and the rest behind in the opposite direction
        self.body: List[Tuple[int, int]] = [start_pos]
        current_pos = start_pos
        dx, dy = self.direction.value
        for _ in range(1, length):
            current_pos = (current_pos[0] - dx, current_pos[1] - dy)
            self.body.append(current_pos)
        self.grow: bool = False

    def move(self) -> None:
        """Move the snake one step in its current direction."""
        head = self.body[0]
        new_head = (head[0] + self.direction.value[0], head[1] + self.direction.value[1])

        # If we should grow, don't remove the tail
        if self.grow:
            self.body.insert(0, new_head)
            self.grow = False
        else:
            self.body.insert(0, new_head)
            self.body.pop()

    def set_direction(self, direction: Direction) -> None:
        """Change the snake's direction, preventing 180-degree turns."""
        # Prevent reversing direction
        if direction == self._opposite_direction(self.direction):
            # ignore reverse turns
            return
        self.direction = direction

    @classmethod
    def _opposite_direction(cls, direction: Direction) -> Direction:
        """Get the opposite direction."""
        if direction == Direction.UP:
            return Direction.DOWN
        elif direction == Direction.DOWN:
            return Direction.UP
        elif direction == Direction.LEFT:
            return Direction.RIGHT
        elif direction == Direction.RIGHT:
            return Direction.LEFT
        return direction

    def get_head(self) -> Tuple[int, int]:
        """Get the snake's head position."""
        return self.body[0]

    def get_tail(self) -> Tuple[int, int]:
        """Get the snake's tail position."""
        return self.body[-1]

    def get_body(self) -> List[Tuple[int, int]]:
        """Get the entire snake body."""
        return self.body.copy()

    def check_collision(self, width: int, height: int) -> bool:
        """
        Check if the snake has collided with walls or itself.

        Args:
            width: Playfield width in columns
            height: Playfield height in rows

        Returns:
            True if collision would occur, False otherwise
        """
        head = self.get_head()

        # Self collision (skip the head when checking for self-collision)
        body = self.body[1:]
        if head in body:
            return True

        return False

    def check_next_move(self, width: int, height: int) -> bool:
        """
        Check if the next move would cause a collision.

        Args:
            width: Playfield width in columns
            height: Playfield height in rows

        Returns:
            True if next move would cause a collision, False otherwise
        """
        head = self.get_head()
        new_head = (head[0] + self.direction.value[0], head[1] + self.direction.value[1])

        # Wall collision
        if new_head[0] < 0 or new_head[0] >= height or new_head[1] < 0 or new_head[1] >= width:
            return True

        # Self collision (exclude tail if not growing, exclude head to avoid false positive)
        if self.grow:
            body_to_check = self.body
        else:
            body_to_check = self.body[:-1]
        if new_head in body_to_check:
            return True

        return False

    def grow_snake(self) -> None:
        """Mark the snake to grow by one segment."""
        self.grow = True


class Food:
    """Food position in the playfield."""

    def __init__(self, width: int, height: int, initial_position: Optional[Tuple[int, int]] = None):
        """
        Initialize food at a random position.

        Args:
            width: Playfield width in columns
            height: Playfield height in rows
            initial_position: Optional initial position to use instead of random
        """
        self.width = width
        self.height = height
        self.position: Tuple[int, int] = (0, 0)
        if initial_position is not None:
            self.position = initial_position
        else:
            self.place()

    def place(self, snake_body: List[Tuple[int, int]] = None) -> None:
        """
        Place food at a random position not occupied by the snake.

        Args:
            snake_body: Snake body positions to avoid
        """
        while True:
            # Generate random position within bounds
            pos = (
                random.randint(0, self.height - 1),
                random.randint(0, self.width - 1)
            )
            # Ensure food is not on snake body
            if snake_body is None or pos not in snake_body:
                self.position = pos
                break

    def get_position(self) -> Tuple[int, int]:
        """Get the current food position."""
        return self.position

    def check_eaten(self, snake_head: Tuple[int, int]) -> bool:
        """
        Check if food has been eaten by the snake.

        Args:
            snake_head: Snake's head position

        Returns:
            True if food was eaten, False otherwise
        """
        return self.get_position() == snake_head

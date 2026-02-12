"""Unit tests for Snake game models."""

import pytest
from snakeclaw.model import Direction, GameStatus, Snake, Food


class TestDirection:
    """Tests for Direction enum."""

    def test_direction_values(self):
        """Test that direction values are correct."""
        assert Direction.UP.value == (-1, 0)
        assert Direction.DOWN.value == (1, 0)
        assert Direction.LEFT.value == (0, -1)
        assert Direction.RIGHT.value == (0, 1)


class TestGameStatus:
    """Tests for GameStatus enum."""

    def test_game_status_values(self):
        """Test that game status values are correct."""
        assert GameStatus.PLAYING.value == "playing"
        assert GameStatus.GAME_OVER.value == "game_over"
        assert GameStatus.QUIT.value == "quit"


class TestSnake:
    """Tests for Snake class."""

    def test_snake_initialization(self):
        """Test snake initializes with correct position and direction."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        assert snake.get_head() == (5, 10)
        assert len(snake.get_body()) == 3

    def test_snake_initial_position(self):
        """Test snake body is built correctly from start position."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        body = snake.get_body()
        assert body[0] == (5, 10)  # Head
        assert body[1] == (5, 9)   # Body
        assert body[2] == (5, 8)   # Tail

    def test_snake_initialization_up(self):
        """Test snake body builds correctly when starting up."""
        snake = Snake((5, 10), length=3, direction=Direction.UP)
        body = snake.get_body()
        assert body[0] == (5, 10)
        assert body[1] == (6, 10)
        assert body[2] == (7, 10)

    def test_snake_initialization_left(self):
        """Test snake body builds correctly when starting left."""
        snake = Snake((5, 10), length=3, direction=Direction.LEFT)
        body = snake.get_body()
        assert body[0] == (5, 10)
        assert body[1] == (5, 11)
        assert body[2] == (5, 12)

    def test_snake_move(self):
        """Test snake moves correctly in its current direction."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        initial_body = snake.get_body()
        snake.move()
        new_body = snake.get_body()
        assert new_body[0] == (5, 11)  # Head moved right
        assert new_body[-1] == initial_body[1]  # Old second segment becomes tail

    def test_snake_move_up(self):
        """Test snake moves correctly when direction is up."""
        snake = Snake((5, 10), length=3, direction=Direction.UP)
        snake.move()
        assert snake.get_head() == (4, 10)

    def test_snake_move_down(self):
        """Test snake moves correctly when direction is down."""
        snake = Snake((5, 10), length=3, direction=Direction.DOWN)
        snake.move()
        assert snake.get_head() == (6, 10)

    def test_snake_move_left(self):
        """Test snake moves correctly when direction is left."""
        snake = Snake((5, 10), length=3, direction=Direction.LEFT)
        snake.move()
        assert snake.get_head() == (5, 9)

    def test_snake_move_no_growth(self):
        """Test snake move without growing."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        body_before = snake.get_body()
        snake.move()
        body_after = snake.get_body()
        assert len(body_after) == len(body_before)

    def test_snake_grow(self):
        """Test snake grows when moving and grow flag is set."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        snake.grow_snake()
        snake.move()
        body = snake.get_body()
        assert len(body) == 4  # Snake should have 4 segments

    def test_snake_grow_snake(self):
        """Test grow_snake method sets grow flag."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        snake.grow_snake()
        assert snake.grow is True

    def test_snake_get_head(self):
        """Test get_head method returns correct position."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        assert snake.get_head() == (5, 10)

    def test_snake_get_tail(self):
        """Test get_tail method returns correct position."""
        snake = Snake((5, 10), length=5, direction=Direction.RIGHT)
        assert snake.get_tail() == (5, 6)

    def test_snake_get_body(self):
        """Test get_body method returns a copy."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        body = snake.get_body()
        assert body is not snake.body  # Should return a copy
        assert len(body) == 3

    def test_snake_set_direction_right(self):
        """Test set_direction changes direction to right."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        snake.set_direction(Direction.LEFT)
        assert snake.direction == Direction.LEFT

    def test_snake_set_direction_up(self):
        """Test set_direction changes direction to up."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        snake.set_direction(Direction.UP)
        assert snake.direction == Direction.UP

    def test_snake_set_direction_down(self):
        """Test set_direction changes direction to down."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        snake.set_direction(Direction.DOWN)
        assert snake.direction == Direction.DOWN

    def test_snake_set_direction_left(self):
        """Test set_direction changes direction to left."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        snake.set_direction(Direction.LEFT)
        assert snake.direction == Direction.LEFT

    def test_snake_set_direction_opposite(self):
        """Test set_direction prevents 180-degree turns."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        snake.set_direction(Direction.LEFT)
        # Direction should remain RIGHT (cannot reverse)
        assert snake.direction == Direction.RIGHT

    def test_snake_set_direction_same(self):
        """Test set_direction with same direction has no effect."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        snake.set_direction(Direction.RIGHT)
        assert snake.direction == Direction.RIGHT

    def test_snake_check_collision_with_self(self):
        """Test check_collision detects collision with self."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        snake.move()  # Move snake to (5, 11), body at (5, 10), (5, 9), (5, 8)
        assert snake.check_collision(60, 30) is True  # Head at (5, 11), body contains it

    def test_snake_check_collision_no_collision(self):
        """Test check_collision returns False when no collision."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        assert snake.check_collision(60, 30) is False

    def test_snake_check_collision_wall(self):
        """Test check_collision detects wall collision."""
        snake = Snake((0, 10), length=3, direction=Direction.DOWN)
        assert snake.check_collision(60, 30) is True

    def test_snake_check_collision_top_wall(self):
        """Test check_collision detects hitting top wall."""
        snake = Snake((0, 10), length=3, direction=Direction.UP)
        assert snake.check_collision(60, 30) is True

    def test_snake_check_collision_bottom_wall(self):
        """Test check_collision detects hitting bottom wall."""
        snake = Snake((29, 10), length=3, direction=Direction.DOWN)
        assert snake.check_collision(60, 30) is True

    def test_snake_check_collision_left_wall(self):
        """Test check_collision detects hitting left wall."""
        snake = Snake((10, 0), length=3, direction=Direction.LEFT)
        assert snake.check_collision(60, 30) is True

    def test_snake_check_collision_right_wall(self):
        """Test check_collision detects hitting right wall."""
        snake = Snake((10, 59), length=3, direction=Direction.RIGHT)
        assert snake.check_collision(60, 30) is True

    def test_snake_check_next_move_collision_with_self(self):
        """Test check_next_move detects collision with self."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        snake.move()  # Move to (5, 11)
        assert snake.check_next_move(60, 30) is True  # Would hit body at (5, 10)

    def test_snake_check_next_move_no_collision(self):
        """Test check_next_move returns False when no collision."""
        snake = Snake((5, 10), length=3, direction=Direction.RIGHT)
        assert snake.check_next_move(60, 30) is False

    def test_snake_check_next_move_wall_collision(self):
        """Test check_next_move detects wall collision."""
        snake = Snake((0, 10), length=3, direction=Direction.DOWN)
        assert snake.check_next_move(60, 30) is True

    def test_snake_check_next_move_top_wall(self):
        """Test check_next_move detects hitting top wall."""
        snake = Snake((0, 10), length=3, direction=Direction.UP)
        assert snake.check_next_move(60, 30) is True

    def test_snake_check_next_move_bottom_wall(self):
        """Test check_next_move detects hitting bottom wall."""
        snake = Snake((29, 10), length=3, direction=Direction.DOWN)
        assert snake.check_next_move(60, 30) is True

    def test_snake_check_next_move_left_wall(self):
        """Test check_next_move detects hitting left wall."""
        snake = Snake((10, 0), length=3, direction=Direction.LEFT)
        assert snake.check_next_move(60, 30) is True

    def test_snake_check_next_move_right_wall(self):
        """Test check_next_move detects hitting right wall."""
        snake = Snake((10, 59), length=3, direction=Direction.RIGHT)
        assert snake.check_next_move(60, 30) is True


class TestFood:
    """Tests for Food class."""

    def test_food_initialization(self):
        """Test food initializes at random position."""
        food = Food(60, 30)
        pos = food.get_position()
        assert isinstance(pos, tuple)
        assert len(pos) == 2
        assert 0 <= pos[0] < 30
        assert 0 <= pos[1] < 60

    def test_food_initialization_with_position(self):
        """Test food can be initialized at specific position."""
        food = Food(60, 30, initial_position=(10, 20))
        assert food.get_position() == (10, 20)

    def test_food_place(self):
        """Test food can be placed at new position."""
        food = Food(60, 30)
        food.place((5, 10))
        assert food.get_position() == (5, 10)

    def test_food_check_eaten_true(self):
        """Test check_eaten returns True when food is at snake head."""
        food = Food(60, 30, initial_position=(5, 10))
        assert food.check_eaten((5, 10)) is True

    def test_food_check_eaten_false(self):
        """Test check_eaten returns False when food is not at snake head."""
        food = Food(60, 30, initial_position=(5, 10))
        assert food.check_eaten((5, 11)) is False

    def test_food_place_avoids_snake_body(self):
        """Test food placement avoids snake body."""
        snake_body = [(5, 10), (5, 9), (5, 8)]
        food = Food(60, 30)
        food.place(snake_body)
        pos = food.get_position()
        # Position should not be on snake body
        assert pos not in snake_body

    def test_food_place_random_position(self):
        """Test food places at random position when snake_body is None."""
        food = Food(60, 30)
        food.place(None)
        pos = food.get_position()
        assert 0 <= pos[0] < 30
        assert 0 <= pos[1] < 60
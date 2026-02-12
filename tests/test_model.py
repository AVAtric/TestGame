"""Unit tests for snakeclaw model logic."""

import pytest

from snakeclaw.model import Direction, GameStatus, Snake, Food


class TestDirection:
    """Tests for Direction enum."""

    def test_direction_values(self):
        """Test direction values are correct tuples."""
        assert Direction.UP.value == (-1, 0)
        assert Direction.DOWN.value == (1, 0)
        assert Direction.LEFT.value == (0, -1)
        assert Direction.RIGHT.value == (0, 1)

    def test_opposite_direction(self):
        """Test opposite direction calculation."""
        assert Snake._opposite_direction(Direction.UP) == Direction.DOWN
        assert Snake._opposite_direction(Direction.DOWN) == Direction.UP
        assert Snake._opposite_direction(Direction.LEFT) == Direction.RIGHT
        assert Snake._opposite_direction(Direction.RIGHT) == Direction.LEFT


class TestSnake:
    """Tests for Snake class."""

    def test_initial_position(self):
        """Test snake starts at correct position with correct length."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        assert len(snake.get_body()) == 3
        assert snake.get_head() == (5, 5)

    def test_move_forward(self):
        """Test snake moves forward in current direction."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        snake.move()
        assert snake.get_head() == (5, 6)

    def test_move_backward(self):
        """Test snake moves backward in opposite direction."""
        snake = Snake((5, 5), length=3, direction=Direction.LEFT)
        snake.move()
        assert snake.get_head() == (5, 4)

    def test_move_up(self):
        """Test snake moves upward."""
        snake = Snake((5, 5), length=3, direction=Direction.UP)
        snake.move()
        assert snake.get_head() == (4, 5)

    def test_move_down(self):
        """Test snake moves downward."""
        snake = Snake((5, 5), length=3, direction=Direction.DOWN)
        snake.move()
        assert snake.get_head() == (6, 5)

    def test_change_direction(self):
        """Test changing snake direction."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        snake.set_direction(Direction.DOWN)
        snake.move()
        assert snake.get_head() == (6, 5)

    def test_prevent_180_turn(self):
        """Test 180-degree turns are prevented."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        snake.set_direction(Direction.LEFT)
        snake.move()
        assert snake.get_head() == (5, 6)  # Should still be moving right

    def test_grow_snake(self):
        """Test snake grows when eating food."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        snake.grow_snake()
        snake.move()
        assert len(snake.get_body()) == 4  # Snake should have grown

    def test_wall_collision(self):
        """Test wall collision detection."""
        # Test collision with top wall (trying to move up from top edge)
        snake = Snake((0, 5), length=3, direction=Direction.UP)
        assert snake.check_next_move(10, 10) is True

        # Test collision with bottom wall (trying to move down from bottom edge)
        snake = Snake((9, 5), length=3, direction=Direction.DOWN)
        assert snake.check_next_move(10, 10) is True

        # Test collision with left wall (trying to move left from left edge)
        snake = Snake((5, 0), length=3, direction=Direction.LEFT)
        assert snake.check_next_move(10, 10) is True

        # Test collision with right wall (trying to move right from right edge)
        snake = Snake((5, 9), length=3, direction=Direction.RIGHT)
        assert snake.check_next_move(10, 10) is True

        # Test collision with corner (bottom-right, trying to move down or right)
        snake = Snake((9, 9), length=3, direction=Direction.DOWN)
        assert snake.check_next_move(10, 10) is True

        # Test no collision when moving away from walls
        snake = Snake((0, 5), length=3, direction=Direction.DOWN)
        assert snake.check_next_move(10, 10) is False

        snake = Snake((5, 9), length=3, direction=Direction.LEFT)
        assert snake.check_next_move(10, 10) is False

    def test_self_collision(self):
        """Test self-collision detection."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        # Move away from head
        snake.move()
        snake.move()
        # Now snake is at positions (5,7), (5,6), (5,5)
        # Move left onto (5,6) which is in the body
        snake.set_direction(Direction.LEFT)
        assert snake.check_next_move(10, 10) is True

        # Another self-collision test: snake moves onto its own body
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        snake.move()
        snake.move()
        # Now snake is at positions (5,7), (5,6), (5,5)
        # Move left onto (5,6) which is in the body
        snake.set_direction(Direction.LEFT)
        assert snake.check_next_move(10, 10) is True

    def test_no_collision(self):
        """Test no collision when safe."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        assert snake.check_next_move(10, 10) is False

        snake = Snake((5, 5), length=3, direction=Direction.UP)
        snake.move()
        assert snake.check_next_move(10, 10) is False


class TestFood:
    """Tests for Food class."""

    def test_initial_placement(self):
        """Test food is placed initially."""
        food = Food(20, 10)
        position = food.get_position()
        assert 0 <= position[0] < 10
        assert 0 <= position[1] < 20

    def test_food_position(self):
        """Test food returns correct position."""
        food = Food(20, 10)
        pos = (5, 10)
        food.position = pos
        assert food.get_position() == pos

    def test_eaten(self):
        """Test food eaten by snake."""
        food = Food(20, 10)
        # Set food to specific position for testing
        food.position = (5, 10)
        snake_head = (5, 10)
        assert food.check_eaten(snake_head) is True

    def test_not_eaten(self):
        """Test food not eaten when snake head is elsewhere."""
        food = Food(20, 10)
        snake_head = (5, 11)
        assert food.check_eaten(snake_head) is False

    def test_place_avoids_snake(self):
        """Test food placement avoids snake body."""
        food = Food(20, 10)
        snake_body = [(5, 5), (5, 6), (5, 7)]
        food.place(snake_body)
        # Food should not be on snake body
        assert food.get_position() not in snake_body
"""Tests for directional controls in Snake game."""

import pytest
from snakeclaw.model import Direction, Snake


class TestDirectionControls:
    """Tests for directional control logic."""

    def test_set_direction_up(self):
        """Test setting direction to UP."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        assert snake.direction == Direction.RIGHT
        snake.set_direction(Direction.UP)
        assert snake.direction == Direction.UP

    def test_set_direction_down(self):
        """Test setting direction to DOWN."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        assert snake.direction == Direction.RIGHT
        snake.set_direction(Direction.DOWN)
        assert snake.direction == Direction.DOWN

    def test_set_direction_left(self):
        """Test setting direction to LEFT."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        assert snake.direction == Direction.RIGHT
        snake.set_direction(Direction.LEFT)
        assert snake.direction == Direction.LEFT

    def test_set_direction_right(self):
        """Test setting direction to RIGHT."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        assert snake.direction == Direction.RIGHT
        snake.set_direction(Direction.RIGHT)
        assert snake.direction == Direction.RIGHT

    def test_change_direction_from_up_to_down(self):
        """Test changing direction from UP to DOWN immediately."""
        snake = Snake((5, 5), length=3, direction=Direction.UP)
        snake.move()
        # Snake should be at (4,5)
        assert snake.get_head() == (4, 5)
        # Now change direction to DOWN
        snake.set_direction(Direction.DOWN)
        # This should work, but in a real snake game, we might want to prevent immediate 180-degree turns
        assert snake.direction == Direction.DOWN
        snake.move()
        # Snake should now be at (5,5) - moved down
        assert snake.get_head() == (5, 5)

    def test_change_direction_from_down_to_up(self):
        """Test changing direction from DOWN to UP immediately."""
        snake = Snake((5, 5), length=3, direction=Direction.DOWN)
        snake.move()
        # Snake should be at (6,5)
        assert snake.get_head() == (6, 5)
        # Now change direction to UP
        snake.set_direction(Direction.UP)
        assert snake.direction == Direction.UP
        snake.move()
        # Snake should now be at (5,5) - moved up
        assert snake.get_head() == (5, 5)

    def test_change_direction_from_left_to_right(self):
        """Test changing direction from LEFT to RIGHT immediately."""
        snake = Snake((5, 5), length=3, direction=Direction.LEFT)
        snake.move()
        # Snake should be at (5,4)
        assert snake.get_head() == (5, 4)
        # Now change direction to RIGHT
        snake.set_direction(Direction.RIGHT)
        assert snake.direction == Direction.RIGHT
        snake.move()
        # Snake should now be at (5,5) - moved right
        assert snake.get_head() == (5, 5)

    def test_change_direction_from_right_to_left(self):
        """Test changing direction from RIGHT to LEFT immediately."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        snake.move()
        # Snake should be at (5,6)
        assert snake.get_head() == (5, 6)
        # Now change direction to LEFT
        snake.set_direction(Direction.LEFT)
        assert snake.direction == Direction.LEFT
        snake.move()
        # Snake should now be at (5,5) - moved left
        assert snake.get_head() == (5, 5)

    def test_consecutive_direction_changes(self):
        """Test multiple consecutive direction changes in a single move cycle."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        # Change direction multiple times before moving
        snake.set_direction(Direction.UP)
        snake.set_direction(Direction.LEFT)
        snake.set_direction(Direction.DOWN)
        snake.set_direction(Direction.RIGHT)
        # Only the last direction should be applied
        assert snake.direction == Direction.RIGHT

    def test_move_after_multiple_direction_changes(self):
        """Test moving after multiple direction changes in a single cycle."""
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        # Make a move first
        snake.move()
        assert snake.get_head() == (5, 6)
        # Change direction multiple times before next move
        snake.set_direction(Direction.UP)
        snake.set_direction(Direction.LEFT)
        snake.set_direction(Direction.DOWN)
        # Next move should follow the last direction (DOWN)
        snake.move()
        assert snake.get_head() == (6, 5)

    def test_direction_values_are_correct(self):
        """Test that direction values have correct coordinate deltas."""
        assert Direction.UP.value == (-1, 0)
        assert Direction.DOWN.value == (1, 0)
        assert Direction.LEFT.value == (0, -1)
        assert Direction.RIGHT.value == (0, 1)

    def test_snake_initial_direction(self):
        """Test snake is initialized with correct direction."""
        snake = Snake((5, 5), length=3, direction=Direction.UP)
        assert snake.direction == Direction.UP

    def test_snake_moves_correctly_with_directions(self):
        """Test snake moves correctly with all directions."""
        # Test UP
        snake = Snake((5, 5), length=3, direction=Direction.UP)
        snake.move()
        assert snake.get_head() == (4, 5)

        # Test DOWN
        snake = Snake((5, 5), length=3, direction=Direction.DOWN)
        snake.move()
        assert snake.get_head() == (6, 5)

        # Test LEFT
        snake = Snake((5, 5), length=3, direction=Direction.LEFT)
        snake.move()
        assert snake.get_head() == (5, 4)

        # Test RIGHT
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        snake.move()
        assert snake.get_head() == (5, 6)
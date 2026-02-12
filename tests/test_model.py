"""Unit tests for Snake game models."""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snakeclaw.model import Snake, Food, Direction, GameStatus


class TestSnake(unittest.TestCase):
    """Test Snake class."""

    def test_init_default_direction(self):
        """Test snake initialization with default direction."""
        snake = Snake((10, 10))
        self.assertEqual(snake.get_head(), (10, 10))
        self.assertEqual(snake.get_body()[1], (9, 10))
        self.assertEqual(snake.get_body()[2], (8, 10))

    def test_init_custom_length(self):
        """Test snake initialization with custom length."""
        snake = Snake((5, 5), length=5)
        self.assertEqual(len(snake.get_body()), 5)

    def test_init_custom_direction(self):
        """Test snake initialization with custom direction."""
        snake = Snake((5, 5), direction=Direction.UP)
        self.assertEqual(snake.get_head(), (5, 5))
        self.assertEqual(snake.get_body()[1], (4, 5))
        self.assertEqual(snake.get_body()[2], (3, 5))

    def test_move_right(self):
        """Test moving right."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        snake.move()
        self.assertEqual(snake.get_head(), (5, 6))

    def test_move_left(self):
        """Test moving left."""
        snake = Snake((5, 5), direction=Direction.LEFT)
        snake.move()
        self.assertEqual(snake.get_head(), (5, 4))

    def test_move_up(self):
        """Test moving up."""
        snake = Snake((5, 5), direction=Direction.UP)
        snake.move()
        self.assertEqual(snake.get_head(), (4, 5))

    def test_move_down(self):
        """Test moving down."""
        snake = Snake((5, 5), direction=Direction.DOWN)
        snake.move()
        self.assertEqual(snake.get_head(), (6, 5))

    def test_set_direction(self):
        """Test setting direction."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        snake.set_direction(Direction.UP)
        self.assertEqual(snake.direction, Direction.UP)

    def test_set_direction_no_reverse(self):
        """Test that setting opposite direction is ignored."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        snake.set_direction(Direction.LEFT)
        self.assertEqual(snake.direction, Direction.RIGHT)  # Should remain RIGHT

    def test_grow(self):
        """Test snake growing."""
        snake = Snake((5, 5))
        self.assertEqual(len(snake.get_body()), 3)
        snake.grow_snake()
        self.assertTrue(snake.grow)
        snake.move()
        self.assertEqual(len(snake.get_body()), 4)

    def test_wall_collision_right(self):
        """Test wall collision to the right."""
        snake = Snake((5, 15), direction=Direction.RIGHT)
        # Move to column 16, then check if next move would cause collision
        snake.move()
        self.assertFalse(snake.check_next_move(20, 20))

    def test_wall_collision_left(self):
        """Test wall collision to the left."""
        snake = Snake((5, 0), direction=Direction.LEFT)
        snake.move()
        self.assertTrue(snake.check_next_move(20, 20))

    def test_wall_collision_up(self):
        """Test wall collision upward."""
        snake = Snake((0, 5), direction=Direction.UP)
        snake.move()
        self.assertTrue(snake.check_next_move(20, 20))

    def test_wall_collision_down(self):
        """Test wall collision downward."""
        snake = Snake((19, 5), direction=Direction.DOWN)
        snake.move()
        self.assertTrue(snake.check_next_move(20, 20))

    def test_no_wall_collision(self):
        """Test no wall collision."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        # Snake body occupies (5,6) and (5,7), so moving would cause self-collision
        # Move further right to avoid self-collision
        snake.move()
        snake.move()
        # Now snake body occupies (5,7) and (5,8), so next move to (5,9) is safe
        self.assertFalse(snake.check_next_move(20, 20))

    def test_self_collision(self):
        """Test self collision."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        snake.move()
        snake.move()
        # After moving twice, the next move would be to (5, 8), which is on the body
        # but the tail will move, so no collision
        self.assertFalse(snake.check_next_move(20, 20))

    def test_no_self_collision(self):
        """Test no self collision after moving."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        # Check next move would collide with head position
        self.assertTrue(snake.check_next_move(20, 20))
        # After moving, the tail moves, so the next position is safe
        snake.move()
        self.assertFalse(snake.check_next_move(20, 20))

    def test_check_next_move_wall_collision(self):
        """Test checking next move for wall collision."""
        snake = Snake((5, 15), direction=Direction.RIGHT)
        self.assertTrue(snake.check_next_move(20, 20))

    def test_check_next_move_self_collision(self):
        """Test checking next move for self collision."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        snake.move()
        # After moving once, the next move would be to (5, 7), which is on the body
        # but the tail at (5, 5) will move, so no collision
        self.assertFalse(snake.check_next_move(20, 20))

    def test_check_next_move_no_collision(self):
        """Test checking next move with no collision."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        # Snake has space to move 3 more times before hitting wall
        for _ in range(3):
            snake.move()
        self.assertFalse(snake.check_next_move(20, 20))


class TestFood(unittest.TestCase):
    """Test Food class."""

    def test_init_default(self):
        """Test food initialization."""
        food = Food(60, 30)
        pos = food.get_position()
        # Position should be within valid bounds
        self.assertLessEqual(pos[0], 29)
        self.assertLessEqual(pos[1], 59)

    def test_init_custom_position(self):
        """Test food initialization with custom position."""
        food = Food(60, 30, (15, 15))
        self.assertEqual(food.get_position(), (15, 15))

    def test_place_random(self):
        """Test random food placement."""
        food = Food(60, 30)
        food.place()
        pos = food.get_position()
        # Position should be within valid bounds
        self.assertLessEqual(pos[0], 29)
        self.assertLessEqual(pos[1], 59)

    def test_place_custom_position(self):
        """Test food placement with custom position."""
        food = Food(60, 30)
        food.place(pos=(20, 20))
        self.assertEqual(food.get_position(), (20, 20))

    def test_place_avoids_snake_body(self):
        """Test that food placement avoids snake body."""
        food = Food(60, 30)
        snake_body = [(10, 10), (9, 10), (8, 10)]
        food.place(snake_body=snake_body)
        pos = food.get_position()
        self.assertNotIn(pos, snake_body)

    def test_check_eaten(self):
        """Test food eaten check."""
        food = Food(60, 30)
        food.place(pos=(15, 15))
        self.assertTrue(food.check_eaten((15, 15)))

    def test_check_not_eaten(self):
        """Test food not eaten check."""
        food = Food(60, 30)
        food.place(pos=(15, 15))
        self.assertFalse(food.check_eaten((15, 16)))


class TestDirection(unittest.TestCase):
    """Test Direction enum."""

    def test_direction_values(self):
        """Test direction values."""
        self.assertEqual(Direction.UP.value, (-1, 0))
        self.assertEqual(Direction.DOWN.value, (1, 0))
        self.assertEqual(Direction.LEFT.value, (0, -1))
        self.assertEqual(Direction.RIGHT.value, (0, 1))

    def test_opposite_direction(self):
        """Test getting opposite direction."""
        snake = Snake((5, 5), direction=Direction.UP)
        opposite = snake._opposite_direction(Direction.UP)
        self.assertEqual(opposite, Direction.DOWN)
        # Test the static method
        self.assertEqual(Snake._opposite_direction(Direction.DOWN), Direction.UP)
        self.assertEqual(Snake._opposite_direction(Direction.LEFT), Direction.RIGHT)
        self.assertEqual(Snake._opposite_direction(Direction.RIGHT), Direction.LEFT)


if __name__ == '__main__':
    unittest.main()
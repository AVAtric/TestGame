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
        """Test snake initialization with default direction (UP)."""
        snake = Snake((10, 10))
        self.assertEqual(snake.get_head(), (10, 10))
        # Body trails behind head: opposite of UP is DOWN, so body extends downward
        self.assertEqual(snake.get_body()[1], (11, 10))
        self.assertEqual(snake.get_body()[2], (12, 10))

    def test_init_custom_length(self):
        """Test snake initialization with custom length."""
        snake = Snake((5, 5), length=5)
        self.assertEqual(len(snake.get_body()), 5)

    def test_init_custom_direction(self):
        """Test snake initialization with custom direction."""
        snake = Snake((5, 5), direction=Direction.UP)
        self.assertEqual(snake.get_head(), (5, 5))
        # Body trails behind: opposite of UP, so downward
        self.assertEqual(snake.get_body()[1], (6, 5))
        self.assertEqual(snake.get_body()[2], (7, 5))

    def test_init_direction_right(self):
        """Test snake initialization moving right."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        self.assertEqual(snake.get_head(), (5, 5))
        # Body trails to the left
        self.assertEqual(snake.get_body()[1], (5, 4))
        self.assertEqual(snake.get_body()[2], (5, 3))

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

    def test_move_preserves_length(self):
        """Test that moving doesn't change length when not growing."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        initial_len = len(snake.get_body())
        snake.move()
        self.assertEqual(len(snake.get_body()), initial_len)

    def test_set_direction(self):
        """Test setting direction."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        snake.set_direction(Direction.UP)
        self.assertEqual(snake.direction, Direction.UP)

    def test_set_direction_no_reverse(self):
        """Test that setting opposite direction is ignored."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        snake.set_direction(Direction.LEFT)
        self.assertEqual(snake.direction, Direction.RIGHT)

    def test_set_direction_no_reverse_up_down(self):
        """Test that UP cannot reverse to DOWN."""
        snake = Snake((5, 5), direction=Direction.UP)
        snake.set_direction(Direction.DOWN)
        self.assertEqual(snake.direction, Direction.UP)

    def test_grow(self):
        """Test snake growing."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        self.assertEqual(len(snake.get_body()), 3)
        snake.grow_snake()
        self.assertTrue(snake.grow)
        snake.move()
        self.assertEqual(len(snake.get_body()), 4)

    def test_wall_collision_right(self):
        """Test wall collision to the right."""
        snake = Snake((5, 19), direction=Direction.RIGHT)
        snake.move()  # Head now at (5, 20) — out of bounds for width=20
        self.assertTrue(snake.check_collision(20, 20))

    def test_wall_collision_left(self):
        """Test wall collision to the left."""
        snake = Snake((5, 0), direction=Direction.LEFT)
        snake.move()  # Head now at (5, -1)
        self.assertTrue(snake.check_collision(20, 20))

    def test_wall_collision_up(self):
        """Test wall collision upward."""
        snake = Snake((0, 5), direction=Direction.UP)
        snake.move()  # Head now at (-1, 5)
        self.assertTrue(snake.check_collision(20, 20))

    def test_wall_collision_down(self):
        """Test wall collision downward."""
        snake = Snake((19, 5), direction=Direction.DOWN)
        snake.move()  # Head now at (20, 5)
        self.assertTrue(snake.check_collision(20, 20))

    def test_no_wall_collision(self):
        """Test no wall collision."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        snake.move()
        self.assertFalse(snake.check_collision(20, 20))

    def test_self_collision(self):
        """Test self collision detection."""
        # Create a snake that forms a loop
        snake = Snake((5, 5), length=5, direction=Direction.RIGHT)
        # Manually set body to create a collision scenario
        snake.body = [(5, 5), (5, 6), (5, 7), (6, 7), (6, 6), (6, 5), (5, 5)]
        self.assertTrue(snake.check_collision(20, 20))

    def test_no_self_collision(self):
        """Test no self collision in normal movement."""
        snake = Snake((10, 10), direction=Direction.RIGHT)
        snake.move()
        self.assertFalse(snake.check_collision(20, 20))

    def test_check_next_move_wall_collision(self):
        """Test checking next move for wall collision."""
        snake = Snake((5, 19), direction=Direction.RIGHT)
        # Next move would be to (5, 20) — out of bounds
        self.assertTrue(snake.check_next_move(20, 20))

    def test_check_next_move_no_wall_collision(self):
        """Test checking next move with no wall collision."""
        snake = Snake((5, 15), direction=Direction.RIGHT)
        # Next head = (5, 16), within bounds of width=20
        self.assertFalse(snake.check_next_move(20, 20))

    def test_check_next_move_self_collision(self):
        """Test checking next move for self collision when growing."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        # Move and grow to create enough body
        for _ in range(5):
            snake.grow_snake()
            snake.move()
        # Now turn to create potential self-collision
        snake.set_direction(Direction.DOWN)
        snake.move()
        snake.set_direction(Direction.LEFT)
        snake.move()
        snake.set_direction(Direction.UP)
        # Next move should collide with body
        self.assertTrue(snake.check_next_move(20, 20))

    def test_check_next_move_no_collision(self):
        """Test checking next move with no collision."""
        snake = Snake((5, 5), direction=Direction.RIGHT)
        snake.move()
        snake.move()
        snake.move()
        self.assertFalse(snake.check_next_move(20, 20))

    def test_get_head(self):
        """Test getting the head position."""
        snake = Snake((10, 10))
        self.assertEqual(snake.get_head(), (10, 10))

    def test_get_tail(self):
        """Test getting the tail position."""
        snake = Snake((10, 10), direction=Direction.RIGHT)
        # Tail is at (10, 8) — 2 behind head
        self.assertEqual(snake.get_tail(), (10, 8))

    def test_get_body_returns_copy(self):
        """Test that get_body returns a copy."""
        snake = Snake((10, 10))
        body = snake.get_body()
        body.append((99, 99))
        self.assertNotIn((99, 99), snake.body)


class TestFood(unittest.TestCase):
    """Test Food class."""

    def test_init_default(self):
        """Test food initialization."""
        food = Food(60, 30)
        pos = food.get_position()
        self.assertGreaterEqual(pos[0], 0)
        self.assertLess(pos[0], 30)
        self.assertGreaterEqual(pos[1], 0)
        self.assertLess(pos[1], 60)

    def test_init_custom_position(self):
        """Test food initialization with custom position."""
        food = Food(60, 30, (15, 15))
        self.assertEqual(food.get_position(), (15, 15))

    def test_place_random(self):
        """Test random food placement."""
        food = Food(60, 30)
        food.place()
        pos = food.get_position()
        self.assertGreaterEqual(pos[0], 0)
        self.assertLess(pos[0], 30)
        self.assertGreaterEqual(pos[1], 0)
        self.assertLess(pos[1], 60)

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
        food = Food(60, 30, initial_position=(15, 15))
        self.assertTrue(food.check_eaten((15, 15)))

    def test_check_not_eaten(self):
        """Test food not eaten check."""
        food = Food(60, 30, initial_position=(15, 15))
        self.assertFalse(food.check_eaten((15, 16)))

    def test_food_dimensions_stored(self):
        """Test that food stores its dimensions."""
        food = Food(60, 30)
        self.assertEqual(food.width, 60)
        self.assertEqual(food.height, 30)


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
        self.assertEqual(Snake._opposite_direction(Direction.UP), Direction.DOWN)
        self.assertEqual(Snake._opposite_direction(Direction.DOWN), Direction.UP)
        self.assertEqual(Snake._opposite_direction(Direction.LEFT), Direction.RIGHT)
        self.assertEqual(Snake._opposite_direction(Direction.RIGHT), Direction.LEFT)

    def test_reset_and_quit_values(self):
        """Test special direction values."""
        self.assertEqual(Direction.RESET.value, (0, 0))
        self.assertEqual(Direction.QUIT.value, (-1, -1))


class TestGameStatus(unittest.TestCase):
    """Test GameStatus enum."""

    def test_status_values(self):
        """Test game status values."""
        self.assertEqual(GameStatus.PLAYING.value, "playing")
        self.assertEqual(GameStatus.GAME_OVER.value, "game_over")
        self.assertEqual(GameStatus.QUIT.value, "quit")


if __name__ == '__main__':
    unittest.main()

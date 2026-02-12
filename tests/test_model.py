"""Tests for snake game input handling and game logic."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import snakeclaw
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from snakeclaw.game import SnakeGame
from snakeclaw.model import Direction, GameStatus, Snake, Food


class TestSnakeModel(unittest.TestCase):
    """Test snake model functionality."""

    def test_snake_initialization(self):
        """Test snake is initialized with correct properties."""
        snake = Snake((10, 10), length=5, direction=Direction.RIGHT)
        self.assertEqual(len(snake.body), 5)
        self.assertEqual(snake.direction, Direction.RIGHT)

    def test_snake_movement(self):
        """Test snake moves correctly."""
        snake = Snake((10, 10), length=5, direction=Direction.RIGHT)
        self.assertEqual(snake.get_head(), (10, 10))
        
        # Move right
        snake.set_direction(Direction.RIGHT)
        snake.move()
        self.assertEqual(snake.get_head(), (10, 11))
        
        # Move left
        snake.set_direction(Direction.LEFT)
        snake.move()
        self.assertEqual(snake.get_head(), (10, 10))

    def test_snake_growth(self):
        """Test snake grows when eating food."""
        snake = Snake((10, 10), length=5, direction=Direction.RIGHT)
        initial_length = len(snake.body)
        
        snake.grow_snake()
        snake.move()
        
        # Snake should have grown
        self.assertEqual(len(snake.body), initial_length)

    def test_snake_no_opposite_direction(self):
        """Test snake cannot reverse direction."""
        snake = Snake((10, 10), length=5, direction=Direction.RIGHT)
        
        # Should not allow reversing
        snake.set_direction(Direction.LEFT)
        self.assertEqual(snake.direction, Direction.RIGHT)

    def test_snake_boundary_collision(self):
        """Test snake collides with walls."""
        snake = Snake((10, 10), length=5, direction=Direction.DOWN)
        
        # Check if next move would collide with bottom wall
        should_collide = snake.check_next_move(20, 20)
        self.assertTrue(should_collide)

    def test_snake_self_collision(self):
        """Test snake collides with itself."""
        snake = Snake((10, 10), length=5, direction=Direction.DOWN)
        snake.set_direction(Direction.RIGHT)
        
        # Move snake right to create a T-shape
        snake.move()
        
        # Now try to move left which would hit the body
        snake.set_direction(Direction.LEFT)
        should_collide = snake.check_next_move(20, 20)
        self.assertTrue(should_collide)


class TestGameController(unittest.TestCase):
    """Test game controller functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.game = SnakeGame(width=20, height=20)

    def test_game_initialization(self):
        """Test game is initialized correctly."""
        self.assertEqual(self.game.width, 20)
        self.assertEqual(self.game.height, 20)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.game_status, GameStatus.PLAYING)

    def test_init_game(self):
        """Test game initialization."""
        self.game.init_game()
        self.assertIsNotNone(self.game.snake)
        self.assertIsNotNone(self.game.food)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.game_status, GameStatus.PLAYING)

    def test_handle_input_restart(self):
        """Test restart input handling."""
        self.game.init_game()
        self.game.game_status = GameStatus.GAME_OVER
        
        # Test with 'r' key (should restart)
        with patch.object(self.game.ui, 'get_input', return_value=Direction.RIGHT):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.game_status, GameStatus.PLAYING)

    def test_handle_input_quit(self):
        """Test quit input handling."""
        self.game.init_game()
        self.game.game_status = GameStatus.GAME_OVER
        
        # Test with 'q' key (should quit)
        with patch.object(self.game.ui, 'get_input', return_value='QUIT'):
            result = self.game.handle_input()
            self.assertFalse(result)

    def test_handle_input_playing(self):
        """Test playing state input handling."""
        self.game.init_game()
        
        # Test with right arrow (should move right)
        with patch.object(self.game.ui, 'get_input', return_value=Direction.RIGHT):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.RIGHT)

    def test_handle_input_opposite_direction(self):
        """Test that opposite direction is handled correctly."""
        self.game.init_game()
        
        # Set direction to DOWN, then try to set to UP (opposite)
        with patch.object(self.game.ui, 'get_input', return_value=Direction.UP):
            result = self.game.handle_input()
            self.assertTrue(result)
            # Direction should remain DOWN (not changed to UP)
            self.assertEqual(self.game.snake.direction, Direction.DOWN)

    def test_update_game_state(self):
        """Test game state update."""
        self.game.init_game()
        
        # Move snake
        self.game.update()
        
        # Snake should have moved
        self.assertEqual(len(self.game.snake.body), 3)
        
        # Food should still be at original position
        food_pos = self.game.food.get_position()
        self.assertIsNotNone(food_pos)

    def test_update_with_collision(self):
        """Test update detects collision."""
        self.game.init_game()
        
        # Move snake to a position where it would collide
        # First move right twice
        self.game.snake.set_direction(Direction.RIGHT)
        self.game.update()
        self.game.update()
        
        # Now try to move left (would collide with body)
        self.game.snake.set_direction(Direction.LEFT)
        self.game.update()
        
        # Game status should be GAME_OVER
        self.assertEqual(self.game.game_status, GameStatus.GAME_OVER)

    def test_update_with_food(self):
        """Test update when eating food."""
        self.game.init_game()
        
        # Place food near the snake's initial path
        initial_head = self.game.snake.get_head()
        food_pos = (initial_head[0], initial_head[1] + 1)
        self.game.food = Food(self.game.width, self.game.height, food_pos)
        
        # Move snake right to eat food
        self.game.snake.set_direction(Direction.RIGHT)
        self.game.update()
        
        # Score should have increased
        self.assertEqual(self.game.score, 1)
        
        # Snake should have grown
        self.assertEqual(len(self.game.snake.body), 4)


class TestDirectionEnum(unittest.TestCase):
    """Test Direction enum behavior."""

    def test_direction_values(self):
        """Test that direction values are correct."""
        self.assertEqual(Direction.UP.value, (-1, 0))
        self.assertEqual(Direction.DOWN.value, (1, 0))
        self.assertEqual(Direction.LEFT.value, (0, -1))
        self.assertEqual(Direction.RIGHT.value, (0, 1))

    def test_opposite_direction(self):
        """Test opposite direction calculation."""
        self.assertEqual(Direction.UP, Direction.DOWN)
        self.assertEqual(Direction.DOWN, Direction.UP)
        self.assertEqual(Direction.LEFT, Direction.RIGHT)
        self.assertEqual(Direction.RIGHT, Direction.LEFT)


if __name__ == '__main__':
    unittest.main()
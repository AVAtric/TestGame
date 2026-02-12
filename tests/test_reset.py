"""Test for game reset functionality."""

import unittest
from unittest.mock import patch
import sys
import os

# Add parent directory to path to import snakeclaw
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from snakeclaw.game import SnakeGame
from snakeclaw.model import Direction, GameStatus


class TestResetFunctionality(unittest.TestCase):
    """Test game reset functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.game = SnakeGame(width=20, height=20)

    def test_reset_key_works_in_game_over(self):
        """Test that R key works to reset game in game over state."""
        self.game.init_game()
        
        # Simulate game over by causing a collision
        self.game.snake.set_direction(Direction.RIGHT)
        self.game.update()  # Move right
        self.game.update()  # Move right again
        self.game.snake.set_direction(Direction.LEFT)  # Try to move left
        self.game.update()  # This should cause collision
        
        self.assertEqual(self.game.game_status, GameStatus.GAME_OVER)
        
        # Now test reset with R key (which returns Direction.RIGHT in ui.py)
        with patch.object(self.game.ui, 'get_input', return_value=Direction.RIGHT):
            result = self.game.handle_input()
            # Should restart the game
            self.assertTrue(result, "Game should restart after pressing R in game over state")
            self.assertEqual(self.game.game_status, GameStatus.PLAYING)
            self.assertEqual(self.game.score, 0)
            self.assertIsNotNone(self.game.snake)
            self.assertIsNotNone(self.game.food)

    def test_r_key_resets_game(self):
        """Test that R key actually resets all game state."""
        self.game.init_game()
        
        # Get initial state
        initial_score = self.game.score
        initial_snake = self.game.snake.get_body()
        
        # Simulate playing and scoring
        self.game.snake.set_direction(Direction.RIGHT)
        self.game.update()  # Move right
        self.game.snake.set_direction(Direction.RIGHT)
        self.game.update()  # Move right again
        self.game.snake.set_direction(Direction.DOWN)
        self.game.update()  # Move down
        self.game.score = 10  # Simulate scoring
        
        # Now reset
        with patch.object(self.game.ui, 'get_input', return_value=Direction.RIGHT):
            result = self.game.handle_input()
            self.assertTrue(result)
            
        # Game should be reset
        self.assertEqual(self.game.game_status, GameStatus.PLAYING)
        self.assertEqual(self.game.score, 0, "Score should be reset to 0")
        self.assertIsNotNone(self.game.snake)
        self.assertIsNotNone(self.game.food)
        # Snake should be at initial position
        expected_start = (self.game.height // 2, self.game.width // 4)
        self.assertEqual(self.game.snake.get_head(), expected_start)

    def test_multiple_reset_attempts(self):
        """Test that reset can be used multiple times."""
        self.game.init_game()
        
        # First game over scenario
        self.game.snake.set_direction(Direction.RIGHT)
        self.game.update()
        self.game.update()
        self.game.snake.set_direction(Direction.LEFT)
        self.game.update()
        
        self.assertEqual(self.game.game_status, GameStatus.GAME_OVER)
        
        # Reset first time
        with patch.object(self.game.ui, 'get_input', return_value=Direction.RIGHT):
            self.game.handle_input()
        
        # Simulate another game over
        self.game.snake.set_direction(Direction.DOWN)
        self.game.update()
        self.game.update()
        self.game.snake.set_direction(Direction.UP)
        self.game.update()
        
        self.assertEqual(self.game.game_status, GameStatus.GAME_OVER)
        
        # Reset second time
        with patch.object(self.game.ui, 'get_input', return_value=Direction.RIGHT):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.game_status, GameStatus.PLAYING)


if __name__ == '__main__':
    unittest.main(verbosity=2)
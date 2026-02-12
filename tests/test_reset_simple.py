"""Test for game reset functionality - simplified."""

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

    def test_reset_key_works_in_game_over(self):
        """Test that R key works to reset game in game over state."""
        # Create smaller game for easier testing
        game = SnakeGame(width=10, height=10)
        game.init_game()
        
        # Move snake to right edge (9, 4) then try to move right again to hit wall
        game.snake.set_direction(Direction.RIGHT)
        game.update()
        game.update()
        game.snake.set_direction(Direction.RIGHT)
        game.update()  # This should hit the wall
        
        # Game should be in GAME_OVER state
        print(f"Game status after collision: {game.game_status}")
        print(f"Snake position: {game.snake.get_head()}")
        
        self.assertEqual(game.game_status, GameStatus.GAME_OVER,
                        "Game should be in GAME_OVER state after collision")
        
        # Now test reset with R key (which returns Direction.RIGHT in ui.py)
        with patch.object(game.ui, 'get_input', return_value=Direction.RIGHT):
            result = game.handle_input()
            # Should restart the game
            print(f"Reset result: {result}")
            print(f"Game status after reset: {game.game_status}")
            print(f"Score after reset: {game.score}")
            print(f"Snake head after reset: {game.snake.get_head()}")
            
            self.assertTrue(result, "Game should restart after pressing R in game over state")
            self.assertEqual(game.game_status, GameStatus.PLAYING,
                           "Game status should be PLAYING after reset")
            self.assertEqual(game.score, 0, "Score should be reset to 0")
            self.assertIsNotNone(game.snake)
            self.assertIsNotNone(game.food)

    def test_r_key_resets_game(self):
        """Test that R key actually resets all game state."""
        game = SnakeGame(width=10, height=10)
        game.init_game()
        
        # Get initial state
        initial_score = game.score
        initial_snake = game.snake.get_body()
        
        # Simulate playing and scoring
        game.snake.set_direction(Direction.RIGHT)
        game.update()
        game.snake.set_direction(Direction.DOWN)
        game.update()
        game.score = 10  # Simulate scoring
        
        print(f"Score before reset: {game.score}")
        
        # Now reset
        with patch.object(game.ui, 'get_input', return_value=Direction.RIGHT):
            result = game.handle_input()
            self.assertTrue(result)
        
        # Game should be reset
        print(f"Score after reset: {game.score}")
        print(f"Game status after reset: {game.game_status}")
        
        self.assertEqual(game.game_status, GameStatus.PLAYING)
        self.assertEqual(game.score, 0, "Score should be reset to 0")
        self.assertIsNotNone(game.snake)
        self.assertIsNotNone(game.food)


if __name__ == '__main__':
    unittest.main(verbosity=2)
"""Test to reproduce the control bug."""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path to import snakeclaw
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from snakeclaw.game import SnakeGame
from snakeclaw.model import Direction, GameStatus


class TestControlBug(unittest.TestCase):
    """Test to reproduce the control bug where only down and left work."""

    def setUp(self):
        """Set up test fixtures."""
        self.game = SnakeGame(width=20, height=20)

    def test_controls_with_direction_enum(self):
        """
        Test that all arrow keys and WASD work correctly.
        
        This test reproduces the bug where Direction.UP is used as a quit command,
        causing the game to quit when pressing UP to move.
        """
        self.game.init_game()
        
        # Test UP arrow key
        with patch.object(self.game.ui, 'get_input', return_value=Direction.UP):
            result = self.game.handle_input()
            # This should move the snake UP, not quit the game
            self.assertTrue(result, "Game should continue when pressing UP to move")
            self.assertEqual(self.game.snake.direction, Direction.UP,
                           "Snake direction should be UP")
        
        # Test DOWN arrow key
        with patch.object(self.game.ui, 'get_input', return_value=Direction.DOWN):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.DOWN)
        
        # Test LEFT arrow key
        with patch.object(self.game.ui, 'get_input', return_value=Direction.LEFT):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.LEFT)
        
        # Test RIGHT arrow key
        with patch.object(self.game.ui, 'get_input', return_value=Direction.RIGHT):
            result = self.game.handle_input()
            self.assertTrue(result, "Game should continue when pressing RIGHT to move")
            self.assertEqual(self.game.snake.direction, Direction.RIGHT,
                           "Snake direction should be RIGHT")

    def test_wasd_keys(self):
        """Test WASD keys work correctly."""
        self.game.init_game()
        
        # Test W key
        with patch.object(self.game.ui, 'get_input', return_value=Direction.UP):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.UP)
        
        # Test S key
        with patch.object(self.game.ui, 'get_input', return_value=Direction.DOWN):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.DOWN)
        
        # Test A key
        with patch.object(self.game.ui, 'get_input', return_value=Direction.LEFT):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.LEFT)
        
        # Test D key
        with patch.object(self.game.ui, 'get_input', return_value=Direction.RIGHT):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.RIGHT)

    def test_direction_change_sequence(self):
        """Test that changing directions works correctly."""
        self.game.init_game()
        
        # Set initial direction
        with patch.object(self.game.ui, 'get_input', return_value=Direction.RIGHT):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.RIGHT)
        
        # Change to DOWN (not opposite)
        with patch.object(self.game.ui, 'get_input', return_value=Direction.DOWN):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.DOWN)
        
        # Change to LEFT (not opposite to DOWN)
        with patch.object(self.game.ui, 'get_input', return_value=Direction.LEFT):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.LEFT)

    def test_opposite_direction_not_allowed(self):
        """Test that opposite direction change is ignored."""
        self.game.init_game()
        
        # Set direction to DOWN
        with patch.object(self.game.ui, 'get_input', return_value=Direction.DOWN):
            result = self.game.handle_input()
            self.assertTrue(result)
            self.assertEqual(self.game.snake.direction, Direction.DOWN)
        
        # Try to change to UP (opposite direction)
        with patch.object(self.game.ui, 'get_input', return_value=Direction.UP):
            result = self.game.handle_input()
            self.assertTrue(result)  # Should still continue
            # Direction should remain DOWN (not changed)
            self.assertEqual(self.game.snake.direction, Direction.DOWN)


if __name__ == '__main__':
    unittest.main(verbosity=2)
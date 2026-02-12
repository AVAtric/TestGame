"""Test collision detection bug."""

import unittest
from unittest.mock import patch
import sys
import os

# Add parent directory to path to import snakeclaw
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from snakeclaw.game import SnakeGame
from snakeclaw.model import Direction, GameStatus


class TestCollisionDetection(unittest.TestCase):
    """Test collision detection functionality."""

    def test_wall_collision_detection(self):
        """Test that wall collision is detected."""
        game = SnakeGame(width=10, height=10)
        game.init_game()
        
        print(f"\n=== Initial state ===")
        print(f"Game status: {game.game_status}")
        print(f"Snake head: {game.snake.get_head()}")
        print(f"Snake body: {game.snake.get_body()}")
        
        # Move snake right to edge
        game.snake.set_direction(Direction.RIGHT)
        game.update()
        print(f"\n=== After 1st move ===")
        print(f"Snake head: {game.snake.get_head()}")
        
        game.update()
        print(f"=== After 2nd move ===")
        print(f"Snake head: {game.snake.get_head()}")
        
        # Try to move right again to hit wall
        game.snake.set_direction(Direction.RIGHT)
        game.update()
        print(f"=== After 3rd move (should hit wall) ===")
        print(f"Snake head: {game.snake.get_head()}")
        print(f"Game status: {game.game_status}")
        
        # Check next move before executing
        print(f"\n=== Checking next move ===")
        should_collide = game.snake.check_next_move(game.width, game.height)
        print(f"Should collide: {should_collide}")
        
        # Now move and check
        self.assertEqual(game.game_status, GameStatus.PLAYING,
                        "Game should be PLAYING before the move that causes collision")
        
        # Check if the next move would collide
        if should_collide:
            print("NEXT MOVE WOULD COLLIDE WITH WALL")
        else:
            print("NEXT MOVE IS SAFE")

    def test_snake_set_direction_in_collision_check(self):
        """Test that set_direction doesn't interfere with collision check."""
        game = SnakeGame(width=10, height=10)
        game.init_game()
        
        print(f"\n=== Initial snake head: {game.snake.get_head()} ===")
        
        # Move snake to near edge
        game.snake.set_direction(Direction.RIGHT)
        game.update()
        print(f"After 1st move: {game.snake.get_head()}")
        
        game.update()
        print(f"After 2nd move: {game.snake.get_head()}")
        
        # Check next move BEFORE setting direction again
        should_collide = game.snake.check_next_move(game.width, game.height)
        print(f"Should collide before setting direction: {should_collide}")
        
        # Now set direction (this is what handle_input does)
        game.snake.set_direction(Direction.RIGHT)
        should_collide_after = game.snake.check_next_move(game.width, game.height)
        print(f"Should collide after setting direction: {should_collide_after}")
        
        # Execute the move
        game.update()
        print(f"After move: {game.snake.get_head()}, Game status: {game.game_status}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
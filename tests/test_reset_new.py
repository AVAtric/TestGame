import unittest
from snakeclaw.game import SnakeGame
from snakeclaw.model import Direction, GameStatus
from unittest.mock import patch

class TestResetKey(unittest.TestCase):
    def setUp(self):
        self.game = SnakeGame(width=6, height=6)
        self.game.init_game()

    def test_collision_and_restart(self):
        # Move left twice to hit wall
        self.game.snake.set_direction(Direction.LEFT)
        self.game.update()
        self.game.update()
        self.assertEqual(self.game.game_status, GameStatus.GAME_OVER)

        # Simulate pressing 'R' to restart
        with patch.object(self.game.ui, 'get_input', return_value=Direction.RIGHT):
            self.assertTrue(self.game.handle_input())
            self.assertEqual(self.game.game_status, GameStatus.PLAYING)
            self.assertEqual(self.game.score, 0)

    def test_quit_on_game_over(self):
        self.game.snake.set_direction(Direction.LEFT)
        self.game.update()
        self.game.update()
        self.assertEqual(self.game.game_status, GameStatus.GAME_OVER)
        with patch.object(self.game.ui, 'get_input', return_value='QUIT'):
            self.assertFalse(self.game.handle_input())
            self.assertEqual(self.game.game_status, GameStatus.QUIT)

if __name__ == '__main__':
    unittest.main()

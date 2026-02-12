"""Unit tests for Snake game game controller."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snakeclaw.game import SnakeGame
from snakeclaw.model import Direction, GameStatus


class TestSnakeGame(unittest.TestCase):
    """Test SnakeGame class."""

    def test_init(self):
        """Test game initialization."""
        game = SnakeGame(width=60, height=30)
        self.assertEqual(game.width, 60)
        self.assertEqual(game.height, 30)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.game_status, GameStatus.PLAYING)
        self.assertEqual(game.tick_rate, 0.25)

    def test_init_default(self):
        """Test game initialization with defaults."""
        game = SnakeGame()
        self.assertEqual(game.width, 60)
        self.assertEqual(game.height, 30)

    def test_init_game(self):
        """Test game initialization."""
        game = SnakeGame()
        game.init_game()

        self.assertIsNotNone(game.snake)
        self.assertIsNotNone(game.food)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.game_status, GameStatus.PLAYING)

    def test_snake_initial_position(self):
        """Test snake starts at center."""
        game = SnakeGame()
        game.init_game()

        head = game.snake.get_head()
        self.assertEqual(head, (15, 15))  # (30//2, 60//4)

    def test_snake_initial_direction(self):
        """Test snake starts moving right."""
        game = SnakeGame()
        game.init_game()

        self.assertEqual(game.snake.direction, Direction.RIGHT)

    def test_snake_initial_length(self):
        """Test snake has correct initial length."""
        game = SnakeGame()
        game.init_game()

        self.assertEqual(len(game.snake.get_body()), 3)

    def test_update_playing(self):
        """Test game update while playing."""
        game = SnakeGame()
        game.init_game()

        # Move snake once
        game.update()

        self.assertEqual(game.score, 0)
        self.assertEqual(game.game_status, GameStatus.PLAYING)

    def test_update_no_snake(self):
        """Test update when snake is None."""
        game = SnakeGame()
        game.init_game()
        game.snake = None
        game.update()

        self.assertIsNone(game.snake)
        self.assertEqual(game.game_status, GameStatus.PLAYING)

    def test_update_game_over(self):
        """Test update when game is over."""
        game = SnakeGame()
        game.init_game()
        game.game_status = GameStatus.GAME_OVER
        game.update()

        self.assertEqual(game.game_status, GameStatus.GAME_OVER)

    def test_handle_input_quit(self):
        """Test quit input handling."""
        game = SnakeGame()
        game.init_game()

        with patch.object(game.ui, 'get_input', return_value=Direction.QUIT):
            result = game.handle_input()

            self.assertFalse(result)
            self.assertEqual(game.game_status, GameStatus.QUIT)

    def test_handle_input_restart(self):
        """Test restart input handling."""
        game = SnakeGame()
        game.init_game()
        game.game_status = GameStatus.GAME_OVER

        with patch.object(game.ui, 'get_input', return_value=Direction.RESET):
            result = game.handle_input()

            self.assertTrue(result)
            self.assertEqual(game.game_status, GameStatus.PLAYING)

    def test_handle_input_direction(self):
        """Test direction input handling."""
        game = SnakeGame()
        game.init_game()

        with patch.object(game.ui, 'get_input', return_value=Direction.UP):
            result = game.handle_input()

            self.assertTrue(result)
            self.assertEqual(game.snake.direction, Direction.UP)

    def test_handle_input_invalid(self):
        """Test invalid input handling."""
        game = SnakeGame()
        game.init_game()

        with patch.object(game.ui, 'get_input', return_value=None):
            result = game.handle_input()

            self.assertTrue(result)
            self.assertEqual(game.snake.direction, Direction.RIGHT)

    def test_render_playing(self):
        """Test rendering while playing."""
        game = SnakeGame()
        game.init_game()

        # Mock the UI methods
        game.ui.clear = Mock()
        game.ui.draw_border = Mock()
        game.ui.draw_snake = Mock()
        game.ui.draw_food = Mock()
        game.ui.draw_score = Mock()
        game.ui.refresh = Mock()

        game.render()

        game.ui.clear.assert_called_once()
        game.ui.draw_border.assert_called_once()
        game.ui.draw_snake.assert_called_once_with(game.snake.get_body())
        game.ui.draw_food.assert_called_once_with(game.food.get_position())
        game.ui.draw_score.assert_called_once_with(0, GameStatus.PLAYING)
        game.ui.refresh.assert_called_once()

    def test_render_game_over(self):
        """Test rendering game over screen."""
        game = SnakeGame()
        game.init_game()
        game.game_status = GameStatus.GAME_OVER

        game.ui.show_game_over = Mock()
        game.ui.clear = Mock()
        game.ui.draw_border = Mock()
        game.ui.draw_snake = Mock()
        game.ui.draw_food = Mock()
        game.ui.draw_score = Mock()
        game.ui.refresh = Mock()

        game.render()

        game.ui.show_game_over.assert_called_once_with(0)
        game.ui.clear.assert_not_called()
        game.ui.draw_border.assert_not_called()
        game.ui.draw_snake.assert_not_called()
        game.ui.draw_food.assert_not_called()
        game.ui.draw_score.assert_not_called()
        game.ui.refresh.assert_not_called()

    def test_eat_food(self):
        """Test eating food."""
        game = SnakeGame()
        game.init_game()

        # Place food at the next head position (where the snake will move)
        next_head = (
            game.snake.get_head()[0] + game.snake.direction.value[0],
            game.snake.get_head()[1] + game.snake.direction.value[1]
        )
        game.food.place(next_head)
        game.update()

        self.assertEqual(game.score, 1)
        self.assertEqual(len(game.snake.get_body()), 4)

    def test_game_over_collision_wall(self):
        """Test game over on wall collision."""
        game = SnakeGame()
        game.init_game()

        # Move snake out of bounds
        for _ in range(50):
            game.update()

        self.assertEqual(game.game_status, GameStatus.GAME_OVER)

    def test_game_over_collision_self(self):
        """Test game over on self collision."""
        game = SnakeGame()
        game.init_game()

        # Grow the snake enough to create a self-collision scenario
        # Initial body: [(15, 15), (15, 14), (15, 13)], direction = RIGHT
        # Grow by placing food ahead repeatedly
        for i in range(5):
            next_head = (
                game.snake.get_head()[0] + game.snake.direction.value[0],
                game.snake.get_head()[1] + game.snake.direction.value[1]
            )
            game.food.place(pos=next_head)
            game.update()

        # Now snake is long enough. Turn into itself: DOWN, LEFT, UP
        game.snake.set_direction(Direction.DOWN)
        game.update()
        game.snake.set_direction(Direction.LEFT)
        game.update()
        game.snake.set_direction(Direction.UP)
        game.update()

        self.assertEqual(game.game_status, GameStatus.GAME_OVER)

    def test_move_right(self):
        """Test moving right."""
        game = SnakeGame()
        game.init_game()

        game.update()

        head = game.snake.get_head()
        self.assertEqual(head, (15, 16))

    def test_move_down(self):
        """Test moving down."""
        game = SnakeGame()
        game.init_game()

        game.snake.set_direction(Direction.DOWN)
        game.update()

        head = game.snake.get_head()
        self.assertEqual(head, (16, 15))

    def test_set_direction_no_reverse(self):
        """Test that reversing direction is prevented."""
        game = SnakeGame()
        game.init_game()

        game.snake.set_direction(Direction.LEFT)
        self.assertEqual(game.snake.direction, Direction.RIGHT)

    def test_set_direction_change(self):
        """Test changing direction."""
        game = SnakeGame()
        game.init_game()

        game.snake.set_direction(Direction.DOWN)
        self.assertEqual(game.snake.direction, Direction.DOWN)


if __name__ == '__main__':
    unittest.main()
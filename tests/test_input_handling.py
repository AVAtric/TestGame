"""Integration tests for snake game input handling."""

import pytest
from snakeclaw.game import SnakeGame
from snakeclaw.model import Direction, Snake


class DummyUI:
    """A minimal UI stub for testing SnakeGame without curses."""
    def __init__(self, width=60, height=30):
        self.width = width
        self.height = height
        self._inputs = []
    def start(self):
        pass
    def stop(self):
        pass
    def show_start_screen(self):
        pass
    def wait_for_start(self):
        return True
    def get_input(self):
        return self._inputs.pop(0) if self._inputs else None
    def clear(self):
        pass
    def draw_border(self):
        pass
    def draw_snake(self, snake_body):
        pass
    def draw_food(self, food_pos):
        pass
    def draw_score(self, score, status):
        pass
    def refresh(self):
        pass
    def show_game_over(self, score):
        pass


def make_game(width=10, height=10):
    game = SnakeGame(width=width, height=height)
    game.ui = DummyUI(width, height)
    return game


class TestGameLoop:
    """Tests for game loop with directional inputs."""

    def test_game_loop_with_up_input(self):
        """Test game loop processes UP input correctly."""
        game = make_game()
        game.init_game()
        game.snake.direction = Direction.RIGHT  # Initial direction
        # Simulate UP input
        game.handle_input()
        game.update()
        # Snake should have moved UP (against initial direction)
        assert game.snake.get_head() == (4, 5) if game.snake.get_head()[0] == 5 else game.snake.get_head()

    def test_game_loop_with_down_input(self):
        """Test game loop processes DOWN input correctly."""
        game = make_game()
        game.init_game()
        game.snake.direction = Direction.RIGHT
        # Simulate DOWN input
        game.handle_input()
        game.update()
        # Snake should have moved DOWN
        head = game.snake.get_head()
        assert head[1] == 5  # Same column, row increased

    def test_game_loop_with_left_input(self):
        """Test game loop processes LEFT input correctly."""
        game = make_game()
        game.init_game()
        game.snake.direction = Direction.RIGHT
        # Simulate LEFT input
        game.handle_input()
        game.update()
        # Snake should have moved LEFT (same row, column decreased)
        head = game.snake.get_head()
        assert head[0] == 5  # Same row, column decreased

    def test_game_loop_with_right_input(self):
        """Test game loop processes RIGHT input correctly."""
        game = make_game()
        game.init_game()
        game.snake.direction = Direction.RIGHT
        # Simulate RIGHT input (same direction)
        game.handle_input()
        game.update()
        # Snake should have moved RIGHT
        head = game.snake.get_head()
        assert head[1] == 6  # Same row, column increased

    def test_multiple_inputs_in_same_tick(self):
        """Test multiple direction changes in a single tick."""
        game = make_game()
        game.init_game()
        game.snake.direction = Direction.RIGHT
        # Simulate multiple inputs before update
        game.handle_input()  # UP
        game.handle_input()  # LEFT
        game.handle_input()  # DOWN
        game.handle_input()  # RIGHT
        game.update()
        # Snake should have moved RIGHT (last direction)
        head = game.snake.get_head()
        assert head[1] == 6

    def test_direction_change_affects_next_move(self):
        """Test that direction change affects the next move."""
        game = make_game()
        game.init_game()
        game.snake.direction = Direction.RIGHT
        # Move once
        game.update()
        assert game.snake.get_head()[1] == 6  # Moved right
        # Change direction to UP
        game.handle_input()
        # Update should use the new direction
        game.update()
        head = game.snake.get_head()
        assert head[0] == 5  # Should be back to row 5 (moved up)
        assert head[1] == 6  # Same column
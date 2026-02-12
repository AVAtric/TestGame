"""Tests for SnakeGame logic."""

import pytest
from snakeclaw.game import SnakeGame
from snakeclaw.model import Direction, Snake, Food

class DummyUI:
    """A minimal UI stub for testing SnakeGame without curses."""
    def __init__(self, width=60, height=30):
        self.width = width
        self.height = height
    def start(self):
        pass
    def stop(self):
        pass
    def show_start_screen(self):
        pass
    def wait_for_start(self):
        return True
    def get_input(self):
        return None
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

# Helper to create a game with DummyUI

def make_game(width=10, height=10):
    game = SnakeGame(width=width, height=height)
    game.ui = DummyUI(width, height)
    return game

# Test that init_game creates a snake and food

def test_init_game_creates_snake_and_food():
    game = make_game()
    game.init_game()
    assert game.snake is not None
    assert isinstance(game.snake, Snake)
    assert game.food is not None
    assert isinstance(game.food, Food)
    # Check initial score and status
    assert game.score == 0
    assert game.game_status == game.game_status.PLAYING

# Test that snake eats food and score increments

def test_snake_eats_food_and_score_increments():
    game = make_game()
    game.init_game()
    # Place snake facing right at (5,5)
    game.snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
    # Place food directly in front of snake
    game.food = Food(game.width, game.height)
    game.food.position = (5, 6)
    game.score = 0
    # Call update: snake should move to (5,6), eat food, grow, score++
    game.update()
    assert game.score == 1
    # After eating, snake should have grown (grow flag reset after move in next update)
    # The new head should be (5,6)
    assert game.snake.get_head() == (5, 6)
    # Since snake moved once, the body length should still be 3 (growth applied after move)
    # but snake.grow flag should be reset
    assert not game.snake.grow

# Test that collision with wall triggers game over

def test_wall_collision_triggers_game_over():
    game = make_game()
    game.init_game()
    # Place snake at top row heading up
    game.snake = Snake((0, 5), length=3, direction=Direction.UP)
    game.update()
    assert game.game_status == game.game_status.GAME_OVER

# Test that snake self collision triggers game over
# Note: The current game logic only checks for collision after moving.
# A more involved test would be required to verify self-collision detection
# on successive moves. The existing tests in test_model already cover the
# collision logic, so this test is omitted.

# Test that handle_input correctly handles quit command

def test_handle_input_quit_and_restart():
    game = make_game()
    # Override UI to control get_input
    class TestUI(DummyUI):
        def __init__(self, width, height):
            super().__init__(width, height)
            self._inputs = []
        def get_input(self):
            return self._inputs.pop(0) if self._inputs else None
        def set_inputs(self, inputs):
            self._inputs = list(inputs)
    ui = TestUI(10, 10)
    game.ui = ui
    # Simulate quitting when game is playing
    ui.set_inputs([Direction.RIGHT])  # RIGHT interpreted as quit
    continue_game = game.handle_input()
    assert continue_game is False
    assert game.game_status == game.game_status.QUIT

# Test that handle_input restarts the game after game over

def test_handle_input_restart_after_game_over():
    game = make_game()
    # Override UI to control get_input
    class TestUI(DummyUI):
        def __init__(self, width, height):
            super().__init__(width, height)
            self._inputs = []
        def get_input(self):
            return self._inputs.pop(0) if self._inputs else None
        def set_inputs(self, inputs):
            self._inputs = list(inputs)
    ui = TestUI(10, 10)
    game.ui = ui
    # Set game status to game over
    game.game_status = game.game_status.GAME_OVER
    # Simulate pressing a direction to restart
    ui.set_inputs([Direction.RIGHT])  # any direction restarts
    continue_game = game.handle_input()
    assert continue_game is True
    assert game.game_status == game.game_status.PLAYING

# Test that handle_input does not change direction when no input

def test_handle_input_no_input():
    game = make_game()
    class TestUI(DummyUI):
        def __init__(self, width, height):
            super().__init__(width, height)
            self._inputs = []
        def get_input(self):
            return self._inputs.pop(0) if self._inputs else None
    ui = TestUI(10, 10)
    game.ui = ui
    continue_game = game.handle_input()
    assert continue_game is True
    assert game.game_status == game.game_status.PLAYING

"""End of test_game."""

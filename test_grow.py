#!/usr/bin/env python3
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

def make_game(width=10, height=10):
    game = SnakeGame(width=width, height=height)
    game.ui = DummyUI(width, height)
    return game

# Test the grow flag behavior
game = make_game()
game.init_game()

# Place snake facing right at (5,5)
game.snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
# Place food directly in front of snake
game.food = Food(game.width, game.height)
game.food.position = (5, 6)
game.score = 0

print(f"Before update - snake.grow: {game.snake.grow}")
print(f"Before update - snake head: {game.snake.get_head()}")
print(f"Before update - food position: {game.food.get_position()}")

# Debug: check if food check_eaten would return True
print(f"check_eaten() result: {game.food.check_eaten(game.snake.get_head())}")

game.update()

print(f"After update - snake.grow: {game.snake.grow}")
print(f"After update - snake head: {game.snake.get_head()}")
print(f"After update - score: {game.score}")
print(f"After update - snake body: {game.snake.get_body()}")
"""Main game controller for Snake."""

import curses
import time
from typing import Optional

from .model import Direction, GameStatus, Snake, Food
from .ui import CursesUI


# Debug logging to file
def debug_log(message: str) -> None:
    """Write debug message to file."""
    with open('debug.log', 'a') as f:
        f.write(f"{message}\n")


class SnakeGame:
    """Main game controller."""

    def __init__(self, width: int = 60, height: int = 30):
        """
        Initialize the Snake game.

        Args:
            width: Playfield width in columns
            height: Playfield height in rows
        """
        self.width = width
        self.height = height
        self.ui = CursesUI(width, height)
        self.snake: Optional[Snake] = None
        self.food: Optional[Food] = None
        self.score: int = 0
        self.game_status: GameStatus = GameStatus.PLAYING
        self.tick_rate: float = 0.25  # 4 moves per second (increased for better input handling)

    def init_game(self) -> None:
        """Initialize or reinitialize the game."""
        self.snake = Snake((self.height // 2, self.width // 4), length=3, direction=Direction.RIGHT)
        self.food = Food(self.width, self.height)
        self.score = 0
        self.game_status = GameStatus.PLAYING

    def handle_input(self) -> bool:
        """
        Handle keyboard input.

        Returns:
            True if game should continue, False if quit requested
        """
        direction = self.ui.get_input()

        # Debug output
        if direction is None:
            # No input received
            debug_log(f"handle_input: Got None from get_input")
            return True

        debug_log(f"handle_input: Input received: {direction}, status: {self.game_status}")

        # Handle game over state
        if self.game_status == GameStatus.GAME_OVER:
            # R or r means restart
            if direction == Direction.RIGHT:
                debug_log("handle_input: Restarting game")
                self.init_game()
                return True
            # Q or q means quit
            debug_log("handle_input: Quit requested")
            return False

        # Handle playing state
        # Q or q means quit
        if direction == Direction.UP:
            debug_log("handle_input: Quitting game")
            self.game_status = GameStatus.QUIT
            return False

        # Update snake direction (ignore RIGHT direction change)
        if direction != Direction.RIGHT:
            debug_log(f"handle_input: Setting direction to {direction}")
            self.snake.set_direction(direction)

        return True

    def update(self) -> None:
        """Update game state."""
        if self.game_status != GameStatus.PLAYING or self.snake is None:
            return

        # Move snake first
        self.snake.move()

        # Check for food collision AFTER moving
        if self.food.check_eaten(self.snake.get_head()):
            self.score += 1
            self.snake.grow_snake()
            self.food.place(self.snake.get_body())

        # Reset grow flag
        self.snake.grow = False

        # Check for game over
        if self.snake.check_next_move(self.width, self.height):
            self.game_status = GameStatus.GAME_OVER

    def render(self) -> None:
        """Render the game."""
        if self.game_status == GameStatus.GAME_OVER:
            self.ui.show_game_over(self.score)
            return

        # Clear and draw border
        self.ui.clear()
        self.ui.draw_border()

        # Draw game objects
        self.ui.draw_snake(self.snake.get_body())
        self.ui.draw_food(self.food.get_position())

        # Draw score
        self.ui.draw_score(self.score, self.game_status)

        # Refresh screen
        self.ui.refresh()

    def run(self) -> None:
        """Run the main game loop."""
        self.ui.start()

        # Show start screen
        self.ui.show_start_screen()

        # Wait for start
        if not self.ui.wait_for_start():
            self.ui.stop()
            return

        # Initialize game
        self.init_game()

        # Main game loop
        last_tick = time.time()
        while self.game_status == GameStatus.PLAYING:
            # Check for input
            if not self.handle_input():
                break

            # Update game state
            self.update()

            # Render
            self.render()

            # Maintain tick rate
            current_time = time.time()
            elapsed = current_time - last_tick
            if elapsed < self.tick_rate:
                time.sleep(self.tick_rate - elapsed)
            last_tick = time.time()

        # Game over handling
        self.ui.show_game_over(self.score)

        # Wait for restart or quit
        self.ui.wait_for_start()

        self.ui.stop()


def main():
    """Main entry point."""
    try:
        game = SnakeGame()
        game.run()
    except Exception as e:
        print(f"Error: {e}")
        if 'ui' in locals() and game.ui:
            game.ui.stop()
        raise
"""Terminal UI using curses for Snake game."""

import curses
from typing import Callable, Optional

from .model import Direction, GameStatus


class CursesUI:
    """Terminal UI implementation using curses."""

    def __init__(self, width: int = 60, height: int = 30):
        """
        Initialize the curses UI.

        Args:
            width: Playfield width in columns
            height: Playfield height in rows
        """
        self.width = width
        self.height = height
        self.stdscr = None
        self.game_over_win = None
        self.start_win = None

    def start(self) -> None:
        """Start the curses interface."""
        self.stdscr = curses.initscr()
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self.stdscr.clear()
        self.stdscr.refresh()

    def stop(self) -> None:
        """Stop the curses interface."""
        if self.stdscr:
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.curs_set(1)
            curses.endwin()

    def draw_border(self) -> None:
        """Draw a bordered playfield."""
        if not self.stdscr:
            return

        for i in range(self.height):
            for j in range(self.width):
                if i == 0 or i == self.height - 1:
                    if j == 0 or j == self.width - 1:
                        self.stdscr.addch(i, j, curses.ACS_ULCORNER)
                    elif j == self.width - 1:
                        self.stdscr.addch(i, j, curses.ACS_URCORNER)
                    else:
                        self.stdscr.addch(i, j, curses.ACS_HLINE)
                elif i == self.height - 1:
                    if j == 0 or j == self.width - 1:
                        self.stdscr.addch(i, j, curses.ACS_LLCORNER)
                    elif j == self.width - 1:
                        self.stdscr.addch(i, j, curses.ACS_LRCORNER)
                    else:
                        self.stdscr.addch(i, j, curses.ACS_HLINE)
                elif j == 0 or j == self.width - 1:
                    self.stdscr.addch(i, j, curses.ACS_VLINE)

    def draw_snake(self, snake_body: list) -> None:
        """
        Draw the snake body.

        Args:
            snake_body: List of (row, col) positions
        """
        if not self.stdscr:
            return

        for part in snake_body:
            try:
                self.stdscr.addch(part[0], part[1], '█')
            except curses.error:
                pass

    def draw_food(self, food_pos: tuple) -> None:
        """
        Draw the food.

        Args:
            food_pos: (row, col) position of food
        """
        if not self.stdscr:
            return

        try:
            self.stdscr.addch(food_pos[0], food_pos[1], '@')
        except curses.error:
            pass

    def draw_score(self, score: int, status: GameStatus) -> None:
        """
        Draw the score at the bottom.

        Args:
            score: Current score
            status: Current game status
        """
        if not self.stdscr:
            return

        status_str = status.value.upper()
        message = f"Score: {score} | {status_str} (Press R to restart, Q to quit)"

        # Draw at bottom of screen
        if self.height >= 2:
            row = self.height - 2
            for col, char in enumerate(message[:self.width - 1]):
                try:
                    self.stdscr.addch(row, col, char)
                except curses.error:
                    pass

    def refresh(self) -> None:
        """Refresh the screen."""
        if self.stdscr:
            self.stdscr.refresh()

    def get_input(self) -> Optional[Direction]:
        """
        Get keyboard input and convert to direction.

        Returns:
            Direction based on key press, or None if no input
        """
        if not self.stdscr:
            return None

        try:
            key = self.stdscr.getch()
        except curses.error:
            return None

        if key == curses.KEY_UP:
            return Direction.UP
        elif key == curses.KEY_DOWN:
            return Direction.DOWN
        elif key == curses.KEY_LEFT:
            return Direction.LEFT
        elif key == curses.KEY_RIGHT:
            return Direction.RIGHT
        elif key == ord('w') or key == ord('W'):
            return Direction.UP
        elif key == ord('s') or key == ord('S'):
            return Direction.DOWN
        elif key == ord('a') or key == ord('A'):
            return Direction.LEFT
        elif key == ord('d') or key == ord('D'):
            return Direction.RIGHT
        elif key == ord('q') or key == ord('Q'):
            return Direction.RIGHT  # Just to stop movement
        elif key == ord('r') or key == ord('R'):
            return Direction.RIGHT  # Just to stop movement
        return None

    def show_game_over(self, score: int) -> None:
        """
        Show game over screen.

        Args:
            score: Final score
        """
        if not self.stdscr:
            return

        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Center the message
        start_row = height // 2 - 2
        start_col = width // 2 - 10

        self.stdscr.addstr(start_row, start_col, "GAME OVER!")
        self.stdscr.addstr(start_row + 1, start_col, f"Final Score: {score}")
        self.stdscr.addstr(start_row + 2, start_col, "Press R to restart")
        self.stdscr.addstr(start_row + 3, start_col, "Press Q to quit")
        self.stdscr.refresh()

    def show_start_screen(self, score_callback: Optional[Callable] = None) -> None:
        """
        Show start screen with controls.

        Args:
            score_callback: Optional callback for initial score
        """
        if not self.stdscr:
            return

        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Title
        title_row = height // 2 - 4
        title = "SNAKE GAME"
        start_col = width // 2 - len(title) // 2
        self.stdscr.addstr(title_row, start_col, title)

        # Instructions
        instructions = [
            "Arrow keys or WASD to move",
            "Eat @ to grow",
            "Avoid walls and yourself",
            "",
            "Press SPACE to start"
        ]

        for i, line in enumerate(instructions):
            self.stdscr.addstr(title_row + 2 + i, start_col, line)

        # Initial score if provided
        if score_callback:
            score = score_callback()
            self.stdscr.addstr(title_row + 7, start_col, f"Press SPACE to start | Score: {score}")

        self.stdscr.refresh()

    def wait_for_start(self) -> bool:
        """
        Wait for spacebar to start the game.

        Returns:
            True if game should start, False if quit
        """
        if not self.stdscr:
            return False

        self.stdscr.timeout(-1)  # Blocking input
        try:
            key = self.stdscr.getch()
        except curses.error:
            key = -1

        self.stdscr.timeout(100)  # Back to non-blocking
        return key == ord(' ')

    def clear(self) -> None:
        """Clear the screen."""
        if self.stdscr:
            self.stdscr.clear()
"""Main game controller — thin shell connecting engine + UI."""

from __future__ import annotations

import time

from .constants import DEFAULT_HEIGHT, DEFAULT_WIDTH
from .engine import GameEngine
from .model import GameState
from .ui import CursesUI


class SnakeGame:
    """Main game controller."""

    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT):
        self.width = width
        self.height = height
        self.engine = GameEngine(width, height)
        self.ui = CursesUI(width, height)

    def run(self) -> None:
        self.ui.start()
        try:
            self._loop()
        finally:
            self.ui.stop()

    def _loop(self) -> None:
        last_tick = time.time()

        # Input handler for blocking states (menu overlays)
        blocking_inputs = {
            GameState.MENU: lambda: self.ui.wait_for_key(),
            GameState.HIGH_SCORES: lambda: self.ui.wait_for_key(),
            GameState.HELP: lambda: self.ui.wait_for_key(),
            GameState.GAME_OVER: lambda: self.ui.wait_for_key(),
            GameState.ENTER_INITIALS: lambda: self.ui.wait_for_key(),
        }

        while self.engine.state != GameState.QUIT:
            state = self.engine.state

            # --- Menu / overlays (blocking input) ---
            inp = blocking_inputs.get(state, self.ui.get_input)

            # Render before input for overlays
            if state in blocking_inputs:
                self._render_overlays()

            inp = inp()
            self.engine.handle_input(inp)

            # --- Playing / Paused (non-blocking input) ---
            if state == GameState.PLAYING:
                now = time.time()
                if now - last_tick >= self.engine.tick_rate:
                    self.engine.tick()
                    last_tick = now

            # --- Playing / Paused (render) ---
            if state in (GameState.PLAYING, GameState.PAUSED):
                self._render_frame()

    def _render_overlays(self) -> None:
        """Render overlay screens (menu, high scores, help, etc.)."""
        state = self.engine.state

        if state == GameState.MENU:
            self.ui.show_menu(self.engine.menu_items,
                              self.engine.menu_index,
                              self.engine.high_scores.best)
        elif state == GameState.HIGH_SCORES:
            entries = self.engine.high_scores.get_top()
            self.ui.show_high_scores(entries)
        elif state == GameState.HELP:
            self.ui.show_help()
        elif state == GameState.GAME_OVER:
            self.ui.show_game_over(self.engine.score,
                                   self.engine.high_score)
        elif state == GameState.ENTER_INITIALS:
            self.ui.show_enter_initials(self.engine.score,
                                        self.engine.current_initials,
                                        self.engine.initials_cursor)

    def _render_frame(self) -> None:
        """Render game frame for playing or paused state."""
        state = self.engine.state
        if state in (GameState.PLAYING, GameState.PAUSED):
            self.ui.render_frame(
                self.engine.snake.get_body(),
                self.engine.food.get_position(),
                self.engine.score,
                self.engine.high_score,
                self.engine.level,
                paused=(self.engine.state == GameState.PAUSED),
                snake_direction=self.engine.snake.direction,
                food_char=self.engine.food.get_char(),
            )


def main():
    """Main entry point."""
    try:
        game = SnakeGame()
        game.run()
    except KeyboardInterrupt:
        pass

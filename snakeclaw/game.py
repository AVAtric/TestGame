"""Main game controller — thin shell connecting engine + UI."""

from __future__ import annotations

import time

from .engine import GameEngine
from .model import GameState
from .ui import CursesUI


class SnakeGame:
    """Main game controller."""

    def __init__(self, width: int = 60, height: int = 30):
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

        while self.engine.state != GameState.QUIT:
            state = self.engine.state

            # --- Menu / overlays (blocking input) ---
            if state == GameState.MENU:
                self.ui.show_menu(self.engine.menu_items,
                                  self.engine.menu_index,
                                  self.engine.high_scores.best)
                inp = self.ui.wait_for_key()
                self.engine.handle_input(inp)
                continue

            if state == GameState.HIGH_SCORES:
                entries = self.engine.high_scores.get_top()
                self.ui.show_high_scores(entries)
                inp = self.ui.wait_for_key()
                self.engine.handle_input(inp)
                continue

            if state == GameState.HELP:
                self.ui.show_help()
                inp = self.ui.wait_for_key()
                self.engine.handle_input(inp)
                continue

            if state == GameState.GAME_OVER:
                self.ui.show_game_over(self.engine.score,
                                       self.engine.high_score)
                inp = self.ui.wait_for_key()
                self.engine.handle_input(inp)
                continue

            # --- Playing / Paused (non-blocking input) ---
            inp = self.ui.get_input()
            self.engine.handle_input(inp)

            if self.engine.state == GameState.PLAYING:
                now = time.time()
                if now - last_tick >= self.engine.tick_rate:
                    self.engine.tick()
                    last_tick = now

            # Render
            if self.engine.state in (GameState.PLAYING, GameState.PAUSED):
                self.ui.render_frame(
                    self.engine.snake.get_body(),
                    self.engine.food.get_position(),
                    self.engine.score,
                    self.engine.high_score,
                    self.engine.level,
                    paused=(self.engine.state == GameState.PAUSED),
                )


def main():
    """Main entry point."""
    try:
        game = SnakeGame()
        game.run()
    except KeyboardInterrupt:
        pass

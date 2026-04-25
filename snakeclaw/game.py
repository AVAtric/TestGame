"""Main game controller — thin shell connecting engine + UI."""

from __future__ import annotations

import time

from .constants import BONUS_FOOD_CHAR, DEFAULT_HEIGHT, DEFAULT_WIDTH
from .engine import GameEngine
from .model import GameState
from .ui import CursesUI


# States where input should block until a key is pressed (overlays/menus).
_BLOCKING_STATES = frozenset({
    GameState.MENU,
    GameState.HIGH_SCORES,
    GameState.HELP,
    GameState.GAME_OVER,
    GameState.ENTER_INITIALS,
})


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

        while self.engine.state != GameState.QUIT:
            state = self.engine.state
            blocking = state in _BLOCKING_STATES

            if blocking:
                self._render_overlays()
                inp = self.ui.wait_for_key()
            else:
                inp = self.ui.get_input()

            self.engine.handle_input(inp)

            # --- Playing / Paused (non-blocking input) ---
            if state == GameState.PLAYING:
                now = time.time()
                if now - last_tick >= self.engine.tick_rate:
                    self.engine.tick()
                    last_tick = now
            else:
                # Reset tick timer when not playing to avoid burst on resume
                last_tick = time.time()

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
        bonus = self.engine.bonus
        bonus_pos = bonus.position if bonus and bonus.active else None
        bonus_char = bonus.char if bonus else BONUS_FOOD_CHAR
        bonus_blink = bool(bonus and bonus.is_blinking())
        self.ui.render_frame(
            self.engine.snake.get_body(),
            self.engine.food.get_position(),
            self.engine.score,
            self.engine.high_score,
            self.engine.level,
            paused=(self.engine.state == GameState.PAUSED),
            snake_direction=self.engine.snake.direction,
            food_char=self.engine.food.get_char(),
            bonus_pos=bonus_pos,
            bonus_char=bonus_char,
            bonus_blink=bonus_blink,
        )


def main():
    """Main entry point."""
    try:
        game = SnakeGame()
        game.run()
    except KeyboardInterrupt:
        pass

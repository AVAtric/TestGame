"""Main game controller — thin shell connecting engine + UI."""

from __future__ import annotations

import time

from .constants import (BONUS_FOOD_CHAR, DEFAULT_HEIGHT, DEFAULT_WIDTH,
                         MODERN_HEIGHT, MODERN_WIDTH)
from .engine import GameEngine
from .model import GameState, WallMode
from .ui import CursesUI


# States where input should block until a key is pressed (overlays/menus).
_BLOCKING_STATES = frozenset({
    GameState.MENU,
    GameState.HIGH_SCORES,
    GameState.HELP,
    GameState.GAME_OVER,
    GameState.ENTER_INITIALS,
    GameState.CONFIRM_QUIT,
})


class SnakeGame:
    """Main game controller."""

    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
                 wall_mode: WallMode = WallMode.WRAP):
        self.width = width
        self.height = height
        self.engine = GameEngine(width, height, wall_mode=wall_mode)
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
        engine = self.engine
        state = engine.state
        # Overlays use the full canvas dimensions; play-area centering only
        # applies during gameplay.
        self.ui.set_play_area(MODERN_WIDTH, MODERN_HEIGHT)

        if state == GameState.MENU:
            # Best across both modes — gives the player one headline number.
            best = max(engine.high_scores_for(WallMode.WRAP).best,
                       engine.high_scores_for(WallMode.SOLID).best)
            self.ui.show_menu(engine.menu_items, engine.menu_index, best)
        elif state == GameState.HIGH_SCORES:
            self.ui.show_high_scores(
                wrap_entries=engine.high_scores_for(WallMode.WRAP).get_top(),
                classic_entries=engine.high_scores_for(WallMode.SOLID).get_top(),
            )
        elif state == GameState.HELP:
            self.ui.show_help()
        elif state == GameState.GAME_OVER:
            self.ui.show_game_over(
                engine.score, engine.high_score,
                streak=engine.session_streak,
                last_score=engine.last_score,
                personal_best=engine.is_personal_best,
                near_miss=engine.near_miss_message,
            )
        elif state == GameState.ENTER_INITIALS:
            self.ui.show_enter_initials(engine.score,
                                        engine.current_initials,
                                        engine.initials_cursor)
        elif state == GameState.CONFIRM_QUIT:
            self.ui.show_confirm_quit(engine.confirm_quit_index)

    def _render_frame(self) -> None:
        """Render game frame for playing or paused state."""
        engine = self.engine
        # Re-center the playfield for the current game's dimensions. Cheap
        # idempotent call — no-op when already at the right size.
        self.ui.set_play_area(engine.width, engine.height)
        fruit = engine.fruit
        power = engine.power_up
        if power and power.active:
            bonus_pos = power.position
            bonus_char = power.get_char()
            bonus_color = power.get_color()
            bonus_blink = power.is_blinking()
            bonus_name = power.kind.name
            bonus_points = power.get_points()
            bonus_remaining = power.remaining()
        else:
            bonus_pos = None
            bonus_char = BONUS_FOOD_CHAR
            bonus_color = 0
            bonus_blink = False
            bonus_name = ""
            bonus_points = 0
            bonus_remaining = 0.0
        self.ui.render_frame(
            engine.snake.get_body(),
            fruit.get_position(),
            engine.score,
            engine.high_score,
            engine.level,
            paused=(engine.state == GameState.PAUSED),
            snake_direction=engine.snake.direction,
            food_char=fruit.get_char(),
            food_color=fruit.get_color(),
            food_name=fruit.kind.name,
            food_points=fruit.get_points(),
            bonus_pos=bonus_pos,
            bonus_char=bonus_char,
            bonus_color=bonus_color,
            bonus_blink=bonus_blink,
            bonus_name=bonus_name,
            bonus_points=bonus_points,
            bonus_remaining=bonus_remaining,
            popups=engine.popups,
            buff_label=engine.speed_buff_label if engine.buff_active else "",
            buff_remaining=engine.buff_remaining,
            wall_mode=engine.wall_mode,
        )


def main():
    """Main entry point."""
    try:
        game = SnakeGame()
        game.run()
    except KeyboardInterrupt:
        pass

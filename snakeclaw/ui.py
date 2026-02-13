"""Terminal UI using curses for Snake game."""

from __future__ import annotations

import curses
from typing import List, Optional, Tuple, Union

from .constants import (
    COLOR_BORDER, COLOR_FOOD, COLOR_HIGHLIGHT, COLOR_HUD,
    COLOR_SNAKE, COLOR_SUCCESS, COLOR_TITLE, COLOR_WARNING,
    DEFAULT_HEIGHT, DEFAULT_WIDTH, FOOD_CHAR, GAME_HINTS,
    GAME_TITLE, HELP_TEXT, INITIALS_HINTS,
    MENU_HINT, MENU_MARKER, MENU_SPACER, RETURN_HINT,
    SNAKE_SEGMENT
)
from .model import Action, Direction


# ---------------------------------------------------------------------------
# Key mapping
# ---------------------------------------------------------------------------

def map_key(key: int) -> Optional[Union[Direction, Action]]:
    """Convert a curses key code to a Direction or Action."""
    mapping = {
        curses.KEY_UP: Direction.UP,
        curses.KEY_DOWN: Direction.DOWN,
        curses.KEY_LEFT: Direction.LEFT,
        curses.KEY_RIGHT: Direction.RIGHT,
        ord('w'): Direction.UP, ord('W'): Direction.UP,
        ord('s'): Direction.DOWN, ord('S'): Direction.DOWN,
        ord('a'): Direction.LEFT, ord('A'): Direction.LEFT,
        ord('d'): Direction.RIGHT, ord('D'): Direction.RIGHT,
        ord('q'): Action.QUIT, ord('Q'): Action.QUIT,
        ord('r'): Action.RESET, ord('R'): Action.RESET,
        ord('p'): Action.PAUSE, ord('P'): Action.PAUSE,
        ord('m'): Action.MENU, ord('M'): Action.MENU,
        ord(' '): Action.SELECT,
        ord('\n'): Action.SELECT,
        10: Action.SELECT,   # enter
        13: Action.SELECT,   # carriage-return
        27: Action.MENU,     # escape → back to menu
    }
    return mapping.get(key)


# ---------------------------------------------------------------------------
# Curses renderer
# ---------------------------------------------------------------------------

class CursesUI:
    """Terminal UI implementation using curses."""

    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT):
        # play-area dimensions (inside the border) - logical grid
        self.play_w = width
        self.play_h = height
        # screen dimensions: use 2 columns per game cell for better aspect ratio
        self.screen_w = width * 2
        # total window: border + HUD row
        self.win_w = self.screen_w + 2   # left/right border cols
        self.win_h = height + 2  # top/bottom border rows
        self.stdscr: Optional[curses.window] = None
        self._has_colors = False

    # -- lifecycle -----------------------------------------------------------

    def start(self) -> None:
        self.stdscr = curses.initscr()
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(COLOR_SNAKE, curses.COLOR_GREEN, -1)      # snake
            curses.init_pair(COLOR_FOOD, curses.COLOR_RED, -1)         # food
            curses.init_pair(COLOR_HUD, curses.COLOR_YELLOW, -1)       # HUD
            curses.init_pair(COLOR_BORDER, curses.COLOR_CYAN, -1)      # border
            curses.init_pair(COLOR_TITLE, curses.COLOR_WHITE, -1)      # title
            curses.init_pair(COLOR_HIGHLIGHT, curses.COLOR_MAGENTA, -1) # highlight
            curses.init_pair(COLOR_SUCCESS, curses.COLOR_GREEN, -1)    # success
            curses.init_pair(COLOR_WARNING, curses.COLOR_RED, -1)      # warning
            self._has_colors = True
        self.stdscr.clear()
        self.stdscr.refresh()

    def stop(self) -> None:
        if self.stdscr:
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.curs_set(1)
            curses.endwin()

    # -- input ---------------------------------------------------------------

    def get_input(self) -> Optional[Union[Direction, Action]]:
        if not self.stdscr:
            return None
        try:
            key = self.stdscr.getch()
        except curses.error:
            return None
        if key == -1:
            return None
        return map_key(key)

    def wait_for_key(self) -> Optional[Union[Direction, Action]]:
        """Block until a key is pressed."""
        if not self.stdscr:
            return None
        self.stdscr.timeout(-1)
        try:
            key = self.stdscr.getch()
        except curses.error:
            key = -1
        self.stdscr.timeout(50)
        if key == -1:
            return None
        return map_key(key)

    # -- helpers -------------------------------------------------------------

    def _attr(self, pair: int, bold: bool = False) -> int:
        a = curses.color_pair(pair) if self._has_colors else 0
        if bold:
            a |= curses.A_BOLD
        return a

    def _safe_addstr(self, row: int, col: int, text: str, attr: int = 0) -> None:
        if not self.stdscr:
            return
        try:
            self.stdscr.addstr(row, col, text, attr)
        except curses.error:
            pass

    def _safe_addch(self, row: int, col: int, ch, attr: int = 0) -> None:
        if not self.stdscr:
            return
        try:
            self.stdscr.addch(row, col, ch, attr)
        except curses.error:
            pass

    def _center_col(self, text: str) -> int:
        return max(0, self.win_w // 2 - len(text) // 2)

    # -- drawing primitives --------------------------------------------------

    def clear(self) -> None:
        if self.stdscr:
            self.stdscr.erase()

    def refresh(self) -> None:
        if self.stdscr:
            self.stdscr.refresh()

    def draw_border(self) -> None:
        """Draw the play-area border (offset by 0,0; play area starts at 1,1)."""
        if not self.stdscr:
            return
        attr = self._attr(COLOR_BORDER)
        # top row
        self._safe_addch(0, 0, curses.ACS_ULCORNER, attr)
        for c in range(1, self.screen_w + 1):
            self._safe_addch(0, c, curses.ACS_HLINE, attr)
        self._safe_addch(0, self.screen_w + 1, curses.ACS_URCORNER, attr)
        # sides
        for r in range(1, self.play_h + 1):
            self._safe_addch(r, 0, curses.ACS_VLINE, attr)
            self._safe_addch(r, self.screen_w + 1, curses.ACS_VLINE, attr)
        # bottom row
        self._safe_addch(self.play_h + 1, 0, curses.ACS_LLCORNER, attr)
        for c in range(1, self.screen_w + 1):
            self._safe_addch(self.play_h + 1, c, curses.ACS_HLINE, attr)
        self._safe_addch(self.play_h + 1, self.screen_w + 1,
                         curses.ACS_LRCORNER, attr)

    def draw_snake(self, body: List[Tuple[int, int]], direction: Optional[Direction] = None) -> None:
        if not self.stdscr or not body:
            return
        
        attr_segment = self._attr(COLOR_SNAKE, bold=True)
        
        # Draw all segments with the same character for consistency
        for segment in body:
            self._safe_addstr(segment[0] + 1, segment[1] * 2 + 1, SNAKE_SEGMENT, attr_segment)

    def draw_food(self, pos: Tuple[int, int], char: str = FOOD_CHAR) -> None:
        if not self.stdscr:
            return
        self._safe_addstr(pos[0] + 1, pos[1] * 2 + 1, char,
                          self._attr(COLOR_FOOD, bold=True))

    def draw_hud(self, score: int, high_score: int, level: int,
                 paused: bool = False) -> None:
        """Draw status bar below the play area."""
        if not self.stdscr:
            return
        row = self.play_h + 2
        attr = self._attr(COLOR_HUD, bold=True)
        parts = [
            f" Score: {score} ",
            f" Hi: {high_score} ",
            f" Lvl: {level} ",
        ]
        if paused:
            parts.append(" ⏸ PAUSED ")
        line = "│".join(parts)
        full = line + GAME_HINTS
        self._safe_addstr(row, 0, full[:self.win_w], attr)

    # -- screens -------------------------------------------------------------

    def show_menu(self, items: List[str], selected: int,
                  high_score: int = 0) -> None:
        if not self.stdscr:
            return
        self.clear()
        mid_r = self.win_h // 2 - len(items)
        
        # ASCII art title
        for i, line in enumerate(GAME_TITLE):
            self._safe_addstr(mid_r - 5 + i, self._center_col(line), line,
                              self._attr(COLOR_SNAKE, bold=True))

        for i, item in enumerate(items):
            marker = MENU_MARKER if i == selected else MENU_SPACER
            text = f"{marker}{item}"
            attr = self._attr(COLOR_HIGHLIGHT, bold=True) if i == selected else self._attr(COLOR_TITLE)
            self._safe_addstr(mid_r + 1 + i * 2, self._center_col(text), text, attr)

        if high_score > 0:
            hs = f"🏆 Best: {high_score}"
            self._safe_addstr(mid_r + 2 + len(items) * 2,
                              self._center_col(hs), hs, self._attr(COLOR_HUD))

        self._safe_addstr(self.win_h - 1, self._center_col(MENU_HINT), MENU_HINT,
                          self._attr(COLOR_BORDER))
        self.refresh()

    def show_high_scores(self, entries) -> None:
        """Show high-score table.  entries: list of HighScoreEntry."""
        if not self.stdscr:
            return
        self.clear()
        title = "🏆 HIGH SCORES 🏆"
        self._safe_addstr(2, self._center_col(title), title,
                          self._attr(COLOR_HUD, bold=True))
        if not entries:
            msg = "No scores yet — go play!"
            self._safe_addstr(5, self._center_col(msg), msg, self._attr(COLOR_TITLE))
        else:
            header = f" {'#':>2}  {'INITIALS':<8} {'SCORE':>6}"
            self._safe_addstr(4, self._center_col(header), header,
                              self._attr(COLOR_TITLE, bold=True))
            for i, e in enumerate(entries[:10]):
                line = f" {i+1:>2}. {e.initials:<8} {e.score:>6}"
                attr = self._attr(COLOR_SUCCESS, bold=True) if i == 0 else self._attr(COLOR_TITLE)
                self._safe_addstr(5 + i, self._center_col(line), line, attr)
        self._safe_addstr(self.win_h - 1, self._center_col(RETURN_HINT), RETURN_HINT,
                          self._attr(COLOR_BORDER))
        self.refresh()

    def show_help(self) -> None:
        if not self.stdscr:
            return
        self.clear()
        title = "📖 HELP 📖"
        self._safe_addstr(2, self._center_col(title), title,
                          self._attr(COLOR_HUD, bold=True))
        start = 5
        for i, line in enumerate(HELP_TEXT):
            self._safe_addstr(start + i, self._center_col(line), line,
                              self._attr(COLOR_TITLE))
        self._safe_addstr(self.win_h - 1, self._center_col(RETURN_HINT), RETURN_HINT,
                          self._attr(COLOR_BORDER))
        self.refresh()

    def show_game_over(self, score: int, high_score: int) -> None:
        if not self.stdscr:
            return
        self.clear()
        self.draw_border()
        mid_r = self.win_h // 2 - 2
        lines = [
            "╔═══════════════════╗",
            "║   GAME  OVER ☠️   ║",
            "╚═══════════════════╝",
            f"  Score: {score}   Best: {high_score}",
            "",
            "R = restart   M = menu   Q = quit",
        ]
        for i, line in enumerate(lines):
            attr = self._attr(COLOR_WARNING, bold=True) if i < 3 else self._attr(COLOR_TITLE)
            self._safe_addstr(mid_r + i, self._center_col(line), line, attr)
        self.refresh()

    def show_enter_initials(self, score: int, initials: List[str], 
                            cursor: int) -> None:
        """Show initials entry screen."""
        if not self.stdscr:
            return
        self.clear()
        self.draw_border()
        mid_r = self.win_h // 2 - 4
        
        title = "╔═══════════════════════╗"
        title2 = "║  🎉 NEW HIGH SCORE! 🎉 ║"
        title3 = "╚═══════════════════════╝"
        
        self._safe_addstr(mid_r, self._center_col(title), title,
                          self._attr(COLOR_SUCCESS, bold=True))
        self._safe_addstr(mid_r + 1, self._center_col(title2), title2,
                          self._attr(COLOR_SUCCESS, bold=True))
        self._safe_addstr(mid_r + 2, self._center_col(title3), title3,
                          self._attr(COLOR_SUCCESS, bold=True))
        
        score_line = f"Score: {score}"
        self._safe_addstr(mid_r + 4, self._center_col(score_line), score_line,
                          self._attr(COLOR_TITLE))
        
        prompt = "Enter your initials:"
        self._safe_addstr(mid_r + 6, self._center_col(prompt), prompt,
                          self._attr(COLOR_TITLE))
        
        # Display initials with current cursor position highlighted
        initials_display = "   ".join(initials)
        initials_col = self._center_col(initials_display)
        
        for i, char in enumerate(initials):
            col = initials_col + i * 4
            attr = self._attr(COLOR_HIGHLIGHT, bold=True) if i == cursor else self._attr(COLOR_SNAKE, bold=True)
            self._safe_addstr(mid_r + 8, col, char, attr)
            if i == cursor:
                # Add cursor indicator
                self._safe_addstr(mid_r + 9, col, "▲", self._attr(COLOR_HIGHLIGHT))
        
        start_hint = mid_r + 11
        for i, hint in enumerate(INITIALS_HINTS):
            self._safe_addstr(start_hint + i, self._center_col(hint), hint,
                              self._attr(COLOR_BORDER))
        
        self.refresh()

    def show_paused(self) -> None:
        """Overlay a PAUSED banner on current screen."""
        if not self.stdscr:
            return
        mid_r = self.win_h // 2
        text = " ⏸  PAUSED — P to resume "
        self._safe_addstr(mid_r, self._center_col(text), text,
                          self._attr(COLOR_HUD, bold=True))
        self.refresh()

    # -- full play-frame render ----------------------------------------------

    def render_frame(self, snake_body: List[Tuple[int, int]],
                     food_pos: Tuple[int, int], score: int,
                     high_score: int, level: int,
                     paused: bool = False, 
                     snake_direction: Optional[Direction] = None,
                     food_char: str = FOOD_CHAR) -> None:
        """Render one complete game frame (border + objects + HUD)."""
        self.clear()
        self.draw_border()
        self.draw_snake(snake_body, snake_direction)
        self.draw_food(food_pos, food_char)
        self.draw_hud(score, high_score, level, paused)
        if paused:
            self.show_paused()
        self.refresh()

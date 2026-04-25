"""Terminal UI using curses for Snake game."""

from __future__ import annotations

import curses
import time
from typing import List, Optional, Tuple, Union

from .constants import (
    BONUS_FOOD_CHAR, COLOR_BORDER, COLOR_FOOD, COLOR_HIGHLIGHT,
    COLOR_HUD, COLOR_SNAKE, COLOR_SUCCESS, COLOR_TITLE, COLOR_WARNING,
    DEFAULT_HEIGHT, DEFAULT_WIDTH, FOOD_CHAR, GAME_HINTS,
    GAME_TITLE, HELP_TEXT, INITIALS_HINTS,
    MENU_HINT, MENU_MARKER, MENU_SPACER, POPUP_RISE_AFTER, POPUP_DURATION,
    RETURN_HINT, SNAKE_SEGMENT, STREAK_HOT_THRESHOLD
)
from .model import Action, Direction, ScorePopup, WallMode


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
        ord('y'): Action.YES, ord('Y'): Action.YES,
        ord('n'): Action.NO, ord('N'): Action.NO,
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
        # `canvas_*` is the fixed outer screen (modern dimensions). `play_*`
        # is the playable rectangle which can be smaller (Classic mode) and
        # centered inside the canvas via play_origin_*.
        self.canvas_w_cells = width
        self.canvas_h_cells = height
        self.play_w = width
        self.play_h = height
        self.screen_w = width * 2
        self.win_w = width * 2 + 2
        self.win_h = height + 2
        self.play_origin_y = 0    # top edge of the play border on stdscr
        self.play_origin_x = 0    # left edge of the play border on stdscr
        self.stdscr: Optional[curses.window] = None
        self._has_colors = False

    def set_play_area(self, play_w: int, play_h: int) -> None:
        """Resize the inner playfield while keeping the outer canvas fixed.

        The smaller playfield is centered within the canvas so a Classic-mode
        13×11 field appears in the middle of the screen instead of clinging
        to the top-left. Overlays (menu, help, high scores) ignore this and
        keep using `win_w`/`win_h` for canvas-relative centering.
        """
        self.play_w = play_w
        self.play_h = play_h
        self.screen_w = play_w * 2
        canvas_screen_w = self.canvas_w_cells * 2 + 2
        canvas_screen_h = self.canvas_h_cells + 2
        self.play_origin_x = max(0, (canvas_screen_w - (self.screen_w + 2)) // 2)
        self.play_origin_y = max(0, (canvas_screen_h - (play_h + 2)) // 2)

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

    def _center_col(self, text: str, width: int | None = None) -> int:
        """Center text in the window. If width is given, use it instead of len(text)."""
        w = width if width is not None else len(text)
        return max(0, self.win_w // 2 - w // 2)

    # -- drawing primitives --------------------------------------------------

    def clear(self) -> None:
        if self.stdscr:
            self.stdscr.erase()

    def refresh(self) -> None:
        if self.stdscr:
            self.stdscr.refresh()

    # Border glyphs picked per wall mode so the player can tell at a glance
    # whether walls are deadly or porous.
    #   SOLID = thick double-line ╔═╗║ in red — visually substantial, "real wall".
    #   WRAP  = a row of `·` middle-dots — porous/transparent, hints that
    #           contact wraps around. Arrow markers reinforce the idea.
    _BORDER_STYLES = {
        WallMode.SOLID: {
            "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
            "h":  "═", "v":  "║",
            "color": COLOR_WARNING,
        },
        WallMode.WRAP: {
            "tl": "·", "tr": "·", "bl": "·", "br": "·",
            "h":  "·", "v":  "·",
            "color": COLOR_BORDER,
        },
    }

    def draw_border(self, wall_mode: WallMode = WallMode.WRAP) -> None:
        """Draw the play-area border at the current origin, styled per mode.

        SOLID = thick double-line red border (lethal walls).
        WRAP  = a string of `·` dots (porous/transparent feel). The dots
                themselves convey the "open walls" idea — no arrows needed.
        """
        if not self.stdscr:
            return
        style = self._BORDER_STYLES[wall_mode]
        attr = self._attr(style["color"], bold=True)
        sw, ph = self.screen_w, self.play_h
        oy, ox = self.play_origin_y, self.play_origin_x
        # Corners
        self._safe_addstr(oy, ox, style["tl"], attr)
        self._safe_addstr(oy, ox + sw + 1, style["tr"], attr)
        self._safe_addstr(oy + ph + 1, ox, style["bl"], attr)
        self._safe_addstr(oy + ph + 1, ox + sw + 1, style["br"], attr)
        # Top + bottom edges
        for c in range(1, sw + 1):
            self._safe_addstr(oy, ox + c, style["h"], attr)
            self._safe_addstr(oy + ph + 1, ox + c, style["h"], attr)
        # Side edges
        for r in range(1, ph + 1):
            self._safe_addstr(oy + r, ox, style["v"], attr)
            self._safe_addstr(oy + r, ox + sw + 1, style["v"], attr)

    def _cell_to_screen(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert a (row, col) playfield cell to absolute screen coords,
        applying the current play-area origin so Classic mode renders at the
        centered offset rather than the top-left."""
        return (self.play_origin_y + 1 + pos[0],
                self.play_origin_x + 1 + pos[1] * 2)

    def draw_snake(self, body: List[Tuple[int, int]], direction: Optional[Direction] = None) -> None:
        if not self.stdscr or not body:
            return
        attr_segment = self._attr(COLOR_SNAKE, bold=True)
        for segment in body:
            r, c = self._cell_to_screen(segment)
            self._safe_addstr(r, c, SNAKE_SEGMENT, attr_segment)

    def draw_food(self, pos: Tuple[int, int], char: str = FOOD_CHAR,
                  color: int = COLOR_FOOD) -> None:
        if not self.stdscr:
            return
        r, c = self._cell_to_screen(pos)
        self._safe_addstr(r, c, char, self._attr(color, bold=True))

    def draw_bonus_food(self, pos: Optional[Tuple[int, int]],
                        char: str = BONUS_FOOD_CHAR,
                        blink: bool = False,
                        color: int = COLOR_HUD) -> None:
        """Draw a power-up at `pos` in its kind's color, blinking when active."""
        if not self.stdscr or pos is None:
            return
        attr = self._attr(color, bold=True)
        if blink:
            attr |= curses.A_BLINK
        r, c = self._cell_to_screen(pos)
        self._safe_addstr(r, c, char, attr)

    def draw_popups(self, popups: List[ScorePopup]) -> None:
        """Draw floating `+N` text on top of the playfield. Older popups drift
        up by one row so a chain of eats reads as a brief rising trail."""
        if not self.stdscr or not popups:
            return
        now = time.time()
        for p in popups:
            age = POPUP_DURATION - (p.expires_at - now)
            offset = -1 if age >= POPUP_RISE_AFTER else 0
            r, c = self._cell_to_screen(p.position)
            attr = self._attr(p.color, bold=True) | curses.A_BOLD
            # Clip text to fit; popups are tiny ("+1".."+99")
            self._safe_addstr(r + offset, c, p.text[:2], attr)

    def draw_hud(self, score: int, high_score: int, level: int,
                 paused: bool = False,
                 buff_label: str = "",
                 buff_remaining: float = 0.0,
                 wall_mode: WallMode = WallMode.WRAP,
                 fruit_char: str = "",
                 fruit_name: str = "",
                 fruit_points: int = 0,
                 fruit_color: int = COLOR_FOOD,
                 powerup_char: str = "",
                 powerup_name: str = "",
                 powerup_points: int = 0,
                 powerup_remaining: float = 0.0,
                 powerup_color: int = COLOR_HUD) -> None:
        """Draw the status area below the playfield.

        Three lines: (1) score / hi / level / wall badge / buff,
        (2) what's on the field right now (fruit + optional power-up timer),
        (3) keyboard hints. Sized to fit within the border width.
        """
        if not self.stdscr:
            return
        # Pin the HUD to the canvas bottom (modern dimensions) — not the
        # current play-area bottom — so a smaller Classic field doesn't
        # collide with the HUD lines drawn over it.
        row = self.canvas_h_cells + 2
        w = self.win_w

        # Line 1 — score & state
        mode_badge = "WRAP" if wall_mode == WallMode.WRAP else "CLASSIC"
        stats = (f" Score: {score}  │  Hi: {high_score}  │  "
                 f"Lvl: {level}  │  Mode: {mode_badge}")
        if buff_label:
            stats += f"  │  ⚡ {buff_label} {buff_remaining:.1f}s"
        if paused:
            stats += "  │  ⏸ PAUSED"
        stats_line = stats.center(w)
        self._safe_addstr(row, 0, stats_line[:w],
                          self._attr(COLOR_HUD, bold=True))

        # Line 2 — what's on the field. We render the fruit info as plain text
        # (one HUD line), then overlay the colored fruit glyph on top so each
        # icon shows in its actual color. Same trick for the power-up.
        if fruit_char and fruit_name:
            fruit_text = f"{fruit_char} {fruit_name} +{fruit_points}"
        else:
            fruit_text = ""
        if powerup_char and powerup_name:
            power_text = (f"{powerup_char} {powerup_name} +{powerup_points} "
                          f"({powerup_remaining:.1f}s)")
        else:
            power_text = ""
        if fruit_text or power_text:
            sep = "   " if (fruit_text and power_text) else ""
            info = f"{fruit_text}{sep}{power_text}"
            info_line = info.center(w)
            self._safe_addstr(row + 1, 0, info_line[:w],
                              self._attr(COLOR_TITLE))
            # Re-paint the fruit glyph in its own color for visual clarity.
            base = (w - len(info)) // 2
            if fruit_char:
                self._safe_addstr(row + 1, max(0, base), fruit_char,
                                  self._attr(fruit_color, bold=True))
            if power_text and powerup_char:
                power_col = base + len(fruit_text) + len(sep)
                self._safe_addstr(row + 1, max(0, power_col), powerup_char,
                                  self._attr(powerup_color, bold=True)
                                  | curses.A_BLINK)

        # Line 3 — hints
        hints = GAME_HINTS.strip()
        hints_line = hints.center(w)
        self._safe_addstr(row + 2, 0, hints_line[:w], self._attr(COLOR_BORDER))

    # -- screens -------------------------------------------------------------

    def show_menu(self, items: List[str], selected: int,
                  high_score: int = 0) -> None:
        if not self.stdscr:
            return
        self.clear()

        # Calculate widths for the menu box
        max_item_len = max(len(MENU_MARKER + item) for item in items)
        box_inner = max_item_len + 2  # padding inside box
        box_w = box_inner + 2  # +2 for borders

        # Calculate total content height for vertical centering
        logo_lines = len(GAME_TITLE)
        # box: top border + items (1 row each) + bottom border
        box_h = len(items) + 2
        total_h = logo_lines + 2 + box_h + 2  # +gaps
        start_row = max(1, (self.win_h - total_h) // 2)

        # ASCII art title - center each line
        for i, line in enumerate(GAME_TITLE):
            self._safe_addstr(start_row + i, self._center_col(line), line,
                              self._attr(COLOR_SNAKE, bold=True))

        # Menu box
        menu_start = start_row + logo_lines + 2
        box_col = self._center_col("x" * box_w)

        # Top border
        top = "╔" + "═" * box_inner + "╗"
        self._safe_addstr(menu_start, box_col, top, self._attr(COLOR_BORDER))

        # Items
        for i, item in enumerate(items):
            marker = MENU_MARKER if i == selected else MENU_SPACER
            label = f"{marker}{item}"
            padded = label.ljust(box_inner)
            row = menu_start + 1 + i
            if i == selected:
                attr = self._attr(COLOR_HIGHLIGHT, bold=True)
            else:
                attr = self._attr(COLOR_TITLE)
            self._safe_addstr(row, box_col, "║", self._attr(COLOR_BORDER))
            self._safe_addstr(row, box_col + 1, padded, attr)
            self._safe_addstr(row, box_col + 1 + box_inner, "║",
                              self._attr(COLOR_BORDER))

        # Bottom border
        bot = "╚" + "═" * box_inner + "╝"
        self._safe_addstr(menu_start + 1 + len(items), box_col, bot,
                          self._attr(COLOR_BORDER))

        # High score below box
        if high_score > 0:
            hs = f"★ Best: {high_score} ★"
            hs_row = menu_start + box_h + 1
            self._safe_addstr(hs_row, self._center_col(hs), hs,
                              self._attr(COLOR_HUD, bold=True))

        # Hint at bottom
        self._safe_addstr(self.win_h - 1, self._center_col(MENU_HINT),
                          MENU_HINT, self._attr(COLOR_BORDER))
        self.refresh()

    def show_high_scores(self,
                         wrap_entries: Optional[list] = None,
                         classic_entries: Optional[list] = None) -> None:
        """Show the high-score screen — two columns, WRAP left / CLASSIC right."""
        if not self.stdscr:
            return
        self.clear()
        col_w = 22  # inner column width
        gap = 4
        block_w = col_w * 2 + gap
        start_col = max(0, (self.win_w - block_w) // 2)
        start_row = 2

        # Banner
        banner = "★ HIGH SCORES ★"
        self._safe_addstr(start_row, self._center_col(banner), banner,
                          self._attr(COLOR_HUD, bold=True))

        # Headers per column (wrap left, classic right)
        wrap_hdr = "─── WRAP ───"
        classic_hdr = "── CLASSIC ──"
        self._safe_addstr(start_row + 2, start_col + (col_w - len(wrap_hdr)) // 2,
                          wrap_hdr, self._attr(COLOR_BORDER, bold=True))
        self._safe_addstr(start_row + 2,
                          start_col + col_w + gap + (col_w - len(classic_hdr)) // 2,
                          classic_hdr, self._attr(COLOR_WARNING, bold=True))

        col_header = f"{'#':>2}  {'NAME':<5} {'SCORE':>6}"
        self._safe_addstr(start_row + 3, start_col + 1, col_header,
                          self._attr(COLOR_TITLE, bold=True))
        self._safe_addstr(start_row + 3, start_col + col_w + gap + 1, col_header,
                          self._attr(COLOR_TITLE, bold=True))

        def _draw_col(entries, base_col):
            if not entries:
                msg = "No scores yet"
                self._safe_addstr(start_row + 5, base_col + (col_w - len(msg)) // 2,
                                  msg, self._attr(COLOR_TITLE))
                return
            for i, e in enumerate(entries[:10]):
                line = f"{i+1:>2}. {e.initials:<5} {e.score:>6}"
                if i == 0:
                    attr = self._attr(COLOR_SUCCESS, bold=True)
                elif i < 3:
                    attr = self._attr(COLOR_HUD, bold=True)
                else:
                    attr = self._attr(COLOR_TITLE)
                self._safe_addstr(start_row + 5 + i, base_col + 1, line, attr)

        _draw_col(wrap_entries or [], start_col)
        _draw_col(classic_entries or [], start_col + col_w + gap)

        self._safe_addstr(self.win_h - 1, self._center_col(RETURN_HINT),
                          RETURN_HINT, self._attr(COLOR_BORDER))
        self.refresh()

    def show_help(self) -> None:
        if not self.stdscr:
            return
        self.clear()
        title = "╔═══════════════════╗"
        title2 = "║    ? CONTROLS ?   ║"
        title3 = "╚═══════════════════╝"
        self._safe_addstr(2, self._center_col(title), title,
                          self._attr(COLOR_HUD, bold=True))
        self._safe_addstr(3, self._center_col(title2), title2,
                          self._attr(COLOR_HUD, bold=True))
        self._safe_addstr(4, self._center_col(title3), title3,
                          self._attr(COLOR_HUD, bold=True))
        start = 6
        for i, line in enumerate(HELP_TEXT):
            attr = self._attr(COLOR_SNAKE) if line.startswith(("Arrow", "P ", "R ", "M ", "Q ")) else self._attr(COLOR_TITLE)
            self._safe_addstr(start + i, self._center_col(line), line, attr)
        self._safe_addstr(self.win_h - 1, self._center_col(RETURN_HINT),
                          RETURN_HINT, self._attr(COLOR_BORDER))
        self.refresh()

    def show_game_over(self, score: int, high_score: int,
                       streak: int = 0,
                       last_score: int = 0,
                       personal_best: bool = False,
                       near_miss: str = "") -> None:
        """Game-over screen with engagement nudges aimed at "just one more".

        The page is structured so the most-positive line is highest in the
        eye-line and the dominant action is RESTART (highlighted). M / Q are
        present but understated.
        """
        if not self.stdscr:
            return
        self.clear()
        self.draw_border()

        # Compose body lines top-down.
        lines: List[Tuple[str, int]] = []  # (text, attr)
        warn = self._attr(COLOR_WARNING, bold=True)
        title = self._attr(COLOR_TITLE)
        success = self._attr(COLOR_SUCCESS, bold=True)
        hud = self._attr(COLOR_HUD, bold=True)
        highlight = self._attr(COLOR_HIGHLIGHT, bold=True)

        lines.append(("╔═══════════════════╗", warn))
        lines.append(("║   GAME  OVER ☠️   ║", warn))
        lines.append(("╚═══════════════════╝", warn))
        lines.append((f"  Score: {score}   Best: {high_score}  ", title))

        # Engagement nudges (the "dark patterns").
        if personal_best:
            lines.append(("✨ NEW PERSONAL BEST! ✨", success))
        if last_score > 0:
            delta = score - last_score
            arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "·")
            sign = "+" if delta > 0 else ""
            cmp_attr = success if delta > 0 else (warn if delta < 0 else title)
            lines.append((f"Last: {last_score}  →  This: {score}  ({arrow}{sign}{delta})", cmp_attr))
        if streak >= STREAK_HOT_THRESHOLD:
            lines.append((f"🔥 {streak} in a row — keep it going!", hud))
        elif streak >= 2:
            lines.append((f"Run #{streak} of the session", title))
        if near_miss:
            lines.append((near_miss, hud))

        lines.append(("", title))  # spacer
        # Make RESTART the dominant call to action.
        lines.append(("▶ R  ──  JUST ONE MORE  ──", highlight))
        lines.append(("M = menu     Q = quit", title))

        # Vertical center the block on the canvas.
        mid_r = max(1, (self.win_h - len(lines)) // 2)
        for i, (text, attr) in enumerate(lines):
            self._safe_addstr(mid_r + i, self._center_col(text), text, attr)
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

    def show_confirm_quit(self, selected_index: int = 0) -> None:
        """"Are you sure you want to quit?" overlay.

        Two buttons: STAY (index 0, default) and QUIT (index 1). The
        non-selected button is dim, the selected one is highlighted. Drawn
        as an overlay so the game/menu underneath is preserved when we
        return — but we currently `clear()` for legibility on small terminals.
        """
        if not self.stdscr:
            return
        self.clear()
        title_lines = [
            "╔════════════════════════════╗",
            "║  Are you sure you want to  ║",
            "║          quit?             ║",
            "╚════════════════════════════╝",
        ]
        mid_r = max(2, self.win_h // 2 - 4)
        for i, line in enumerate(title_lines):
            self._safe_addstr(mid_r + i, self._center_col(line), line,
                              self._attr(COLOR_WARNING, bold=True))

        # Buttons — STAY is the default-safe option, drawn green when picked;
        # QUIT renders red when picked. Non-selected sides stay neutral.
        labels = ("STAY", "QUIT")
        button_strs = [f"[ {l} ]" for l in labels]
        gap = 6
        total_w = sum(len(s) for s in button_strs) + gap
        col = self._center_col("x" * total_w)
        for i, s in enumerate(button_strs):
            if i == selected_index:
                attr = self._attr(COLOR_SUCCESS if i == 0 else COLOR_WARNING,
                                  bold=True)
            else:
                attr = self._attr(COLOR_TITLE)
            self._safe_addstr(mid_r + len(title_lines) + 2, col, s, attr)
            col += len(s) + gap

        hint = "←/→ choose · Enter confirm · Y = quit · N/Esc = stay"
        self._safe_addstr(mid_r + len(title_lines) + 4,
                          self._center_col(hint), hint,
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
                     food_char: str = FOOD_CHAR,
                     food_color: int = COLOR_FOOD,
                     food_name: str = "",
                     food_points: int = 0,
                     bonus_pos: Optional[Tuple[int, int]] = None,
                     bonus_char: str = BONUS_FOOD_CHAR,
                     bonus_color: int = COLOR_HUD,
                     bonus_blink: bool = False,
                     bonus_name: str = "",
                     bonus_points: int = 0,
                     bonus_remaining: float = 0.0,
                     popups: Optional[List[ScorePopup]] = None,
                     buff_label: str = "",
                     buff_remaining: float = 0.0,
                     wall_mode: WallMode = WallMode.WRAP) -> None:
        """Render one complete game frame (border + objects + HUD)."""
        self.clear()
        self.draw_border(wall_mode=wall_mode)
        self.draw_snake(snake_body, snake_direction)
        self.draw_food(food_pos, food_char, color=food_color)
        self.draw_bonus_food(bonus_pos, bonus_char, bonus_blink,
                             color=bonus_color)
        if popups:
            self.draw_popups(popups)
        self.draw_hud(
            score, high_score, level, paused,
            buff_label=buff_label, buff_remaining=buff_remaining,
            wall_mode=wall_mode,
            fruit_char=food_char, fruit_name=food_name,
            fruit_points=food_points, fruit_color=food_color,
            powerup_char=bonus_char if bonus_pos else "",
            powerup_name=bonus_name if bonus_pos else "",
            powerup_points=bonus_points, powerup_remaining=bonus_remaining,
            powerup_color=bonus_color,
        )
        if paused:
            self.show_paused()
        self.refresh()

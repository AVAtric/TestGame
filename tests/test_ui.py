"""Unit tests for UI key mapping (no real terminal needed)."""

import curses
import pytest
from unittest.mock import MagicMock

from snakeclaw.ui import map_key, CursesUI
from snakeclaw.model import Action, Direction


class TestMapKey:
    @pytest.mark.parametrize("key,expected", [
        (curses.KEY_UP, Direction.UP),
        (curses.KEY_DOWN, Direction.DOWN),
        (curses.KEY_LEFT, Direction.LEFT),
        (curses.KEY_RIGHT, Direction.RIGHT),
        (ord('w'), Direction.UP),
        (ord('W'), Direction.UP),
        (ord('a'), Direction.LEFT),
        (ord('s'), Direction.DOWN),
        (ord('d'), Direction.RIGHT),
        (ord('q'), Action.QUIT),
        (ord('Q'), Action.QUIT),
        (ord('r'), Action.RESET),
        (ord('R'), Action.RESET),
        (ord('p'), Action.PAUSE),
        (ord('P'), Action.PAUSE),
        (ord('m'), Action.MENU),
        (ord(' '), Action.SELECT),
        (10, Action.SELECT),  # enter
        (27, Action.MENU),    # escape
    ])
    def test_known_keys(self, key, expected):
        assert map_key(key) == expected

    def test_unknown_key(self):
        assert map_key(ord('z')) is None


class TestCursesUINoScreen:
    """Test CursesUI methods gracefully handle missing stdscr."""

    def test_get_input_none(self):
        ui = CursesUI()
        assert ui.get_input() is None

    def test_clear_no_crash(self):
        CursesUI().clear()

    def test_refresh_no_crash(self):
        CursesUI().refresh()

    def test_draw_border_no_crash(self):
        CursesUI().draw_border()

    def test_draw_snake_no_crash(self):
        CursesUI().draw_snake([(1, 1)])

    def test_draw_food_no_crash(self):
        CursesUI().draw_food((1, 1))

    def test_draw_hud_no_crash(self):
        CursesUI().draw_hud(0, 0, 1)

    def test_show_menu_no_crash(self):
        CursesUI().show_menu(["A"], 0)

    def test_show_high_scores_no_crash(self):
        CursesUI().show_high_scores([])

    def test_show_help_no_crash(self):
        CursesUI().show_help()

    def test_show_game_over_no_crash(self):
        CursesUI().show_game_over(10, 20)

    def test_show_paused_no_crash(self):
        CursesUI().show_paused()

    def test_wait_for_key_no_crash(self):
        assert CursesUI().wait_for_key() is None


def _ui():
    ui = CursesUI(width=20, height=10)
    ui.stdscr = MagicMock()
    ui._has_colors = False
    return ui


class TestCursesUIWithMock:

    def test_get_input_maps_key(self):
        ui = _ui()
        ui.stdscr.getch.return_value = ord('p')
        assert ui.get_input() == Action.PAUSE

    def test_get_input_no_key(self):
        ui = _ui()
        ui.stdscr.getch.return_value = -1
        assert ui.get_input() is None

    def test_get_input_curses_error(self):
        ui = _ui()
        ui.stdscr.getch.side_effect = curses.error()
        assert ui.get_input() is None

    @pytest.fixture(autouse=False)
    def _patch_acs(self):
        import curses as _c
        for name in ('ACS_ULCORNER', 'ACS_URCORNER', 'ACS_LLCORNER',
                      'ACS_LRCORNER', 'ACS_HLINE', 'ACS_VLINE'):
            if not hasattr(_c, name):
                setattr(_c, name, ord('+'))
        yield

    def test_render_frame_calls(self, _patch_acs):
        ui = _ui()
        ui.render_frame([(5, 5), (5, 4)], (3, 3), 10, 20, 2)
        assert ui.stdscr.erase.called
        assert ui.stdscr.refresh.called

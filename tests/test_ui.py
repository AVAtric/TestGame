"""Unit tests for UI key mapping (no real terminal needed)."""

import curses
import pytest
from unittest.mock import MagicMock

from snakeclaw.ui import map_key, CursesUI
from snakeclaw.model import Action, Direction, WallMode


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
        CursesUI().show_high_scores()  # both columns empty

    def test_show_help_no_crash(self):
        CursesUI().show_help()

    def test_show_game_over_no_crash(self):
        CursesUI().show_game_over(10, 20)

    def test_show_paused_no_crash(self):
        CursesUI().show_paused()

    def test_show_confirm_quit_no_crash(self):
        CursesUI().show_confirm_quit()
        CursesUI().show_confirm_quit(selected_index=1)

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

    def test_render_frame_with_full_hud(self, _patch_acs):
        # Smoke-test the full HUD payload (mode badge, fruit info, power-up
        # countdown, buffs) — exercises the new wide signature end-to-end.
        ui = _ui()
        ui.render_frame(
            [(5, 5)], (3, 3), score=12, high_score=42, level=2,
            food_char="()", food_color=2, food_name="apple", food_points=1,
            bonus_pos=(2, 2), bonus_char="XX", bonus_color=3,
            bonus_blink=True, bonus_name="bonus", bonus_points=5,
            bonus_remaining=3.4,
            buff_label="FAST", buff_remaining=4.1,
            wall_mode=WallMode.SOLID,
        )
        assert ui.stdscr.refresh.called

    def test_show_high_scores_dual(self):
        # New side-by-side rendering path. Stub entries must not crash.
        from types import SimpleNamespace
        e = SimpleNamespace(initials="AAA", score=10)
        ui = _ui()
        ui.show_high_scores(
            wrap_entries=[e, e, e],
            classic_entries=[e],
        )
        assert ui.stdscr.refresh.called

    def test_draw_border_per_mode(self):
        # Both wall modes should call into stdscr without raising.
        ui = _ui()
        ui.draw_border(wall_mode=WallMode.WRAP)
        ui.draw_border(wall_mode=WallMode.SOLID)
        # The two styles draw different glyphs, so addstr should be called
        # many times for each — sanity-check the call count.
        assert ui.stdscr.addstr.call_count > 0

    def test_wrap_border_has_no_arrows(self):
        # Wrap walls should be pure dots — no `↔` or `↕` glyphs anymore.
        ui = _ui()
        ui.draw_border(wall_mode=WallMode.WRAP)
        text_args = [call.args[2] for call in ui.stdscr.addstr.call_args_list
                     if len(call.args) >= 3]
        assert "↔" not in text_args
        assert "↕" not in text_args

    def test_set_play_area_centers_smaller_field(self):
        # A small play area (Classic) should compute non-zero origin offsets
        # so it doesn't render in the corner.
        ui = CursesUI(width=48, height=30)
        ui.set_play_area(17, 11)
        assert ui.play_origin_x > 0
        assert ui.play_origin_y > 0

    def test_hud_drawn_at_canvas_bottom_not_play_h(self):
        # Pin the HUD to the canvas bottom so a small Classic playfield (which
        # would otherwise cause HUD lines to land *inside* the play area)
        # doesn't overlap with the score bar.
        ui = _ui()
        ui.set_play_area(17, 11)  # classic-sized inner playfield
        ui.draw_hud(0, 0, 1)
        rows = [call.args[0] for call in ui.stdscr.addstr.call_args_list
                if len(call.args) >= 1]
        # canvas_h_cells is 10 (test UI uses height=10); HUD lines are at
        # rows 12, 13, 14 — strictly below the canvas, never inside the
        # 11-row Classic playfield region.
        assert all(r >= ui.canvas_h_cells + 2 for r in rows)

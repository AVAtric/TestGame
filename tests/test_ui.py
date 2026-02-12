"""Unit tests for Snake game UI."""

import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import curses
from snakeclaw.ui import CursesUI
from snakeclaw.model import Direction, GameStatus


def _make_ui_with_mock_stdscr(width=60, height=30):
    """Helper: create a CursesUI with a mocked stdscr (no curses.initscr)."""
    ui = CursesUI(width=width, height=height)
    ui.stdscr = MagicMock()
    return ui


@patch('curses.curs_set')
@patch('curses.cbreak')
@patch('curses.noecho')
@patch('curses.initscr')
class TestCursesUIStart(unittest.TestCase):
    """Test CursesUI start/stop."""

    def test_start(self, mock_initscr, mock_noecho, mock_cbreak, mock_curs_set):
        """Test UI start method."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr

        ui = CursesUI(width=60, height=30)
        ui.start()

        mock_initscr.assert_called_once()
        mock_stdscr.keypad.assert_called_once_with(True)
        mock_stdscr.nodelay.assert_called_once_with(True)
        mock_noecho.assert_called_once()
        mock_cbreak.assert_called_once()
        mock_curs_set.assert_called_once_with(0)

    @patch('curses.endwin')
    @patch('curses.echo')
    @patch('curses.nocbreak')
    def test_stop(self, mock_nocbreak, mock_echo, mock_endwin,
                  mock_initscr, mock_noecho, mock_cbreak, mock_curs_set):
        """Test UI stop method."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr

        ui = CursesUI(width=60, height=30)
        ui.start()
        # Reset mocks from start
        mock_curs_set.reset_mock()

        ui.stop()

        mock_nocbreak.assert_called_once()
        mock_stdscr.keypad.assert_called_with(False)
        mock_echo.assert_called_once()
        mock_curs_set.assert_called_once_with(1)
        mock_endwin.assert_called_once()


class TestCursesUIDrawing(unittest.TestCase):
    """Test CursesUI drawing methods (no curses init needed)."""

    @patch.object(curses, 'ACS_ULCORNER', ord('+'), create=True)
    @patch.object(curses, 'ACS_URCORNER', ord('+'), create=True)
    @patch.object(curses, 'ACS_LLCORNER', ord('+'), create=True)
    @patch.object(curses, 'ACS_LRCORNER', ord('+'), create=True)
    @patch.object(curses, 'ACS_HLINE', ord('-'), create=True)
    @patch.object(curses, 'ACS_VLINE', ord('|'), create=True)
    def test_draw_border(self):
        """Test drawing border."""
        ui = _make_ui_with_mock_stdscr(width=10, height=10)
        ui.draw_border()
        self.assertGreater(ui.stdscr.addch.call_count, 0)

    def test_draw_border_no_stdscr(self):
        """Test drawing border when stdscr is None."""
        ui = CursesUI(width=10, height=10)
        ui.draw_border()  # Should not crash

    def test_draw_snake(self):
        """Test drawing snake."""
        ui = _make_ui_with_mock_stdscr()
        snake_body = [(10, 10), (10, 11), (10, 12)]
        ui.draw_snake(snake_body)
        self.assertEqual(ui.stdscr.addch.call_count, 3)

    def test_draw_snake_no_stdscr(self):
        """Test drawing snake when stdscr is None."""
        ui = CursesUI(width=60, height=30)
        ui.draw_snake([(10, 10)])  # Should not crash

    def test_draw_food(self):
        """Test drawing food."""
        ui = _make_ui_with_mock_stdscr()
        ui.draw_food((10, 10))
        ui.stdscr.addch.assert_called_once_with(10, 10, '@')

    def test_draw_food_no_stdscr(self):
        """Test drawing food when stdscr is None."""
        ui = CursesUI(width=60, height=30)
        ui.draw_food((10, 10))  # Should not crash

    def test_draw_score(self):
        """Test drawing score."""
        ui = _make_ui_with_mock_stdscr()
        ui.draw_score(10, GameStatus.PLAYING)
        ui.stdscr.addstr.assert_called_once()

    def test_draw_score_game_over(self):
        """Test drawing score with game over status."""
        ui = _make_ui_with_mock_stdscr()
        ui.draw_score(10, GameStatus.GAME_OVER)
        ui.stdscr.addstr.assert_called_once()

    def test_draw_score_no_stdscr(self):
        """Test drawing score when stdscr is None."""
        ui = CursesUI(width=60, height=30)
        ui.draw_score(10, GameStatus.PLAYING)  # Should not crash

    def test_refresh(self):
        """Test refresh method."""
        ui = _make_ui_with_mock_stdscr()
        ui.refresh()
        ui.stdscr.refresh.assert_called_once()

    def test_refresh_no_stdscr(self):
        """Test refresh when stdscr is None."""
        ui = CursesUI(width=60, height=30)
        ui.refresh()  # Should not crash

    def test_clear(self):
        """Test clear method."""
        ui = _make_ui_with_mock_stdscr()
        ui.clear()
        ui.stdscr.clear.assert_called_once()

    def test_clear_no_stdscr(self):
        """Test clear when stdscr is None."""
        ui = CursesUI(width=60, height=30)
        ui.clear()  # Should not crash

    def test_show_game_over(self):
        """Test showing game over screen."""
        ui = _make_ui_with_mock_stdscr()
        ui.stdscr.getmaxyx.return_value = (25, 80)
        ui.show_game_over(10)
        self.assertGreater(ui.stdscr.addstr.call_count, 0)
        ui.stdscr.refresh.assert_called_once()

    def test_show_game_over_no_stdscr(self):
        """Test show_game_over when stdscr is None."""
        ui = CursesUI(width=60, height=30)
        ui.show_game_over(10)  # Should not crash

    def test_show_start_screen(self):
        """Test showing start screen."""
        ui = _make_ui_with_mock_stdscr()
        ui.stdscr.getmaxyx.return_value = (25, 80)
        ui.show_start_screen()
        self.assertGreater(ui.stdscr.addstr.call_count, 0)
        ui.stdscr.refresh.assert_called_once()

    def test_show_start_screen_no_stdscr(self):
        """Test show_start_screen when stdscr is None."""
        ui = CursesUI(width=60, height=30)
        ui.show_start_screen()  # Should not crash


class TestCursesUIInput(unittest.TestCase):
    """Test CursesUI input handling."""

    def _make_ui_with_key(self, key_value):
        ui = _make_ui_with_mock_stdscr()
        ui.stdscr.getch.return_value = key_value
        return ui

    def test_get_input_up(self):
        ui = self._make_ui_with_key(curses.KEY_UP)
        self.assertEqual(ui.get_input(), Direction.UP)

    def test_get_input_down(self):
        ui = self._make_ui_with_key(curses.KEY_DOWN)
        self.assertEqual(ui.get_input(), Direction.DOWN)

    def test_get_input_left(self):
        ui = self._make_ui_with_key(curses.KEY_LEFT)
        self.assertEqual(ui.get_input(), Direction.LEFT)

    def test_get_input_right(self):
        ui = self._make_ui_with_key(curses.KEY_RIGHT)
        self.assertEqual(ui.get_input(), Direction.RIGHT)

    def test_get_input_w(self):
        ui = self._make_ui_with_key(ord('w'))
        self.assertEqual(ui.get_input(), Direction.UP)

    def test_get_input_W(self):
        ui = self._make_ui_with_key(ord('W'))
        self.assertEqual(ui.get_input(), Direction.UP)

    def test_get_input_s(self):
        ui = self._make_ui_with_key(ord('s'))
        self.assertEqual(ui.get_input(), Direction.DOWN)

    def test_get_input_a(self):
        ui = self._make_ui_with_key(ord('a'))
        self.assertEqual(ui.get_input(), Direction.LEFT)

    def test_get_input_d(self):
        ui = self._make_ui_with_key(ord('d'))
        self.assertEqual(ui.get_input(), Direction.RIGHT)

    def test_get_input_quit(self):
        ui = self._make_ui_with_key(ord('q'))
        self.assertEqual(ui.get_input(), Direction.QUIT)

    def test_get_input_quit_upper(self):
        ui = self._make_ui_with_key(ord('Q'))
        self.assertEqual(ui.get_input(), Direction.QUIT)

    def test_get_input_restart(self):
        ui = self._make_ui_with_key(ord('r'))
        self.assertEqual(ui.get_input(), Direction.RESET)

    def test_get_input_restart_upper(self):
        ui = self._make_ui_with_key(ord('R'))
        self.assertEqual(ui.get_input(), Direction.RESET)

    def test_get_input_none(self):
        ui = self._make_ui_with_key(ord('x'))
        self.assertIsNone(ui.get_input())

    def test_get_input_curses_error(self):
        ui = _make_ui_with_mock_stdscr()
        ui.stdscr.getch.side_effect = curses.error()
        self.assertIsNone(ui.get_input())

    def test_get_input_no_stdscr(self):
        ui = CursesUI(width=60, height=30)
        self.assertIsNone(ui.get_input())

    def test_wait_for_start_space(self):
        ui = _make_ui_with_mock_stdscr()
        ui.stdscr.getch.return_value = ord(' ')
        self.assertTrue(ui.wait_for_start())

    def test_wait_for_start_other(self):
        ui = _make_ui_with_mock_stdscr()
        ui.stdscr.getch.return_value = ord('x')
        self.assertFalse(ui.wait_for_start())

    def test_wait_for_start_no_stdscr(self):
        ui = CursesUI(width=60, height=30)
        self.assertFalse(ui.wait_for_start())


if __name__ == '__main__':
    unittest.main()

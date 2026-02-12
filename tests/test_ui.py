"""Unit tests for Snake game UI."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snakeclaw.ui import CursesUI
from snakeclaw.model import Direction, GameStatus


class TestCursesUI(unittest.TestCase):
    """Test CursesUI class."""

    @patch('curses.initscr')
    @patch('curses.nocbreak')
    @patch('curses.keypad')
    @patch('curses.echo')
    @patch('curses.curs_set')
    @patch('curses.endwin')
    def test_start(self, mock_endwin, mock_curs_set, mock_echo, mock_keypad, mock_nocbreak, mock_initscr):
        """Test UI start method."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr

        ui = CursesUI(width=60, height=30)
        ui.start()

        mock_stdscr.keypad.assert_called_once_with(True)
        mock_stdscr.nodelay.assert_called_once_with(True)
        mock_echo.assert_called_once()
        mock_curs_set.assert_called_once_with(0)

    @patch('curses.initscr')
    @patch('curses.nocbreak')
    @patch('curses.keypad')
    @patch('curses.echo')
    @patch('curses.curs_set')
    @patch('curses.endwin')
    def test_stop(self, mock_endwin, mock_curs_set, mock_echo, mock_keypad, mock_nocbreak, mock_initscr):
        """Test UI stop method."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr

        ui = CursesUI(width=60, height=30)
        ui.start()
        ui.stop()

        mock_nocbreak.assert_called_once()
        mock_stdscr.keypad.assert_called_once_with(False)
        mock_echo.assert_called_once()
        mock_curs_set.assert_called_once_with(1)
        mock_endwin.assert_called_once()

    def test_draw_border(self):
        """Test drawing border."""
        ui = CursesUI(width=10, height=10)
        ui.stdscr = MagicMock()

        ui.draw_border()

        # Should have called addch multiple times
        self.assertGreater(ui.stdscr.addch.call_count, 0)

    def test_draw_border_no_stdscr(self):
        """Test drawing border when stdscr is None."""
        ui = CursesUI(width=10, height=10)

        ui.draw_border()

        # Should not crash

    def test_draw_snake(self):
        """Test drawing snake."""
        ui = CursesUI(width=60, height=30)
        ui.stdscr = MagicMock()

        snake_body = [(10, 10), (10, 11), (10, 12)]
        ui.draw_snake(snake_body)

        # Should have called addch for each snake part
        self.assertEqual(ui.stdscr.addch.call_count, 3)

    def test_draw_snake_no_stdscr(self):
        """Test drawing snake when stdscr is None."""
        ui = CursesUI(width=60, height=30)

        snake_body = [(10, 10), (10, 11), (10, 12)]
        ui.draw_snake(snake_body)

        # Should not crash

    def test_draw_food(self):
        """Test drawing food."""
        ui = CursesUI(width=60, height=30)
        ui.stdscr = MagicMock()

        food_pos = (10, 10)
        ui.draw_food(food_pos)

        # Should have called addch once
        ui.stdscr.addch.assert_called_once_with(10, 10, '@')

    def test_draw_food_no_stdscr(self):
        """Test drawing food when stdscr is None."""
        ui = CursesUI(width=60, height=30)

        food_pos = (10, 10)
        ui.draw_food(food_pos)

        # Should not crash

    def test_draw_score(self):
        """Test drawing score."""
        ui = CursesUI(width=60, height=30)
        ui.stdscr = MagicMock()

        ui.draw_score(10, GameStatus.PLAYING)

        # Should have called addch multiple times
        self.assertGreater(ui.stdscr.addch.call_count, 0)

    def test_draw_score_game_over(self):
        """Test drawing score with game over status."""
        ui = CursesUI(width=60, height=30)
        ui.stdscr = MagicMock()

        ui.draw_score(10, GameStatus.GAME_OVER)

        # Should have called addch multiple times
        self.assertGreater(ui.stdscr.addch.call_count, 0)

    def test_draw_score_no_stdscr(self):
        """Test drawing score when stdscr is None."""
        ui = CursesUI(width=60, height=30)

        ui.draw_score(10, GameStatus.PLAYING)

        # Should not crash

    def test_refresh(self):
        """Test refresh method."""
        ui = CursesUI(width=60, height=30)
        ui.stdscr = MagicMock()

        ui.refresh()

        ui.stdscr.refresh.assert_called_once()

    def test_refresh_no_stdscr(self):
        """Test refresh when stdscr is None."""
        ui = CursesUI(width=60, height=30)

        ui.refresh()

        # Should not crash

    @patch('curses.initscr')
    def test_get_input_up(self, mock_initscr):
        """Test getting UP input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = curses.KEY_UP

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertEqual(result, Direction.UP)

    @patch('curses.initscr')
    def test_get_input_down(self, mock_initscr):
        """Test getting DOWN input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = curses.KEY_DOWN

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertEqual(result, Direction.DOWN)

    @patch('curses.initscr')
    def test_get_input_left(self, mock_initscr):
        """Test getting LEFT input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = curses.KEY_LEFT

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertEqual(result, Direction.LEFT)

    @patch('curses.initscr')
    def test_get_input_right(self, mock_initscr):
        """Test getting RIGHT input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = curses.KEY_RIGHT

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertEqual(result, Direction.RIGHT)

    @patch('curses.initscr')
    def test_get_input_w(self, mock_initscr):
        """Test getting W input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = ord('w')

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertEqual(result, Direction.UP)

    @patch('curses.initscr')
    def test_get_input_s(self, mock_initscr):
        """Test getting S input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = ord('s')

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertEqual(result, Direction.DOWN)

    @patch('curses.initscr')
    def test_get_input_a(self, mock_initscr):
        """Test getting A input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = ord('a')

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertEqual(result, Direction.LEFT)

    @patch('curses.initscr')
    def test_get_input_d(self, mock_initscr):
        """Test getting D input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = ord('d')

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertEqual(result, Direction.RIGHT)

    @patch('curses.initscr')
    def test_get_input_quit(self, mock_initscr):
        """Test getting Q input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = ord('q')

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertEqual(result, Direction.QUIT)

    @patch('curses.initscr')
    def test_get_input_restart(self, mock_initscr):
        """Test getting R input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = ord('r')

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertEqual(result, Direction.RESET)

    @patch('curses.initscr')
    def test_get_input_none(self, mock_initscr):
        """Test getting no input."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.return_value = ord('x')  # Invalid key

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertIsNone(result)

    @patch('curses.initscr')
    def test_get_input_curses_error(self, mock_initscr):
        """Test handling curses error."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr
        mock_stdscr.getch.side_effect = curses.error()

        ui = CursesUI(width=60, height=30)
        ui.start()

        result = ui.get_input()

        self.assertIsNone(result)

    @patch('curses.initscr')
    def test_get_input_no_stdscr(self, mock_initscr):
        """Test get_input when stdscr is None."""
        ui = CursesUI(width=60, height=30)

        result = ui.get_input()

        self.assertIsNone(result)

    @patch('curses.initscr')
    def test_show_game_over(self, mock_initscr):
        """Test showing game over screen."""
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (25, 80)
        mock_initscr.return_value = mock_stdscr

        ui = CursesUI(width=60, height=30)
        ui.start()

        ui.show_game_over(10)

        # Should have called addstr multiple times
        self.assertGreater(ui.stdscr.addstr.call_count, 0)
        ui.stdscr.refresh.assert_called_once()

    @patch('curses.initscr')
    def test_show_start_screen(self, mock_initscr):
        """Test showing start screen."""
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (25, 80)
        mock_initscr.return_value = mock_stdscr

        ui = CursesUI(width=60, height=30)
        ui.start()

        ui.show_start_screen()

        # Should have called addstr multiple times
        self.assertGreater(ui.stdscr.addstr.call_count, 0)
        ui.stdscr.refresh.assert_called_once()

    @patch('curses.initscr')
    def test_wait_for_start_space(self, mock_initscr):
        """Test waiting for spacebar."""
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (25, 80)
        mock_initscr.return_value = mock_stdscr

        ui = CursesUI(width=60, height=30)
        ui.start()

        mock_stdscr.getch.return_value = ord(' ')

        result = ui.wait_for_start()

        self.assertTrue(result)

    @patch('curses.initscr')
    def test_wait_for_start_other(self, mock_initscr):
        """Test waiting for non-space input."""
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (25, 80)
        mock_initscr.return_value = mock_stdscr

        ui = CursesUI(width=60, height=30)
        ui.start()

        mock_stdscr.getch.return_value = ord('x')

        result = ui.wait_for_start()

        self.assertFalse(result)

    @patch('curses.initscr')
    def test_clear(self, mock_initscr):
        """Test clear method."""
        mock_stdscr = MagicMock()
        mock_initscr.return_value = mock_stdscr

        ui = CursesUI(width=60, height=30)
        ui.start()

        ui.clear()

        mock_stdscr.clear.assert_called_once()


# Import curses for testing
try:
    import curses
except ImportError:
    curses = None


if __name__ == '__main__':
    unittest.main()
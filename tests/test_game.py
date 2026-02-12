"""Integration-level tests for SnakeGame (mocked UI)."""

import pytest
from unittest.mock import MagicMock, patch

from snakeclaw.game import SnakeGame
from snakeclaw.model import Action, Direction, GameState


class TestSnakeGameInit:
    def test_creates_engine_and_ui(self):
        g = SnakeGame(width=40, height=20)
        assert g.engine.width == 40
        assert g.engine.height == 20
        assert g.ui.play_w == 40
        assert g.ui.play_h == 20

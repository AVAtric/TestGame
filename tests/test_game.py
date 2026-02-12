"""Integration-level tests for SnakeGame (mocked UI)."""

from snakeclaw.game import SnakeGame

class TestSnakeGameInit:
    def test_creates_engine_and_ui(self):
        g = SnakeGame(width=40, height=20)
        assert g.engine.width == 40
        assert g.engine.height == 20
        assert g.ui.play_w == 40
        assert g.ui.play_h == 20

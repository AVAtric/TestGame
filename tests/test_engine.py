"""Unit tests for GameEngine (pure logic, no terminal)."""

import json
import os

from snakeclaw.engine import GameEngine, HighScoreManager, HighScoreEntry, SPEED_LEVELS, POINTS_PER_LEVEL
from snakeclaw.model import Action, Direction, GameState, WallMode


# ── HighScoreManager ──────────────────────────────────────────────────────

def _tmp_path(tmp_path):
    return str(tmp_path / "hs.json")


class TestHighScoreManager:

    def test_empty_on_missing_file(self, tmp_path):
        mgr = HighScoreManager(path=_tmp_path(tmp_path))
        assert mgr.get_top() == []
        assert mgr.best == 0

    def test_add_and_retrieve(self, tmp_path):
        mgr = HighScoreManager(path=_tmp_path(tmp_path))
        mgr.add(42, "AAA")
        assert mgr.best == 42
        assert len(mgr.get_top()) == 1
        assert mgr.get_top()[0].initials == "AAA"

    def test_persist_and_reload(self, tmp_path):
        p = _tmp_path(tmp_path)
        mgr = HighScoreManager(path=p)
        mgr.add(10); mgr.add(20); mgr.add(30)
        mgr2 = HighScoreManager(path=p)
        assert mgr2.best == 30
        assert len(mgr2.get_top()) == 3

    def test_max_entries(self, tmp_path):
        mgr = HighScoreManager(path=_tmp_path(tmp_path), max_entries=3)
        for i in range(5):
            mgr.add(i * 10)
        assert len(mgr.get_top()) == 3
        assert mgr.get_top()[0].score == 40

    def test_is_high_score_empty(self, tmp_path):
        mgr = HighScoreManager(path=_tmp_path(tmp_path))
        assert mgr.is_high_score(1)
        assert not mgr.is_high_score(0)

    def test_is_high_score_full(self, tmp_path):
        mgr = HighScoreManager(path=_tmp_path(tmp_path), max_entries=2)
        mgr.add(10); mgr.add(20)
        assert mgr.is_high_score(15)  # beats min(10)
        assert not mgr.is_high_score(5)

    def test_corrupted_file(self, tmp_path):
        p = _tmp_path(tmp_path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write("NOT JSON")
        mgr = HighScoreManager(path=p)
        assert mgr.get_top() == []

    def test_wrong_structure_file(self, tmp_path):
        p = _tmp_path(tmp_path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            json.dump({"not": "a list"}, f)
        mgr = HighScoreManager(path=p)
        assert mgr.get_top() == []

    def test_entry_round_trip(self):
        e = HighScoreEntry(score=99, timestamp=1234.5, initials="ZZZ")
        d = e.to_dict()
        e2 = HighScoreEntry.from_dict(d)
        assert e2.score == 99 and e2.initials == "ZZZ"

    def test_add_skips_non_qualifying(self, tmp_path):
        # Full board of high scores; a low score must not be appended,
        # and must not touch disk.
        p = _tmp_path(tmp_path)
        mgr = HighScoreManager(path=p, max_entries=2)
        mgr.add(50, "AAA"); mgr.add(40, "BBB")
        mtime_before = os.path.getmtime(p)
        mgr.add(10, "CCC")  # below the cut
        assert [e.score for e in mgr.get_top()] == [50, 40]
        assert os.path.getmtime(p) == mtime_before  # no rewrite

    def test_add_zero_score_skipped(self, tmp_path):
        mgr = HighScoreManager(path=_tmp_path(tmp_path))
        mgr.add(0, "ZZZ")
        assert mgr.get_top() == []

    def test_save_is_atomic_no_tmp_left(self, tmp_path):
        p = _tmp_path(tmp_path)
        mgr = HighScoreManager(path=p)
        mgr.add(100, "AAA")
        # The temp sentinel must not linger after a successful save.
        assert not os.path.exists(p + ".tmp")


# ── GameEngine state transitions ──────────────────────────────────────────

class TestEngineMenu:
    def test_starts_in_menu(self):
        e = GameEngine()
        assert e.state == GameState.MENU

    def test_menu_navigate_down(self):
        e = GameEngine()
        assert e.menu_index == 0
        e.handle_input(Direction.DOWN)
        assert e.menu_index == 1

    def test_menu_navigate_up_wraps(self):
        e = GameEngine()
        e.handle_input(Direction.UP)
        assert e.menu_index == len(e.menu_items) - 1

    def test_menu_start_game(self):
        e = GameEngine()
        e.handle_input(Action.SELECT)  # "Start Game" is index 0
        assert e.state == GameState.PLAYING

    def test_menu_high_scores(self):
        e = GameEngine()
        e.menu_index = 2  # Start, Wall, [High Scores], Help, Quit
        e.handle_input(Action.SELECT)
        assert e.state == GameState.HIGH_SCORES

    def test_menu_help(self):
        e = GameEngine()
        e.menu_index = 3
        e.handle_input(Action.SELECT)
        assert e.state == GameState.HELP

    def test_menu_quit(self):
        e = GameEngine()
        e.menu_index = 4
        e.handle_input(Action.SELECT)
        assert e.state == GameState.QUIT

    def test_menu_toggles_wall_mode(self):
        e = GameEngine()
        assert e.wall_mode == WallMode.WRAP  # default
        e.menu_index = 1  # Wall toggle
        e.handle_input(Action.SELECT)
        assert e.wall_mode == WallMode.SOLID
        e.handle_input(Action.SELECT)
        assert e.wall_mode == WallMode.WRAP

    def test_menu_label_reflects_wall_mode(self):
        e = GameEngine()
        assert e.menu_items[1] == "Wall: Wrap"
        e.menu_index = 1
        e.handle_input(Action.SELECT)
        assert e.menu_items[1] == "Wall: Solid"

    def test_menu_q_quits(self):
        e = GameEngine()
        e.handle_input(Action.QUIT)
        assert e.state == GameState.QUIT


def _playing(tmp_path, wall_mode=WallMode.WRAP):
    e = GameEngine(highscore_path=str(tmp_path / "hs.json"),
                   wall_mode=wall_mode)
    e.new_game()
    return e


class TestEnginePlaying:

    def test_new_game_state(self, tmp_path):
        e = _playing(tmp_path)
        assert e.state == GameState.PLAYING
        assert e.score == 0
        assert e.level == 1
        assert e.snake is not None
        assert e.food is not None

    def test_direction_change(self, tmp_path):
        e = _playing(tmp_path)
        e.handle_input(Direction.DOWN)
        assert e.snake.direction == Direction.DOWN

    def test_pause(self, tmp_path):
        e = _playing(tmp_path)
        e.handle_input(Action.PAUSE)
        assert e.state == GameState.PAUSED

    def test_quit_while_playing(self, tmp_path):
        e = _playing(tmp_path)
        e.handle_input(Action.QUIT)
        assert e.state == GameState.QUIT

    def test_tick_moves_snake(self, tmp_path):
        e = _playing(tmp_path)
        head_before = e.snake.get_head()
        e.tick()
        assert e.snake.get_head() != head_before

    def test_tick_does_nothing_when_paused(self, tmp_path):
        e = _playing(tmp_path)
        e.state = GameState.PAUSED
        head_before = e.snake.get_head()
        e.tick()
        assert e.snake.get_head() == head_before

    def test_eat_food_scores(self, tmp_path):
        e = _playing(tmp_path)
        head = e.snake.get_head()
        d = e.snake.direction.value
        next_pos = (head[0] + d[0], head[1] + d[1])
        e.food.place(pos=next_pos)
        e.tick()
        assert e.score == 1

    def test_eat_food_grows_snake(self, tmp_path):
        e = _playing(tmp_path)
        initial_len = len(e.snake.get_body())
        head = e.snake.get_head()
        d = e.snake.direction.value
        e.food.place(pos=(head[0] + d[0], head[1] + d[1]))
        e.tick()
        assert len(e.snake.get_body()) == initial_len + 1

    def test_wall_collision_game_over(self, tmp_path):
        # Solid mode: walls are deadly. Pin food off the snake's rightward
        # path so it dies hitting the wall rather than scoring.
        e = _playing(tmp_path, wall_mode=WallMode.SOLID)
        e.food.place(pos=(0, 0))
        for _ in range(100):
            e.tick()
            if e.state == GameState.GAME_OVER:
                break
        assert e.state == GameState.GAME_OVER

    def test_wrap_mode_passes_through_wall(self, tmp_path):
        # Default WRAP mode: snake survives wall contact and re-enters opposite.
        e = _playing(tmp_path, wall_mode=WallMode.WRAP)
        # Park snake just before the right wall, body trailing left.
        e.snake.body = [(5, e.width - 1), (5, e.width - 2), (5, e.width - 3)]
        e.snake.direction = Direction.RIGHT
        e.snake._last_moved_direction = Direction.RIGHT
        # Pin food away so eating doesn't change state.
        e.food.place(pos=(0, 0))
        e.tick()
        assert e.state == GameState.PLAYING
        assert e.snake.get_head() == (5, 0)  # wrapped to opposite side

    def test_level_increases(self, tmp_path):
        e = _playing(tmp_path)
        for i in range(POINTS_PER_LEVEL):
            head = e.snake.get_head()
            d = e.snake.direction.value
            e.food.place(pos=(head[0] + d[0], head[1] + d[1]))
            e.tick()
        assert e.level == 2

    def test_self_collision_game_over(self, tmp_path):
        e = _playing(tmp_path)
        # Grow snake then turn into itself
        for i in range(6):
            head = e.snake.get_head()
            d = e.snake.direction.value
            e.food.place(pos=(head[0] + d[0], head[1] + d[1]))
            e.tick()
        e.handle_input(Direction.DOWN); e.tick()
        e.handle_input(Direction.LEFT); e.tick()
        e.handle_input(Direction.UP); e.tick()
        # Should be in ENTER_INITIALS state since we have a score
        assert e.state == GameState.ENTER_INITIALS
        # Confirm initials to proceed to GAME_OVER
        e.handle_input(Action.SELECT)
        assert e.state == GameState.GAME_OVER


class TestEnginePaused:
    def test_resume(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game()
        e.handle_input(Action.PAUSE)
        assert e.state == GameState.PAUSED
        e.handle_input(Action.PAUSE)
        assert e.state == GameState.PLAYING

    def test_quit_while_paused(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game()
        e.handle_input(Action.PAUSE)
        e.handle_input(Action.QUIT)
        assert e.state == GameState.QUIT

    def test_reset_while_paused(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game()
        e.score = 5
        e.handle_input(Action.PAUSE)
        e.handle_input(Action.RESET)
        assert e.state == GameState.PLAYING
        assert e.score == 0


class TestEngineGameOver:
    def test_restart(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game()
        e.state = GameState.GAME_OVER
        e.handle_input(Action.RESET)
        assert e.state == GameState.PLAYING

    def test_back_to_menu(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game()
        e.state = GameState.GAME_OVER
        e.handle_input(Action.MENU)
        assert e.state == GameState.MENU

    def test_quit(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game()
        e.state = GameState.GAME_OVER
        e.handle_input(Action.QUIT)
        assert e.state == GameState.QUIT

    def test_score_saved_on_game_over(self, tmp_path):
        # Solid mode so the snake reliably dies on the wall within 100 ticks.
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"),
                       wall_mode=WallMode.SOLID)
        e.new_game()
        # Feed snake to get score
        head = e.snake.get_head()
        d = e.snake.direction.value
        e.food.place(pos=(head[0] + d[0], head[1] + d[1]))
        e.tick()
        assert e.score == 1
        # Force game over
        for _ in range(100):
            e.tick()
            if e.state in (GameState.GAME_OVER, GameState.ENTER_INITIALS):
                break
        # If we're in ENTER_INITIALS, confirm to save the score
        if e.state == GameState.ENTER_INITIALS:
            e.handle_input(Action.SELECT)
        assert e.high_scores.best >= 1


class TestEngineOverlays:
    def test_high_scores_returns_to_menu(self):
        e = GameEngine()
        e.state = GameState.HIGH_SCORES
        e.handle_input(Action.SELECT)
        assert e.state == GameState.MENU

    def test_help_returns_to_menu(self):
        e = GameEngine()
        e.state = GameState.HELP
        e.handle_input(Direction.UP)  # any input
        assert e.state == GameState.MENU


class TestEngineFoodReachability:
    """Food (and bonus food) must spawn on cells the snake can actually reach
    from its current head — otherwise a coiled snake or solid-wall pocket can
    trap food where the player can never get to it."""

    def test_food_lands_on_reachable_cell(self, tmp_path):
        # Solid walls + a body that splits the playfield. Force the engine's
        # placement and confirm food never lands on the unreachable side.
        e = GameEngine(width=10, height=6,
                       highscore_path=str(tmp_path / "hs.json"),
                       wall_mode=WallMode.SOLID)
        e.new_game()
        # Build a vertical wall of snake at column 5; head on the left.
        e.snake.body = [(0, 0)] + [(r, 5) for r in range(6)]
        for _ in range(50):
            e._place_food_reachable()
            food_r, food_c = e.food.get_position()
            assert food_c < 5, f"food landed unreachable at {(food_r, food_c)}"

    def test_food_falls_back_when_no_reachable_cells(self, tmp_path):
        # If the head is fully walled in, _place_food_reachable should still
        # place the food somewhere (fallback) rather than infinite-loop.
        e = GameEngine(width=5, height=5,
                       highscore_path=str(tmp_path / "hs.json"),
                       wall_mode=WallMode.SOLID)
        e.new_game()
        # Head boxed in.
        e.snake.body = [(2, 2), (2, 1), (2, 3), (1, 2), (3, 2)]
        e._place_food_reachable()
        # Position must at least be inside the grid.
        r, c = e.food.get_position()
        assert 0 <= r < 5 and 0 <= c < 5

    def test_bonus_food_spawn_reachable(self, tmp_path):
        e = GameEngine(width=10, height=6,
                       highscore_path=str(tmp_path / "hs.json"),
                       wall_mode=WallMode.SOLID)
        e.new_game()
        e.snake.body = [(0, 0)] + [(r, 5) for r in range(6)]
        e.food.place(pos=(0, 1))  # left side, reachable
        for _ in range(20):
            e.bonus.despawn()
            e._spawn_bonus_reachable()
            if e.bonus.active:
                _, c = e.bonus.position
                assert c < 5

    def test_bonus_skips_when_nothing_reachable(self, tmp_path):
        e = GameEngine(width=5, height=5,
                       highscore_path=str(tmp_path / "hs.json"),
                       wall_mode=WallMode.SOLID)
        e.new_game()
        e.snake.body = [(2, 2), (2, 1), (2, 3), (1, 2), (3, 2)]
        e.bonus.despawn()
        e._spawn_bonus_reachable()
        assert not e.bonus.active


class TestEngineTickRate:
    def test_tick_rate_level_1(self):
        e = GameEngine()
        e.level = 1
        assert e.tick_rate == SPEED_LEVELS[1]

    def test_tick_rate_increases_with_level(self):
        e = GameEngine()
        e.level = 3
        assert e.tick_rate < SPEED_LEVELS[1]  # faster = smaller

    def test_none_input_ignored(self):
        e = GameEngine()
        state_before = e.state
        e.handle_input(None)
        assert e.state == state_before

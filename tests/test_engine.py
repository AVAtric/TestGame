"""Unit tests for GameEngine (pure logic, no terminal)."""

import json
import os

from snakeclaw.engine import GameEngine, HighScoreManager, HighScoreEntry, SPEED_LEVELS, POINTS_PER_LEVEL
from snakeclaw.constants import (CLASSIC_HEIGHT, CLASSIC_WIDTH, MODERN_HEIGHT,
                                  MODERN_WIDTH, NEAR_MISS_THRESHOLD,
                                  REGULAR_FRUITS)
from snakeclaw.model import (Action, Direction, Effect, FruitKind, GameMode,
                             GameState, WallMode)

# Single-point apple kind so eating-related tests can assert on exact scores.
APPLE = next(k for k in REGULAR_FRUITS if k.points == 1)


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
        # Menu order: Start, Classic, [High Scores], Help, Quit
        e = GameEngine()
        e.menu_index = 2
        e.handle_input(Action.SELECT)
        assert e.state == GameState.HIGH_SCORES

    def test_menu_help(self):
        e = GameEngine()
        e.menu_index = 3
        e.handle_input(Action.SELECT)
        assert e.state == GameState.HELP

    def test_menu_quit_goes_through_confirm(self):
        # Selecting "Quit" from the menu must also ask for confirmation —
        # consistent with pressing Q anywhere else in the game.
        e = GameEngine()
        e.menu_index = 4
        e.handle_input(Action.SELECT)
        assert e.state == GameState.CONFIRM_QUIT
        e.handle_input(Action.YES)
        assert e.state == GameState.QUIT

    def test_menu_start_uses_wrap_walls(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.menu_index = 0  # Start Game
        e.handle_input(Action.SELECT)
        assert e.state == GameState.PLAYING
        assert e.wall_mode == WallMode.WRAP

    def test_menu_classic_uses_solid_walls(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.menu_index = 1  # Classic Game
        e.handle_input(Action.SELECT)
        assert e.state == GameState.PLAYING
        assert e.wall_mode == WallMode.SOLID

    def test_menu_labels(self):
        e = GameEngine()
        assert e.menu_items[0] == "Start Game"
        assert e.menu_items[1] == "Classic Game"
        assert e.menu_items[2] == "High Scores"

    def test_high_scores_per_mode_separate(self, tmp_path):
        # Solid-mode entries shouldn't leak into the wrap leaderboard.
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.wall_mode = WallMode.WRAP
        e.high_scores.add(50, "WRP")
        e.wall_mode = WallMode.SOLID
        e.high_scores.add(20, "CLS")
        # Wrap table only has the wrap entry.
        wrap_top = e.high_scores_for(WallMode.WRAP).get_top()
        solid_top = e.high_scores_for(WallMode.SOLID).get_top()
        assert [x.initials for x in wrap_top] == ["WRP"]
        assert [x.initials for x in solid_top] == ["CLS"]

    def test_menu_q_opens_quit_confirm(self):
        # Q is no longer an instant-quit — the player has to confirm. Also
        # verifies the default-selected button is "Stay" (index 0).
        e = GameEngine()
        e.handle_input(Action.QUIT)
        assert e.state == GameState.CONFIRM_QUIT
        assert e.confirm_quit_index == 0

    def test_menu_q_then_yes_quits(self):
        e = GameEngine()
        e.handle_input(Action.QUIT)
        e.handle_input(Action.YES)
        assert e.state == GameState.QUIT

    def test_menu_q_then_no_returns_to_menu(self):
        e = GameEngine()
        e.handle_input(Action.QUIT)
        e.handle_input(Action.NO)
        assert e.state == GameState.MENU


def _playing(tmp_path, wall_mode=WallMode.WRAP):
    # new_game() now picks wall_mode from the GameMode (MODERN→WRAP,
    # CLASSIC→SOLID). For tests that need to exercise solid-wall behavior
    # *with* the modern feature set, override wall_mode after the reset.
    e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
    e.new_game()
    e.wall_mode = wall_mode
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

    def test_quit_while_playing_asks_confirm(self, tmp_path):
        # Quitting mid-game must now go through the confirm overlay. The
        # original state is preserved so cancel returns the player to play.
        e = _playing(tmp_path)
        e.handle_input(Action.QUIT)
        assert e.state == GameState.CONFIRM_QUIT
        assert e._pre_quit_state == GameState.PLAYING

    def test_quit_confirm_cancel_resumes_play(self, tmp_path):
        e = _playing(tmp_path)
        e.handle_input(Action.QUIT)
        e.handle_input(Action.NO)
        assert e.state == GameState.PLAYING

    def test_quit_confirm_yes_actually_quits(self, tmp_path):
        e = _playing(tmp_path)
        e.handle_input(Action.QUIT)
        e.handle_input(Action.YES)
        assert e.state == GameState.QUIT

    def test_quit_confirm_arrow_select_quit(self, tmp_path):
        # Arrow keys + Enter is the menu-driven path: ←/→ toggles between
        # Stay (0) and Quit (1), and SELECT confirms whichever is highlighted.
        e = _playing(tmp_path)
        e.handle_input(Action.QUIT)
        e.handle_input(Direction.RIGHT)
        assert e.confirm_quit_index == 1
        e.handle_input(Action.SELECT)
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
        # Pin to apple (1pt) so the assertion is deterministic; in normal play
        # the kind is weighted-random and would score 1–3.
        e.food.place(pos=next_pos, kind=APPLE)
        e.tick()
        assert e.score == 1

    def test_eat_food_grows_snake(self, tmp_path):
        e = _playing(tmp_path)
        initial_len = len(e.snake.get_body())
        head = e.snake.get_head()
        d = e.snake.direction.value
        e.food.place(pos=(head[0] + d[0], head[1] + d[1]), kind=APPLE)
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
            e.food.place(pos=(head[0] + d[0], head[1] + d[1]), kind=APPLE)
            e.tick()
        assert e.level == 2

    def test_self_collision_game_over(self, tmp_path):
        e = _playing(tmp_path)
        # Grow snake then turn into itself
        for i in range(6):
            head = e.snake.get_head()
            d = e.snake.direction.value
            e.food.place(pos=(head[0] + d[0], head[1] + d[1]), kind=APPLE)
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
        e.handle_input(Action.YES)  # confirm
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
        e.handle_input(Action.YES)  # confirm
        assert e.state == GameState.QUIT

    def test_score_saved_on_game_over(self, tmp_path):
        # Solid mode so the snake reliably dies on the wall within 100 ticks.
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game()
        e.wall_mode = WallMode.SOLID
        # Feed snake to get score (apple is 1 pt)
        head = e.snake.get_head()
        d = e.snake.direction.value
        e.food.place(pos=(head[0] + d[0], head[1] + d[1]), kind=APPLE)
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
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(width=10, height=6)
        e.wall_mode = WallMode.SOLID
        # Build a vertical wall of snake at column 5; head on the left.
        e.snake.body = [(0, 0)] + [(r, 5) for r in range(6)]
        for _ in range(50):
            e._place_fruit_pathfinder()
            food_r, food_c = e.food.get_position()
            assert food_c < 5, f"food landed unreachable at {(food_r, food_c)}"

    def test_food_falls_back_when_no_reachable_cells(self, tmp_path):
        # If the head is fully walled in, _place_fruit_pathfinder should still
        # place the food somewhere (fallback) rather than infinite-loop.
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(width=5, height=5)
        e.wall_mode = WallMode.SOLID
        # Head boxed in.
        e.snake.body = [(2, 2), (2, 1), (2, 3), (1, 2), (3, 2)]
        e._place_fruit_pathfinder()
        # Position must at least be inside the grid.
        r, c = e.food.get_position()
        assert 0 <= r < 5 and 0 <= c < 5

    def test_bonus_food_spawn_reachable(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(width=10, height=6)
        e.wall_mode = WallMode.SOLID
        e.snake.body = [(0, 0)] + [(r, 5) for r in range(6)]
        e.food.place(pos=(0, 1))  # left side, reachable
        for _ in range(20):
            e.bonus.despawn()
            e._spawn_power_up_pathfinder()
            if e.bonus.active:
                _, c = e.bonus.position
                assert c < 5

    def test_bonus_skips_when_nothing_reachable(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(width=5, height=5)
        e.wall_mode = WallMode.SOLID
        e.snake.body = [(2, 2), (2, 1), (2, 3), (1, 2), (3, 2)]
        e.bonus.despawn()
        e._spawn_power_up_pathfinder()
        assert not e.bonus.active


class TestEngineGameModes:
    """The two game modes — Modern (full features) and Classic (Nokia-pure)."""

    def test_classic_uses_small_field_and_solid_walls(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.CLASSIC)
        assert e.width == CLASSIC_WIDTH
        assert e.height == CLASSIC_HEIGHT
        assert e.wall_mode == WallMode.SOLID
        assert e.power_up is None  # no power-ups in classic
        # Classic fruit is apples-only; eating must always score exactly 1.
        head = e.snake.get_head()
        d = e.snake.direction.value
        e.fruit.place(pos=(head[0] + d[0], head[1] + d[1]))
        e.tick()
        assert e.score == 1

    def test_modern_uses_full_field_and_wrap_walls(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.MODERN)
        assert e.width == MODERN_WIDTH
        assert e.height == MODERN_HEIGHT
        assert e.wall_mode == WallMode.WRAP
        assert e.power_up is not None

    def test_classic_suppresses_popups(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.CLASSIC)
        head = e.snake.get_head()
        d = e.snake.direction.value
        e.fruit.place(pos=(head[0] + d[0], head[1] + d[1]))
        e.tick()
        assert e.popups == []  # silent classic

    def test_modern_emits_popups(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.MODERN)
        head = e.snake.get_head()
        d = e.snake.direction.value
        e.fruit.place(pos=(head[0] + d[0], head[1] + d[1]))
        e.tick()
        assert len(e.popups) == 1


class TestEngineEngagementNudges:
    """Game-over engagement nudges (the dark-pattern fields)."""

    def test_streak_increments_on_restart_from_game_over(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.MODERN)
        assert e.session_streak == 1
        e.state = GameState.GAME_OVER
        e.handle_input(Action.RESET)
        assert e.session_streak == 2
        e.state = GameState.GAME_OVER
        e.handle_input(Action.RESET)
        assert e.session_streak == 3

    def test_streak_resets_when_returning_to_menu(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.MODERN)
        e.state = GameState.GAME_OVER
        e.handle_input(Action.RESET)
        assert e.session_streak == 2
        e.handle_input(Action.MENU)  # bail out — streak should die
        assert e.session_streak == 0

    def test_personal_best_flag_set(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.MODERN)
        e.score = 10
        e._on_collision()
        assert e.is_personal_best is True

    def test_personal_best_not_set_when_below_best(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.MODERN)
        e.high_scores.add(50, "ZZZ")
        e.score = 10
        e._on_collision()
        assert e.is_personal_best is False

    def test_near_miss_message_when_close_to_best(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.MODERN)
        e.high_scores.add(20, "ZZZ")
        e.score = 18  # 2 away — within threshold
        e._on_collision()
        assert "2" in e.near_miss_message
        assert "best" in e.near_miss_message.lower()

    def test_no_near_miss_when_personal_best(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.MODERN)
        e.high_scores.add(10, "ZZZ")
        e.score = 100
        e._on_collision()
        assert e.near_miss_message == ""

    def test_last_score_remembered_for_next_round(self, tmp_path):
        e = GameEngine(highscore_path=str(tmp_path / "hs.json"))
        e.new_game(GameMode.MODERN)
        e.score = 7
        e._on_collision()
        assert e.last_score == 7


class TestEngineEffectsAndPopups:
    """Power-up effects (buffs, shrink) and the floating-score popup queue."""

    def _eat_powerup(self, e, kind: FruitKind):
        """Force-spawn a power-up of the given kind right in front of the
        snake's head and tick once so the snake eats it."""
        head = e.snake.get_head()
        d = e.snake.direction.value
        target = (head[0] + d[0], head[1] + d[1])
        e.power_up.spawn_at(target, kind=kind)
        e.tick()

    def _kind(self, name: str) -> FruitKind:
        return next(k for k in __import__('snakeclaw.constants',
                                          fromlist=['POWER_UPS']).POWER_UPS
                    if k.name == name)

    def test_speed_up_sets_buff(self, tmp_path):
        e = _playing(tmp_path)
        base_rate = e.tick_rate
        self._eat_powerup(e, self._kind("speed"))
        assert e.buff_active
        assert e.speed_buff_label == "FAST"
        assert e.tick_rate < base_rate  # faster = smaller interval

    def test_slow_down_sets_buff(self, tmp_path):
        e = _playing(tmp_path)
        base_rate = e.tick_rate
        self._eat_powerup(e, self._kind("slow"))
        assert e.buff_active
        assert e.speed_buff_label == "SLOW"
        assert e.tick_rate > base_rate  # slower = bigger interval

    def test_shrink_removes_segments(self, tmp_path):
        e = _playing(tmp_path)
        # Grow first so there's enough body to shrink (start length=3).
        for _ in range(4):
            head = e.snake.get_head()
            d = e.snake.direction.value
            e.food.place(pos=(head[0] + d[0], head[1] + d[1]), kind=APPLE)
            e.tick()
        before = len(e.snake.body)
        self._eat_powerup(e, self._kind("shrink"))
        # Eating grows by 1, then shrink removes SHRINK_AMOUNT (=2), so net -1.
        from snakeclaw.constants import SHRINK_AMOUNT
        assert len(e.snake.body) == before + 1 - SHRINK_AMOUNT

    def test_eating_creates_popup(self, tmp_path):
        e = _playing(tmp_path)
        head = e.snake.get_head()
        d = e.snake.direction.value
        e.food.place(pos=(head[0] + d[0], head[1] + d[1]), kind=APPLE)
        e.tick()
        assert len(e.popups) == 1
        assert e.popups[0].text == "+1"

    def test_buff_expires(self, tmp_path):
        # Fast-forward by reaching back into the buff timer.
        e = _playing(tmp_path)
        self._eat_powerup(e, self._kind("speed"))
        assert e.buff_active
        e.speed_buff_until = 0.0  # simulate expiry without sleeping
        # Need an actual time check — call _expire_buffs directly.
        e._expire_buffs()
        assert not e.buff_active
        assert e.speed_multiplier == 1.0


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

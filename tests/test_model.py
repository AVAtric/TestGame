"""Unit tests for Snake game models."""

import pytest
from snakeclaw.model import (Direction, Effect, Fruit, FruitKind, GameState,
                             OPPOSITE, PowerUp, ScorePopup, Snake, WallMode,
                             bfs_distances, pick_kind, reachable_cells)


# Lightweight fixtures-as-helpers — keep tests self-contained.
APPLE = FruitKind(name="apple", char="()", points=1, color=2, weight=1.0)
CHERRY = FruitKind(name="cherry", char="cc", points=2, color=3, weight=1.0)
SPEED_UP = FruitKind(name="speed", char=">>", points=3, color=7, weight=1.0,
                     effect=Effect.SPEED_UP, lifetime=4.0)
SHRINKER = FruitKind(name="shrink", char="vv", points=4, color=6, weight=1.0,
                     effect=Effect.SHRINK, lifetime=4.0)


def _fruit(width=60, height=30, pos=None, kinds=(APPLE,)):
    return Fruit(width, height, kinds=kinds, initial_position=pos)


def _power(width=20, height=20, kinds=(SPEED_UP,)):
    return PowerUp(width, height, kinds=kinds)


# ── Direction ──────────────────────────────────────────────────────────────

class TestDirection:
    def test_values(self):
        assert Direction.UP.value == (-1, 0)
        assert Direction.DOWN.value == (1, 0)
        assert Direction.LEFT.value == (0, -1)
        assert Direction.RIGHT.value == (0, 1)

    def test_opposite_map(self):
        assert OPPOSITE[Direction.UP] == Direction.DOWN
        assert OPPOSITE[Direction.DOWN] == Direction.UP
        assert OPPOSITE[Direction.LEFT] == Direction.RIGHT
        assert OPPOSITE[Direction.RIGHT] == Direction.LEFT


class TestGameState:
    def test_all_states_exist(self):
        for name in ("MENU", "PLAYING", "PAUSED", "GAME_OVER",
                      "HIGH_SCORES", "HELP", "QUIT"):
            assert hasattr(GameState, name)


# ── Snake ──────────────────────────────────────────────────────────────────

class TestSnakeInit:
    def test_default_direction_up(self):
        s = Snake((10, 10))
        assert s.get_head() == (10, 10)
        assert s.get_body()[1] == (11, 10)  # trails downward
        assert len(s.get_body()) == 3

    def test_custom_length(self):
        s = Snake((5, 5), length=5)
        assert len(s.get_body()) == 5

    def test_direction_right(self):
        s = Snake((5, 5), direction=Direction.RIGHT)
        assert s.get_body()[1] == (5, 4)  # trails left

    def test_direction_left(self):
        s = Snake((5, 5), direction=Direction.LEFT)
        assert s.get_body()[1] == (5, 6)  # trails right


class TestSnakeMovement:
    @pytest.mark.parametrize("direction,expected_head", [
        (Direction.UP, (4, 5)),
        (Direction.DOWN, (6, 5)),
        (Direction.LEFT, (5, 4)),
        (Direction.RIGHT, (5, 6)),
    ])
    def test_move(self, direction, expected_head):
        s = Snake((5, 5), direction=direction)
        s.move()
        assert s.get_head() == expected_head

    def test_move_preserves_length(self):
        s = Snake((5, 5), direction=Direction.RIGHT)
        before = len(s.get_body())
        s.move()
        assert len(s.get_body()) == before

    def test_grow_increases_length(self):
        s = Snake((5, 5), direction=Direction.RIGHT)
        s.grow_snake()
        s.move()
        assert len(s.get_body()) == 4


class TestSnakeDirection:
    def test_set_valid_direction(self):
        s = Snake((5, 5), direction=Direction.RIGHT)
        s.set_direction(Direction.UP)
        assert s.direction == Direction.UP

    def test_reject_180_right_left(self):
        s = Snake((5, 5), direction=Direction.RIGHT)
        s.set_direction(Direction.LEFT)
        assert s.direction == Direction.RIGHT

    def test_reject_180_up_down(self):
        s = Snake((5, 5), direction=Direction.UP)
        s.set_direction(Direction.DOWN)
        assert s.direction == Direction.UP

    def test_reject_180_down_up(self):
        s = Snake((5, 5), direction=Direction.DOWN)
        s.set_direction(Direction.UP)
        assert s.direction == Direction.DOWN

    def test_reject_180_left_right(self):
        s = Snake((5, 5), direction=Direction.LEFT)
        s.set_direction(Direction.RIGHT)
        assert s.direction == Direction.LEFT

    def test_reject_180_via_double_input_in_one_tick(self):
        # Snake going RIGHT. Two perpendicular inputs queued before the next move
        # must not stack into a 180° turn (RIGHT → UP → LEFT) — that would drive
        # the head straight back into its own neck on the following tick.
        s = Snake((5, 5), direction=Direction.RIGHT)
        s.set_direction(Direction.UP)
        s.set_direction(Direction.LEFT)
        assert s.direction == Direction.UP


class TestSnakeCollision:
    def test_wall_right(self):
        s = Snake((5, 19), direction=Direction.RIGHT)
        s.move()
        assert s.check_collision(20, 20)

    def test_wall_left(self):
        s = Snake((5, 0), direction=Direction.LEFT)
        s.move()
        assert s.check_collision(20, 20)

    def test_wall_up(self):
        s = Snake((0, 5), direction=Direction.UP)
        s.move()
        assert s.check_collision(20, 20)

    def test_wall_down(self):
        s = Snake((19, 5), direction=Direction.DOWN)
        s.move()
        assert s.check_collision(20, 20)

    def test_no_collision(self):
        s = Snake((5, 5), direction=Direction.RIGHT)
        s.move()
        assert not s.check_collision(20, 20)

    def test_self_collision(self):
        s = Snake((5, 5), length=5, direction=Direction.RIGHT)
        s.body = [(5, 5), (5, 6), (5, 7), (6, 7), (6, 6), (6, 5), (5, 5)]
        assert s.check_collision(20, 20)

    def test_check_next_move_wall(self):
        s = Snake((5, 19), direction=Direction.RIGHT)
        assert s.check_next_move(20, 20)

    def test_check_next_move_safe(self):
        s = Snake((5, 15), direction=Direction.RIGHT)
        assert not s.check_next_move(20, 20)

    def test_check_next_move_self(self):
        s = Snake((5, 5), direction=Direction.RIGHT)
        for _ in range(5):
            s.grow_snake()
            s.move()
        s.set_direction(Direction.DOWN); s.move()
        s.set_direction(Direction.LEFT); s.move()
        s.set_direction(Direction.UP)
        assert s.check_next_move(20, 20)


class TestSnakeWrap:
    def test_compute_next_head_wraps_right(self):
        s = Snake((5, 19), direction=Direction.RIGHT)
        assert s.compute_next_head(20, 20, wrap=True) == (5, 0)

    def test_compute_next_head_wraps_up(self):
        s = Snake((0, 5), direction=Direction.UP)
        assert s.compute_next_head(20, 20, wrap=True) == (19, 5)

    def test_compute_next_head_no_wrap(self):
        s = Snake((5, 19), direction=Direction.RIGHT)
        assert s.compute_next_head(20, 20, wrap=False) == (5, 20)

    def test_check_next_move_wrap_ignores_walls(self):
        s = Snake((5, 19), direction=Direction.RIGHT)
        assert not s.check_next_move(20, 20, wrap=True)

    def test_move_with_explicit_head(self):
        s = Snake((5, 5), direction=Direction.RIGHT)
        s.move(new_head=(5, 0))  # caller-supplied wrap position
        assert s.get_head() == (5, 0)

    def test_wall_mode_enum_values(self):
        assert WallMode.WRAP.value == "wrap"
        assert WallMode.SOLID.value == "solid"


class TestSnakeHelpers:
    def test_get_head(self):
        s = Snake((10, 10))
        assert s.get_head() == (10, 10)

    def test_get_tail(self):
        s = Snake((10, 10), direction=Direction.RIGHT)
        assert s.get_tail() == (10, 8)

    def test_get_body_returns_copy(self):
        s = Snake((10, 10))
        body = s.get_body()
        body.append((99, 99))
        assert (99, 99) not in s.body


# ── Fruit ──────────────────────────────────────────────────────────────────

class TestFruit:
    def test_init_random_in_bounds(self):
        f = _fruit()
        r, c = f.get_position()
        assert 0 <= r < 30
        assert 0 <= c < 60

    def test_init_custom_position(self):
        f = _fruit(pos=(15, 15))
        assert f.get_position() == (15, 15)

    def test_place_explicit(self):
        f = _fruit()
        f.place(pos=(20, 20))
        assert f.get_position() == (20, 20)

    def test_place_avoids_snake(self):
        body = [(r, 10) for r in range(30)]  # full column
        f = _fruit()
        f.place(snake_body=body)
        assert f.get_position() not in body

    def test_check_eaten(self):
        f = _fruit(pos=(15, 15))
        assert f.check_eaten((15, 15))

    def test_check_not_eaten(self):
        f = _fruit(pos=(15, 15))
        assert not f.check_eaten((15, 16))

    def test_dimensions_stored(self):
        f = _fruit()
        assert f.width == 60 and f.height == 30

    def test_kind_drives_points_and_char(self):
        f = _fruit(kinds=(CHERRY,))
        f.place(pos=(0, 0))
        assert f.get_points() == 2
        assert f.get_char() == "cc"

    def test_weighted_pick_picks_only_kind_when_single(self):
        # With one kind, every pick must be that kind regardless of weight.
        for _ in range(20):
            assert pick_kind((APPLE,)) is APPLE

    def test_requires_kinds(self):
        with pytest.raises(ValueError):
            Fruit(60, 30, kinds=())


# ── PowerUp ────────────────────────────────────────────────────────────────

class TestPowerUp:
    def test_inactive_does_not_blink(self):
        b = _power()
        assert not b.active
        assert not b.is_blinking()

    def test_blinks_immediately_after_spawn(self):
        # Power-ups blink the entire time they're on screen.
        b = _power()
        b.spawn_at((1, 1))
        assert b.active
        assert b.is_blinking()

    def test_despawn_clears_position(self):
        b = _power()
        b.spawn_at((3, 3))
        b.despawn()
        assert not b.active
        assert b.position is None

    def test_spawn_uses_kind_lifetime(self):
        # When the kind specifies a lifetime, that overrides default_duration.
        kind = FruitKind(name="x", char="xx", points=1, color=1,
                         lifetime=2.5)
        b = PowerUp(20, 20, kinds=(kind,), default_duration=99.0)
        b.spawn_at((0, 0))
        assert b.duration == 2.5

    def test_get_effect_reports_kind_effect(self):
        b = _power(kinds=(SPEED_UP,))
        b.spawn_at((1, 1))
        assert b.get_effect() == Effect.SPEED_UP


class TestSnakeShrink:
    def test_shrink_removes_tail(self):
        s = Snake((5, 5), length=5, direction=Direction.RIGHT)
        removed = s.shrink(2)
        assert removed == 2
        assert len(s.body) == 3

    def test_shrink_preserves_head(self):
        # Even with a giant ask, snake never falls below 1 segment.
        s = Snake((5, 5), length=3, direction=Direction.RIGHT)
        removed = s.shrink(10)
        assert removed == 2  # only 2 tail segments to remove
        assert len(s.body) == 1


class TestScorePopup:
    def test_expires_after_deadline(self):
        p = ScorePopup(position=(0, 0), text="+1", color=2, expires_at=100.0)
        assert not p.is_expired(now=99.9)
        assert p.is_expired(now=100.0)
        assert p.is_expired(now=200.0)


# ── BFS distances (the new pathfinder primitive) ──────────────────────────

class TestBfsDistances:
    def test_distance_increases_with_steps(self):
        d = bfs_distances([(2, 2)], head=(2, 2),
                          width=5, height=5, wrap=False)
        assert d[(2, 3)] == 1
        assert d[(2, 4)] == 2
        assert d[(0, 0)] == 4  # |2-0| + |2-0|

    def test_head_not_in_distances(self):
        d = bfs_distances([(0, 0)], head=(0, 0),
                          width=3, height=3, wrap=False)
        assert (0, 0) not in d

    def test_wrap_shortens_corner(self):
        d = bfs_distances([(0, 0)], head=(0, 0),
                          width=4, height=4, wrap=True)
        # corner-to-corner under wrap is at most 2+2=4 but the closest one is
        # actually (0,3): wraps to dist 1 horizontally.
        assert d[(0, 3)] == 1
        assert d[(3, 0)] == 1


# ── reachable_cells ───────────────────────────────────────────────────────

class TestReachableCells:
    def test_open_grid_reaches_everything(self):
        cells = reachable_cells([(2, 2)], head=(2, 2),
                                width=5, height=5, wrap=False)
        assert len(cells) == 24  # 5x5 - head

    def test_excludes_head(self):
        cells = reachable_cells([(2, 2)], head=(2, 2),
                                width=5, height=5, wrap=False)
        assert (2, 2) not in cells

    def test_body_blocks_partition(self):
        # Vertical wall of body cells splits the 5x5 grid in two when walls
        # are solid; head on the left can only reach the left side.
        body = [(r, 2) for r in range(5)] + [(0, 0)]
        cells = reachable_cells(body, head=(0, 0),
                                width=5, height=5, wrap=False)
        # left half (cols 0,1) minus head and (0,0 already head)
        assert all(c < 2 for _, c in cells)
        # No cell on the right side leaks through.
        assert not any(c > 2 for _, c in cells)

    def test_wrap_bypasses_partition(self):
        # Same vertical wall, but wrap mode means the head can go around
        # the torus and reach the right side.
        body = [(r, 2) for r in range(5)] + [(0, 0)]
        cells = reachable_cells(body, head=(0, 0),
                                width=5, height=5, wrap=True)
        assert any(c > 2 for _, c in cells)

    def test_fully_walled_head_returns_empty(self):
        # Head boxed in by body on all 4 sides.
        body = [(0, 0), (0, 1), (1, 0), (2, 1), (1, 2)]
        cells = reachable_cells(body, head=(1, 1),
                                width=5, height=5, wrap=False)
        assert cells == set()

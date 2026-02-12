"""Unit tests for Snake game models."""

import pytest
from snakeclaw.model import Snake, Food, Direction, GameState, OPPOSITE


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

    def test_opposite_direction_static(self):
        assert Snake._opposite_direction(Direction.UP) == Direction.DOWN
        assert Snake._opposite_direction(Direction.LEFT) == Direction.RIGHT


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


# ── Food ───────────────────────────────────────────────────────────────────

class TestFood:
    def test_init_random_in_bounds(self):
        f = Food(60, 30)
        r, c = f.get_position()
        assert 0 <= r < 30
        assert 0 <= c < 60

    def test_init_custom_position(self):
        f = Food(60, 30, (15, 15))
        assert f.get_position() == (15, 15)

    def test_place_explicit(self):
        f = Food(60, 30)
        f.place(pos=(20, 20))
        assert f.get_position() == (20, 20)

    def test_place_avoids_snake(self):
        body = [(r, 10) for r in range(30)]  # full column
        f = Food(60, 30)
        f.place(snake_body=body)
        assert f.get_position() not in body

    def test_check_eaten(self):
        f = Food(60, 30, (15, 15))
        assert f.check_eaten((15, 15))

    def test_check_not_eaten(self):
        f = Food(60, 30, (15, 15))
        assert not f.check_eaten((15, 16))

    def test_dimensions_stored(self):
        f = Food(60, 30)
        assert f.width == 60 and f.height == 30

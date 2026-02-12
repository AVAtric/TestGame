import pytest
from snakeclaw.model import Snake, Direction, Food


class TestSnakeGrowth:
    def test_snake_grows_when_eating(self):
        # Place snake near food
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        food = Food(width=10, height=10, initial_position=(5, 6))

        # Simulate a game tick manually: check next move before moving
        next_head = (snake.body[0][0] + snake.direction.value[0], snake.body[0][1] + snake.direction.value[1])
        assert food.check_eaten(next_head)
        snake.grow_snake()
        food.place(snake.get_body())

        # Move snake
        snake.move()

        # After moving and eating, snake should have grown by 1 segment
        assert len(snake.get_body()) == 4
        assert snake.get_head() == (5, 6)


class TestDirectionPrevention:
    def test_prevent_180_degree_turn(self):
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        # Move once to update body
        snake.move()
        assert snake.get_head() == (5, 6)
        # Attempt to reverse direction
        snake.set_direction(Direction.LEFT)
        # Direction should remain RIGHT
        assert snake.direction == Direction.RIGHT
        # Move again; head should move right
        snake.move()
        assert snake.get_head() == (5, 7)

    def test_allowed_direction_change(self):
        snake = Snake((5, 5), length=3, direction=Direction.RIGHT)
        snake.set_direction(Direction.UP)
        assert snake.direction == Direction.UP
        snake.move()
        assert snake.get_head() == (4, 5)


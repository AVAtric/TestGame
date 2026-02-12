"""Pure game engine — no terminal/curses dependency."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import List, Optional, Union

from .model import Action, Direction, Food, GameState, Snake


# ---------------------------------------------------------------------------
# High-score persistence
# ---------------------------------------------------------------------------

@dataclass
class HighScoreEntry:
    score: int
    timestamp: float
    initials: str = "---"

    def to_dict(self) -> dict:
        return {"score": self.score, "timestamp": self.timestamp,
                "initials": self.initials}

    @classmethod
    def from_dict(cls, d: dict) -> "HighScoreEntry":
        return cls(score=int(d.get("score", 0)),
                   timestamp=float(d.get("timestamp", 0)),
                   initials=str(d.get("initials", "---")))


class HighScoreManager:
    """Manage persisted high-score list."""

    DEFAULT_PATH = os.path.join(
        os.path.dirname(__file__), "data", "highscores.json")

    def __init__(self, path: Optional[str] = None, max_entries: int = 10):
        self.path = path or self.DEFAULT_PATH
        self.max_entries = max_entries
        self._scores: List[HighScoreEntry] = []
        self.load()

    # -- persistence ---------------------------------------------------------

    def load(self) -> None:
        try:
            with open(self.path, "r") as fh:
                data = json.load(fh)
            if not isinstance(data, list):
                data = []
            self._scores = [HighScoreEntry.from_dict(e) for e in data]
        except (FileNotFoundError, json.JSONDecodeError, TypeError, KeyError):
            self._scores = []

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as fh:
            json.dump([e.to_dict() for e in self._scores], fh, indent=2)

    # -- queries -------------------------------------------------------------

    def get_top(self, n: Optional[int] = None) -> List[HighScoreEntry]:
        n = n or self.max_entries
        return sorted(self._scores, key=lambda e: e.score, reverse=True)[:n]

    def is_high_score(self, score: int) -> bool:
        if len(self._scores) < self.max_entries:
            return score > 0
        return score > min(e.score for e in self._scores)

    @property
    def best(self) -> int:
        return max((e.score for e in self._scores), default=0)

    # -- mutations -----------------------------------------------------------

    def add(self, score: int, initials: str = "---") -> None:
        entry = HighScoreEntry(score=score, timestamp=time.time(),
                               initials=initials)
        self._scores.append(entry)
        self._scores = sorted(self._scores, key=lambda e: e.score,
                              reverse=True)[:self.max_entries]
        self.save()


# ---------------------------------------------------------------------------
# Game engine (pure logic, no I/O)
# ---------------------------------------------------------------------------

# Speed curve: level → tick interval in seconds
SPEED_LEVELS = {
    1: 0.18,
    2: 0.15,
    3: 0.13,
    4: 0.11,
    5: 0.09,
    6: 0.07,
}
POINTS_PER_LEVEL = 5  # advance level every N points


class GameEngine:
    """Core game logic with no terminal dependency."""

    def __init__(self, width: int = 48, height: int = 30,
                 highscore_path: Optional[str] = None):
        self.width = width
        self.height = height
        self.state: GameState = GameState.MENU
        self.snake: Optional[Snake] = None
        self.food: Optional[Food] = None
        self.score: int = 0
        self.level: int = 1
        self.high_scores = HighScoreManager(path=highscore_path)

        # Menu state
        self.menu_items = ["Start Game", "High Scores", "Help", "Quit"]
        self.menu_index: int = 0

        # Initials entry state
        self.current_initials: List[str] = ['A', 'A', 'A']
        self.initials_cursor: int = 0

    # -- helpers -------------------------------------------------------------

    @property
    def tick_rate(self) -> float:
        return SPEED_LEVELS.get(self.level, 0.07)

    @property
    def high_score(self) -> int:
        return max(self.high_scores.best, self.score)

    # -- init / reset --------------------------------------------------------

    def new_game(self) -> None:
        self.snake = Snake((self.height // 2, self.width // 4),
                           length=3, direction=Direction.RIGHT)
        self.food = Food(self.width, self.height)
        # Ensure food not on snake
        self.food.place(snake_body=self.snake.get_body())
        self.score = 0
        self.level = 1
        self.state = GameState.PLAYING

    # -- input handling ------------------------------------------------------

    def handle_input(self, inp: Optional[Union[Direction, Action]]) -> None:
        """Process a single input event."""
        if inp is None:
            return

        if self.state == GameState.MENU:
            self._handle_menu_input(inp)
        elif self.state == GameState.PLAYING:
            self._handle_playing_input(inp)
        elif self.state == GameState.PAUSED:
            self._handle_paused_input(inp)
        elif self.state == GameState.GAME_OVER:
            self._handle_game_over_input(inp)
        elif self.state == GameState.ENTER_INITIALS:
            self._handle_initials_input(inp)
        elif self.state in (GameState.HIGH_SCORES, GameState.HELP):
            self._handle_overlay_input(inp)

    def _handle_menu_input(self, inp: Union[Direction, Action]) -> None:
        if inp in (Direction.UP, Action.MENU_UP):
            self.menu_index = (self.menu_index - 1) % len(self.menu_items)
        elif inp in (Direction.DOWN, Action.MENU_DOWN):
            self.menu_index = (self.menu_index + 1) % len(self.menu_items)
        elif inp in (Action.SELECT, Action.START):
            selected = self.menu_items[self.menu_index]
            if selected == "Start Game":
                self.new_game()
            elif selected == "High Scores":
                self.state = GameState.HIGH_SCORES
            elif selected == "Help":
                self.state = GameState.HELP
            elif selected == "Quit":
                self.state = GameState.QUIT
        elif inp == Action.QUIT:
            self.state = GameState.QUIT

    def _handle_playing_input(self, inp: Union[Direction, Action]) -> None:
        if isinstance(inp, Direction):
            self.snake.set_direction(inp)
        elif inp == Action.PAUSE:
            self.state = GameState.PAUSED
        elif inp == Action.MENU:
            self.state = GameState.MENU
            self.menu_index = 0
        elif inp == Action.QUIT:
            self.state = GameState.QUIT

    def _handle_paused_input(self, inp: Union[Direction, Action]) -> None:
        if inp == Action.PAUSE:
            self.state = GameState.PLAYING
        elif inp == Action.MENU:
            self.state = GameState.MENU
            self.menu_index = 0
        elif inp == Action.QUIT:
            self.state = GameState.QUIT
        elif inp == Action.RESET:
            self.new_game()

    def _handle_game_over_input(self, inp: Union[Direction, Action]) -> None:
        if inp == Action.RESET:
            self.new_game()
        elif inp == Action.MENU:
            self.state = GameState.MENU
            self.menu_index = 0
        elif inp == Action.QUIT:
            self.state = GameState.QUIT

    def _handle_overlay_input(self, inp: Union[Direction, Action]) -> None:
        # Any key returns to menu
        self.state = GameState.MENU

    def _handle_initials_input(self, inp: Union[Direction, Action]) -> None:
        """Handle input for entering initials (3 characters)."""
        if inp == Direction.UP:
            # Increment current letter
            current = self.current_initials[self.initials_cursor]
            if current == 'Z':
                self.current_initials[self.initials_cursor] = 'A'
            elif current == ' ':
                self.current_initials[self.initials_cursor] = 'A'
            else:
                self.current_initials[self.initials_cursor] = chr(ord(current) + 1)
        elif inp == Direction.DOWN:
            # Decrement current letter
            current = self.current_initials[self.initials_cursor]
            if current == 'A':
                self.current_initials[self.initials_cursor] = ' '
            elif current == ' ':
                self.current_initials[self.initials_cursor] = 'Z'
            else:
                self.current_initials[self.initials_cursor] = chr(ord(current) - 1)
        elif inp == Direction.RIGHT:
            # Move to next position
            if self.initials_cursor < 2:
                self.initials_cursor += 1
        elif inp == Direction.LEFT:
            # Move to previous position
            if self.initials_cursor > 0:
                self.initials_cursor -= 1
        elif inp == Action.SELECT:
            # Confirm and save
            initials = ''.join(self.current_initials)
            self.high_scores.add(self.score, initials)
            self.state = GameState.GAME_OVER
        elif inp == Action.MENU:
            # Cancel - use default initials
            self.high_scores.add(self.score, '---')
            self.state = GameState.MENU
            self.menu_index = 0
        elif inp == Action.QUIT:
            self.state = GameState.QUIT

    # -- tick ----------------------------------------------------------------

    def tick(self) -> None:
        """Advance game by one frame. Call at tick_rate intervals."""
        if self.state != GameState.PLAYING or self.snake is None:
            return

        # Collision check before move
        if self.snake.check_next_move(self.width, self.height):
            # Check if it's a high score
            if self.high_scores.is_high_score(self.score):
                # Reset initials entry state
                self.current_initials = ['A', 'A', 'A']
                self.initials_cursor = 0
                self.state = GameState.ENTER_INITIALS
            else:
                self.state = GameState.GAME_OVER
                if self.score > 0:
                    self.high_scores.add(self.score, '---')
            return

        # Check food before moving
        head = self.snake.get_head()
        next_head = (head[0] + self.snake.direction.value[0],
                     head[1] + self.snake.direction.value[1])

        if self.food.check_eaten(next_head):
            self.score += 1
            self.snake.grow_snake()
            self.food.place(snake_body=self.snake.get_body())
            # Level up
            self.level = min(len(SPEED_LEVELS),
                             1 + self.score // POINTS_PER_LEVEL)

        self.snake.move()

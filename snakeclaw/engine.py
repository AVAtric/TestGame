"""Pure game engine — no terminal/curses dependency."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import List, Optional, Union

from .constants import (
    DEFAULT_HEIGHT, DEFAULT_WIDTH, FOOD_CHARS, INITIAL_SNAKE_LENGTH,
    INITIALS_LENGTH, MAX_HIGH_SCORE_ENTRIES, MENU_ITEMS,
    POINTS_PER_LEVEL, SPEED_LEVELS
)
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

    def __init__(self, path: Optional[str] = None, 
                 max_entries: int = MAX_HIGH_SCORE_ENTRIES):
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

class GameEngine:
    """Core game logic with no terminal dependency."""

    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
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
        self.menu_items = MENU_ITEMS
        self.menu_index: int = 0

        # Initials entry state
        self.current_initials: List[str] = ['A'] * INITIALS_LENGTH
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
                           length=INITIAL_SNAKE_LENGTH, direction=Direction.RIGHT)
        self.food = Food(self.width, self.height, food_chars=FOOD_CHARS)
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

        # Handle common actions first
        if self._handle_common_input(inp):
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

    def _handle_common_input(self, inp: Union[Direction, Action]) -> bool:
        """Handle actions common across multiple states. Returns True if handled."""
        if inp == Action.QUIT:
            self.state = GameState.QUIT
            return True
        
        # MENU action returns to menu from most states
        if inp == Action.MENU and self.state not in (GameState.MENU, GameState.ENTER_INITIALS):
            self.state = GameState.MENU
            self.menu_index = 0
            return True
        
        return False

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

    def _handle_playing_input(self, inp: Union[Direction, Action]) -> None:
        if isinstance(inp, Direction):
            self.snake.set_direction(inp)
        elif inp == Action.PAUSE:
            self.state = GameState.PAUSED

    def _handle_paused_input(self, inp: Union[Direction, Action]) -> None:
        if inp == Action.PAUSE:
            self.state = GameState.PLAYING
        elif inp == Action.RESET:
            self.new_game()

    def _handle_game_over_input(self, inp: Union[Direction, Action]) -> None:
        if inp == Action.RESET:
            self.new_game()

    def _handle_overlay_input(self, inp: Union[Direction, Action]) -> None:
        # Any key returns to menu
        self.state = GameState.MENU

    def _handle_initials_input(self, inp: Union[Direction, Action]) -> None:
        """Handle input for entering initials."""
        if inp == Direction.UP:
            self._cycle_initial(1)
        elif inp == Direction.DOWN:
            self._cycle_initial(-1)
        elif inp == Direction.RIGHT:
            self.initials_cursor = min(self.initials_cursor + 1, INITIALS_LENGTH - 1)
        elif inp == Direction.LEFT:
            self.initials_cursor = max(self.initials_cursor - 1, 0)
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

    def _cycle_initial(self, delta: int) -> None:
        """Cycle current initial character up or down."""
        current = self.current_initials[self.initials_cursor]
        if current == ' ':
            new_char = 'A' if delta > 0 else 'Z'
        elif current == 'A' and delta < 0:
            new_char = ' '
        elif current == 'Z' and delta > 0:
            new_char = 'A'
        else:
            new_char = chr(ord(current) + delta)
        self.current_initials[self.initials_cursor] = new_char

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
                self.current_initials = ['A'] * INITIALS_LENGTH
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

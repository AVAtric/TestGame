"""Pure game engine — no terminal/curses dependency."""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple, Union

from .constants import (
    CLASSIC_FRUITS, CLASSIC_HEIGHT, CLASSIC_WIDTH, DEFAULT_HEIGHT,
    DEFAULT_WIDTH, FRUIT_MAX_DIST, FRUIT_MIN_DIST, INITIAL_SNAKE_LENGTH,
    INITIALS_LENGTH, MAX_HIGH_SCORE_ENTRIES, MODERN_HEIGHT, MODERN_WIDTH,
    NEAR_MISS_THRESHOLD, POINTS_PER_LEVEL, POPUP_DURATION, POWER_UP_CHANCE,
    POWER_UP_DEFAULT_LIFETIME, POWER_UP_LIFETIME_BUFFER, POWER_UP_MIN_DIST,
    POWER_UPS, REGULAR_FRUITS, SHRINK_AMOUNT, SLOW_BUFF_DURATION,
    SLOW_BUFF_FACTOR, SPEED_BUFF_DURATION, SPEED_BUFF_FACTOR, SPEED_LEVELS
)
from .model import (Action, Direction, Effect, Fruit, GameMode, GameState,
                    PowerUp, ScorePopup, Snake, WallMode, bfs_distances,
                    pick_kind)


# Menu actions, in display order. "start" launches a wrap-walls game,
# "classic" launches solid-walls — each has its own high-score table.
_MENU_ACTIONS = ("start", "classic", "scores", "help", "quit")


def _default_highscore_path(mode: WallMode) -> str:
    """Resolve the per-mode high-score file alongside the package data dir."""
    return os.path.join(os.path.dirname(__file__), "data",
                        f"highscores_{mode.value}.json")


def _split_paths(highscore_path: Optional[str]) -> Dict[WallMode, str]:
    """Compute the wrap/classic high-score file paths.

    With no path given, use the package defaults. With one given (legacy /
    test override), reuse the same stem for the wrap file and add a
    `_classic` suffix for the solid-mode file so they don't collide.
    """
    if highscore_path is None:
        return {m: _default_highscore_path(m) for m in WallMode}
    # Single override path — derive a sibling for the other mode.
    base, ext = os.path.splitext(highscore_path)
    return {WallMode.WRAP: highscore_path,
            WallMode.SOLID: f"{base}_classic{ext or '.json'}"}


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
        except (OSError, json.JSONDecodeError, UnicodeDecodeError,
                TypeError, KeyError, ValueError):
            self._scores = []

    def save(self) -> None:
        """Persist scores atomically — write to a temp file, then rename.

        Why: a crash or kill mid-write would otherwise leave a truncated/empty
        JSON file and silently wipe the leaderboard on next load.
        """
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w") as fh:
            json.dump([e.to_dict() for e in self._scores], fh, indent=2)
        os.replace(tmp_path, self.path)

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
        """Add a score if it qualifies for the leaderboard. No-op otherwise."""
        if not self.is_high_score(score):
            return
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
                 highscore_path: Optional[str] = None,
                 wall_mode: WallMode = WallMode.WRAP):
        self.width = width
        self.height = height
        self.state: GameState = GameState.MENU
        self.snake: Optional[Snake] = None
        self.fruit: Optional[Fruit] = None
        self.score: int = 0
        self.level: int = 1
        self.wall_mode: WallMode = wall_mode
        self.mode: GameMode = GameMode.MODERN
        # Two separate high-score tables — one per wall mode. Wrap and solid
        # are different difficulty curves, so a single shared list would let
        # one mode dominate the other.
        paths = _split_paths(highscore_path)
        self._high_scores: Dict[WallMode, HighScoreManager] = {
            m: HighScoreManager(path=paths[m]) for m in WallMode
        }

        # Menu state
        self.menu_index: int = 0

        # Power-up
        self.power_up: Optional[PowerUp] = None

        # Score popups (floating "+N" text after eating something)
        self.popups: List[ScorePopup] = []

        # Speed buff (tick-rate multiplier; 1.0 = no buff)
        self.speed_multiplier: float = 1.0
        self.speed_buff_until: float = 0.0
        self.speed_buff_label: str = ""

        # Initials entry state
        self.current_initials: List[str] = ['A'] * INITIALS_LENGTH
        self.initials_cursor: int = 0

        # "Just one more" engagement state. Tracked across games within a
        # single session so the game-over screen can show streaks, near-miss
        # nudges, and personal-best celebrations to keep the player going.
        self.session_streak: int = 0
        self.last_score: int = 0
        self.is_personal_best: bool = False
        self.near_miss_message: str = ""

        # Quit-confirmation overlay state. `_pre_quit_state` is where we
        # bounce back to if the player cancels; `confirm_quit_index` is the
        # selected button (0 = Stay, 1 = Quit) defaulted to the safe option.
        self._pre_quit_state: GameState = GameState.MENU
        self.confirm_quit_index: int = 0

    # -- ergonomic attribute aliases ----------------------------------------
    # Tests and external readers often think in terms of "food" / "bonus"
    # rather than the internal "fruit" / "power_up" names. These are tiny
    # read-write properties that pass through, nothing more.

    @property
    def food(self) -> Optional[Fruit]:
        return self.fruit

    @food.setter
    def food(self, value: Optional[Fruit]) -> None:
        self.fruit = value

    @property
    def bonus(self) -> Optional[PowerUp]:
        return self.power_up

    @bonus.setter
    def bonus(self, value: Optional[PowerUp]) -> None:
        self.power_up = value

    # -- helpers -------------------------------------------------------------

    @property
    def tick_rate(self) -> float:
        base = SPEED_LEVELS[self.level]
        if self.speed_buff_until and time.time() < self.speed_buff_until:
            return base * self.speed_multiplier
        return base

    @property
    def buff_active(self) -> bool:
        return bool(self.speed_buff_until and time.time() < self.speed_buff_until)

    @property
    def buff_remaining(self) -> float:
        if not self.speed_buff_until:
            return 0.0
        return max(0.0, self.speed_buff_until - time.time())

    @property
    def high_score(self) -> int:
        return max(self.high_scores.best, self.score)

    # -- per-mode high-score routing ----------------------------------------

    @property
    def high_scores(self) -> HighScoreManager:
        """The high-score manager for the *current* wall mode."""
        return self._high_scores[self.wall_mode]

    def high_scores_for(self, mode: WallMode) -> HighScoreManager:
        """Lookup either mode's table — used by the high-scores screen which
        shows wrap and classic side-by-side."""
        return self._high_scores[mode]

    @property
    def menu_items(self) -> List[str]:
        """Display labels for the menu, in order."""
        return [self._menu_label(a) for a in _MENU_ACTIONS]

    def _menu_label(self, action: str) -> str:
        if action == "start":
            return "Start Game"
        if action == "classic":
            return "Classic Game"
        if action == "scores":
            return "High Scores"
        if action == "help":
            return "Help"
        if action == "quit":
            return "Quit"
        return action

    def _recompute_level(self) -> None:
        self.level = min(len(SPEED_LEVELS), 1 + self.score // POINTS_PER_LEVEL)

    # -- init / reset --------------------------------------------------------

    def new_game(self, mode: Optional[GameMode] = None,
                 width: Optional[int] = None,
                 height: Optional[int] = None) -> None:
        """Start a new game. `mode` overrides the current mode if given.

        `width`/`height` override the mode's default field dimensions —
        useful for tests that need a tiny grid; not used by the menu paths.

        Restarts launched from GAME_OVER count toward `session_streak` (the
        engagement nudge); starts from MENU reset the streak to 1.
        """
        # Streak: continuing from a death = +1, fresh start = reset to 1.
        # Computed before we reset state so we can read self.state.
        is_restart = self.state == GameState.GAME_OVER
        self.session_streak = (self.session_streak + 1) if is_restart else 1

        if mode is not None:
            self.mode = mode
        # Mode dictates wall_mode and default field size; the optional
        # arguments below let tests override dimensions while keeping the
        # mode's feature set (fruits, power-ups).
        if self.mode == GameMode.CLASSIC:
            self.width, self.height = CLASSIC_WIDTH, CLASSIC_HEIGHT
            self.wall_mode = WallMode.SOLID
        else:  # MODERN
            self.width, self.height = MODERN_WIDTH, MODERN_HEIGHT
            self.wall_mode = WallMode.WRAP
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

        # Build fruits + power-ups at the *final* (post-override) dimensions
        # so the playfield they reference matches the snake's playable area.
        if self.mode == GameMode.CLASSIC:
            self.fruit = Fruit(self.width, self.height, kinds=CLASSIC_FRUITS)
            self.power_up = None
        else:
            self.fruit = Fruit(self.width, self.height, kinds=REGULAR_FRUITS)
            self.power_up = PowerUp(self.width, self.height, kinds=POWER_UPS,
                                    default_duration=POWER_UP_DEFAULT_LIFETIME)

        self.snake = Snake((self.height // 2, self.width // 4),
                           length=INITIAL_SNAKE_LENGTH, direction=Direction.RIGHT)
        self.popups = []
        self.speed_multiplier = 1.0
        self.speed_buff_until = 0.0
        self.speed_buff_label = ""
        self.is_personal_best = False
        self.near_miss_message = ""
        self._place_fruit_pathfinder()
        self.score = 0
        self.level = 1
        self.state = GameState.PLAYING

    # -- pathfinder placement ------------------------------------------------

    def _bfs_distances(self,
                       extra_obstacles: Iterable[Tuple[int, int]] = ()
                       ) -> Dict[Tuple[int, int], int]:
        """Distance map from the snake's head, minus extra blocked cells."""
        wrap = self.wall_mode == WallMode.WRAP
        head = self.snake.get_head()
        body = self.snake.get_body()
        dists = bfs_distances(body, head, self.width, self.height, wrap)
        for extra in extra_obstacles:
            dists.pop(extra, None)
        return dists

    def _pick_pathfinder_cell(self,
                              distances: Dict[Tuple[int, int], int],
                              min_dist: int,
                              max_dist: int) -> Optional[Tuple[int, int]]:
        """Pick a random cell whose BFS distance falls in [min, max].

        Falls back gracefully: if no cells in band, widens to "anything ≤ max",
        then to "anything reachable". Returns None only if `distances` is empty.
        """
        if not distances:
            return None
        band = [c for c, d in distances.items() if min_dist <= d <= max_dist]
        if band:
            return random.choice(band)
        capped = [c for c, d in distances.items() if d <= max_dist]
        if capped:
            return random.choice(capped)
        return random.choice(list(distances.keys()))

    def _place_fruit_pathfinder(self) -> None:
        """Place the regular fruit on a reachable cell in the sweet-spot band.

        If the snake's head is fully walled in, falls back to a non-snake cell
        so the game can keep running rather than crash.
        """
        distances = self._bfs_distances()
        cell = self._pick_pathfinder_cell(distances, FRUIT_MIN_DIST, FRUIT_MAX_DIST)
        if cell is not None:
            self.fruit.place(pos=cell)
            return
        # Pathological: head walled off entirely. Random non-body cell.
        self.fruit.place(snake_body=self.snake.get_body())

    def _spawn_power_up_pathfinder(self) -> None:
        """Spawn a power-up on a cell reachable within its lifetime.

        We pick the kind up front so we know its lifetime, then bound the BFS
        target distance to "moves the snake can take before this kind times
        out". Otherwise a speed-boost dropped 40 cells away wastes the bonus.
        """
        if self.power_up is None:
            return
        chosen = pick_kind(self.power_up.kinds)
        lifetime = chosen.lifetime or self.power_up.default_duration
        moves_available = max(1, int(lifetime * POWER_UP_LIFETIME_BUFFER /
                                     max(self.tick_rate, 1e-3)))
        max_dist = min(moves_available, self.width * self.height)
        distances = self._bfs_distances(
            extra_obstacles=(self.fruit.get_position(),))
        cell = self._pick_pathfinder_cell(distances, POWER_UP_MIN_DIST, max_dist)
        if cell is None:
            return  # nothing reachable
        self.power_up.spawn_at(cell, kind=chosen)

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
        elif self.state == GameState.CONFIRM_QUIT:
            self._handle_confirm_quit_input(inp)
        elif self.state in (GameState.HIGH_SCORES, GameState.HELP):
            self._handle_overlay_input(inp)

    def _handle_common_input(self, inp: Union[Direction, Action]) -> bool:
        """Handle actions common across multiple states. Returns True if handled."""
        if inp == Action.QUIT:
            # Q in the confirm dialog cancels (don't stack confirms).
            if self.state == GameState.CONFIRM_QUIT:
                self.state = self._pre_quit_state
                return True
            # Otherwise open the "Are you sure?" overlay. The default button
            # is "Stay" (index 0) so an accidental Enter doesn't quit.
            self._pre_quit_state = self.state
            self.confirm_quit_index = 0
            self.state = GameState.CONFIRM_QUIT
            return True

        # MENU action returns to menu from most states. Going back to the
        # menu also breaks the "just one more" streak — the player explicitly
        # opted out of continuing, so the next run starts fresh.
        if inp == Action.MENU and self.state not in (
                GameState.MENU, GameState.ENTER_INITIALS,
                GameState.CONFIRM_QUIT):
            self.state = GameState.MENU
            self.menu_index = 0
            self.session_streak = 0
            return True

        return False

    def _handle_menu_input(self, inp: Union[Direction, Action]) -> None:
        if inp in (Direction.UP, Action.MENU_UP):
            self.menu_index = (self.menu_index - 1) % len(_MENU_ACTIONS)
        elif inp in (Direction.DOWN, Action.MENU_DOWN):
            self.menu_index = (self.menu_index + 1) % len(_MENU_ACTIONS)
        elif inp in (Action.SELECT, Action.START):
            action = _MENU_ACTIONS[self.menu_index]
            if action == "start":
                self.new_game(GameMode.MODERN)
            elif action == "classic":
                self.new_game(GameMode.CLASSIC)
            elif action == "scores":
                self.state = GameState.HIGH_SCORES
            elif action == "help":
                self.state = GameState.HELP
            elif action == "quit":
                # Route through the confirm overlay so this matches the
                # Q-key behavior — never quit without asking.
                self._pre_quit_state = GameState.MENU
                self.confirm_quit_index = 0
                self.state = GameState.CONFIRM_QUIT

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

    def _handle_confirm_quit_input(self, inp: Union[Direction, Action]) -> None:
        """Handle the "Are you sure?" overlay. Two buttons: Stay (default,
        safe) and Quit. ←/→ toggles, Enter confirms; Y is a direct quit
        shortcut, N / Esc / M / Q all cancel back to the previous state."""
        if inp in (Direction.LEFT, Direction.RIGHT):
            self.confirm_quit_index = 1 - self.confirm_quit_index
        elif inp == Action.YES:
            self.state = GameState.QUIT
        elif inp in (Action.NO, Action.MENU):
            self.state = self._pre_quit_state
        elif inp == Action.SELECT:
            if self.confirm_quit_index == 1:
                self.state = GameState.QUIT
            else:
                self.state = self._pre_quit_state

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

    # -- effects / popups ---------------------------------------------------

    def _add_popup(self, pos: Tuple[int, int], points: int, color: int) -> None:
        # Classic mode is intentionally minimal — no floating "+1" overlays.
        if self.mode == GameMode.CLASSIC:
            return
        text = f"+{points}" if points >= 0 else str(points)
        self.popups.append(ScorePopup(
            position=pos, text=text, color=color,
            expires_at=time.time() + POPUP_DURATION,
        ))

    def _prune_popups(self) -> None:
        now = time.time()
        self.popups = [p for p in self.popups if not p.is_expired(now)]

    def _apply_effect(self, effect: Effect, pos: Tuple[int, int]) -> None:
        """Apply a power-up effect. `pos` is where the effect was triggered
        (used for any effect-related popup beyond the points popup)."""
        if effect == Effect.SPEED_UP:
            self.speed_multiplier = SPEED_BUFF_FACTOR
            self.speed_buff_until = time.time() + SPEED_BUFF_DURATION
            self.speed_buff_label = "FAST"
        elif effect == Effect.SLOW_DOWN:
            self.speed_multiplier = SLOW_BUFF_FACTOR
            self.speed_buff_until = time.time() + SLOW_BUFF_DURATION
            self.speed_buff_label = "SLOW"
        elif effect == Effect.SHRINK:
            self.snake.shrink(SHRINK_AMOUNT)

    def _expire_buffs(self) -> None:
        """Reset buff state once it stops being active. Robust to either the
        timer running out naturally or being cleared from outside."""
        if self.buff_active:
            return
        if self.speed_multiplier != 1.0 or self.speed_buff_label:
            self.speed_buff_until = 0.0
            self.speed_multiplier = 1.0
            self.speed_buff_label = ""

    # -- tick ----------------------------------------------------------------

    def tick(self) -> None:
        """Advance game by one frame. Call at tick_rate intervals."""
        if self.state != GameState.PLAYING or self.snake is None:
            return

        self._expire_buffs()
        self._prune_popups()

        if self.power_up and self.power_up.is_expired():
            self.power_up.despawn()

        wrap = self.wall_mode == WallMode.WRAP
        if self.snake.check_next_move(self.width, self.height, wrap=wrap):
            self._on_collision()
            return

        next_head = self.snake.compute_next_head(self.width, self.height,
                                                 wrap=wrap)

        ate_fruit = self.fruit.check_eaten(next_head)
        ate_power = (self.power_up is not None and
                     self.power_up.check_eaten(next_head))

        fruit_points = self.fruit.get_points() if ate_fruit else 0
        fruit_color = self.fruit.get_color() if ate_fruit else 0
        power_points = self.power_up.get_points() if ate_power else 0
        power_color = self.power_up.get_color() if ate_power else 0
        power_effect = self.power_up.get_effect() if ate_power else Effect.NONE

        if ate_fruit:
            self.score += fruit_points
            self.snake.grow_snake()
        if ate_power:
            self.score += power_points
            self.snake.grow_snake()
            self.power_up.despawn()
        if ate_fruit or ate_power:
            self._recompute_level()

        # Advance the snake before placing new food so the pathfinder runs
        # from the post-move head position.
        self.snake.move(new_head=next_head)

        if ate_fruit:
            self._add_popup(next_head, fruit_points, fruit_color)
            self._place_fruit_pathfinder()
        if ate_power:
            self._add_popup(next_head, power_points, power_color)
            self._apply_effect(power_effect, next_head)

        if ate_fruit and self.power_up and not self.power_up.active:
            if random.random() < POWER_UP_CHANCE:
                self._spawn_power_up_pathfinder()

    def _on_collision(self) -> None:
        """Handle the snake hitting a wall or itself.

        Routes to ENTER_INITIALS for qualifying scores so the player can
        record their initials, otherwise straight to GAME_OVER. add() in
        HighScoreManager is itself defensive — it no-ops on non-qualifiers.

        Computes the dark-pattern nudge fields (last_score, is_personal_best,
        near_miss_message) that the game-over screen reads to entice "just
        one more" without the player consciously deciding to continue.
        """
        self.last_score = self.score
        # Personal best is computed *before* this score is added to the
        # leaderboard, so it's always against history, not against itself.
        self.is_personal_best = (self.score > 0 and
                                 self.score > self.high_scores.best)
        self.near_miss_message = self._compute_near_miss()

        if self.high_scores.is_high_score(self.score):
            self.current_initials = ['A'] * INITIALS_LENGTH
            self.initials_cursor = 0
            self.state = GameState.ENTER_INITIALS
        else:
            self.state = GameState.GAME_OVER

    def _compute_near_miss(self) -> str:
        """Build a "you were so close!" message if the player almost broke a
        threshold — empty string when the score is far from any milestone.

        Personal-best is celebrated separately (see is_personal_best), so
        this only fires for *missed* milestones to drive the regret nudge.
        """
        if self.is_personal_best:
            return ""
        best = self.high_scores.best
        if best > 0:
            gap = best - self.score
            if 0 < gap <= NEAR_MISS_THRESHOLD:
                return f"Just {gap} away from your best!"
        # Adjacent leaderboard rank ("3 away from #4!").
        for i, entry in enumerate(self.high_scores.get_top()):
            ahead = entry.score - self.score
            if 0 < ahead <= NEAR_MISS_THRESHOLD:
                return f"Just {ahead} away from #{i + 1}!"
        return ""

"""Game constants and configuration."""

from .model import Effect, FruitKind

# ---------------------------------------------------------------------------
# Game dimensions
# ---------------------------------------------------------------------------
# Modern mode plays on the full canvas; Classic uses a small Nokia-3310-ish
# field centered inside the same canvas so the menu/HUD layout stays stable.
MODERN_WIDTH = 48
MODERN_HEIGHT = 30
CLASSIC_WIDTH = 17
CLASSIC_HEIGHT = 11

# DEFAULT_* still points at MODERN — that's the canvas size the UI is built
# around. CLASSIC just reduces the inner play rectangle.
DEFAULT_WIDTH = MODERN_WIDTH
DEFAULT_HEIGHT = MODERN_HEIGHT

# ---------------------------------------------------------------------------
# Gameplay constants
# ---------------------------------------------------------------------------
INITIAL_SNAKE_LENGTH = 3
POINTS_PER_LEVEL = 5  # advance level every N points

# Speed curve: level → tick interval in seconds
SPEED_LEVELS = {
    1: 0.18,
    2: 0.15,
    3: 0.13,
    4: 0.11,
    5: 0.09,
    6: 0.07,
}

# ---------------------------------------------------------------------------
# High score configuration
# ---------------------------------------------------------------------------
MAX_HIGH_SCORE_ENTRIES = 10
INITIALS_LENGTH = 3

# ---------------------------------------------------------------------------
# UI Visual Characters
# ---------------------------------------------------------------------------
# Use 2 characters wide for better aspect ratio (terminal chars are ~2:1 tall:wide)

# Snake - using 2-char ASCII blocks for reliable rendering
SNAKE_SEGMENT = '██'    # Solid block (2 chars)
SNAKE_HEAD =    '██'    # Same as body for consistency
SNAKE_BODY =    '██'    # fallback

# ---------------------------------------------------------------------------
# Color pairs (indices for curses.init_pair)
# ---------------------------------------------------------------------------
COLOR_SNAKE = 1
COLOR_FOOD = 2
COLOR_HUD = 3
COLOR_BORDER = 4
COLOR_TITLE = 5
COLOR_HIGHLIGHT = 6
COLOR_SUCCESS = 7
COLOR_WARNING = 8

# ---------------------------------------------------------------------------
# Fruits — regular (always one on the field, weighted random kind on each spawn)
# ---------------------------------------------------------------------------
# Tuned so common = low points, rare = higher points: roughly half the time
# you get an apple (1pt), the rest skews up to a 3-pt berry.
REGULAR_FRUITS = (
    FruitKind(name="apple",  char="()", points=1, color=COLOR_FOOD,      weight=50),
    FruitKind(name="cherry", char="cC", points=2, color=COLOR_WARNING,   weight=25),
    FruitKind(name="berry",  char="@@", points=3, color=COLOR_HIGHLIGHT, weight=15),
    FruitKind(name="lemon",  char="##", points=2, color=COLOR_HUD,       weight=10),
)

# Classic mode food: a single brick, +1 point. No variety, no power-ups —
# pure Nokia-3310-style snake. The block glyph reads as a brick / pellet.
CLASSIC_FRUITS = (
    FruitKind(name="brick", char="▓▓", points=1, color=COLOR_FOOD, weight=1),
)

FOOD_CHAR = '()'  # legacy fallback used by the UI when the engine has none

# ---------------------------------------------------------------------------
# Power-ups — rare, blink the whole time, often carry a side-effect
# ---------------------------------------------------------------------------
POWER_UPS = (
    FruitKind(name="bonus",  char="XX", points=5, color=COLOR_HUD,
              weight=30, effect=Effect.NONE,       lifetime=6.0),
    FruitKind(name="speed",  char=">>", points=3, color=COLOR_SUCCESS,
              weight=25, effect=Effect.SPEED_UP,   lifetime=6.0),
    FruitKind(name="slow",   char="<<", points=3, color=COLOR_BORDER,
              weight=20, effect=Effect.SLOW_DOWN,  lifetime=6.0),
    FruitKind(name="shrink", char="vV", points=4, color=COLOR_HIGHLIGHT,
              weight=20, effect=Effect.SHRINK,     lifetime=6.0),
)

POWER_UP_CHANCE = 0.20          # chance per fruit eaten to spawn a power-up
POWER_UP_DEFAULT_LIFETIME = 6.0  # used if a kind has no lifetime override

# Fallback glyph for `draw_bonus_food` when no power-up is on screen — the
# UI still accepts this as a default param so it can render an empty cell
# without the engine needing to pass a kind through.
BONUS_FOOD_CHAR = 'XX'

# ---------------------------------------------------------------------------
# Buffs (active effect timers)
# ---------------------------------------------------------------------------
SPEED_BUFF_DURATION = 5.0
SPEED_BUFF_FACTOR = 0.55   # multiplier on tick interval (smaller = faster)
SLOW_BUFF_DURATION = 5.0
SLOW_BUFF_FACTOR = 1.7     # multiplier on tick interval (larger = slower)
SHRINK_AMOUNT = 2          # tail segments removed by SHRINK effect

# ---------------------------------------------------------------------------
# Score popups — floating "+N" text after eating
# ---------------------------------------------------------------------------
POPUP_DURATION = 0.7   # seconds visible
POPUP_RISE_AFTER = 0.35  # after this long, the popup drifts up by 1 row

# ---------------------------------------------------------------------------
# "Dark pattern" engagement nudges shown on the game-over screen.
# These exist to make the player want to press R one more time.
# ---------------------------------------------------------------------------
NEAR_MISS_THRESHOLD = 5     # within this many points = "almost!" message
STREAK_HOT_THRESHOLD = 3    # streak count where the 🔥 icon kicks in

# ---------------------------------------------------------------------------
# Pathfinder placement — pick spawn cells in a "sweet spot" distance band
# ---------------------------------------------------------------------------
# Don't drop fruit immediately under the head (boring) and don't park it where
# the snake would have to wander forever (frustrating). For a 48x30 grid these
# bounds bias toward medium-range targets without preventing fallback if the
# snake is small (early game) or coiled (late game).
FRUIT_MIN_DIST = 4
FRUIT_MAX_DIST = 60
# Power-ups must be reachable in their lifetime — engine clamps to whatever
# the snake can actually traverse before despawn.
POWER_UP_MIN_DIST = 3
POWER_UP_LIFETIME_BUFFER = 0.7  # require reach in <70% of lifetime

# ---------------------------------------------------------------------------
# UI Messages
# ---------------------------------------------------------------------------
GAME_TITLE = [
"╔═╗╔╗╔╔═╗╦╔═╔═╗",
"╚═╗║║║╠═╣╠╩╗║╣ ",
"╚═╝╝╚╝╩ ╩╩ ╩╚═╝",
"╔═╗╦  ╔═╗╦ ╦",
"║  ║  ╠═╣║ ║",
"╚═╝╩═╝╩ ╩╚╩╝",
"─ T E R M I N A L ─",
]

# Menu characters
MENU_MARKER = ' ▶ '
MENU_SPACER = '   '

# Hints and help text
MENU_HINT = "↑/↓ navigate  Enter/Space select  Q quit"
GAME_HINTS = " P=pause  M=menu  R=restart  Q=quit"
RETURN_HINT = "Press any key to return"

HELP_TEXT = [
    "Arrow keys / WASD ─ move the snake",
    "P ─ pause / resume",
    "R ─ restart game",
    "M / Esc ─ back to menu",
    "Q ─ quit",
    "",
    "Game modes (each has its own high-score list):",
    "  Start Game   ─ wrap walls (·) + fruits + power-ups",
    "  Classic Game ─ solid walls + bricks only, Nokia-style",
    "",
    "Modern fruits — eat to grow:",
    "  ()  apple  +1     cC  cherry +2",
    "  @@  berry  +3     ##  lemon  +2",
    "Modern power-ups (blink, time-limited):",
    "  XX  bonus  +5     >>  speed boost",
    "  <<  slow down     vV  shrink snake",
    "Speed increases every 5 points.",
]

INITIALS_HINTS = [
    "↑/↓ = change letter",
    "←/→ = move cursor",
    "Enter = confirm",
    "Esc = skip",
]

"""Game constants and configuration."""

# ---------------------------------------------------------------------------
# Game dimensions
# ---------------------------------------------------------------------------
DEFAULT_WIDTH = 48
DEFAULT_HEIGHT = 30

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
SNAKE_HEAD = '▶▶'  # default / fallback
SNAKE_BODY = '▓▓'  # fallback

# Food characters - randomly selected each time food spawns
FOOD_CHARS = ['🟢', '🟨', '🔴', '⬛', '💚', '🌟', '🟩']
FOOD_CHAR = '🟩'  # fallback if list is empty

# Direction-specific snake segments - works for both head and body!
SNAKE_SEGMENTS = {
    'UP': '🔼',
    'DOWN': '🔽',
    'LEFT': '◀️',
    'RIGHT': '▶️',
}

# Menu characters
MENU_MARKER = ' ▶ '
MENU_SPACER = '   '

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
# UI Messages
# ---------------------------------------------------------------------------
GAME_TITLE = [
    "  ╔═╗╔╗╔╔═╗╦╔═╔═╗  ",
    "  ╚═╗║║║╠═╣╠╩╗║╣   ",
    "  ╚═╝╝╚╝╩ ╩╩ ╩╚═╝  ",
]

GAME_SUBTITLE = "~ Terminal Snake ~"

# Menu items
MENU_ITEMS = ["Start Game", "High Scores", "Help", "Quit"]

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
    "Eat food to grow and score points.",
    "Avoid walls and your own tail!",
    "Speed increases every 5 points.",
    "Enter your initials for high scores!",
]

INITIALS_HINTS = [
    "↑/↓ = change letter",
    "←/→ = move cursor",
    "Enter = confirm",
    "Esc = skip",
]

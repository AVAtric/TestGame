# 🐍 SnakeClaw

A polished terminal Snake game built with Python and curses.
<div align="center">
<pre>
   ╔═╗╔╗╔╔═╗╦╔═╔═╗
  ╚═╗║║║╠═╣╠╩╗║╣
   ╚═╝╝╚╝╩ ╩╩ ╩╚═╝
   ╔═╗╦  ╔═╗╦ ╦
   ║  ║  ╠═╣║ ║
   ╚═╝╩═╝╩ ╩╚╩╝
   ─ T E R M I N A L ─
</pre>
</div>


## Features

- **Classic Snake gameplay** with smooth curses rendering
- **Wall modes** — toggle between **Wrap** (default; pass through walls to the opposite side) and **Solid** (walls are deadly), right from the main menu
- **Progressive difficulty** — 6 speed levels that ramp up as you score
- **High score board** — Top 10 saved to disk with 3-letter initials
- **Reachable food** — placement runs a BFS from the snake's head so food never spawns in a pocket the player can't enter
- **Bonus food** — blinking `XX` appears randomly, worth 5 points, vanishes after 5 seconds
- **Color terminal UI** — Border, snake, food, and HUD all color-coded
- **Aspect ratio correction** — 2 terminal columns per game cell for square appearance
- **Multiple food styles** — `()` `[]` `{}` `##` `@@` rotate randomly

## Quick Start

```bash
# Clone and set up
cd TestGame
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Play
snakeclaw
```

Or run directly:

```bash
python3 -m snakeclaw
```

## Controls

| Key | Action |
|---|---|
| Arrow keys / WASD | Move snake |
| P | Pause / resume |
| R | Restart (from game over) |
| M / Esc | Back to menu |
| Q | Quit |
| Enter / Space | Select menu item |

**High score entry:** ↑/↓ to change letter, ←/→ to move cursor, Enter to confirm, Esc to skip.

## Game Mechanics

| Setting | Value |
|---|---|
| Grid size | 48 × 30 (96 × 30 on screen) |
| Starting length | 3 segments |
| Speed range | 0.18s → 0.07s per tick |
| Level up | Every 5 points |
| Wall mode | Wrap (default) or Solid — toggled from the menu |
| Food placement | BFS-restricted to cells reachable from the snake's head |
| Bonus food | ~8% chance after eating, worth 5 pts, lasts 5s, blinks while visible |
| High scores | Top 10, persisted atomically as JSON |

## Architecture

```
snakeclaw/
├── model.py      # Pure data: Snake, Food, BonusFood, Direction, GameState
├── engine.py     # Game logic & state machine (no I/O)
├── ui.py         # Curses rendering & input mapping
├── game.py       # Thin controller wiring engine ↔ UI
├── constants.py  # All tunable values in one place
└── data/
    └── highscores.json
```

**Design principles:**
- Engine has zero terminal dependency — fully testable without curses
- State machine drives all transitions: Menu → Playing → Paused → Game Over → Initials
- All magic numbers live in `constants.py`

## Testing

```bash
pip install -e ".[test]"
python3 -m pytest tests/ -v
```

140 tests covering model logic, engine state transitions, high-score persistence, wall modes, BFS reachability for food placement, and UI key mapping.

## Requirements

- Python 3.12+
- A terminal with curses support (built-in on Linux/macOS; `windows-curses` on Windows)

## License

MIT

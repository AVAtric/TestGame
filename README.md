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

**Two genuinely different game modes** picked from the menu:

- **Start Game (Modern)** — 48×30 grid, wrap walls drawn as a porous row of
  `·` dots, weighted fruit variety (apple/cherry/berry/lemon), blinking
  power-ups with effects, score popups, active-buff badge, 6-step speed ramp.
- **Classic Game** — small 17×11 Nokia-3310-style grid centered on the
  canvas, solid red double-line walls, brick (`▓▓`) food only at +1, no
  power-ups, no popups, no buffs. Pure Snake.

**Modern fruits and power-ups**

- Fruits: `()` apple +1, `cC` cherry +2, `##` lemon +2, `@@` berry +3 — each in its own color.
- Power-ups (~20% spawn chance, blink while visible, time-limited):
  `XX` bonus +5, `>>` speed boost, `<<` slow-mo, `vV` shrink (-2 tail segments).

**Per-mode high-score tables** — each mode has its own Top-10 leaderboard
persisted as `highscores_wrap.json` / `highscores_classic.json`. The
high-scores screen shows them side-by-side.

**Engagement nudges on game over**

- Session streak counter (`🔥 4 in a row!`)
- Last-score vs this-score arrow (`Last: 8 → This: 12 (↑+4)`)
- `✨ NEW PERSONAL BEST! ✨` celebration when you beat the mode's best
- `Just N away from your best!` near-miss messaging
- A dominant `▶ R ── JUST ONE MORE` call-to-action; menu/quit are de-emphasized

**Always-confirm quit** — pressing Q (or selecting Quit from the menu)
opens an "Are you sure?" overlay with `STAY` selected by default. `Y`
confirms instantly, `N`/`Esc` cancels back to whatever you were doing.

**Pathfinder food placement** — BFS from the snake's head picks a
reachable cell in a sweet-spot distance band so fruit is never trivially
adjacent or trapped in an unreachable pocket.

**Color terminal UI** with 2 terminal columns per game cell for a square
look on real terminals.

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

### Running from PyCharm

1. Open the project in PyCharm — it ships with a **SnakeClaw** run configuration
   (top-right dropdown). Just click the green ▶ button.
2. Or open `main.py` and click the green ▶ in the gutter next to
   `if __name__ == "__main__":`.

The bundled config has **Emulate terminal in output console** enabled, which
`curses` requires to draw the playfield. If you build your own configuration,
make sure that option is checked — without it you'll get
`_curses.error: setupterm: could not find terminal`.

## Controls

| Key | Action |
|---|---|
| Arrow keys / WASD | Move snake |
| P | Pause / resume |
| R | Restart (from game over) |
| M / Esc | Back to menu |
| Q | Quit (asks for confirmation first) |
| Y / N | Confirm / cancel in the quit dialog |
| Enter / Space | Select menu item |

**High score entry:** ↑/↓ to change letter, ←/→ to move cursor, Enter to confirm, Esc to skip.

## Game Mechanics

| Setting | Value |
|---|---|
| Modern grid | 48 × 30 (96 × 30 on screen), wrap walls |
| Classic grid | 17 × 11 centered on the canvas, solid walls — Nokia-3310 vibe |
| Starting length | 3 segments |
| Speed range | 0.18s → 0.07s per tick (6 levels, Modern only) |
| Level up | Every 5 points |
| Fruit placement | BFS pathfinder picks a reachable cell in a tuned distance band (4–60) |
| Modern fruits | apple (1), cherry (2), lemon (2), berry (3) — weighted random |
| Classic fruits | brick `▓▓` only, +1 |
| Power-ups (Modern) | ~20% chance after eating; blink while visible; placed within their lifetime |
| Buff durations | speed/slow last 5s; shrink removes 2 segments instantly |
| Score popups | `+N` floats up at the eaten cell for ~0.7s (Modern only) |
| Game-over nudges | streak counter, last-score delta, personal-best celebration, near-miss message |
| High scores | Top 10 per mode (`highscores_wrap.json`, `highscores_classic.json`) |

## Architecture

```
snakeclaw/
├── model.py      # Snake, Fruit, PowerUp, FruitKind, ScorePopup, GameMode,
│                 # GameState, WallMode, BFS pathfinder helpers
├── engine.py     # State machine + scoring + per-mode high-score tables
│                 # (no terminal dependency)
├── ui.py         # Curses rendering & input mapping
├── game.py       # Thin controller wiring engine ↔ UI
├── constants.py  # All tunable values + fruit/power-up registries
└── data/
    ├── highscores_wrap.json     # Modern leaderboard
    └── highscores_classic.json  # Classic leaderboard
```

**Design principles:**
- Engine has zero terminal dependency — fully testable without curses
- State machine: `Menu → Playing ↔ Paused → Game Over → Enter Initials`,
  with a `Confirm Quit` overlay layered on top of any state
- All magic numbers, fruit kinds, and power-ups live in `constants.py`

## Testing

```bash
pip install -e ".[test]"
python3 -m pytest tests/ -v
```

181 tests covering model logic, engine state transitions, per-mode high-score persistence, BFS pathfinder placement, fruit kinds, power-up effects (speed/slow/shrink), score popups, the Modern vs Classic mode split, engagement nudges (streak/personal-best/near-miss), the quit-confirmation flow, and UI rendering.

## Requirements

- **CPython 3.12+** (stock Python from python.org or your distro)
- A terminal with curses support (built-in on Linux/macOS; `windows-curses` on Windows)

## License

MIT

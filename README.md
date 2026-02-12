# Snake Claw

A polished Snake game for the terminal/console written in Python.

## Features

- 🎮 Classic Snake gameplay with smooth console rendering
- 🖥️ Terminal UI using curses with colour support
- ⌨️ Arrow keys or WASD controls
- 📊 Score, high-score, and level tracking (HUD)
- ⏸ Pause / Resume (P)
- 🔄 Restart (R) without restarting the process
- 📋 Main menu: Start Game / High Scores / Help / Quit
- 🏆 Persistent high-score table (top 10, JSON)
- 🧪 116 unit tests covering logic, state, and persistence
- ✨ Type hints throughout
- 📦 Minimal dependencies

## Requirements

- Python 3.12 or higher
- Linux, macOS, or Windows with a terminal emulator that supports curses
- pip (for installation)

## Installation

### Using pip (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Running the Game

### Using console script (after installation)

```bash
source .venv/bin/activate
snakeclaw
```

### Using Python module

```bash
source .venv/bin/activate
python3 -m snakeclaw
```

## Controls

| Key              | Action                          |
|------------------|---------------------------------|
| Arrow keys / WASD | Move the snake                |
| P                | Pause / Resume                  |
| R                | Restart game                    |
| M / Esc          | Back to menu (game over screen) |
| Enter / Space    | Select menu item                |
| Q                | Quit                            |

## Gameplay

1. Use the **main menu** to start a game, view high scores, or read help
2. Control the snake with arrow keys or WASD
3. Eat **●** food to grow, score points, and increase speed
4. Speed increases every 5 points (6 levels)
5. Avoid hitting the walls or your own body
6. After game over, press **R** to restart, **M** for menu, or **Q** to quit
7. High scores persist across sessions in `snakeclaw/data/highscores.json`

## Architecture

### Project Structure

```
TestGame/
├── snakeclaw/
│   ├── __init__.py      # Package init
│   ├── __main__.py      # Entry point for python -m snakeclaw
│   ├── engine.py        # Pure game engine (no I/O) — logic, state, scores
│   ├── game.py          # Thin controller connecting engine ↔ UI
│   ├── model.py         # Data models (Snake, Food, Direction, enums)
│   ├── ui.py            # Terminal renderer using curses
│   └── data/
│       └── highscores.json  # Persisted high scores (auto-created)
├── tests/
│   ├── test_model.py    # Snake, Food, Direction tests
│   ├── test_engine.py   # Engine logic, state transitions, high scores
│   ├── test_game.py     # Integration smoke tests
│   └── test_ui.py       # Key mapping & rendering tests
├── setup.py             # Package setup
└── README.md            # This file
```

### Design Principles

- **Separation of concerns**: `engine.py` contains all game logic with zero terminal dependency; `ui.py` is a thin curses renderer
- **Testability**: The engine is fully testable without a real terminal (116 tests, all pure-logic)
- **State machine**: Clean `GameState` enum drives menu → playing → paused → game over transitions

### Game Settings

- **Playfield size**: 60 × 30 (configurable in `GameEngine`)
- **Speed levels**: 6 tiers from 0.18 s to 0.07 s per tick
- **Snake initial length**: 3 segments
- **Food**: ● symbol | Snake head: ◆ | Body: █

## Running Tests

```bash
source .venv/bin/activate
python3 -m pytest tests/ -v
```

## License

MIT License

## Author

Coding Agent

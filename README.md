# 🐍 Snake Claw

A polished terminal Snake game with modern features and clean architecture.

## ✨ Features

- 🎮 **Classic gameplay** with smooth terminal rendering using curses
- 🏆 **High score system** with personalized name entry
- 📊 **Live HUD** showing score, high score, and level
- ⚡ **Progressive difficulty** — 6 speed levels that increase with score
- 🎨 **Color support** with proper aspect ratio (2:1 column correction)
- ⌨️ **Intuitive controls** — Arrow keys or WASD
- 📋 **Polished UI** — Menu, pause, help screens, high score table
- 💾 **Persistent storage** — Top 10 scores saved to JSON
- 🧪 **Well-tested** — 115 unit tests with full coverage
- 🐍 **Modern Python** — Type hints, clean separation of concerns
- 🎲 **Random food variety** — Different ASCII symbols spawn each time: (), [], {}, <>, ##, **, @@
- 🎨 **Clean ASCII rendering** — Solid blocks (██) for snake, varied symbols for food

## 🚀 Quick Start

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Run

```bash
snakeclaw
```

Or via module:

```bash
python3 -m snakeclaw
```

## 🎮 How to Play

1. **Navigate the menu** with ↑/↓ and Enter
2. **Move the snake** with arrow keys or WASD
3. **Eat food** (random emojis) to grow and score points
4. **Avoid walls and yourself** — collision ends the game
5. **Enter your name** when you achieve a high score!
6. **Press M** anytime to return to menu

### Controls

| Key | Action |
|-----|--------|
| **Arrow Keys / WASD** | Move snake |
| **P** | Pause / Resume |
| **M / Esc** | Return to menu |
| **R** | Restart game (from game over) |
| **Q** | Quit |
| **Enter / Space** | Select menu item / Confirm |

### High Score Entry

When you beat a high score, you'll be prompted to enter your initials:

- **↑/↓** — Change current letter (A-Z or space)
- **←/→** — Move cursor between the 3 characters
- **Enter** — Confirm and save
- **Esc** — Skip and use default "---"

## 🏗️ Architecture

### Clean Design

```
┌─────────────┐
│   game.py   │  ← Thin controller (game loop)
└──────┬──────┘
       │
   ┌───┴────┐
   ▼        ▼
┌────────┐ ┌────────┐
│engine  │ │  ui    │  ← Separated concerns
│(logic) │ │(render)│
└────┬───┘ └────────┘
     │
     ▼
┌─────────┐
│ model   │  ← Pure data structures
└─────────┘
```

**Key principles:**

- **Zero I/O in game logic** — `engine.py` is terminal-independent
- **Testability first** — All game logic tested without real terminal
- **State machine** — Clean transitions: menu → playing → paused → game over → enter initials
- **Aspect ratio fix** — 2 terminal columns per cell for square appearance

### Project Structure

```
TestGame/
├── snakeclaw/
│   ├── model.py         # Data structures (Snake, Food, Direction, State)
│   ├── engine.py        # Game logic & state machine
│   ├── ui.py            # Curses rendering
│   ├── game.py          # Main game loop controller
│   └── data/
│       └── highscores.json  # Persistent top 10 scores
├── tests/               # 115 unit tests
└── setup.py
```

## ⚙️ Game Mechanics

- **Playfield:** 60×30 logical grid (120×30 on screen with 2-column cells)
- **Starting snake:** 3 segments, moving right
- **Speed progression:** 6 levels, from 0.18s to 0.07s per tick
- **Level up:** Every 5 points scored
- **High scores:** Top 10 saved with initials and timestamps

## 🧪 Testing

Run the full test suite:

```bash
python3 -m pytest tests/ -v
```

**Coverage:**
- Model logic (Snake movement, collision, food placement)
- Engine (state transitions, scoring, high score management)
- UI (key mapping, rendering safety)
- Integration (game flow)

## 📋 Requirements

- **Python:** 3.12+ (uses modern type hints and features)
- **Platform:** Linux, macOS, or Windows with curses-compatible terminal
- **Dependencies:** Minimal (curses is built-in on Unix; windows-curses for Windows)

## 🛠️ Development

The codebase follows strict conventions:

- ✅ Type hints throughout
- ✅ PEP 8 style
- ✅ Docstrings on public methods
- ✅ Separation of concerns
- ✅ No global state

## 📝 License

MIT License — Free to use, modify, and distribute.

## 🤖 Credits

Built by a coding agent with attention to architecture, testing, and user experience.

---

**Enjoy the game! May your snake grow long and your reflexes stay sharp.** 🐍✨

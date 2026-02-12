# Snake Claw

A simple Snake game for the terminal/console written in Python.

## Features

- 🎮 Classic Snake gameplay
- 🖥️ Terminal UI using curses
- ⌨️ Arrow keys or WASD controls
- 📊 Score tracking
- 🔄 Restart game after game over
- 🧪 Unit tests for game logic
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

- **Arrow Keys**: Move up, down, left, right
- **W / A / S / D**: Alternative movement keys (up, left, down, right)
- **Space**: Start the game
- **R**: Restart game after game over
- **Q**: Quit game

## Gameplay

1. Press **Space** to start the game
2. Use arrow keys or WASD to control the snake
3. Eat the **@** food to grow and increase your score
4. Avoid hitting the walls or your own tail or body
5. After game over, press **R** to restart or **Q** to quit

## Architecture

### Project Structure

```
TestGame/
├── snakeclaw/
│   ├── __init__.py      # Package initialization
│   ├── __main__.py      # Entry point for python -m snakeclaw
│   ├── game.py          # Main game controller
│   ├── model.py         # Game models (Snake, Food, etc.)
│   └── ui.py            # Terminal UI using curses
├── tests/
│   └── test_model.py    # Unit tests for game logic
│   └── test_game.py    
│   └── test_ui.py    
├── setup.py             # Package setup configuration
└── README.md            # This file
```

### Design Principles

- **Separation of concerns**: Game logic is separated from UI and input handling
- **Testability**: Non-UI logic (movement, collision, food placement) is completely unit testable

### Game Settings

- **Playfield size**: 60 columns x 30 rows (configurable in `SnakeGame` class)
- **Tick rate**: 10 moves per second (configurable in `SnakeGame` class)
- **Snake initial length**: 3 segments
- **Food appearance**: @ symbol

## License

MIT License

## Author

Coding Agent

## Credits

Snake Claw is a simple implementation of the classic Snake game for the terminal.
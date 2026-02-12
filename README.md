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
cd TestGame
pip install -e .
```

### Manual Installation

If you don't want to install via pip, you can run the game directly:

```bash
cd TestGame
python -m snakeclaw
```

## Running the Game

### Using console script (after installation)

```bash
snakeclaw
```

### Using Python module

```bash
cd TestGame
python -m snakeclaw
```

### From the source directory

```bash
cd TestGame
python snakeclaw/__main__.py
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
4. Avoid hitting the walls or your own tail
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
├── setup.py             # Package setup configuration
└── README.md            # This file
```

### Design Principles

- **Separation of concerns**: Game logic is separated from UI and input handling
- **Testability**: Non-UI logic (movement, collision, food placement) is completely unit testable
- **Type hints**: All functions use Python type hints for better code clarity
- **Minimal dependencies**: Only uses Python standard library (curses is standard on Unix-like systems)

## Development

### Running Tests

```bash
cd TestGame
pytest tests/
```

### Running with specific test file

```bash
pytest tests/test_model.py
```

### Running with verbose output

```bash
pytest tests/ -v
```

## Notes

### Platform Considerations

#### macOS/Linux
- curses is available by default on Unix-like systems
- No additional dependencies required

#### Windows
- **Important**: Windows does not have a native curses library
- **Option 1**: Use Windows Terminal with Git Bash or similar (recommended)
- **Option 2**: Use WSL (Windows Subsystem for Linux)
- **Option 3**: Use an alternative UI library (would require changing the implementation)

If you encounter curses-related errors on Windows, make sure you're using a terminal that supports curses.

### Why curses?
- ✅ Standard in Unix-like systems (Linux, macOS)
- ✅ No external dependencies required
- ✅ Excellent for terminal-based games
- ✅ Provides good performance for simple games
- ✅ Works with all major terminal emulators

### Game Settings

- **Playfield size**: 60 columns x 30 rows (configurable in `SnakeGame` class)
- **Tick rate**: 10 moves per second (configurable in `SnakeGame` class)
- **Snake initial length**: 3 segments
- **Food appearance**: @ symbol

## License

MIT License

## Author

Your Name (or "Coding Agent")

## Credits

Snake Claw is a simple implementation of the classic Snake game for the terminal.
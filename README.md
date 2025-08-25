# Wordle Game Implementation

### Implemented Features
- A Python implementation of the classic Wordle game, replicating the original NYTimes version
- Uses tkinter library for graphical user interface
- Supports both keyboard input and on-screen virtual keyboard for letter entry

- Next planned update: Client-server architecture
  - Server will manage game state and validate inputs
  - Client will not have access to answers until game completion
  - Maintains same core gameplay and scoring rules

### File Structure
```
wordle_task/
├── main.py           # Entry point with dependency validation
├── wordle_game.py    # Core game engine and business logic
├── wordle_gui.py     # GUI implementation and user interaction
├── game_settings.py  # Configuration constants and validation
└── README.md         # Project documentation
```
### Setup 

#### Prerequisites
- Python 3.7+ with tkinter support
- No external dependencies required

#### Installation
```bash
# Clone/download the project files
# Ensure all Python files are in the same directory
```

#### Running the Game
```bash

python main.py
```

#### Configuration
- Modify `game_settings.py` to add words or change default rounds

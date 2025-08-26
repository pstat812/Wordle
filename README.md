# Wordle Game Implementation

## Development Notes
 - Currently using a simplified word list (10 words) for development purposes
 - A complete word list will be implemented in future updates

## Implemented Features
- A Python implementation of the classic Wordle game with client-server architecture
- Server manages game state and validates inputs using REST API
- Client provides graphical user interface using tkinter library
- Supports both keyboard input and on-screen virtual keyboard for letter entry
- Multiple concurrent games supported with unique game IDs
- Secure game state management - client cannot access answers until game completion
- Maintains same core gameplay and scoring rules as original NYTimes version

## File Structure
```
wordle_task/
├── Client/
│   ├── main.py              # Client entry point
│   └── wordle_client.py     # GUI implementation and API communication
├── Server/
│   ├── main.py              # Server entry point
│   ├── wordle_server.py     # Flask server and API endpoints
│   └── game_settings.py     # Game configuration and word list
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

## Setup 

### Prerequisites
- Python 3.7+ with tkinter support
- Flask and requests libraries (see requirements.txt)

### Installation
```bash
# Clone/download the project files
pip install -r requirements.txt
```

### Running the Game
```bash
# Start the server (in one terminal)
cd Server
python main.py

# Start the client (in another terminal)
cd Client
python main.py
```

## API Documentation

The server provides the following REST API endpoints:

### Create New Game
```http
POST /api/new_game
Content-Type: application/json

Body: {"max_rounds": 6}  # Optional

Response: {
    "success": true,
    "game_id": "uuid-string",
    "state": { ... game state ... }
}
```

### Get Game State
```http
GET /api/game/<game_id>/state

Response: {
    "success": true,
    "state": { ... game state ... }
}
```

### Submit Guess
```http
POST /api/game/<game_id>/guess
Content-Type: application/json

Body: {"guess": "HELLO"}

Response: {
    "success": true,
    "state": { ... updated game state ... }
}
```

### Health Check
```http
GET /api/health

Response: {
    "status": "healthy",
    "active_games": 0
}
```

### Delete Game
```http
DELETE /api/game/<game_id>

Response: {
    "success": true
}
```

## Development and Configuration

### Adding Words
Edit `Server/game_settings.py` to modify the `WORD_LIST`:
```python
WORD_LIST = [
    "ABOUT",
    "AFTER", 
    "AGAIN",
    "BRAIN",
    "CHAIR",
    # Add more 5-letter words...
]
```

When adding new words, ensure they meet these requirements:
- **Exactly 5 characters long** - Required for Wordle game mechanics
- **Only alphabetic characters** - No numbers, spaces, or special characters
- **Uppercase format** - All words must be in UPPERCASE
- **No duplicates** - Each word should appear only once in the list

To validate your word list, run:
```bash
cd Server
python game_settings.py
```

This will check for validation errors and display word list statistics. Any configuration issues will be reported with specific error messages.


### Server Configuration
The server runs on `127.0.0.1:5000` by default. To change this, modify the server startup in `Server/main.py`.


## Design Trade-offs

### Framework and Architecture Decisions

#### 1. Server Framework Choice: Flask vs Alternatives
- **Decision**: Flask web framework for REST API
- **Alternatives considered**: FastAPI, Django, vanilla HTTP server, TCP sockets
- **Trade-offs**: Flask provides the right balance of simplicity and robustness for a game server, with built-in JSON support and minimal boilerplate, though it has slightly more overhead than raw sockets

#### 2. Game Rules: Original Wordle vs Custom Variations  
- **Decision**: Stick to authentic Wordle rules exactly
- **Alternatives considered**: Custom scoring, different word lengths
- **Trade-offs**: User familiarity and consistency with the beloved original game outweighs innovation risks

#### 3. Client-Server Architecture vs Monolithic Design
- **Decision**: Separate client and server with REST API communication
- **Alternatives considered**: Single executable, embedded server, peer-to-peer
- **Trade-offs**: Enables security (client can't cheat), scalability, and multiple concurrent games, but increases deployment complexity and network dependency

#### 4. Word List Management: Embedded vs External Database
- **Decision**: Embedded word list in `game_settings.py` 
- **Alternatives considered**: External file (JSON/CSV), database, API lookup, large dictionary
- **Trade-offs**: Simple deployment and fast access in current development process

#### 5. Configuration Management: Centralized vs Distributed
- **Decision**: Centralized configuration in `game_settings.py` with Python constants
- **Alternatives considered**: Environment variables, config files, command-line arguments  
- **Trade-offs**: Single source of truth with type safety, but requires code changes for configuration updates and less deployment flexibility


## The Bells and Whistles
1. **Dual input support**: Both GUI virtual keyboard and physical keyboard input
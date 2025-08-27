# Multiplayer Wordle Game Implementation

A Python implementation of the classic Wordle game featuring both single-player and multiplayer modes with client-server architecture, user authentication, and real-time competitive gameplay.


## Features

### Core Features
- Authentic Wordle game mechanics
- Both single-player and multiplayer competitive modes
- Real-time multiplayer lobby system 
- User authentication and registration system

### Security Features
- Password hashing using SHA-256 encryption
- Secure game state management preventing client-side cheating
- Input validation and sanitization
- Session-based authentication
- Comprehensive error handling and logging

### Next Move
- Display player game statistic e.g win count , play count, winrate, highest countinous win
- UI Update e.g darkmode, customize HIT, PRESENT, MISS color
- Add new rules to multiple player mode to enrich the game 
- History function to show player gameplay history

## Game Rules and Mechanics

### Single Player Mode
- Classic Wordle gameplay with configurable attempt limits

### Multiplayer Mode(In development)
- Two players compete with the same target word with configurable attempt limits
- First player to guess correctly wins immediately
- If both players exhaust attempts, winner determined by HIT count

## File Structure

```
wordle_task/
├── Client/
│   ├── main.py                  # Application entry point and navigation controller
│   ├── login_page.py           # User authentication interface
│   ├── lobby_page.py           # Multiplayer lobby and room interface
│   ├── multiplayer_client.py   # Competitive multiplayer game interface
│   ├── wordle_client.py        # Single-player game interface
│   └── popup_dialog.py         # Reusable dialog system (Facade pattern)
├── Server/
│   ├── main.py                 # Server entry point
│   ├── wordle_server.py        # Core server logic and REST API
│   ├── database.py             # MongoDB operations (Repository pattern)
│   ├── game_settings.py        # Configuration constants and validation
│   ├── utils.py                # Development utilities and testing tools
│   └── logs/                   # Server logs with rotation
│       └── wordle_server.log
├── requirements.txt            # Python dependencies
└── README.md                  # Project documentation
```

## Tech Stack

### Backend Technologies
- **Python 3.7+**: Core programming language
- **Flask 2.0+**: Web framework for REST API implementation
- **MongoDB**: NoSQL database for user management and game data persistence
- **PyMongo 4.0+**: Official MongoDB driver for Python
- **UUID**: Unique identifier generation for game sessions
- **Hashlib**: SHA-256 password hashing for security
- **Logging**: Rotating file logs with structured formatting

### Frontend Technologies
- **Tkinter**: Native Python GUI framework for cross-platform desktop interface
- **Requests 2.25+**: HTTP client library for server communication
- **Threading**: Background polling for real-time multiplayer updates

### Development and Testing
- **Custom Utils Module**: Development utilities for word list validation
- **Configuration Management**: Centralized game settings and constants
- **Error Handling**: Comprehensive exception management and user feedback

## Architecture 

### Client-Server Architecture Pattern
The application implements a clear separation between client and server responsibilities:

**Server Responsibilities:**
- Game state management and validation
- Word selection and answer security
- User authentication and session management
- Database operations and data persistence

**Client Responsibilities:**
- User interface rendering and interaction handling
- Server communication via REST API
- Local state management for UI updates
- Simple Input validation and formatting e.g input word must be 5 letters

### Observer Pattern
The multiplayer system implements observer-like behavior through polling mechanisms where clients continuously observe server state changes for room status updates and game progression, enabling real-time multiplayer synchronization.

### State Pattern
Game state management is handled through the `GameState` dataclass, which encapsulates all game-related state information and transitions. This pattern allows for clean state transitions and simplified state management logic.

### Bridge Pattern
The separation between game logic (server) and presentation (client) implements the Bridge pattern, allowing both sides to vary independently without affecting each other.

### Facade Pattern
The `PopupDialog` class provides a facade for the complex tkinter messagebox system, offering a simplified interface for displaying various types of user messages throughout the application.

### Model-View-Controller (MVC)
The overall architecture follows MVC principles:
- **Model**: Server-side game logic, database operations, and data structures
- **View**: Tkinter GUI components and user interface elements  
- **Controller**: Client-side classes that handle user input and coordinate between view and server

## API Documentation

The server provides comprehensive REST API endpoints:

### Authentication Endpoints
```http
POST /api/auth/register
POST /api/auth/login
```

### Game Management
```http
POST /api/new_game
GET /api/game/<game_id>/state
POST /api/game/<game_id>/guess
DELETE /api/game/<game_id>
```

### Multiplayer System
```http
GET /api/rooms
POST /api/rooms/<room_id>/join
DELETE /api/rooms/<room_id>/leave
```

### System Health
```http
GET /api/health
```

## Setup and Installation

### Prerequisites
- Python 3.7+ with tkinter support
- MongoDB database access

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Configure MongoDB connection in Server/database.py
# Update the connection URI with your MongoDB credentials
```

### Running the Application
```bash
# Start the server (Terminal 1)
cd Server
python main.py

# Start the client (Terminal 2)  
cd Client
python main.py
```


## Development and Configuration

### Adding Words
Modify `WORD_LIST` in `Server/game_settings.py`:
```python
WORD_LIST = [
    "ABOUT", "AFTER", "AGAIN", "BRAIN", "CHAIR",
    # more 5-letter uppercase words will be added in production stage
]
```

### Word List Validation
```bash
cd Server
python game_settings.py  # Validate configuration
python utils.py          # Run comprehensive tests
```

### Server Configuration
Default server runs on `127.0.0.1:5000`. Modify `Server/main.py` to change host/port settings.

### Database Configuration
Update MongoDB connection string in `Server/database.py` with database credentials.

## Design Trade-offs

### Framework and Architecture Decisions

#### 1. Server Framework Choice: Flask vs Alternatives
- **Decision**: Flask web framework for REST API
- **Alternatives considered**: FastAPI, Django, vanilla HTTP server, TCP sockets
- **Trade-offs**: Flask provides the right balance of simplicity and robustness for a game server, with built-in JSON support and minimal boilerplate, though it has slightly more overhead than raw sockets

#### 2. Client-Server Architecture vs Monolithic Design
- **Decision**: Separate client and server with REST API communication
- **Alternatives considered**: Single executable, embedded server, peer-to-peer
- **Trade-offs**: Enables security (client can't cheat), scalability, and multiple concurrent games, but increases deployment complexity and network dependency

#### 3. Word List Management: Embedded vs External Database
- **Decision**: Embedded word list in `game_settings.py` 
- **Alternatives considered**: External file (JSON/CSV), database, API lookup, large dictionary
- **Trade-offs**: Simple deployment and fast access in current development process

#### 4. Configuration Management: Centralized vs Distributed
- **Decision**: Centralized configuration in `game_settings.py` with Python constants
- **Alternatives considered**: Environment variables, config files, command-line arguments  
- **Trade-offs**: Single source of truth with type safety, but requires code changes for configuration updates and less deployment flexibility

## The Bells and Whistles
1. **Dual input support**: Both GUI virtual keyboard and physical keyboard input to simulate the origin game on Web
2. **logging system**: server monitoring, easier for error logging with timestamps for troubleshooting




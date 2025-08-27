"""
Wordle Game Server - Server-side Game Logic and API

This module implements the server-side game engine for the client-server Wordle architecture.
The server manages game state, word selection, and validation while keeping the answer
secure from the client until game completion.

"""

import random
import uuid
import logging
import logging.handlers
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from flask import Flask, request, jsonify
from game_settings import WORD_LIST, DEFAULT_MAX_ROUNDS
from database import get_db_manager


def setup_logging():
    """Configure logging for the Wordle server."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logger
    logger = logging.getLogger('wordle_server')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create file handler with rotation (keeps last 5 files, 10MB each)
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/wordle_server.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Create console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Also configure Flask's logger to reduce noise
    flask_logger = logging.getLogger('werkzeug')
    flask_logger.setLevel(logging.WARNING)
    
    return logger


# Create logger instance
logger = setup_logging()


class LetterStatus(Enum):
    """Letter evaluation status matching the original game logic."""
    HIT = "HIT"
    PRESENT = "PRESENT"
    MISS = "MISS"
    UNUSED = "UNUSED"


@dataclass
class GameState:
    """Server-side game state representation."""
    game_id: str
    current_round: int
    max_rounds: int
    game_over: bool
    won: bool
    guesses: List[str]
    guess_results: List[List[Tuple[str, str]]]  # Letter status as string for JSON serialization
    letter_status: Dict[str, str]
    answer: Optional[str] = None  # Only included when game is over
    entire_game_over: bool = False  # True when entire multiplayer game is finished


class WordleServer:
    """
    Server-side Wordle game engine managing multiple game sessions.
    
    This class handles:
    - Game session management with unique game IDs
    - Word selection and secure answer storage
    - Guess validation and evaluation
    - Game state management without exposing answers to clients
    - Multiplayer room management
    - User authentication
    """
    
    def __init__(self):
        self.games: Dict[str, Dict] = {}  # Store active games by game_id
        self.rooms: Dict[int, Dict] = {1: {"players": [], "ready": {}, "game_id": None}, 
                                      2: {"players": [], "ready": {}, "game_id": None}, 
                                      3: {"players": [], "ready": {}, "game_id": None}}  # Room management
        self.word_list = WORD_LIST.copy()
        self.db_manager = get_db_manager()
        logger.info("Wordle server initialized with %d words", len(self.word_list))
    
    def create_new_game(self, max_rounds: Optional[int] = None) -> str:
        """
        Creates a new game session with a randomly selected word.
        
        Args:
            max_rounds: Maximum attempts allowed (default from settings)
            
        Returns:
            str: Unique game ID for this session
        """
        game_id = str(uuid.uuid4())
        max_rounds = max_rounds or DEFAULT_MAX_ROUNDS
        
        # Select random word (server keeps this secret)
        target_word = random.choice(self.word_list)
        
        # Initialize game state
        game_data = {
            "target_word": target_word,
            "current_round": 0,
            "max_rounds": max_rounds,
            "game_over": False,
            "won": False,
            "guesses": [],
            "guess_results": [],
            "letter_status": {letter: LetterStatus.UNUSED.value for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
        }
        
        self.games[game_id] = game_data
        
        # Log game creation (without revealing the answer)
        logger.info("New game created - ID: %s, max_rounds: %d, active_games: %d", 
                   game_id[:8], max_rounds, len(self.games))
        
        return game_id
    
    def get_game_state(self, game_id: str) -> Optional[GameState]:
        """
        Returns the current game state for a session (without revealing the answer).
        
        Args:
            game_id: Unique game identifier
            
        Returns:
            GameState object or None if game not found
        """
        if game_id not in self.games:
            return None
        
        game = self.games[game_id]
        
        # Create state object without exposing the answer unless game is over
        answer = game["target_word"] if game["game_over"] else None
        
        return GameState(
            game_id=game_id,
            current_round=game["current_round"],
            max_rounds=game["max_rounds"],
            game_over=game["game_over"],
            won=game["won"],
            guesses=game["guesses"].copy(),
            guess_results=game["guess_results"].copy(),
            letter_status=game["letter_status"].copy(),
            answer=answer
        )
    
    def is_valid_guess(self, game_id: str, guess: str) -> Tuple[bool, str]:
        """
        Validates a guess for a specific game session.
        
        Args:
            game_id: Unique game identifier
            guess: The word to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if game_id not in self.games:
            return False, "Game not found"
        
        game = self.games[game_id]
        
        if game["game_over"]:
            return False, "Game is already over"
        
        if not guess or not isinstance(guess, str):
            return False, "Guess must be a valid string"
        
        normalized_guess = guess.strip().upper()
        
        if len(normalized_guess) != 5:
            return False, "Guess must be exactly 5 letters"
        
        if not normalized_guess.isalpha():
            return False, "Guess must contain only letters"
        
        if normalized_guess not in self.word_list:
            logger.warning("Invalid word attempted for game %s: %s - not in word list", 
                          game_id[:8], normalized_guess)
            return False, "Word not in word list"
        
        return True, ""
    
    def make_guess(self, game_id: str, guess: str) -> Optional[GameState]:
        """
        Processes a guess and updates game state.
        
        Args:
            game_id: Unique game identifier
            guess: The 5-letter word guess
            
        Returns:
            Updated GameState or None if invalid
        """
        is_valid, error = self.is_valid_guess(game_id, guess)
        if not is_valid:
            logger.warning("Invalid guess for game %s: %s - Error: %s", 
                          game_id[:8], guess, error)
            return None
        
        game = self.games[game_id]
        normalized_guess = guess.strip().upper()
        target_word = game["target_word"]
        
        # Log the guess attempt
        logger.info("Guess submitted for game %s: %s (round %d/%d)", 
                   game_id[:8], normalized_guess, game["current_round"] + 1, game["max_rounds"])
        
        # Evaluate guess using the same algorithm as the original game
        evaluations = self._evaluate_guess_against_target(normalized_guess, target_word)
        
        # Update game state
        game["current_round"] += 1
        game["guesses"].append(normalized_guess)
        game["guess_results"].append([(letter, status.value) for letter, status in evaluations])
        
        # Update letter status
        self._update_letter_status(game["letter_status"], evaluations)
        
        # Check win condition
        if normalized_guess == target_word:
            game["won"] = True
            game["game_over"] = True
            logger.info("Game %s WON! Answer: %s, rounds: %d", 
                       game_id[:8], target_word, game["current_round"])
        
        # Check loss condition
        elif game["current_round"] >= game["max_rounds"]:
            game["game_over"] = True
            logger.info("Game %s LOST! Answer: %s, max rounds reached", 
                       game_id[:8], target_word)
        
        return self.get_game_state(game_id)
    
    def join_room(self, room_id: int, username: str) -> Dict[str, any]:
        """Join a room for multiplayer."""
        if room_id not in self.rooms:
            return {"success": False, "error": "Room does not exist"}
        
        room = self.rooms[room_id]
        
        # Check if there's an ended game in this room and clean it up
        if room["game_id"] and room["game_id"] in self.games:
            game = self.games[room["game_id"]]
            if all(p["game_over"] for p in game["players"].values()):
                logger.info("Cleaning up ended game %s when user %s joins room %d", 
                           room["game_id"][:8], username, room_id)
                self.cleanup_completed_game(room["game_id"])
        
        # After cleanup, check room capacity (but ignore if user was in the ended game)
        current_active_players = [p for p in room["players"] if p != username]
        if len(current_active_players) >= 2:
            return {"success": False, "error": "Room is full"}
        
        # Remove user from room["players"] if they were there from previous game
        if username in room["players"]:
            room["players"].remove(username)
        if username in room["ready"]:
            del room["ready"][username]
        
        # Remove user from other rooms first
        for rid, r in self.rooms.items():
            if username in r["players"]:
                r["players"].remove(username)
                if username in r["ready"]:
                    del r["ready"][username]
        
        room["players"].append(username)
        room["ready"][username] = True  # Auto-ready when joining
        
        logger.info("User %s joined room %d", username, room_id)
        
        # Check if room is now full (2 players) and auto-start game
        if len(room["players"]) == 2:
            # Start game immediately
            game_data = self.start_multiplayer_game(room_id)
            return {"success": True, "game_starting": True, "game_data": game_data}
        
        return {"success": True, "game_starting": False}
    
    def leave_room(self, room_id: int, username: str) -> Dict[str, bool]:
        """Leave a room."""
        if room_id not in self.rooms:
            return {"success": False, "error": "Room does not exist"}
        
        room = self.rooms[room_id]
        
        if username in room["players"]:
            room["players"].remove(username)
        
        if username in room["ready"]:
            del room["ready"][username]
        
        # If there's a completed game and room is now empty, clean it up
        if room["game_id"] and len(room["players"]) == 0:
            if room["game_id"] in self.games:
                game = self.games[room["game_id"]]
                if all(p["game_over"] for p in game["players"].values()):
                    self.cleanup_completed_game(room["game_id"])
        
        logger.info("User %s left room %d", username, room_id)
        return {"success": True}
    

    
    def start_multiplayer_game(self, room_id: int) -> Dict[str, any]:
        """Start a multiplayer game for a room."""
        room = self.rooms[room_id]
        players = room["players"]
        
        if len(players) != 2:
            return {"error": "Need exactly 2 players"}
        
        game_id = str(uuid.uuid4())
        
        # Automatically select random words for each player (same word for both)
        target_word = random.choice(self.word_list)
        
        # Initialize multiplayer game state
        game_data = {
            "game_type": "multiplayer",
            "room_id": room_id,
            "players": {
                players[0]: {
                    "selected_word": target_word,
                    "current_round": 0,
                    "max_rounds": DEFAULT_MAX_ROUNDS,
                    "game_over": False,
                    "won": False,
                    "guesses": [],
                    "guess_results": [],
                    "letter_status": {letter: LetterStatus.UNUSED.value for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
                },
                players[1]: {
                    "selected_word": target_word,
                    "current_round": 0,
                    "max_rounds": DEFAULT_MAX_ROUNDS,
                    "game_over": False,
                    "won": False,
                    "guesses": [],
                    "guess_results": [],
                    "letter_status": {letter: LetterStatus.UNUSED.value for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
                }
            },

            "game_started": True,  # Game starts immediately
            "winner": None,
            "target_word": target_word  # Store the common target word
        }
        
        self.games[game_id] = game_data
        room["game_id"] = game_id
        
        logger.info("Multiplayer game started - ID: %s, Room: %d, Players: %s, Word: %s", 
                   game_id[:8], room_id, players, target_word)
        
        # Return game data with opponent info for each player
        return {
            "game_id": game_id,
            "room_id": room_id,
            "players": players,
            "target_word": target_word
        }
    

    
    def make_guess_multiplayer(self, game_id: str, username: str, guess: str) -> tuple[Optional[GameState], str]:
        """
        Process a guess in multiplayer game.
        
        Returns:
            tuple: (GameState or None, error_message)
        """
        if game_id not in self.games:
            return None, "Game not found"
        
        game = self.games[game_id]
        
        if username not in game["players"]:
            return None, "Player not in game"
        
        player_data = game["players"][username]
        
        if not player_data["selected_word"]:
            return None, "Word not selected"
        
        if player_data["game_over"]:
            return None, "You have already finished the game"
        
        # Check if player has used all attempts
        if player_data["current_round"] >= player_data["max_rounds"]:
            return None, "You have used all your attempts"
        
        # Validate guess
        normalized_guess = guess.strip().upper()
        
        if len(normalized_guess) != 5 or not normalized_guess.isalpha():
            return None, "Guess must be exactly 5 letters"
        
        if normalized_guess not in self.word_list:
            return None, "Word not in word list"
        
        target_word = player_data["selected_word"]
        
        # Evaluate guess
        evaluations = self._evaluate_guess_against_target(normalized_guess, target_word)
        
        # Update player state
        player_data["current_round"] += 1
        player_data["guesses"].append(normalized_guess)
        player_data["guess_results"].append([(letter, status.value) for letter, status in evaluations])
        
        # Update letter status
        self._update_letter_status(player_data["letter_status"], evaluations)
        
        # Check win condition
        if normalized_guess == target_word:
            player_data["won"] = True
            player_data["game_over"] = True
            game["winner"] = username
            
            # Mark opponent as lost
            for other_user, other_data in game["players"].items():
                if other_user != username:
                    other_data["game_over"] = True
                    other_data["won"] = False
            
            # Update user stats
            self.db_manager.update_user_stats(username, True)
            for other_user in game["players"]:
                if other_user != username:
                    self.db_manager.update_user_stats(other_user, False)
            
            # Don't clean up immediately - let both players see the end state
            # Cleanup will happen when players leave or after timeout
            
            logger.info("Multiplayer game %s WON by %s! Word: %s", 
                       game_id[:8], username, target_word)
        
        # Check if player exhausted attempts without winning
        elif player_data["current_round"] >= player_data["max_rounds"]:
            player_data["game_over"] = True
            
            # Check if both players are done (either won or exhausted attempts)
            all_players_done = True
            for p in game["players"].values():
                if not p["game_over"]:
                    all_players_done = False
                    break
            
            if all_players_done:
                # Determine winner by HIT count if no one guessed correctly
                if not game.get("winner"):
                    self._determine_winner_by_hits(game)
                
                # Don't clean up immediately - let both players see the end state  
                # Cleanup will happen when players leave or after timeout
        
        return self.get_multiplayer_game_state(game_id, username), "Success"
    
    def _determine_winner_by_hits(self, game: Dict[str, Any]) -> None:
        """
        Determine winner based on HIT count when both players exhaust attempts.
        Updates game state and database accordingly.
        """
        player_hit_counts = {}
        
        # Calculate HIT count for each player
        for username, player_data in game["players"].items():
            hit_count = 0
            for guess_result in player_data["guess_results"]:
                for letter, status in guess_result:
                    if status == LetterStatus.HIT.value:
                        hit_count += 1
            player_hit_counts[username] = hit_count
        
        # Find the maximum HIT count
        max_hits = max(player_hit_counts.values())
        winners = [username for username, hits in player_hit_counts.items() if hits == max_hits]
        
        if len(winners) == 1:
            # Single winner based on HIT count
            winner = winners[0]
            game["winner"] = winner
            game["players"][winner]["won"] = True
            
            # Update database stats
            self.db_manager.update_user_stats(winner, True)
            for username in game["players"]:
                if username != winner:
                    self.db_manager.update_user_stats(username, False)
            
            logger.info("Multiplayer game %s decided by HIT count: %s wins with %d HITs", 
                       game.get("game_id", "")[:8], winner, max_hits)
        else:
            # Draw - multiple players with same HIT count
            game["winner"] = "DRAW"
            for username in game["players"]:
                game["players"][username]["won"] = False
            
            # Update games_played for both players, but no wins awarded
            for username in game["players"]:
                self.db_manager.update_user_stats(username, False)
            
            logger.info("Multiplayer game %s ended in DRAW: all players had %d HITs", 
                       game.get("game_id", "")[:8], max_hits)
    
    def cleanup_completed_game(self, game_id: str) -> None:
        """Clean up completed game and reset room."""
        if game_id not in self.games:
            return
        
        game = self.games[game_id]
        room_id = game.get("room_id")
        
        # Reset the room
        if room_id and room_id in self.rooms:
            room = self.rooms[room_id]
            room["players"] = []
            room["ready"] = {}
            room["game_id"] = None
            logger.info("Room %d cleaned up after game %s completion", room_id, game_id[:8])
        
        # Remove the game
        del self.games[game_id]
        logger.info("Game %s cleaned up and removed", game_id[:8])
    
    def get_multiplayer_game_state(self, game_id: str, username: str) -> Optional[GameState]:
        """Get game state for multiplayer game."""
        if game_id not in self.games:
            return None
        
        game = self.games[game_id]
        
        if username not in game["players"]:
            return None
        
        player_data = game["players"][username]
        
        # Include answer only if entire game is over
        answer = player_data["selected_word"] if (game.get("winner") is not None or all(p["game_over"] for p in game["players"].values())) else None
        
        # Check if opponent won
        opponent_won = game["winner"] is not None and game["winner"] != username
        
        # Check if entire game is over (all players finished or someone won)
        entire_game_over = game.get("winner") is not None or all(p["game_over"] for p in game["players"].values())
        
        return GameState(
            game_id=game_id,
            current_round=player_data["current_round"],
            max_rounds=player_data["max_rounds"],
            game_over=player_data["game_over"],
            won=player_data["won"],
            guesses=player_data["guesses"].copy(),
            guess_results=player_data["guess_results"].copy(),
            letter_status=player_data["letter_status"].copy(),
            answer=answer,
            entire_game_over=entire_game_over
        )
    
    def get_rooms_status(self) -> Dict[str, Dict]:
        """Get status of all rooms."""
        result = {}
        for room_id, room in self.rooms.items():
            # Check for ended games and clean them up proactively
            if room["game_id"] and room["game_id"] in self.games:
                game = self.games[room["game_id"]]
                if all(p["game_over"] for p in game["players"].values()):
                    logger.info("Proactively cleaning up ended game %s in room %d", 
                               room["game_id"][:8], room_id)
                    self.cleanup_completed_game(room["game_id"])
            
            room_data = {
                "players": room["players"],
                "ready": room["ready"],
                "game_id": room["game_id"]
            }
            
            # If there's an active game, include the target word
            if room["game_id"] and room["game_id"] in self.games:
                game = self.games[room["game_id"]]
                room_data["target_word"] = game.get("target_word")
            
            result[str(room_id)] = room_data
        
        return result
    
    def _evaluate_guess_against_target(self, guess: str, target: str) -> List[Tuple[str, LetterStatus]]:
        """
        Implements the authentic Wordle letter evaluation algorithm.
        Same logic as the original game engine.
        """
        result: List[Tuple[str, Optional[LetterStatus]]] = []
        
        # Create working copies to track letter consumption
        target_chars = list(target)
        guess_chars = list(guess)
        
        # First pass: Mark all exact position matches (HIT)
        for i in range(5):
            if guess_chars[i] == target_chars[i]:
                result.append((guess_chars[i], LetterStatus.HIT))
                # Mark as consumed to prevent double-counting
                target_chars[i] = None  # type: ignore
                guess_chars[i] = None   # type: ignore
            else:
                result.append((guess_chars[i], None))  # Placeholder for second pass
        
        # Second pass: Mark present letters (PRESENT) and misses (MISS)
        for i in range(5):
            if result[i][1] is None:  # Not already marked as HIT
                letter = guess[i]
                
                # Check if letter exists in remaining target characters
                if letter in target_chars:
                    result[i] = (letter, LetterStatus.PRESENT)
                    # Remove first occurrence to prevent double-counting
                    target_chars[target_chars.index(letter)] = None  # type: ignore
                else:
                    result[i] = (letter, LetterStatus.MISS)
        
        # Type assertion: all placeholders should be resolved
        return [(letter, status) for letter, status in result if status is not None]
    
    def _update_letter_status(self, letter_status: Dict[str, str], evaluations: List[Tuple[str, LetterStatus]]) -> None:
        """
        Updates global letter status tracking based on guess results.
        """
        for letter, new_status in evaluations:
            current_status = LetterStatus(letter_status[letter])
            
            # Status can only progress in priority order
            if new_status == LetterStatus.HIT:
                letter_status[letter] = LetterStatus.HIT.value
            elif new_status == LetterStatus.PRESENT and current_status != LetterStatus.HIT:
                letter_status[letter] = LetterStatus.PRESENT.value
            elif new_status == LetterStatus.MISS and current_status == LetterStatus.UNUSED:
                letter_status[letter] = LetterStatus.MISS.value
    
    def delete_game(self, game_id: str) -> bool:
        """
        Removes a completed game session from memory.
        
        Args:
            game_id: Unique game identifier
            
        Returns:
            bool: True if game was deleted, False if not found
        """
        if game_id in self.games:
            del self.games[game_id]
            logger.info("Game %s deleted, active_games: %d", game_id[:8], len(self.games))
            return True
        
        logger.warning("Attempted to delete non-existent game: %s", game_id[:8])
        return False


# Flask REST API setup
app = Flask(__name__)
server = WordleServer()
db_manager = get_db_manager()


@app.route('/api/new_game', methods=['POST'])
def new_game():
    """Create a new game session."""
    client_ip = request.remote_addr
    data = request.get_json() or {}
    max_rounds = data.get('max_rounds')
    
    logger.info("New game request from %s, max_rounds: %s", client_ip, max_rounds)
    
    try:
        game_id = server.create_new_game(max_rounds)
        state = server.get_game_state(game_id)
        
        logger.info("New game created successfully for %s - Game ID: %s", 
                   client_ip, game_id[:8])
        
        return jsonify({
            'success': True,
            'game_id': game_id,
            'state': asdict(state)
        })
    except Exception as e:
        logger.error("Failed to create new game for %s: %s", client_ip, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400





@app.route('/api/game/<game_id>', methods=['DELETE'])
def delete_game(game_id):
    """Delete a completed game session."""
    client_ip = request.remote_addr
    logger.info("Delete game request from %s for game %s", client_ip, game_id[:8])
    
    success = server.delete_game(game_id)
    return jsonify({
        'success': success
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    active_games = len(server.games)
    logger.info("Health check - Active games: %d", active_games)
    
    return jsonify({
        'status': 'healthy',
        'active_games': active_games
    })


# Authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    client_ip = request.remote_addr
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        logger.warning("Invalid registration request from %s: missing data", client_ip)
        return jsonify({
            'success': False,
            'error': 'Username and password are required'
        }), 400
    
    username = data['username']
    password = data['password']
    
    logger.info("Registration request from %s for user: %s", client_ip, username)
    
    result = db_manager.register_user(username, password)
    
    if result['success']:
        logger.info("User registered successfully: %s", username)
        return jsonify(result)
    else:
        logger.warning("Registration failed for user %s: %s", username, result['error'])
        return jsonify(result), 400


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user login."""
    client_ip = request.remote_addr
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        logger.warning("Invalid login request from %s: missing data", client_ip)
        return jsonify({
            'success': False,
            'error': 'Username and password are required'
        }), 400
    
    username = data['username']
    password = data['password']
    
    logger.info("Login request from %s for user: %s", client_ip, username)
    
    result = db_manager.authenticate_user(username, password)
    
    if result['success']:
        return jsonify(result)
    else:
        logger.warning("Authentication failed for user %s: %s", username, result['error'])
        return jsonify(result), 401


# Room management endpoints
@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """Get status of all rooms."""
    rooms_status = server.get_rooms_status()
    return jsonify({
        'success': True,
        'rooms': rooms_status
    })


@app.route('/api/rooms/<int:room_id>/join', methods=['POST'])
def join_room(room_id):
    """Join a room."""
    client_ip = request.remote_addr
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({
            'success': False,
            'error': 'Username is required'
        }), 400
    
    username = data['username']
    logger.info("Room join request from %s: user %s to room %d", client_ip, username, room_id)
    
    result = server.join_room(room_id, username)
    
    if result['success']:
        logger.info("User %s joined room %d successfully", username, room_id)
    else:
        logger.warning("User %s failed to join room %d: %s", username, room_id, result['error'])
    
    return jsonify(result)


@app.route('/api/rooms/<int:room_id>/leave', methods=['POST'])
def leave_room(room_id):
    """Leave a room."""
    client_ip = request.remote_addr
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({
            'success': False,
            'error': 'Username is required'
        }), 400
    
    username = data['username']
    logger.info("Room leave request from %s: user %s from room %d", client_ip, username, room_id)
    
    result = server.leave_room(room_id, username)
    return jsonify(result)





# Multiplayer game endpoints - word selection is now automatic

@app.route('/api/game/<game_id>/opponent', methods=['GET'])
def get_opponent_info(game_id):
    """Get opponent information for multiplayer game."""
    client_ip = request.remote_addr
    username = request.args.get('username')
    
    if not username:
        return jsonify({
            'success': False,
            'error': 'Username is required'
        }), 400
    
    if game_id not in server.games:
        return jsonify({
            'success': False,
            'error': 'Game not found'
        }), 404
    
    game = server.games[game_id]
    
    if username not in game["players"]:
        return jsonify({
            'success': False,
            'error': 'Player not in game'
        }), 400
    
    # Get opponent name
    opponent = None
    for player in game["players"]:
        if player != username:
            opponent = player
            break
    
    return jsonify({
        'success': True,
        'opponent': opponent,
        'target_word': game.get("target_word", "UNKNOWN"),
        'winner': game.get("winner")
    })


# Override existing guess endpoint to handle both single and multiplayer
@app.route('/api/game/<game_id>/guess', methods=['POST'])
def make_guess_endpoint(game_id):
    """Submit a guess for validation and evaluation (supports both single and multiplayer)."""
    client_ip = request.remote_addr
    data = request.get_json()
    
    if not data or 'guess' not in data:
        logger.warning("Invalid guess request from %s for game %s: missing guess", 
                      client_ip, game_id[:8])
        return jsonify({
            'success': False,
            'error': 'Guess is required'
        }), 400
    
    guess = data['guess']
    username = data.get('username')  # For multiplayer games
    
    logger.info("Guess request from %s for game %s: %s", 
               client_ip, game_id[:8], guess)
    
    # Check if this is a multiplayer game
    if game_id in server.games and server.games[game_id].get('game_type') == 'multiplayer':
        if not username:
            return jsonify({
                'success': False,
                'error': 'Username is required for multiplayer games'
            }), 400
        
        # Process multiplayer guess
        state, error_msg = server.make_guess_multiplayer(game_id, username, guess)
        if state is None:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
    else:
        # Process single player guess (original logic)
        is_valid, error = server.is_valid_guess(game_id, guess)
        if not is_valid:
            logger.warning("Invalid guess from %s for game %s: %s - %s", 
                          client_ip, game_id[:8], guess, error)
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        state = server.make_guess(game_id, guess)
        if state is None:
            logger.error("Failed to process guess from %s for game %s: %s", 
                        client_ip, game_id[:8], guess)
            return jsonify({
                'success': False,
                'error': 'Failed to process guess'
            }), 500
    
    return jsonify({
        'success': True,
        'state': asdict(state)
    })


# Override existing state endpoint to handle both single and multiplayer
@app.route('/api/game/<game_id>/state', methods=['GET'])
def get_state_endpoint(game_id):
    """Get current game state (supports both single and multiplayer)."""
    client_ip = request.remote_addr
    username = request.args.get('username')  # For multiplayer games
    
    logger.info("Game state request from %s for game %s", client_ip, game_id[:8])
    
    # Check if this is a multiplayer game
    if game_id in server.games and server.games[game_id].get('game_type') == 'multiplayer':
        if not username:
            return jsonify({
                'success': False,
                'error': 'Username is required for multiplayer games'
            }), 400
        
        state = server.get_multiplayer_game_state(game_id, username)
    else:
        # Original single player logic
        state = server.get_game_state(game_id)
    
    if state is None:
        logger.warning("Game state request for non-existent game %s from %s", 
                      game_id[:8], client_ip)
        return jsonify({
            'success': False,
            'error': 'Game not found'
        }), 404
    
    return jsonify({
        'success': True,
        'state': asdict(state)
    })


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Starting Wordle Server...")
    logger.info("Server configuration:")
    logger.info("  Host: 127.0.0.1")
    logger.info("  Port: 5000")
    logger.info("  Word list size: %d", len(WORD_LIST))
    logger.info("  Default max rounds: %d", DEFAULT_MAX_ROUNDS)
    logger.info("API endpoints:")
    logger.info("  POST /api/new_game - Create new game")
    logger.info("  GET /api/game/<id>/state - Get game state")
    logger.info("  POST /api/game/<id>/guess - Submit guess")
    logger.info("  DELETE /api/game/<id> - Delete game")
    logger.info("  GET /api/health - Health check")
    logger.info("=" * 50)
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False)  # Turn off debug for cleaner logs
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error("Server crashed: %s", str(e))
    finally:
        logger.info("Wordle server stopped")

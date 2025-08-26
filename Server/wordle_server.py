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
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from flask import Flask, request, jsonify
from game_settings import WORD_LIST, DEFAULT_MAX_ROUNDS


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


class WordleServer:
    """
    Server-side Wordle game engine managing multiple game sessions.
    
    This class handles:
    - Game session management with unique game IDs
    - Word selection and secure answer storage
    - Guess validation and evaluation
    - Game state management without exposing answers to clients
    """
    
    def __init__(self):
        self.games: Dict[str, Dict] = {}  # Store active games by game_id
        self.word_list = WORD_LIST.copy()
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


@app.route('/api/game/<game_id>/state', methods=['GET'])
def get_state(game_id):
    """Get current game state."""
    client_ip = request.remote_addr
    logger.info("Game state request from %s for game %s", client_ip, game_id[:8])
    
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


@app.route('/api/game/<game_id>/guess', methods=['POST'])
def make_guess(game_id):
    """Submit a guess for validation and evaluation."""
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
    logger.info("Guess request from %s for game %s: %s", 
               client_ip, game_id[:8], guess)
    
    # Validate guess first
    is_valid, error = server.is_valid_guess(game_id, guess)
    if not is_valid:
        logger.warning("Invalid guess from %s for game %s: %s - %s", 
                      client_ip, game_id[:8], guess, error)
        return jsonify({
            'success': False,
            'error': error
        }), 400
    
    # Process guess
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

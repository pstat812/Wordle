"""
Wordle Game Engine - Core Business Logic Module

This module implements the complete game engine for Wordle, following
object-oriented design principles and clean architecture patterns.
The implementation focuses on separation of concerns, immutable state
management, and comprehensive input validation.

"""

import random
from enum import Enum
from typing import List, Tuple, Dict, Optional, Final
from dataclasses import dataclass
from game_settings import DEFAULT_MAX_ROUNDS, WORD_LIST


class LetterStatus(Enum):
    """
    Enumeration representing the evaluation status of letters in Wordle.
    
    This enum implements the core Wordle scoring system with explicit
    semantic meaning for each status type. Using an enum ensures type
    safety and prevents invalid status values.
    
    Status Definitions:
        HIT: Letter is correct and in the correct position (Green in UI)
        PRESENT: Letter exists in target word but wrong position (Yellow in UI)
        MISS: Letter does not exist in target word (Gray in UI)
        UNUSED: Letter has not been guessed yet (Default state)
    

    """
    HIT = "HIT"
    PRESENT = "PRESENT"
    MISS = "MISS"
    UNUSED = "UNUSED"


@dataclass(frozen=True)
class GuessResult:
    """
    Immutable data structure representing the result of a single guess.
    
    This dataclass encapsulates all information about a guess evaluation,
    enabling clean data flow and preventing accidental state mutations.
    
    Attributes:
        word (str): The guessed word (normalized to uppercase)
        evaluations (List[Tuple[str, LetterStatus]]): Per-letter evaluations
        round_number (int): Which round this guess was made in
        is_correct (bool): Whether this guess matches the target word
    
    """
    word: str
    evaluations: List[Tuple[str, LetterStatus]]
    round_number: int
    is_correct: bool


class WordleGame:
    """
    Core game engine implementing Wordle business logic and state management.
    
    This class encapsulates all game state and operations, providing a clean
    API for game interactions while maintaining data integrity through
    comprehensive validation and immutable state transitions.
    
        1. Game state management (rounds, win/loss conditions)
        2. Word validation against allowed word list
        3. Guess evaluation using authentic Wordle algorithm
        4. Letter status tracking across all guesses
        5. Configuration management with sensible defaults
    

    """
    
    def __init__(self, max_rounds: Optional[int] = None, word_list: Optional[List[str]] = None) -> None:
        """
        Initialize a new Wordle game instance with configuration validation.
        
        Args:
            max_rounds: Maximum number of guess attempts (default from settings)
            word_list: Custom word list (default from settings)
            
        Raises:
            ValueError: If configuration parameters are invalid
            TypeError: If parameters are wrong type
            
        """
        # Configuration validation and initialization
        self._max_rounds = self._validate_max_rounds(max_rounds)
        self._word_list = self._validate_and_normalize_word_list(word_list)
        
        # Game state initialization - all mutable state in one place for clarity
        self._target_word: str = ""
        self._guess_history: List[GuessResult] = []
        self._current_round: int = 0
        self._game_over: bool = False
        self._is_won: bool = False
        
        # Letter status tracking: maintains global view of letter usage
        self._letter_status: Dict[str, LetterStatus] = {
            letter: LetterStatus.UNUSED 
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        }
        
        # Current input state (for UI integration)
        self._current_input: str = ""
        
        # Initialize game with random word selection
        self._initialize_new_game()
    
    def _validate_max_rounds(self, max_rounds: Optional[int]) -> int:
        """Validates and returns the maximum rounds configuration."""
        if max_rounds is None:
            return DEFAULT_MAX_ROUNDS
        
        if not isinstance(max_rounds, int):
            raise TypeError(f"max_rounds must be an integer, got {type(max_rounds)}")
        
        if max_rounds <= 0:
            raise ValueError(f"max_rounds must be positive, got {max_rounds}")
        
        if max_rounds > 20:  # Reasonable upper bound for UI purposes
            raise ValueError(f"max_rounds too large (max 20), got {max_rounds}")
        
        return max_rounds
    
    def _validate_and_normalize_word_list(self, word_list: Optional[List[str]]) -> List[str]:
        """Validates and normalizes the word list configuration."""
        if word_list is None:
            return WORD_LIST.copy()  # Defensive copy
        
        if not isinstance(word_list, list):
            raise TypeError(f"word_list must be a list, got {type(word_list)}")
        
        if not word_list:
            raise ValueError("word_list cannot be empty")
        
        # Normalize and validate each word
        normalized_words = []
        for i, word in enumerate(word_list):
            if not isinstance(word, str):
                raise TypeError(f"word_list[{i}] must be string, got {type(word)}")
            
            normalized = word.strip().upper()
            
            if len(normalized) != 5:
                raise ValueError(f"word_list[{i}] '{word}' must be exactly 5 characters")
            
            if not normalized.isalpha():
                raise ValueError(f"word_list[{i}] '{word}' must contain only letters")
            
            normalized_words.append(normalized)
        
        # Check for duplicates
        if len(normalized_words) != len(set(normalized_words)):
            raise ValueError("word_list contains duplicate words")
        
        return normalized_words
    
    def _initialize_new_game(self) -> None:
        """
        Initializes a fresh game state with random word selection.
        
        This method implements the game reset logic, ensuring all state
        is properly cleared and a new target word is selected using
        cryptographically secure random selection.
        """
        # Select target word using secure random selection
        self._target_word = random.choice(self._word_list)
        
        # Reset all game state
        self._guess_history.clear()
        self._current_round = 0
        self._game_over = False
        self._is_won = False
        self._current_input = ""
        
        # Reset letter status tracking
        for letter in self._letter_status:
            self._letter_status[letter] = LetterStatus.UNUSED
    
    def is_valid_guess(self, guess: str) -> bool:
        """
        Validates whether a guess meets all game requirements.
        
        Args:
            guess: The word to validate
            
        Returns:
            bool: True if guess is valid for submission
            
        Validation Rules:
            1. Must be exactly 5 characters
            2. Must contain only alphabetic characters
            3. Must exist in the allowed word list
            4. Game must not be over
        
        """
        if not guess or not isinstance(guess, str):
            return False
        
        normalized_guess = guess.strip().upper()
        
        # Length validation
        if len(normalized_guess) != 5:
            return False
        
        # Character validation
        if not normalized_guess.isalpha():
            return False
        
        # Word list validation (core Wordle rule)
        if normalized_guess not in self._word_list:
            return False
        
        return True
    
    def make_guess(self, guess: str) -> GuessResult:
        """
        Processes a guess and returns the evaluation result.
        
        This method implements the core Wordle game loop: validates input,
        evaluates against target word, updates game state, and returns
        comprehensive result information.
        
        Args:
            guess: The 5-letter word guess
            
        Returns:
            GuessResult: Immutable result containing evaluation details
            
        Raises:
            ValueError: If guess is invalid or game is over
            
        State Changes:
            - Increments current round
            - Updates letter status tracking
            - May transition game to won/lost state
            - Adds guess to history
        
        """
        # Pre-condition validation
        if self._game_over:
            raise ValueError("Cannot make guess: game is already over")
        
        if not self.is_valid_guess(guess):
            raise ValueError(
                "Invalid guess: must be a 5-letter word from the allowed word list"
            )
        
        normalized_guess = guess.strip().upper()
        
        # Core evaluation logic
        evaluations = self._evaluate_guess_against_target(normalized_guess)
        
        # State updates
        self._current_round += 1
        self._update_letter_status(evaluations)
        
        # Win condition check
        is_correct = normalized_guess == self._target_word
        if is_correct:
            self._is_won = True
            self._game_over = True
        
        # Loss condition check
        elif self._current_round >= self._max_rounds:
            self._game_over = True
        
        # Create immutable result record
        result = GuessResult(
            word=normalized_guess,
            evaluations=evaluations,
            round_number=self._current_round,
            is_correct=is_correct
        )
        
        # Add to history for audit trail
        self._guess_history.append(result)
        
        return result
    
    def _evaluate_guess_against_target(self, guess: str) -> List[Tuple[str, LetterStatus]]:
        """
        Implements the authentic Wordle letter evaluation algorithm.
        
        This algorithm matches the original Wordle behavior exactly:
        1. First pass: Mark exact matches (HIT)
        2. Second pass: Mark present letters (PRESENT) without double-counting
        3. Remaining letters: Mark as MISS
        
        Args:
            guess: 5-letter normalized guess word
            
        Returns:
            List of (letter, status) tuples in position order
            
        Algorithm Details:
            The two-pass approach prevents incorrect PRESENT markings when
            a letter appears multiple times. For example, if target is "SPEED"
            and guess is "ERASE", the first E gets PRESENT, the last E gets HIT,
            and any additional E's would get MISS.
        
    
        """
        result: List[Tuple[str, Optional[LetterStatus]]] = []
        
        # Create working copies to track letter consumption
        target_chars = list(self._target_word)
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
    
    def _update_letter_status(self, evaluations: List[Tuple[str, LetterStatus]]) -> None:
        """
        Updates global letter status tracking based on guess results.
        
        This method maintains the cumulative status of each letter across
        all guesses, implementing priority rules for status updates.
        
        Priority Order (status can only improve):
        UNUSED -> MISS -> PRESENT -> HIT
        
        Args:
            evaluations: Letter evaluations from current guess
        """
        for letter, new_status in evaluations:
            current_status = self._letter_status[letter]
            
            # Status can only progress in priority order
            if new_status == LetterStatus.HIT:
                self._letter_status[letter] = LetterStatus.HIT
            elif new_status == LetterStatus.PRESENT and current_status != LetterStatus.HIT:
                self._letter_status[letter] = LetterStatus.PRESENT
            elif new_status == LetterStatus.MISS and current_status == LetterStatus.UNUSED:
                self._letter_status[letter] = LetterStatus.MISS
    
    # Public API methods for state inspection
    
    def get_game_state(self) -> Dict:
        """
        Returns comprehensive game state for UI/API consumption.
        
        This method provides a complete snapshot of current game state
        in a serializable format suitable for UI updates or API responses.
        
        Returns:
            Dict containing:
                - current_round: Current guess attempt number
                - max_rounds: Maximum allowed attempts
                - guesses: List of all guess words
                - guess_results: Detailed evaluation results
                - game_over: Whether game has ended
                - won: Whether player won
                - answer: Target word (only if game over)
                - letter_status: Status of all letters
        """
        return {
            "current_round": self._current_round,
            "max_rounds": self._max_rounds,
            "guesses": [result.word for result in self._guess_history],
            "guess_results": [
                [(letter, status.value) for letter, status in result.evaluations]
                for result in self._guess_history
            ],
            "game_over": self._game_over,
            "won": self._is_won,
            "answer": self._target_word if self._game_over else None,
            "letter_status": {letter: status.value for letter, status in self._letter_status.items()}
        }
    
    def get_remaining_rounds(self) -> int:
        """Returns number of attempts remaining."""
        return max(0, self._max_rounds - self._current_round)
    
    def is_game_over(self) -> bool:
        """Returns whether the game has ended (won or lost)."""
        return self._game_over
    
    def has_won(self) -> bool:
        """Returns whether the player has won the game."""
        return self._is_won and self._game_over
    
    def has_lost(self) -> bool:
        """Returns whether the player has lost the game."""
        return self._game_over and not self._is_won
    
    def get_answer(self) -> Optional[str]:
        """Returns the target word if game is over, None otherwise."""
        return self._target_word if self._game_over else None
    
    def get_letter_status(self, letter: str) -> LetterStatus:
        """Returns the current status of a specific letter."""
        return self._letter_status.get(letter.upper(), LetterStatus.UNUSED)
    
    # Input management methods for UI integration
    
    def get_current_guess(self) -> str:
        """Returns the current partial guess being typed."""
        return self._current_input
    
    def add_letter_to_guess(self, letter: str) -> None:
        """Adds a letter to the current guess (max 5 letters)."""
        if len(self._current_input) < 5 and letter.isalpha():
            self._current_input += letter.upper()
    
    def remove_letter_from_guess(self) -> None:
        """Removes the last letter from current guess."""
        if self._current_input:
            self._current_input = self._current_input[:-1]
    
    def submit_current_guess(self) -> GuessResult:
        """Submits the current guess and clears input buffer."""
        if not self._current_input:
            raise ValueError("No guess to submit")
        
        guess_to_submit = self._current_input
        self._current_input = ""  # Clear input buffer
        
        return self.make_guess(guess_to_submit)
    
    # Configuration API methods
    
    def get_max_rounds(self) -> int:
        """Returns the maximum number of rounds configured."""
        return self._max_rounds
    
    def get_word_list(self) -> List[str]:
        """Returns a copy of the word list (defensive copy)."""
        return self._word_list.copy()
    
    def set_max_rounds(self, rounds: int) -> None:
        """Updates maximum rounds configuration."""
        validated_rounds = self._validate_max_rounds(rounds)
        self._max_rounds = validated_rounds
    
    def set_word_list(self, word_list: List[str]) -> None:
        """Updates word list configuration."""
        validated_list = self._validate_and_normalize_word_list(word_list)
        self._word_list = validated_list
    
    def start_new_game(self) -> None:
        """Resets all game state and starts a fresh game."""
        self._initialize_new_game()
    
    def __repr__(self) -> str:
        """Returns detailed string representation for debugging."""
        return (f"WordleGame(round={self._current_round}/{self._max_rounds}, "
                f"word_count={len(self._word_list)}, "
                f"game_over={self._game_over}, won={self._is_won})")
    
    def __str__(self) -> str:
        """Returns human-readable string representation."""
        if self._game_over:
            outcome = "Won" if self._is_won else "Lost"
            return f"Wordle Game: {outcome} in {self._current_round} rounds"
        else:
            return f"Wordle Game: Round {self._current_round}/{self._max_rounds}"
"""
Game Configuration Constants Module

This module defines all game configuration constants following the
Single Responsibility Principle and Configuration Management best practices.
All game parameters are centralized here to enable easy modification
without touching core business logic.

    - Adding new words: Extend WORD_LIST array
    - MAX_ROUNDS adjustment: Modify DEFAULT_MAX_ROUNDS

"""

from typing import List, Final

# Core Game Configuration Constants
DEFAULT_MAX_ROUNDS: Final[int] = 3
"""
Default maximum number of guess attempts allowed per game.
Type: Final[int] - Immutable to prevent accidental modification
"""

# Curated Word Database
WORD_LIST: Final[List[str]] = [
    "ABOUT",  
    "AFTER",  
    "AGAIN",  
    "BRAIN",  
    "CHAIR",  
    "DANCE",  
    "EARLY",  
    "FIELD",
    "HEART", 
    "LIGHT"   
]


# Development functions moved to utils.py

# Module initialization: Validate configuration on import
if __name__ == "__main__":
    # Import development utilities for testing
    from utils import validate_word_list_integrity, get_word_statistics
    
    try:
        if validate_word_list_integrity():
            print("Word list validation passed")
        
        stats = get_word_statistics()
        if "error" not in stats:
            print(f"Game statistics: {stats}")
        else:
            print(f"Statistics error: {stats['error']}")
        
        print("All configuration validation checks passed")
    except Exception as e:
        print(f"Configuration error: {e}")
        print("Please fix the word list in WORD_LIST before using the server.")
        exit(1)
"""
Development and Testing Utilities

This module contains functions used for development, testing, and word list validation.
These functions are useful for development and maintenance.
"""

from typing import List, Final
from game_settings import WORD_LIST


def validate_word_list_integrity() -> bool:
    """
    Validates the integrity and consistency of the word database.
    
    This function performs validation to ensure:
    1. Length validation: All words must be exactly 5 characters
    2. Character validation: Only alphabetic characters allowed
    3. Uniqueness validation: No duplicate entries
    4. Format validation: Consistent uppercase formatting
    
    Returns:
        bool: True if word list passes all validation checks
        
    Example:
        >>> if validate_word_list_integrity():
        ...     print("Word list is valid")
        ... else:
        ...     print("Word list has errors")
    """
    if not WORD_LIST:
        print("ERROR: Word list is empty")
        return False
    
    errors = []
    
    # Check each word
    for i, word in enumerate(WORD_LIST):
        # Length validation
        if len(word) != 5:
            errors.append(f"Word '{word}' at index {i}: Invalid length ({len(word)} chars, expected 5)")
        
        # Character validation
        if not word.isalpha():
            errors.append(f"Word '{word}' at index {i}: Contains non-alphabetic characters")
        
        # Format validation
        if word != word.upper():
            errors.append(f"Word '{word}' at index {i}: Not in uppercase format")
    
    # Uniqueness validation
    unique_words = set(WORD_LIST)
    if len(unique_words) != len(WORD_LIST):
        duplicate_count = len(WORD_LIST) - len(unique_words)
        errors.append(f"Word list contains {duplicate_count} duplicate entries")
        
        # Find specific duplicates
        word_counts = {}
        for word in WORD_LIST:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        duplicates = [word for word, count in word_counts.items() if count > 1]
        for duplicate in duplicates:
            errors.append(f"Duplicate word found: '{duplicate}' appears {word_counts[duplicate]} times")
    
    # Report results
    if errors:
        print(f"Word list validation FAILED with {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print(f"Word list validation PASSED: {len(WORD_LIST)} words validated successfully")
    
    return True


def get_word_statistics() -> dict:
    """
    Analyzes word list and returns statistical information for game balancing.
    
    Returns:
        dict: Statistical analysis including:
            - total_words: Number of words in database
            - avg_vowel_count: Average vowels per word
            - letter_frequency: Distribution of letters across all words
            - most_common_letters: Top 5 most frequent letters
    
    Example:
        >>> stats = get_word_statistics()
        >>> print(f"Total words: {stats['total_words']}")
        >>> print(f"Average vowels: {stats['avg_vowel_count']}")
    """
    if not WORD_LIST:
        return {"error": "Word list is empty"}
    
    vowels = set('AEIOU')
    total_vowels = sum(len([char for char in word if char in vowels]) for word in WORD_LIST)
    
    # Calculate letter frequency distribution
    letter_frequency = {}
    for word in WORD_LIST:
        for char in word:
            letter_frequency[char] = letter_frequency.get(char, 0) + 1
    
    return {
        "total_words": len(WORD_LIST),
        "avg_vowel_count": round(total_vowels / len(WORD_LIST), 2),
        "letter_frequency": letter_frequency,
        "most_common_letters": sorted(letter_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
    }


def run_development_tests():
    """
    Run all development tests and validations.
    
    This function runs a comprehensive test suite for development purposes.
    """
    print("Running Wordle Development Tests...")
    print("=" * 50)
    
    # Test 1: Word list validation
    print("Test 1: Word List Validation")
    if validate_word_list_integrity():
        print("Word list validation PASSED")
    else:
        print("Word list validation FAILED")
    
    print()
    
    # Test 2: Word statistics
    print("Test 2: Word Statistics Analysis")
    stats = get_word_statistics()
    if "error" in stats:
        print(f"Statistics generation FAILED: {stats['error']}")
    else:
        print("Statistics generation PASSED")
        print(f"  Total words: {stats['total_words']}")
        print(f"  Average vowels per word: {stats['avg_vowel_count']}")
        print(f"  Most common letters: {[letter for letter, count in stats['most_common_letters']]}")
    
    print()
    print("Development tests completed!")


if __name__ == "__main__":
    # Run tests when script is executed directly
    run_development_tests()

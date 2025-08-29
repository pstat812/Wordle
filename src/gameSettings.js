/**
 * Game Configuration Constants Module
 *
 * This module defines all game configuration constants following the
 * Single Responsibility Principle and Configuration Management best practices.
 * All game parameters are centralized here to enable easy modification
 * without touching core business logic.
 *
 * Usage:
 *   - Adding new words: Extend WORD_LIST array
 *   - Difficulty adjustment: Modify DEFAULT_MAX_ROUNDS
 *   - Game balancing: Update word list based on analytics
 */

// Core Game Configuration Constants
export const DEFAULT_MAX_ROUNDS = 6;
/**
 * Default maximum number of guess attempts allowed per game.
 * Type: Immutable constant to prevent accidental modification
 */

// Curated Word Database
export const WORD_LIST = [
  "ABOUT",
  "AFTER",
  "AGAIN",
  "BRAIN",
  "CHAIR",
  "DANCE",
  "EARLY",
  "FIELD",
  "HEART",
  "LIGHT",
  "HELLO",
  "WORLD",
  "WORDS",
  "TESTS",
  "QUICK"
];

/**
 * Validates the integrity and consistency of the word database.
 *
 * This function performs validation to ensure:
 * 1. Length validation: All words must be exactly 5 characters
 * 2. Character validation: Only alphabetic characters allowed
 * 3. Uniqueness validation: No duplicate entries
 * 4. Format validation: Consistent uppercase formatting
 *
 * @returns {boolean} True if word list passes all validation checks
 * @throws {Error} If any validation check fails with detailed error message
 */
export function validateWordListIntegrity() {
  if (!WORD_LIST || WORD_LIST.length === 0) {
    throw new Error("Word list cannot be empty");
  }

  // Validate each word meets game requirements
  for (let index = 0; index < WORD_LIST.length; index++) {
    const word = WORD_LIST[index];
    
    if (word.length !== 5) {
      throw new Error(`Word at index ${index} '${word}' is not 5 characters long`);
    }

    if (!/^[A-Z]+$/.test(word)) {
      throw new Error(`Word at index ${index} '${word}' contains non-alphabetic characters or is not uppercase`);
    }
  }

  // Validate uniqueness (no duplicates)
  const uniqueWords = new Set(WORD_LIST);
  if (WORD_LIST.length !== uniqueWords.size) {
    const duplicates = WORD_LIST.filter((word, index) => WORD_LIST.indexOf(word) !== index);
    throw new Error(`Duplicate words found in word list: ${duplicates.join(', ')}`);
  }

  return true;
}

/**
 * Analyzes word list and returns statistical information for game balancing.
 *
 * @returns {object} Statistical analysis including:
 *   - totalWords: Number of words in database
 *   - avgVowelCount: Average vowels per word
 *   - letterFrequency: Distribution of letters across all words
 *   - mostCommonLetters: Top 5 most common letters
 */
export function getWordStatistics() {
  if (!WORD_LIST || WORD_LIST.length === 0) {
    return { error: "Word list is empty" };
  }

  const vowels = new Set(['A', 'E', 'I', 'O', 'U']);
  const totalVowels = WORD_LIST.reduce((sum, word) => {
    return sum + Array.from(word).filter(char => vowels.has(char)).length;
  }, 0);

  // Calculate letter frequency distribution
  const letterFrequency = {};
  WORD_LIST.forEach(word => {
    Array.from(word).forEach(char => {
      letterFrequency[char] = (letterFrequency[char] || 0) + 1;
    });
  });

  const mostCommonLetters = Object.entries(letterFrequency)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return {
    totalWords: WORD_LIST.length,
    avgVowelCount: Math.round((totalVowels / WORD_LIST.length) * 100) / 100,
    letterFrequency,
    mostCommonLetters
  };
}

// Module initialization: Validate configuration on load
try {
  validateWordListIntegrity();
  console.log("Word list validation passed");
  
  const stats = getWordStatistics();
  console.log("Game statistics:", stats);
  
  console.log("All configuration validation checks passed");
} catch (configError) {
  console.error("Configuration validation failed:", configError.message);
}

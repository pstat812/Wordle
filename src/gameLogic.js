/**
 * Wordle Game Engine - Core Business Logic Module
 *
 * This module implements the complete game engine for Wordle, following
 * functional programming principles and React patterns.
 * The implementation focuses on immutable state management and
 * comprehensive input validation.
 */

import { DEFAULT_MAX_ROUNDS, WORD_LIST } from './gameSettings';

// Letter Status Enumeration
export const LETTER_STATUS = {
  HIT: "HIT",         // Letter is correct and in the correct position (Green in UI)
  PRESENT: "PRESENT", // Letter exists in target word but wrong position (Yellow in UI)
  MISS: "MISS",       // Letter does not exist in target word (Gray in UI)
  UNUSED: "UNUSED"    // Letter has not been guessed yet (Default state)
};

/**
 * Creates initial game state
 * @param {number} maxRounds - Maximum number of guess attempts
 * @param {string[]} wordList - List of valid words
 * @returns {object} Initial game state
 */
export function createInitialGameState(maxRounds = DEFAULT_MAX_ROUNDS, wordList = WORD_LIST) {
  // Validate configuration
  if (!Number.isInteger(maxRounds) || maxRounds <= 0) {
    throw new Error(`maxRounds must be a positive integer, got ${maxRounds}`);
  }
  
  if (maxRounds > 20) {
    throw new Error(`maxRounds too large (max 20), got ${maxRounds}`);
  }

  if (!Array.isArray(wordList) || wordList.length === 0) {
    throw new Error("wordList must be a non-empty array");
  }

  // Initialize letter status tracking
  const letterStatus = {};
  for (let i = 65; i <= 90; i++) { // A-Z ASCII codes
    letterStatus[String.fromCharCode(i)] = LETTER_STATUS.UNUSED;
  }

  return {
    targetWord: selectRandomWord(wordList),
    guessHistory: [],
    currentRound: 0,
    gameOver: false,
    isWon: false,
    letterStatus,
    currentInput: "",
    maxRounds,
    wordList: [...wordList] // Defensive copy
  };
}

/**
 * Selects a random word from the word list
 * @param {string[]} wordList - List of valid words
 * @returns {string} Randomly selected word
 */
function selectRandomWord(wordList) {
  const randomIndex = Math.floor(Math.random() * wordList.length);
  return wordList[randomIndex];
}

/**
 * Validates whether a guess meets all game requirements
 * @param {string} guess - The word to validate
 * @param {object} gameState - Current game state
 * @returns {boolean} True if guess is valid for submission
 */
export function isValidGuess(guess, gameState) {
  if (!guess || typeof guess !== 'string') {
    return false;
  }

  const normalizedGuess = guess.trim().toUpperCase();

  // Length validation
  if (normalizedGuess.length !== 5) {
    return false;
  }

  // Character validation
  if (!/^[A-Z]+$/.test(normalizedGuess)) {
    return false;
  }

  // Word list validation (core Wordle rule)
  if (!gameState.wordList.includes(normalizedGuess)) {
    return false;
  }

  return true;
}

/**
 * Processes a guess and returns the updated game state
 * @param {object} gameState - Current game state
 * @param {string} guess - The 5-letter word guess
 * @returns {object} Updated game state with guess result
 */
export function makeGuess(gameState, guess) {
  // Pre-condition validation
  if (gameState.gameOver) {
    throw new Error("Cannot make guess: game is already over");
  }

  if (!isValidGuess(guess, gameState)) {
    throw new Error("Invalid guess: must be a 5-letter word from the allowed word list");
  }

  const normalizedGuess = guess.trim().toUpperCase();

  // Core evaluation logic
  const evaluations = evaluateGuessAgainstTarget(normalizedGuess, gameState.targetWord);

  // Create guess result
  const guessResult = {
    word: normalizedGuess,
    evaluations,
    roundNumber: gameState.currentRound + 1,
    isCorrect: normalizedGuess === gameState.targetWord
  };

  // Update state
  const newCurrentRound = gameState.currentRound + 1;
  const newLetterStatus = updateLetterStatus(gameState.letterStatus, evaluations);
  const isCorrect = normalizedGuess === gameState.targetWord;
  const isGameOver = isCorrect || newCurrentRound >= gameState.maxRounds;

  return {
    ...gameState,
    guessHistory: [...gameState.guessHistory, guessResult],
    currentRound: newCurrentRound,
    letterStatus: newLetterStatus,
    gameOver: isGameOver,
    isWon: isCorrect,
    currentInput: "" // Clear input buffer
  };
}

/**
 * Implements the authentic Wordle letter evaluation algorithm
 * @param {string} guess - 5-letter normalized guess word
 * @param {string} target - 5-letter target word
 * @returns {Array} Array of [letter, status] tuples in position order
 */
function evaluateGuessAgainstTarget(guess, target) {
  const result = [];
  
  // Create working copies to track letter consumption
  const targetChars = Array.from(target);
  const guessChars = Array.from(guess);

  // First pass: Mark all exact position matches (HIT)
  for (let i = 0; i < 5; i++) {
    if (guessChars[i] === targetChars[i]) {
      result[i] = [guessChars[i], LETTER_STATUS.HIT];
      // Mark as consumed to prevent double-counting
      targetChars[i] = null;
      guessChars[i] = null;
    } else {
      result[i] = [guessChars[i], null]; // Placeholder for second pass
    }
  }

  // Second pass: Mark present letters (PRESENT) and misses (MISS)
  for (let i = 0; i < 5; i++) {
    if (result[i][1] === null) { // Not already marked as HIT
      const letter = guess[i];
      
      // Check if letter exists in remaining target characters
      const targetIndex = targetChars.indexOf(letter);
      if (targetIndex !== -1) {
        result[i] = [letter, LETTER_STATUS.PRESENT];
        // Remove first occurrence to prevent double-counting
        targetChars[targetIndex] = null;
      } else {
        result[i] = [letter, LETTER_STATUS.MISS];
      }
    }
  }

  return result;
}

/**
 * Updates global letter status tracking based on guess results
 * @param {object} currentLetterStatus - Current letter status mapping
 * @param {Array} evaluations - Letter evaluations from current guess
 * @returns {object} Updated letter status mapping
 */
function updateLetterStatus(currentLetterStatus, evaluations) {
  const newLetterStatus = { ...currentLetterStatus };

  evaluations.forEach(([letter, newStatus]) => {
    const currentStatus = newLetterStatus[letter];

    // Status can only progress in priority order: UNUSED -> MISS -> PRESENT -> HIT
    if (newStatus === LETTER_STATUS.HIT) {
      newLetterStatus[letter] = LETTER_STATUS.HIT;
    } else if (newStatus === LETTER_STATUS.PRESENT && currentStatus !== LETTER_STATUS.HIT) {
      newLetterStatus[letter] = LETTER_STATUS.PRESENT;
    } else if (newStatus === LETTER_STATUS.MISS && currentStatus === LETTER_STATUS.UNUSED) {
      newLetterStatus[letter] = LETTER_STATUS.MISS;
    }
  });

  return newLetterStatus;
}

/**
 * Adds a letter to the current guess input
 * @param {object} gameState - Current game state
 * @param {string} letter - Letter to add
 * @returns {object} Updated game state
 */
export function addLetterToGuess(gameState, letter) {
  if (gameState.gameOver) {
    return gameState;
  }

  if (gameState.currentInput.length >= 5 || !/^[A-Z]$/i.test(letter)) {
    return gameState;
  }

  return {
    ...gameState,
    currentInput: gameState.currentInput + letter.toUpperCase()
  };
}

/**
 * Removes the last letter from current guess input
 * @param {object} gameState - Current game state
 * @returns {object} Updated game state
 */
export function removeLetterFromGuess(gameState) {
  if (gameState.gameOver) {
    return gameState;
  }

  return {
    ...gameState,
    currentInput: gameState.currentInput.slice(0, -1)
  };
}

/**
 * Starts a new game with the same configuration
 * @param {object} gameState - Current game state
 * @returns {object} Fresh game state
 */
export function startNewGame(gameState) {
  return createInitialGameState(gameState.maxRounds, gameState.wordList);
}

/**
 * Updates game configuration
 * @param {object} gameState - Current game state
 * @param {object} config - New configuration { maxRounds?, wordList? }
 * @returns {object} Updated game state with new configuration
 */
export function updateGameConfig(gameState, config) {
  const newMaxRounds = config.maxRounds !== undefined ? config.maxRounds : gameState.maxRounds;
  const newWordList = config.wordList !== undefined ? config.wordList : gameState.wordList;

  return createInitialGameState(newMaxRounds, newWordList);
}

/**
 * Gets comprehensive game state information
 * @param {object} gameState - Current game state
 * @returns {object} Formatted game state for UI consumption
 */
export function getGameStateInfo(gameState) {
  return {
    currentRound: gameState.currentRound,
    maxRounds: gameState.maxRounds,
    guesses: gameState.guessHistory.map(result => result.word),
    guessResults: gameState.guessHistory.map(result => 
      result.evaluations.map(([letter, status]) => [letter, status])
    ),
    gameOver: gameState.gameOver,
    won: gameState.isWon,
    answer: gameState.gameOver ? gameState.targetWord : null,
    letterStatus: gameState.letterStatus,
    currentInput: gameState.currentInput,
    remainingRounds: Math.max(0, gameState.maxRounds - gameState.currentRound)
  };
}

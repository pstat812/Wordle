/**
 * Custom React Hook for Wordle Game State Management
 *
 * This hook encapsulates all game state logic and provides a clean API
 * for React components to interact with the game engine.
 */

import { useState, useCallback } from 'react';
import {
  createInitialGameState,
  makeGuess,
  addLetterToGuess,
  removeLetterFromGuess,
  startNewGame,
  updateGameConfig,
  getGameStateInfo,
  isValidGuess
} from './gameLogic';
import { DEFAULT_MAX_ROUNDS, WORD_LIST } from './gameSettings';

/**
 * Custom hook for managing Wordle game state
 * @param {number} initialMaxRounds - Initial maximum rounds
 * @param {string[]} initialWordList - Initial word list
 * @returns {object} Game state and control functions
 */
export function useWordleGame(initialMaxRounds = DEFAULT_MAX_ROUNDS, initialWordList = WORD_LIST) {
  const [gameState, setGameState] = useState(() => 
    createInitialGameState(initialMaxRounds, initialWordList)
  );

  // Add letter to current guess
  const addLetter = useCallback((letter) => {
    setGameState(currentState => addLetterToGuess(currentState, letter));
  }, []);

  // Remove letter from current guess
  const removeLetter = useCallback(() => {
    setGameState(currentState => removeLetterFromGuess(currentState));
  }, []);

  // Submit current guess
  const submitGuess = useCallback(() => {
    setGameState(currentState => {
      if (!currentState.currentInput) {
        throw new Error("No guess to submit");
      }

      if (currentState.currentInput.length !== 5) {
        throw new Error("Guess must be exactly 5 letters");
      }

      return makeGuess(currentState, currentState.currentInput);
    });
  }, []);

  // Start new game
  const newGame = useCallback(() => {
    setGameState(currentState => startNewGame(currentState));
  }, []);

  // Update game configuration
  const updateConfig = useCallback((config) => {
    setGameState(currentState => updateGameConfig(currentState, config));
  }, []);

  // Check if current input is valid for submission
  const canSubmitGuess = useCallback(() => {
    const gameInfo = getGameStateInfo(gameState);
    return gameInfo.currentInput.length === 5 && 
           isValidGuess(gameInfo.currentInput, gameState);
  }, [gameState]);

  // Get formatted game state for UI
  const gameInfo = getGameStateInfo(gameState);

  return {
    // Game state
    ...gameInfo,
    
    // Game actions
    addLetter,
    removeLetter,
    submitGuess,
    newGame,
    updateConfig,
    
    // Utility functions
    canSubmitGuess,
    isValidGuess: (guess) => isValidGuess(guess, gameState)
  };
}

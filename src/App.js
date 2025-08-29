/**
 * Wordle Game Application - Main Component
 *
 * This is the main React component that orchestrates the entire Wordle game.
 * It handles game state, user interactions, and UI updates following React best practices.
 */

import React, { useState, useEffect, useCallback } from 'react';
import GameBoard from './components/GameBoard';
import Keyboard from './components/Keyboard';
import SettingsModal from './components/SettingsModal';
import DropdownMenu from './components/DropdownMenu';
import { useWordleGame } from './useWordleGame';
import './App.css';

function App() {
  const game = useWordleGame();
  const [showGameOver, setShowGameOver] = useState(false);
  const [gameOverShown, setGameOverShown] = useState(false);
  const [isProcessingGuess, setIsProcessingGuess] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Submit guess handler
  const handleSubmitGuess = useCallback(() => {
    if (isProcessingGuess) return; // Prevent multiple submissions
    
    try {
      if (!game.canSubmitGuess()) {
        alert("Please enter a 5-letter word from the word list!");
        return;
      }
      
      setIsProcessingGuess(true);
      game.submitGuess();
      
      // Small delay to ensure state updates are processed
      setTimeout(() => {
        setIsProcessingGuess(false);
      }, 100);
    } catch (error) {
      setIsProcessingGuess(false);
      alert(error.message);
    }
  }, [game, isProcessingGuess]);

  // Unified input handlers for both physical and virtual keyboards
  const handleLetterInput = useCallback((letter) => {
    if (game.gameOver || isProcessingGuess) return;
    game.addLetter(letter);
  }, [game, isProcessingGuess]);

  const handleBackspaceInput = useCallback(() => {
    if (game.gameOver || isProcessingGuess) return;
    game.removeLetter();
  }, [game, isProcessingGuess]);

  const handleEnterInput = useCallback(() => {
    if (game.gameOver || isProcessingGuess) return;
    handleSubmitGuess();
  }, [game.gameOver, isProcessingGuess, handleSubmitGuess]);

  // Handle keyboard input
  const handleKeyPress = useCallback((event) => {
    if (game.gameOver || isProcessingGuess) return;

    const key = event.key.toUpperCase();

    if (/^[A-Z]$/.test(key)) {
      handleLetterInput(key);
    } else if (key === 'ENTER') {
      handleEnterInput();
    } else if (key === 'BACKSPACE') {
      handleBackspaceInput();
    }
  }, [game.gameOver, isProcessingGuess, handleLetterInput, handleEnterInput, handleBackspaceInput]);

  // Set up keyboard event listener
  useEffect(() => {
    document.addEventListener('keydown', handleKeyPress);
    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [handleKeyPress]);

  // Handle game over state
  useEffect(() => {
    if (game.gameOver && !showGameOver && !gameOverShown) {
      // Small delay to let the last guess animate
      setTimeout(() => {
        setShowGameOver(true);
        setGameOverShown(true);
      }, 600);
    }
  }, [game.gameOver, showGameOver, gameOverShown]);

  const handleNewGame = () => {
    game.newGame();
    setShowGameOver(false);
    setGameOverShown(false);
  };

  const handleGameOverResponse = (playAgain) => {
    setShowGameOver(false);
    if (playAgain) {
      handleNewGame();
    }
  };

  return (
    <div className={`app ${isDarkMode ? 'app--dark' : 'app--light'}`}>
      <div className="app__container">
        <header className="app__header">
          <div className="app__header-line"></div>
          <div className="app__controls">
            <DropdownMenu
              options={[
                {
                  id: 'new-game',
                  label: 'New Game',
                  icon: '🎮',
                  onClick: handleNewGame
                },
                {
                  id: 'settings',
                  label: 'Settings',
                  icon: '⚙️',
                  onClick: () => setShowSettings(true)
                }
              ]}
              disabled={isProcessingGuess}
            />
          </div>
        </header>

        <main className="app__main">
          <GameBoard
            guesses={game.guesses}
            guessResults={game.guessResults}
            currentInput={game.currentInput}
            maxRounds={game.maxRounds}
            gameOver={game.gameOver}
          />

          <Keyboard
            letterStatus={game.letterStatus}
            onLetterClick={handleLetterInput}
            onEnterClick={handleEnterInput}
            onBackspaceClick={handleBackspaceInput}
            gameOver={game.gameOver || isProcessingGuess}
          />
          
          <footer className="app__footer">
            <div className="app__footer-line"></div>
          </footer>
        </main>
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        isDarkMode={isDarkMode}
        onToggleDarkMode={setIsDarkMode}
      />

      {/* Game Over Modal */}
      {showGameOver && (
        <div className="game-over-modal__overlay">
          <div className="game-over-modal">
            <div className="game-over-modal__content">
              <h2 className="game-over-modal__title">
                {game.won ? "🎉 You Won!" : "😔 Game Over"}
              </h2>
              <div className="game-over-modal__message">
                {game.won ? (
                  <p>
                    Congratulations!<br />
                    You guessed <strong>'{game.answer}'</strong> in {game.currentRound} attempts!
                  </p>
                ) : (
                  <p>
                    The word was: <strong>{game.answer}</strong><br />
                    Better luck next time!
                  </p>
                )}
              </div>
                              <div className="game-over-modal__buttons">
                  <button 
                    className="game-over-modal__button game-over-modal__button--play-again"
                    onClick={() => handleGameOverResponse(true)}
                  >
                    Play Again
                  </button>
                  <button 
                    className="game-over-modal__button game-over-modal__button--close"
                    onClick={() => handleGameOverResponse(false)}
                  >
                    Close
                  </button>
                </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

# React Wordle

### Implemented Features
- A React implementation of the classic Wordle game, replicating the original NYTimes version
- Supports both keyboard input and on-screen virtual keyboard for letter entry
- Supports Dark Mode to enhance user experience 

- Next planned update: Client-server architecture
  - Server will manage game state and validate inputs
  - Client will not have access to answers until game completion
  - Maintains same core gameplay and scoring rules

### Development Notes
- The current word list contains a small set of test words. A comprehensive word list will be added in a future update.

### Game Rules

1. Guess the 5-letter word in the given number of attempts (default: 6)
2. Each guess must be a valid 5-letter word from the word list
3. After each guess, the color of the tiles will change:
   - Green: Letter is correct and in the right position
   - Yellow: Letter is in the word but in the wrong position
   - Gray: Letter is not in the word at all

### Project Structure

```
react-wordle/
├── public/
│   ├── index.html          # Main HTML template
│   └── manifest.json       # Web app manifest
├── src/
│   ├── components/         # React components
│   │   ├── GameBoard.js    # Game board with tiles
│   │   ├── GameTile.js     # Individual tile component
│   │   ├── Keyboard.js     # Virtual keyboard
│   │   ├── SettingsModal.js # Settings configuration
│   │   ├── DropdownMenu.js # Navigation dropdown
│   │   └── InteractiveHoverButton.js # Enhanced button component
│   ├── gameSettings.js     # Game configuration constants
│   ├── gameLogic.js        # Core game engine
│   ├── useWordleGame.js    # Custom React hook for game state
│   ├── App.js              # Main application component
│   └── index.js            # React entry point
├── package.json            # Dependencies and scripts
└── README.md              # This file
```

### Setup and Installation

#### Prerequisites

- Node.js 14.0 or higher
- npm or yarn package manager

#### Installation

1. Clone or download the project files

2. Install dependencies
   ```bash
   npm install
   ```

#### Running the Application

1. Start the development server
   ```bash
   npm start
   ```

2. Open your browser and navigate to `http://localhost:3000`


#### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

### Configuration

#### Modifying Game Settings

1. Word List: Edit `src/gameSettings.js` to add or modify words
   ```javascript
   export const WORD_LIST = [
     "ABOUT", "AFTER", "AGAIN", "BRAIN", "CHAIR",
     // Add your words here
   ];
   ```

2. Default Rounds: Change the default maximum attempts
   ```javascript
   export const DEFAULT_MAX_ROUNDS = 6; // Change this value
   ```


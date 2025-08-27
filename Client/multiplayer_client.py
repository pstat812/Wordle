"""
Multiplayer Wordle Client Module

This module handles the *Multiplayer Game* interface where two players
compete to guess their respective words first. This is used to handle the game logic and the UI.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import requests
import threading
import time
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
from popup_dialog import PopupDialog


class LetterStatus(Enum):
    """Letter evaluation status matching the server."""
    HIT = "HIT"
    PRESENT = "PRESENT"
    MISS = "MISS"
    UNUSED = "UNUSED"


class MultiplayerClient:
    """
    Multiplayer Wordle game client for competitive gameplay.
    """
    
    def __init__(self, root: tk.Tk, username: str, game_data: Dict[str, Any],
                 server_url: str = "http://127.0.0.1:5000",
                 on_game_end: Optional[Callable[[], None]] = None):
        """
        Initialize the multiplayer game client.
        
        Args:
            root: Main tkinter window
            username: Current player's username
            game_data: Game initialization data from server
            server_url: Server URL for API calls
            on_game_end: Callback when game ends
        """
        self.root = root
        self.username = username
        self.server_url = server_url
        self.on_game_end = on_game_end
        
        # Game state
        self.game_id = game_data.get("game_id")
        self.room_id = game_data.get("room_id")
        self.players = game_data.get("players", [])
        self.target_word = game_data.get("target_word")
        
        # Get opponent name
        self.opponent_name = None
        for player in self.players:
            if player != self.username:
                self.opponent_name = player
                break
        
        self.game_state = None
        self.current_input = ""
        self.game_started = True  # Game starts immediately
        self.game_end_handled = False  # Track if game end is being handled
        
        # Polling control
        self.polling_active = False
        self.polling_thread = None
        
        # Track scheduled callbacks for cleanup
        self.scheduled_callbacks = []
        
        # UI setup
        self.setup_window()
        self.setup_colors()
        self.setup_fonts()
        
        # Start game immediately (no word selection needed)
        self.create_game_ui()
        self.start_game_polling()
    

    
    def setup_window(self) -> None:
        """Configure the main window."""
        opponent_name = self.opponent_name or "Unknown"
        self.root.title(f"Wordle - Playing against {opponent_name}")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#ffffff")
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_colors(self) -> None:
        """Setup color scheme matching original Wordle."""
        self.colors = {
            "bg": "#ffffff",
            "tile_empty": "#ffffff",
            "tile_typing": "#f8f9fa",
            "tile_border": "#d3d6da",
            "tile_miss": "#787c7e",
            "tile_present": "#c9b458", 
            "tile_hit": "#6aaa64",
            "text_dark": "#212529",
            "text_light": "#ffffff",
            "key_bg": "#d3d6da",
            "key_miss": "#787c7e",
            "key_present": "#c9b458",
            "key_hit": "#6aaa64",
            "primary": "#6aaa64",
            "secondary": "#787c7e",
            "accent": "#c9b458"
        }
    
    def setup_fonts(self) -> None:
        """Setup custom fonts."""
        self.fonts = {
            "title": tkFont.Font(family="Arial", size=20, weight="bold"),
            "tile": tkFont.Font(family="Arial", size=18, weight="bold"),
            "key": tkFont.Font(family="Arial", size=11, weight="bold"),
            "button": tkFont.Font(family="Arial", size=11, weight="bold"),
            "status": tkFont.Font(family="Arial", size=12)
        }
    

    
    def create_game_ui(self) -> None:
        """Create the main game interface."""
        # Clear existing content
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_frame.pack(expand=True, fill="both")
        
        # Header
        self.create_game_header()
        
        # Game board
        self.create_game_board()
        
        # Virtual keyboard
        self.create_keyboard()
        
        # Bind keyboard events
        self.root.bind('<Key>', self.on_key_press)
        self.root.focus_set()
        
        # Initialize empty game state for display
        self.game_state = {
            "guesses": [],
            "guess_results": [],
            "letter_status": {letter: "UNUSED" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
            "game_over": False,
            "max_rounds": 6  # Default until server provides actual value
        }
        
        # Update display
        self.update_display()
    
    def create_game_header(self) -> None:
        """Create game header with player info."""
        header_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Player info
        player_label = tk.Label(
            header_frame,
            text=f"You: {self.username}",
            font=self.fonts["status"],
            fg=self.colors["primary"],
            bg=self.colors["bg"]
        )
        player_label.pack(side="left")
        
        # VS label
        vs_label = tk.Label(
            header_frame,
            text="VS",
            font=self.fonts["status"],
            fg=self.colors["secondary"],
            bg=self.colors["bg"]
        )
        vs_label.pack(side="left", padx=20)
        
        # Opponent info
        opponent_label = tk.Label(
            header_frame,
            text=f"{self.opponent_name}",
            font=self.fonts["status"],
            fg=self.colors["accent"],
            bg=self.colors["bg"]
        )
        opponent_label.pack(side="left")
        
        # Game status
        self.game_status_label = tk.Label(
            header_frame,
            text="Game in progress...",
            font=self.fonts["status"],
            fg=self.colors["secondary"],
            bg=self.colors["bg"]
        )
        self.game_status_label.pack(side="right")
    
    def create_game_board(self) -> None:
        """Create the game board."""
        self.board_frame = tk.Frame(self.main_frame, bg=self.colors["bg"], pady=20)
        self.board_frame.pack()
        
        # Use max_rounds from game state, fallback to 6 if not available yet
        max_rounds = 6  # Default fallback
        if self.game_state and "max_rounds" in self.game_state:
            max_rounds = self.game_state["max_rounds"]
        
        self.tiles = []
        
        for row in range(max_rounds):
            tile_row = []
            row_frame = tk.Frame(self.board_frame, bg=self.colors["bg"])
            row_frame.pack(pady=2)
            
            for col in range(5):
                tile = tk.Label(
                    row_frame,
                    text="",
                    font=self.fonts["tile"],
                    width=3,
                    height=1,
                    bg=self.colors["tile_empty"],
                    fg=self.colors["text_dark"],
                    relief="solid",
                    borderwidth=2
                )
                tile.configure(highlightcolor=self.colors["tile_border"])
                tile.pack(side="left", padx=2)
                tile_row.append(tile)
            
            self.tiles.append(tile_row)
    
    def recreate_game_board(self) -> None:
        """Recreate the game board with correct number of rows."""
        if hasattr(self, 'board_frame'):
            self.board_frame.destroy()
        self.create_game_board()
    
    def create_keyboard(self) -> None:
        """Create virtual keyboard."""
        self.keyboard_frame = tk.Frame(self.main_frame, bg=self.colors["bg"], pady=20)
        self.keyboard_frame.pack(side="bottom")
        
        # Keyboard layout
        keyboard_rows = [
            "QWERTYUIOP",
            "ASDFGHJKL",
            "ZXCVBNM"
        ]
        
        self.key_buttons = {}
        
        for i, row in enumerate(keyboard_rows):
            row_frame = tk.Frame(self.keyboard_frame, bg=self.colors["bg"])
            row_frame.pack(pady=2)
            
            # Add ENTER button to third row (start)
            if i == 2:
                enter_btn = tk.Button(
                    row_frame,
                    text="ENTER",
                    font=self.fonts["key"],
                    bg=self.colors["key_bg"],
                    fg=self.colors["text_dark"],
                    width=6,
                    height=2,
                    relief="raised",
                    command=self.submit_guess
                )
                enter_btn.pack(side="left", padx=2)
            
            # Letter keys
            for letter in row:
                key_btn = tk.Button(
                    row_frame,
                    text=letter,
                    font=self.fonts["key"],
                    bg=self.colors["key_bg"],
                    fg=self.colors["text_dark"],
                    width=3,
                    height=2,
                    relief="raised",
                    command=lambda l=letter: self.add_letter(l)
                )
                key_btn.pack(side="left", padx=2)
                self.key_buttons[letter] = key_btn
            
            # Add BACKSPACE button to third row (end)
            if i == 2:
                backspace_btn = tk.Button(
                    row_frame,
                    text="DEL",
                    font=self.fonts["key"],
                    bg=self.colors["key_bg"],
                    fg=self.colors["text_dark"],
                    width=6,
                    height=2,
                    relief="raised",
                    command=self.remove_letter
                )
                backspace_btn.pack(side="left", padx=2)
    
    def add_letter(self, letter: str) -> None:
        """Add letter to current guess."""
        if not self.game_started or not self.game_state:
            return
        
        # Check if this player specifically has finished
        if self.game_state.get('game_over'):
            return
        
        # Check if this player has exhausted attempts
        current_round = self.game_state.get('current_round', 0)
        max_rounds = self.game_state.get('max_rounds', 6)
        if current_round >= max_rounds:
            return
        
        if len(self.current_input) < 5 and letter.isalpha():
            self.current_input += letter.upper()
            self.update_display()
    
    def remove_letter(self) -> None:
        """Remove last letter from current guess."""
        if not self.game_started or not self.game_state:
            return
        
        # Check if this player specifically has finished
        if self.game_state.get('game_over'):
            return
        
        # Check if this player has exhausted attempts
        current_round = self.game_state.get('current_round', 0)
        max_rounds = self.game_state.get('max_rounds', 6)
        if current_round >= max_rounds:
            return
        
        if self.current_input:
            self.current_input = self.current_input[:-1]
            self.update_display()
    
    def submit_guess(self) -> None:
        """Submit current guess to server."""
        if not self.game_started or not self.game_state:
            return
        
        # Check if this player specifically has finished
        if self.game_state.get('game_over'):
            return
        
        # Check if this player has exhausted attempts
        current_round = self.game_state.get('current_round', 0)
        max_rounds = self.game_state.get('max_rounds', 6)
        if current_round >= max_rounds:
            return
        
        if len(self.current_input) != 5:
            PopupDialog.show_invalid_word()
            return
        
        # Submit to server
        guess_to_submit = self.current_input
        self.current_input = ""  # Clear input before submission to prevent display flicker
        
        if not self.submit_guess_to_server(guess_to_submit):
            # If submission failed, restore the input
            self.current_input = guess_to_submit
    
    def submit_guess_to_server(self, guess: str) -> bool:
        """Submit a guess to the server."""
        try:
            response = requests.post(
                f"{self.server_url}/api/game/{self.game_id}/guess",
                json={"username": self.username, "guess": guess},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    # Check if max_rounds changed and recreate board if needed
                    old_max_rounds = self.game_state.get("max_rounds", 6) if self.game_state else 6
                    self.game_state = data["state"]
                    new_max_rounds = self.game_state.get("max_rounds", 6)
                    
                    if old_max_rounds != new_max_rounds:
                        self.recreate_game_board()
                    
                    # Update display immediately to show the latest guess result
                    self.update_display()
                    
                    # Check for game end after display update (only when entire game is over)
                    if self.game_state.get("entire_game_over") and not self.game_end_handled:
                        self.game_end_handled = True
                        # Add a small delay to let users see the final result before showing game end message
                        callback_id = self.root.after(1000, self.handle_game_end)  # 1 second delay
                        if hasattr(self, 'scheduled_callbacks'):
                            self.scheduled_callbacks.append(callback_id)
                    
                    return True
                else:
                    error = data.get("error", "Unknown error")
                    if "not in word list" in error.lower():
                        PopupDialog.show_word_not_in_list()
                    else:
                        PopupDialog.show_error("Invalid Guess", error)
            else:
                PopupDialog.show_error("Server Error", "Failed to submit guess")
        
        except requests.RequestException:
            PopupDialog.show_error("Connection Error", "Failed to submit guess")
        
        return False
    
    def update_display(self) -> None:
        """Update the game display based on current state."""
        if not self.game_state or not hasattr(self, 'tiles'):
            return
        
        # Clear all tiles
        for row in self.tiles:
            for tile in row:
                tile.configure(
                    text="",
                    bg=self.colors["tile_empty"],
                    fg=self.colors["text_dark"],
                    relief="solid",
                    borderwidth=2
                )
        
        # Update completed guesses
        guesses = self.game_state.get("guesses", [])
        guess_results = self.game_state.get("guess_results", [])
        
        for row_idx, guess in enumerate(guesses):
            if row_idx < len(guess_results):
                for col_idx, (letter, status_str) in enumerate(guess_results[row_idx]):
                    if row_idx < len(self.tiles) and col_idx < len(self.tiles[row_idx]):
                        tile = self.tiles[row_idx][col_idx]
                        status = LetterStatus(status_str)
                        
                        tile.configure(text=letter)
                        
                        if status == LetterStatus.HIT:
                            tile.configure(bg=self.colors["tile_hit"], fg=self.colors["text_light"])
                        elif status == LetterStatus.PRESENT:
                            tile.configure(bg=self.colors["tile_present"], fg=self.colors["text_light"])
                        else:  # MISS
                            tile.configure(bg=self.colors["tile_miss"], fg=self.colors["text_light"])
        
        # Update current guess being typed
        if not self.game_state.get('game_over'):
            current_row = len(guesses)
            
            for i, letter in enumerate(self.current_input):
                if i < 5 and current_row < len(self.tiles):
                    self.tiles[current_row][i].configure(
                        text=letter,
                        bg=self.colors["tile_typing"],
                        fg=self.colors["text_dark"],
                        relief="solid",
                        borderwidth=2
                    )
        
        # Update keyboard colors
        self.update_keyboard()
        
        # Update game status display
        self.update_game_status()
    
    def update_keyboard(self) -> None:
        """Update keyboard key colors based on letter status."""
        if not self.game_state or not hasattr(self, 'key_buttons'):
            return
        
        letter_status = self.game_state.get("letter_status", {})
        
        for letter, button in self.key_buttons.items():
            status_str = letter_status.get(letter, "UNUSED")
            status = LetterStatus(status_str)
            
            if status == LetterStatus.HIT:
                button.configure(bg=self.colors["key_hit"], fg=self.colors["text_light"])
            elif status == LetterStatus.PRESENT:
                button.configure(bg=self.colors["key_present"], fg=self.colors["text_light"])
            elif status == LetterStatus.MISS:
                button.configure(bg=self.colors["key_miss"], fg=self.colors["text_light"])
            else:  # UNUSED
                button.configure(bg=self.colors["key_bg"], fg=self.colors["text_dark"])
    
    def update_game_status(self) -> None:
        """Update game status display."""
        if not self.game_state or not hasattr(self, 'game_status_label'):
            return
        
        current_round = self.game_state.get('current_round', 0)
        max_rounds = self.game_state.get('max_rounds', 6)
        game_over = self.game_state.get('game_over', False)
        
        # Check if entire game is over
        entire_game_over = self.game_state.get('entire_game_over', False)
        
        if entire_game_over:
            if self.game_state.get('won', False):
                self.game_status_label.configure(text="You won!", fg=self.colors["accent"])
            else:
                self.game_status_label.configure(text="Game over", fg=self.colors["secondary"])
        elif game_over or current_round >= max_rounds:
            self.game_status_label.configure(
                text="All attempts used - Waiting for opponent...", 
                fg=self.colors["secondary"]
            )
        else:
            attempts_left = max_rounds - current_round
            self.game_status_label.configure(
                text=f"Attempts left: {attempts_left}", 
                fg=self.colors["primary"]
            )
    
    def handle_game_end(self) -> None:
        """Handle game end event."""
        self.stop_game_polling()
        
        if not self.game_state:
            return
        
        won = self.game_state.get("won", False)
        answer = self.game_state.get("answer", "UNKNOWN")
        attempts = self.game_state.get("current_round", 0)
        
        # Check for draw scenario
        # Get opponent data to determine if it was a draw
        try:
            response = requests.get(
                f"{self.server_url}/api/game/{self.game_id}/opponent",
                params={"username": self.username},
                timeout=10
            )
            
            if response.status_code == 200:
                opponent_data = response.json()
                if opponent_data.get("winner") == "DRAW":
                    # Draw scenario
                    PopupDialog.show_info(
                        "Game Draw",
                        f"It's a draw!\n\nBoth players had the same number of correct letters.\nThe word was: {answer}\n\nReturning to lobby..."
                    )
                else:
                    # Normal win/loss scenario
                    PopupDialog.show_game_result(won, self.opponent_name, answer, attempts)
            else:
                # Fallback to normal result display
                PopupDialog.show_game_result(won, self.opponent_name, answer, attempts)
        except:
            # Error getting opponent data, fallback to normal result display
            PopupDialog.show_game_result(won, self.opponent_name, answer, attempts)
        
        # Always return to lobby
        self.end_game()
    
    def start_game_polling(self) -> None:
        """Start polling for game updates."""
        self.polling_active = True
        self.polling_thread = threading.Thread(target=self._poll_game, daemon=True)
        self.polling_thread.start()
    
    def stop_game_polling(self) -> None:
        """Stop polling for game updates."""
        self.polling_active = False
        if self.polling_thread:
            self.polling_thread.join(timeout=1.0)
    
    def _poll_game(self) -> None:
        """Background thread function to poll game status."""
        while self.polling_active:
            try:
                response = requests.get(
                    f"{self.server_url}/api/game/{self.game_id}/state",
                    params={"username": self.username},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data["success"]:
                        state = data["state"]
                        
                        # Check if max_rounds changed and recreate board if needed
                        old_max_rounds = self.game_state.get("max_rounds", 6) if self.game_state else 6
                        self.game_state = state
                        new_max_rounds = self.game_state.get("max_rounds", 6)
                        
                        if old_max_rounds != new_max_rounds:
                            callback_id = self.root.after(0, self.recreate_game_board)
                            if hasattr(self, 'scheduled_callbacks'):
                                self.scheduled_callbacks.append(callback_id)
                        
                        callback_id = self.root.after(0, self.update_display)
                        if hasattr(self, 'scheduled_callbacks'):
                            self.scheduled_callbacks.append(callback_id)
                        
                        # Check for game end (only if not already handled and entire game is over)
                        if state.get("entire_game_over") and not self.game_end_handled:
                            self.game_end_handled = True
                            callback_id = self.root.after(0, self.handle_game_end)
                            if hasattr(self, 'scheduled_callbacks'):
                                self.scheduled_callbacks.append(callback_id)
                            break
                        
            except requests.RequestException:
                pass  # Continue polling on network errors
            except Exception:
                pass  # Continue polling on other errors
            
            time.sleep(1)  # Poll every second during game
    
    def on_key_press(self, event) -> None:
        """Handle keyboard input."""
        if not self.game_started or not self.game_state:
            return
        
        # Check if this player specifically has finished
        if self.game_state.get('game_over'):
            return
        
        # Check if this player has exhausted attempts
        current_round = self.game_state.get('current_round', 0)
        max_rounds = self.game_state.get('max_rounds', 6)
        if current_round >= max_rounds:
            return
        
        key = event.keysym.upper()
        
        if key in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.add_letter(key)
        elif key in ["RETURN", "ENTER"]:
            self.submit_guess()
        elif key in ["BACKSPACE", "DELETE"]:
            self.remove_letter()
    
    def end_game(self) -> None:
        """End the game and return to lobby."""
        self.stop_game_polling()
        
        # Remove player from room when ending game
        if self.room_id:
            self.leave_room_on_game_end()
        
        if self.on_game_end:
            self.on_game_end()
    
    def leave_room_on_game_end(self) -> None:
        """Leave the room when game ends."""
        try:
            response = requests.post(
                f"{self.server_url}/api/rooms/{self.room_id}/leave",
                json={"username": self.username},
                timeout=5
            )
            # Don't show errors since this is cleanup during game end
        except:
            pass  # Silent failure - player will be removed when they join another room anyway
    
    def destroy(self) -> None:
        """Clean up the multiplayer client."""
        self.stop_game_polling()
        
        # Cancel any scheduled callbacks
        if hasattr(self, 'scheduled_callbacks'):
            for callback_id in self.scheduled_callbacks:
                try:
                    self.root.after_cancel(callback_id)
                except (tk.TclError, AttributeError):
                    pass
            self.scheduled_callbacks.clear()
        
        if hasattr(self, 'main_frame'):
            try:
                self.main_frame.destroy()
            except tk.TclError:
                pass

"""
Wordle Game Client - Client-side GUI and Server Communication

This module implements the client-side interface for the *SINGLE PLAYER* server-client Wordle architecture.
The client handles UI interactions and communicates with the server for game logic,
without having access to the answer until game completion.

"""

import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkFont
import requests
from typing import Dict, List, Optional
from enum import Enum


class LetterStatus(Enum):
    """Letter evaluation status matching the server."""
    HIT = "HIT"
    PRESENT = "PRESENT"
    MISS = "MISS"
    UNUSED = "UNUSED"


class WordleClient:
    """
    Client-side GUI controller that communicates with the Wordle server.
    
    This class manages the user interface and handles all server communication
    for game state, validation, and guess submission without accessing game secrets.
    """
    
    def __init__(self, root, server_url="http://127.0.0.1:5000", on_exit=None):
        self.root = root
        self.server_url = server_url
        self.on_exit = on_exit
        self.game_id = None
        self.current_input = ""
        self.game_state = None
        
        # Initialize UI
        self.setup_window()
        self.setup_colors()
        self.setup_fonts()
        self.create_widgets()
        
        # Check server connection and start new game
        if self.check_server_connection():
            self.start_new_game()
        else:
            self.show_connection_error()
        
        # Bind keyboard events
        self.root.bind('<Key>', self.on_key_press)
        self.root.focus_set()
    
    def setup_window(self):
        """Configure the main window."""
        self.root.title("Wordle Game - Client")
        self.root.resizable(False, False)
        self.root.configure(bg="#ffffff")
    
    def setup_colors(self):
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
            "key_hit": "#6aaa64"
        }
    
    def setup_fonts(self):
        """Setup custom fonts."""
        self.fonts = {
            "title": tkFont.Font(family="Arial", size=24, weight="bold"),
            "tile": tkFont.Font(family="Arial", size=20, weight="bold"),
            "key": tkFont.Font(family="Arial", size=12, weight="bold"),
            "button": tkFont.Font(family="Arial", size=11),
            "status": tkFont.Font(family="Arial", size=14)
        }
    
    def check_server_connection(self) -> bool:
        """Check if server is available."""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def show_connection_error(self):
        """Show error when server is not available."""
        messagebox.showerror(
            "Connection Error",
            f"Cannot connect to Wordle server at {self.server_url}\n\n"
            "Please ensure the server is running and try again."
        )
        self.root.quit()
    
    def start_new_game(self, max_rounds=None):
        """Start a new game session with the server."""
        try:
            payload = {}
            if max_rounds:
                payload['max_rounds'] = max_rounds
            
            response = requests.post(
                f"{self.server_url}/api/new_game",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.game_id = data['game_id']
                    self.game_state = data['state']
                    self.current_input = ""
                    
                    # Recreate UI if max_rounds changed
                    if hasattr(self, 'board_frame'):
                        self.recreate_game_board()
                    else:
                        self.create_widgets()
                    
                    self.update_display()
                    return True
                else:
                    messagebox.showerror("Game Error", data.get('error', 'Unknown error'))
            else:
                messagebox.showerror("Server Error", f"Server returned status {response.status_code}")
        
        except requests.RequestException as e:
            messagebox.showerror("Connection Error", f"Failed to start new game: {str(e)}")
        
        return False
    
    def get_game_state(self):
        """Fetch current game state from server."""
        if not self.game_id:
            return False
        
        try:
            response = requests.get(
                f"{self.server_url}/api/game/{self.game_id}/state",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.game_state = data['state']
                    return True
                else:
                    messagebox.showerror("Game Error", data.get('error', 'Unknown error'))
            else:
                messagebox.showerror("Server Error", f"Server returned status {response.status_code}")
        
        except requests.RequestException as e:
            messagebox.showerror("Connection Error", f"Failed to get game state: {str(e)}")
        
        return False
    
    def submit_guess_to_server(self, guess: str) -> bool:
        """Submit a guess to the server for validation and evaluation."""
        if not self.game_id:
            return False
        
        try:
            response = requests.post(
                f"{self.server_url}/api/game/{self.game_id}/guess",
                json={'guess': guess},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.game_state = data['state']
                    return True
                else:
                    messagebox.showerror("Invalid Guess", data.get('error', 'Unknown error'))
            else:
                data = response.json()
                messagebox.showerror("Invalid Guess", data.get('error', 'Server error'))
        
        except requests.RequestException as e:
            messagebox.showerror("Connection Error", f"Failed to submit guess: {str(e)}")
        
        return False
    
    def create_widgets(self):
        """Create all UI widgets."""
        # Create main container frame
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_frame.pack(expand=True, fill="both")
        
        # Game board at the top
        self.create_game_board()
        
        # Virtual keyboard at the bottom
        self.create_keyboard()
        
        # Update window size
        self.update_window_size()
    
    def create_game_board(self):
        """Create the dynamic game board based on server settings."""
        self.board_frame = tk.Frame(self.main_frame, bg=self.colors["bg"], pady=20)
        self.board_frame.pack()
        
        if not self.game_state:
            max_rounds = 6  # Default
        else:
            max_rounds = self.game_state['max_rounds']
        
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
    
    def create_keyboard(self):
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
    
    def update_window_size(self):
        """Update window size based on game board."""
        if not self.game_state:
            max_rounds = 6
        else:
            max_rounds = self.game_state['max_rounds']
        
        # Base height for keyboard only + dynamic height for game board
        base_height = 220  # Just keyboard and padding
        tile_height = 60   # Height per row of tiles
        dynamic_height = base_height + (max_rounds * tile_height)
        
        # Set reasonable bounds
        min_height = 350
        max_height = 800
        final_height = max(min_height, min(dynamic_height, max_height))
        
        self.root.geometry(f"500x{final_height}")
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def add_letter(self, letter):
        """Add letter to current guess."""
        if not self.game_state or self.game_state['game_over']:
            return
        
        if len(self.current_input) < 5 and letter.isalpha():
            self.current_input += letter.upper()
            self.update_display()
    
    def remove_letter(self):
        """Remove last letter from current guess."""
        if not self.game_state or self.game_state['game_over']:
            return
        
        if self.current_input:
            self.current_input = self.current_input[:-1]
            self.update_display()
    
    def submit_guess(self):
        """Submit current guess to server."""
        if not self.game_state or self.game_state['game_over']:
            return
        
        if len(self.current_input) != 5:
            messagebox.showwarning("Invalid Guess", "Please enter a 5-letter word!")
            return
        
        # Submit to server
        if self.submit_guess_to_server(self.current_input):
            self.current_input = ""  # Clear input on successful submission
            self.update_display()
            
            # Check game over conditions
            if self.game_state and self.game_state['game_over']:
                self.show_game_over()
    
    def update_display(self):
        """Update the game display based on current state."""
        if not self.game_state:
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
        for row_idx, guess in enumerate(self.game_state["guesses"]):
            for col_idx, (letter, status_str) in enumerate(self.game_state["guess_results"][row_idx]):
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
        if not self.game_state['game_over']:
            current_row = len(self.game_state["guesses"])
            max_rounds = self.game_state["max_rounds"]
            
            for i, letter in enumerate(self.current_input):
                if i < 5 and current_row < max_rounds:
                    self.tiles[current_row][i].configure(
                        text=letter,
                        bg=self.colors["tile_typing"],
                        fg=self.colors["text_dark"],
                        relief="solid",
                        borderwidth=2
                    )
        
        # Update keyboard colors
        self.update_keyboard()
    
    def update_keyboard(self):
        """Update keyboard key colors based on letter status."""
        if not self.game_state:
            return
        
        for letter, button in self.key_buttons.items():
            status_str = self.game_state["letter_status"].get(letter, "UNUSED")
            status = LetterStatus(status_str)
            
            if status == LetterStatus.HIT:
                button.configure(bg=self.colors["key_hit"], fg=self.colors["text_light"])
            elif status == LetterStatus.PRESENT:
                button.configure(bg=self.colors["key_present"], fg=self.colors["text_light"])
            elif status == LetterStatus.MISS:
                button.configure(bg=self.colors["key_miss"], fg=self.colors["text_light"])
            else:  # UNUSED
                button.configure(bg=self.colors["key_bg"], fg=self.colors["text_dark"])
    
    def show_game_over(self):
        """Show game over dialog."""
        if not self.game_state:
            return
        
        if self.game_state['won']:
            message = f"Congratulations!\n\nYou guessed '{self.game_state['answer']}' in {self.game_state['current_round']} attempts!"
            title = "You Won!"
        else:
            message = f"Game Over!\n\nThe word was: {self.game_state['answer']}\n\nBetter luck next time!"
            title = "Game Over"
        
        # Create a custom dialog with multiple options
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.configure(bg="#ffffff")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (125)
        dialog.geometry(f"+{x}+{y}")
        
        # Message frame
        msg_frame = tk.Frame(dialog, bg="#ffffff")
        msg_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Title label
        title_label = tk.Label(
            msg_frame,
            text=title,
            font=("Arial", 16, "bold"),
            fg="#333333",
            bg="#ffffff"
        )
        title_label.pack(pady=(0, 10))
        
        # Message label
        msg_label = tk.Label(
            msg_frame,
            text=message,
            font=("Arial", 12),
            fg="#666666",
            bg="#ffffff",
            justify="center"
        )
        msg_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = tk.Frame(msg_frame, bg="#ffffff")
        button_frame.pack(fill="x")
        
        def play_again():
            dialog.destroy()
            max_rounds = self.game_state['max_rounds'] if self.game_state else None
            self.start_new_game(max_rounds)
        
        def return_to_menu():
            dialog.destroy()
            if self.on_exit:
                self.on_exit()
        
        def quit_game():
            dialog.destroy()
            self.root.quit()
        
        # Play Again button
        tk.Button(
            button_frame,
            text="Play Again",
            font=("Arial", 11, "bold"),
            bg="#6aaa64",
            fg="white",
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=10,
            command=play_again,
            cursor="hand2"
        ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        # Main Menu button (only if callback available)
        if self.on_exit:
            tk.Button(
                button_frame,
                text="Main Menu",
                font=("Arial", 11, "bold"),
                bg="#787c7e",
                fg="white",
                relief="flat",
                borderwidth=0,
                padx=20,
                pady=10,
                command=return_to_menu,
                cursor="hand2"
            ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        # Quit button
        tk.Button(
            button_frame,
            text="Quit",
            font=("Arial", 11, "bold"),
            bg="#d32f2f",
            fg="white",
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=10,
            command=quit_game,
            cursor="hand2"
        ).pack(side="left", fill="x", expand=True)
    
    def recreate_game_board(self):
        """Recreate the game board when settings change."""
        # Destroy existing board
        if hasattr(self, 'board_frame'):
            self.board_frame.destroy()
        
        # Create new board with current settings
        self.create_game_board()
        
        # Update window size
        self.update_window_size()
    
    def destroy(self):
        """Clean up the single player client."""
        if hasattr(self, 'root'):
            for widget in self.root.winfo_children():
                widget.destroy()
    
    def on_key_press(self, event):
        """Handle keyboard input."""
        if not self.game_state or self.game_state['game_over']:
            return
        
        key = event.keysym.upper()
        
        if key in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.add_letter(key)
        elif key in ["RETURN", "ENTER"]:
            self.submit_guess()
        elif key in ["BACKSPACE", "DELETE"]:
            self.remove_letter()


def main():
    """Main function to run the Wordle Client GUI"""
    root = tk.Tk()
    app = WordleClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()

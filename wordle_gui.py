"""
Wordle Game - Graphical User Interface Module

This module implements a professional-grade GUI for the Wordle game using
tkinter. The implementation follows MVC architectural principles, separating
presentation logic from business logic for maintainability and testability.

"""

import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkFont
from typing import Dict, List, Optional, Callable
from wordle_game import WordleGame, LetterStatus


class WordleGUI:
    """
    Main GUI controller implementing the presentation layer for Wordle.
    
    This class manages all user interface components and coordinates between
    user input and the game engine. It implements the View and Controller
    aspects of the MVC pattern.
    
    """
    
    
    def __init__(self, root):
        self.root = root
        self.root.title("Wordle Game")
        # Dynamic height will be calculated after config is loaded
        self.root.resizable(False, False)
        self.root.configure(bg="#ffffff")
        
        # Color scheme matching original Wordle
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
        
        # Initialize game
        self.game = WordleGame()
        
        # UI Components
        self.setup_fonts()
        self.create_widgets()
        self.update_display()
        
        # Set dynamic window size based on number of rows
        self.update_window_size()
        
        # Bind keyboard events
        self.root.bind('<Key>', self.on_key_press)
        self.root.focus_set()
    
    def setup_fonts(self):
        """Setup custom fonts"""
        self.fonts = {
            "title": tkFont.Font(family="Arial", size=24, weight="bold"),
            "tile": tkFont.Font(family="Arial", size=20, weight="bold"),
            "key": tkFont.Font(family="Arial", size=12, weight="bold"),
            "button": tkFont.Font(family="Arial", size=11),
            "status": tkFont.Font(family="Arial", size=14)
        }
    
    def update_window_size(self):
        """Update window size based on number of rows"""
        max_rounds = self.game.get_max_rounds()
        # Base height for UI elements + dynamic height for game board
        base_height = 300  # Keyboard only
        tile_height = 60   # Height per row of tiles
        dynamic_height = base_height + (max_rounds * tile_height)
        
        # Set reasonable bounds
        min_height = 400
        max_height = 1000
        final_height = max(min_height, min(dynamic_height, max_height))
        
        self.root.geometry(f"600x{final_height}")
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Create main container frame for centering
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_frame.pack(expand=True, fill="both")
        
        # Center the main content
        self.content_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        self.content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Game board
        self.create_game_board()
        
        # Virtual keyboard
        self.create_keyboard()
    
    def create_game_board(self):
        """Create the dynamic NxM game board with tiles based on max_rounds"""
        self.board_frame = tk.Frame(self.content_frame, bg=self.colors["bg"], pady=20)
        self.board_frame.pack()
        
        max_rounds = self.game.get_max_rounds()
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
        """Create virtual keyboard"""
        self.keyboard_frame = tk.Frame(self.content_frame, bg=self.colors["bg"], pady=20)
        self.keyboard_frame.pack()
        
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
    
    def create_controls(self):
        """Create control buttons"""
        self.control_frame = tk.Frame(self.root, bg=self.colors["bg"], pady=20)
        self.control_frame.pack()
        
        # New Game button
        new_game_btn = tk.Button(
            self.control_frame,
            text="New Game",
            font=self.fonts["button"],
            bg="#4CAF50",
            fg="white",
            width=12,
            height=2,
            relief="raised",
            command=self.new_game
        )
        new_game_btn.pack(side="left", padx=10)
        
        # Settings button
        settings_btn = tk.Button(
            self.control_frame,
            text="Settings",
            font=self.fonts["button"],
            bg="#2196F3",
            fg="white",
            width=12,
            height=2,
            relief="raised",
            command=self.show_settings
        )
        settings_btn.pack(side="left", padx=10)
        
        # Quit button
        quit_btn = tk.Button(
            self.control_frame,
            text="Quit",
            font=self.fonts["button"],
            bg="#f44336",
            fg="white",
            width=12,
            height=2,
            relief="raised",
            command=self.root.quit
        )
        quit_btn.pack(side="left", padx=10)
    
    def add_letter(self, letter):
        """Add letter to current guess"""
        if not self.game.is_game_over():
            self.game.add_letter_to_guess(letter)
            self.update_display()
    
    def remove_letter(self):
        """Remove last letter from current guess"""
        if not self.game.is_game_over():
            self.game.remove_letter_from_guess()
            self.update_display()
    
    def submit_guess(self):
        """Submit current guess"""
        if self.game.is_game_over():
            return
        
        try:
            current_guess = self.game.get_current_guess()
            if len(current_guess) != 5:
                messagebox.showwarning("Invalid Guess", "Please enter a 5-letter word from the word list!")
                return
            
            result = self.game.submit_current_guess()
            self.update_display()
            
            # Check game over conditions
            if self.game.is_game_over():
                self.show_game_over()
            
        except ValueError as e:
            messagebox.showerror("Invalid Guess", str(e))
    
    def update_display(self):
        """Update the game display"""
        state = self.game.get_game_state()
        
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
        for row_idx, guess in enumerate(state["guesses"]):
            for col_idx, (letter, status_str) in enumerate(state["guess_results"][row_idx]):
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
        if not self.game.is_game_over():
            current_guess = self.game.get_current_guess()
            current_row = len(state["guesses"])
            max_rounds = state["max_rounds"]
            
            for i, letter in enumerate(current_guess):
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
        """Update keyboard key colors based on letter status"""
        for letter, button in self.key_buttons.items():
            status = self.game.get_letter_status(letter)
            
            if status == LetterStatus.HIT:
                button.configure(bg=self.colors["key_hit"], fg=self.colors["text_light"])
            elif status == LetterStatus.PRESENT:
                button.configure(bg=self.colors["key_present"], fg=self.colors["text_light"])
            elif status == LetterStatus.MISS:
                button.configure(bg=self.colors["key_miss"], fg=self.colors["text_light"])
            else:  # UNUSED
                button.configure(bg=self.colors["key_bg"], fg=self.colors["text_dark"])
    
    def show_game_over(self):
        """Show game over dialog"""
        if self.game.has_won():
            message = f"Congratulations!\n\nYou guessed '{self.game.get_answer()}' in {self.game.current_round} attempts!"
            title = "You Won!"
        else:
            message = f"Game Over!\n\nThe word was: {self.game.get_answer()}\n\nBetter luck next time!"
            title = "Game Over"
        
        result = messagebox.askquestion(
            title,
            message + "\n\nWould you like to play again?",
            icon="question"
        )
        
        if result == "yes":
            self.new_game()
    
    def recreate_game_board(self):
        """Recreate the game board when settings change"""
        # Destroy existing board
        if hasattr(self, 'board_frame'):
            self.board_frame.destroy()
        
        # Create new board with current settings - insert before keyboard
        self.create_game_board_with_position()
        
        # Update window size
        self.update_window_size()
    
    def create_game_board_with_position(self):
        """Create the dynamic game board in the correct position"""
        self.board_frame = tk.Frame(self.root, bg=self.colors["bg"], pady=20)
        # Pack before the keyboard frame to maintain proper order
        self.board_frame.pack(before=self.keyboard_frame)
        
        max_rounds = self.game.get_max_rounds()
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
    
    def new_game(self):
        """Start a new game"""
        self.game.start_new_game()
        self.update_display()
    
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Game Settings")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        settings_window.configure(bg=self.colors["bg"])
        
        # Max rounds setting
        tk.Label(
            settings_window,
            text="Maximum Rounds:",
            font=self.fonts["button"],
            bg=self.colors["bg"]
        ).pack(pady=10)
        
        rounds_var = tk.StringVar(value=str(self.game.get_max_rounds()))
        rounds_entry = tk.Entry(
            settings_window,
            textvariable=rounds_var,
            font=self.fonts["button"],
            width=10,
            justify="center"
        )
        rounds_entry.pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(settings_window, bg=self.colors["bg"])
        button_frame.pack(pady=20)
        
        def apply_settings():
            try:
                new_rounds = int(rounds_var.get())
                if new_rounds <= 0:
                    raise ValueError("Rounds must be positive")
                if new_rounds > 20:
                    raise ValueError("Maximum 20 rounds allowed for UI practicality")
                
                self.game.set_max_rounds(new_rounds)
                
                # Recreate the game board with new dimensions
                self.recreate_game_board()
                
                # Start new game with new settings
                self.new_game()
                
                settings_window.destroy()
                messagebox.showinfo("Settings Applied", f"New settings applied! Game board now has {new_rounds} rows.\nA new game has started.")
                
            except ValueError as e:
                messagebox.showerror("Invalid Input", f"Please enter a valid positive number for rounds (1-20).\n\nError: {e}")
        
        tk.Button(
            button_frame,
            text="Apply",
            font=self.fonts["button"],
            bg="#4CAF50",
            fg="white",
            width=10,
            command=apply_settings
        ).pack(side="left", padx=10)
        
        tk.Button(
            button_frame,
            text="Cancel",
            font=self.fonts["button"],
            bg="#f44336",
            fg="white",
            width=10,
            command=settings_window.destroy
        ).pack(side="left", padx=10)
    
    def on_key_press(self, event):
        """Handle keyboard input"""
        if self.game.is_game_over():
            return
        
        key = event.keysym.upper()
        
        if key in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.add_letter(key)
        elif key in ["RETURN", "ENTER"]:
            self.submit_guess()
        elif key in ["BACKSPACE", "DELETE"]:
            self.remove_letter()


def main():
    """Main function to run the Wordle GUI"""
    root = tk.Tk()
    app = WordleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

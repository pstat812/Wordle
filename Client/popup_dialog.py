"""
Reusable Popup Dialog Module

This module provides a centralized way to display various types of popup messages
including error messages, warnings, confirmations, and information dialogs.
This replaces scattered messagebox calls throughout the application.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable


class PopupDialog:
    """
    Centralized popup dialog manager for consistent user messaging.
    """
    
    @staticmethod
    def show_error(title: str, message: str, parent: Optional[tk.Widget] = None) -> None:
        """
        Display an error popup dialog.
        
        Args:
            title: Dialog window title
            message: Error message to display
            parent: Parent widget (optional)
        """
        messagebox.showerror(title, message, parent=parent)
    
    @staticmethod
    def show_warning(title: str, message: str, parent: Optional[tk.Widget] = None) -> None:
        """
        Display a warning popup dialog.
        
        Args:
            title: Dialog window title
            message: Warning message to display
            parent: Parent widget (optional)
        """
        messagebox.showwarning(title, message, parent=parent)
    
    @staticmethod
    def show_info(title: str, message: str, parent: Optional[tk.Widget] = None) -> None:
        """
        Display an information popup dialog.
        
        Args:
            title: Dialog window title
            message: Information message to display
            parent: Parent widget (optional)
        """
        messagebox.showinfo(title, message, parent=parent)
    
    @staticmethod
    def show_confirmation(title: str, message: str, parent: Optional[tk.Widget] = None) -> bool:
        """
        Display a confirmation dialog with Yes/No buttons.
        
        Args:
            title: Dialog window title
            message: Confirmation message to display
            parent: Parent widget (optional)
            
        Returns:
            bool: True if user clicked Yes, False if No
        """
        result = messagebox.askquestion(title, message, parent=parent, icon="question")
        return result == "yes"
    
    @staticmethod
    def show_invalid_word() -> None:
        """Display popup for invalid 5-letter word."""
        PopupDialog.show_warning(
            "Invalid Word", 
            "Please enter a valid 5-letter word!"
        )
    
    @staticmethod
    def show_word_not_in_list() -> None:
        """Display popup for word not in word list."""
        PopupDialog.show_error(
            "Invalid Word", 
            "Word not found in our dictionary. Please try another word."
        )
    
    @staticmethod
    def show_login_error(error_type: str) -> None:
        """
        Display login-related error messages.
        
        Args:
            error_type: Type of login error (wrong_password, user_not_exist, etc.)
        """
        error_messages = {
            "wrong_password": "Incorrect password. Please try again.",
            "user_not_exist": "User does not exist. Please register first.",
            "user_exists": "Username already exists. Please choose a different username.",
            "empty_fields": "Please fill in both username and password.",
            "connection_error": "Unable to connect to server. Please try again later.",
            "invalid_credentials": "Invalid username or password format."
        }
        
        message = error_messages.get(error_type, "An unknown error occurred.")
        PopupDialog.show_error("Login Error", message)
    
    @staticmethod
    def show_room_error(error_type: str) -> None:
        """
        Display room/lobby related error messages.
        
        Args:
            error_type: Type of room error
        """
        error_messages = {
            "room_full": "This room is full. Please try another room.",
            "already_in_room": "You are already in a room.",
            "room_not_exist": "Room does not exist.",
            "connection_lost": "Connection to server lost. Please reconnect."
        }
        
        message = error_messages.get(error_type, "An unknown room error occurred.")
        PopupDialog.show_error("Room Error", message)
    
    @staticmethod
    def show_game_result(won: bool, opponent_name: str, word: str, attempts: int) -> None:
        """
        Display game result popup for multiplayer game.
        
        Args:
            won: Whether the player won
            opponent_name: Name of the opponent
            word: The target word
            attempts: Number of attempts taken
        """
        if won:
            title = "You Won!"
            message = f"Congratulations!\n\nYou beat {opponent_name}!\nThe word was: {word}\nYou guessed it in {attempts} attempts!\n\nReturning to lobby..."
        else:
            title = "Game Over"
            message = f"Better luck next time!\n\n{opponent_name} won this round.\nThe word was: {word}\n\nReturning to lobby..."
        
        PopupDialog.show_info(title, message)
    
    @staticmethod
    def show_connection_error(server_url: str) -> None:
        """Display server connection error."""
        PopupDialog.show_error(
            "Connection Error",
            f"Cannot connect to Wordle server at {server_url}\n\n"
            "Please ensure the server is running and try again."
        )
    
# Common error types for easy reference
class ErrorTypes:
    """Constants for common error types to avoid typos."""
    
    # Login errors
    WRONG_PASSWORD = "wrong_password"
    USER_NOT_EXIST = "user_not_exist"
    USER_EXISTS = "user_exists"
    EMPTY_FIELDS = "empty_fields"
    CONNECTION_ERROR = "connection_error"
    INVALID_CREDENTIALS = "invalid_credentials"
    
    # Room errors
    ROOM_FULL = "room_full"
    ALREADY_IN_ROOM = "already_in_room"
    ROOM_NOT_EXIST = "room_not_exist"
    CONNECTION_LOST = "connection_lost"

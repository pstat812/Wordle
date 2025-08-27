#!/usr/bin/env python3
"""
Wordle Client Launcher

Launcher for the Wordle game client.
"""

import sys
import tkinter as tk
from tkinter import messagebox

def validate_runtime_dependencies() -> bool:
    """Validates that tkinter is available."""
    try:
        test_root = tk.Tk()
        test_root.withdraw()
        test_root.destroy()
        return True
    except Exception:
        return False

def main():
    """Main function to launch the Wordle client."""
    # Validate dependencies
    if not validate_runtime_dependencies():
        print("Error: tkinter is not available. Please ensure Python tkinter is properly installed.")
        sys.exit(1)
    
    try:
        print("Launching Multiplayer Wordle Game Client...")
        print("Make sure the server is running at http://127.0.0.1:5000")
        
        # Import required modules
        from login_page import LoginPage
        from lobby_page import LobbyPage
        from multiplayer_client import MultiplayerClient
        from wordle_client import WordleClient
        
        # Create main window
        root = tk.Tk()
        
        # Application state
        current_page = None
        current_username = None
        
        def show_login():
            """Show login page."""
            nonlocal current_page
            if current_page:
                try:
                    current_page.destroy()
                except (AttributeError, tk.TclError):
                    # Page may have already been destroyed or not have destroy method
                    pass
            current_page = LoginPage(root, on_login_success=show_lobby, on_single_player=show_single_player)
        
        def show_single_player():
            """Show single player game."""
            nonlocal current_page
            if current_page:
                try:
                    current_page.destroy()
                except (AttributeError, tk.TclError):
                    # Page may have already been destroyed or not have destroy method
                    pass
            current_page = WordleClient(root, on_exit=show_login)
        
        def show_lobby(username):
            """Show lobby page after successful login."""
            nonlocal current_page, current_username
            current_username = username
            if current_page:
                try:
                    current_page.destroy()
                except (AttributeError, tk.TclError):
                    # Page may have already been destroyed or not have destroy method
                    pass
            current_page = LobbyPage(root, username, on_game_start=start_game, on_logout=show_login)
        
        def start_game(username, game_data):
            """Start multiplayer game."""
            nonlocal current_page
            if current_page:
                try:
                    current_page.destroy()
                except (AttributeError, tk.TclError):
                    # Page may have already been destroyed or not have destroy method
                    pass
            current_page = MultiplayerClient(root, username, game_data, on_game_end=lambda: show_lobby(username))
        
        # Start with login page
        show_login()
        
        # Start main loop
        root.mainloop()
        
    except ImportError as e:
        print(f"Error: Could not import client module: {e}")
        print("Please ensure all required files are in the Client directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

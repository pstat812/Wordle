"""
Lobby Page Module

This module provides the lobby interface where users can join game rooms.
There are 3 rooms available, each allowing 2 players maximum.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import requests
import threading
import time
from typing import Callable, Optional, Dict, Any
from popup_dialog import PopupDialog, ErrorTypes


class LobbyPage:
    """
    Lobby page for joining game rooms and waiting for opponents.
    """
    
    def __init__(self, root: tk.Tk, username: str, server_url: str = "http://127.0.0.1:5000",
                 on_game_start: Optional[Callable[[str, Dict[str, Any]], None]] = None,
                 on_logout: Optional[Callable[[], None]] = None):
        """
        Initialize the lobby page.
        
        Args:
            root: Main tkinter window
            username: Current logged-in username
            server_url: Server URL for API calls
            on_game_start: Callback when game starts
            on_logout: Callback when user logs out
        """
        self.root = root
        self.username = username
        self.server_url = server_url
        self.on_game_start = on_game_start
        self.on_logout = on_logout
        
        # State variables
        self.current_room = None
        self.polling_active = False
        self.polling_thread = None
        
        # Track scheduled callbacks for cleanup
        self.scheduled_callbacks = []
        
        # UI setup
        self.setup_window()
        self.setup_colors()
        self.setup_fonts()
        self.create_widgets()
        
        # Start polling for room updates
        self.start_room_polling()
    
    def setup_window(self) -> None:
        """Configure the main window for lobby page."""
        self.root.title("Wordle - Lobby")
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
        """Setup color scheme matching Wordle theme."""
        self.colors = {
            "bg": "#ffffff",
            "primary": "#6aaa64",
            "secondary": "#787c7e",
            "accent": "#c9b458",
            "text_dark": "#212529",
            "text_light": "#ffffff",
            "room_bg": "#f8f9fa",
            "room_border": "#d3d6da",
            "room_occupied": "#ffebee",
            "room_available": "#e8f5e8",
            "ready_color": "#4caf50",
            "not_ready_color": "#ff9800"
        }
    
    def setup_fonts(self) -> None:
        """Setup custom fonts."""
        self.fonts = {
            "title": tkFont.Font(family="Arial", size=24, weight="bold"),
            "username": tkFont.Font(family="Arial", size=16, weight="bold"),
            "room_title": tkFont.Font(family="Arial", size=14, weight="bold"),
            "room_info": tkFont.Font(family="Arial", size=11),
            "button": tkFont.Font(family="Arial", size=11, weight="bold"),
            "status": tkFont.Font(family="Arial", size=12)
        }
    
    def create_widgets(self) -> None:
        """Create all UI widgets for the lobby page."""
        # Main container
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_frame.pack(expand=True, fill="both", padx=30, pady=20)
        
        # Header frame
        header_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="WORDLE LOBBY",
            font=self.fonts["title"],
            fg=self.colors["primary"],
            bg=self.colors["bg"]
        )
        title_label.pack(side="left")
        
        # Welcome message
        welcome_label = tk.Label(
            header_frame,
            text=f"Welcome, {self.username}!",
            font=self.fonts["username"],
            fg=self.colors["secondary"],
            bg=self.colors["bg"]
        )
        welcome_label.pack(side="right")
        
        # Logout button
        self.logout_button = tk.Button(
            header_frame,
            text="Logout",
            font=self.fonts["button"],
            bg=self.colors["secondary"],
            fg=self.colors["text_light"],
            relief="flat",
            borderwidth=0,
            command=self.logout,
            cursor="hand2"
        )
        self.logout_button.pack(side="right", padx=(0, 20))
        
        # Instructions
        instructions_label = tk.Label(
            self.main_frame,
            text="Choose a room to join",
            font=self.fonts["room_info"],
            fg=self.colors["secondary"],
            bg=self.colors["bg"]
        )
        instructions_label.pack(pady=(0, 20))
        
        # Rooms container
        self.rooms_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        self.rooms_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Create room widgets
        self.room_widgets = {}
        self.create_room_widgets()
        
        # Current room status frame
        self.status_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        self.status_frame.pack(fill="x", pady=(20, 0))
        
        # Status labels
        self.room_status_label = tk.Label(
            self.status_frame,
            text="Not in any room",
            font=self.fonts["status"],
            fg=self.colors["secondary"],
            bg=self.colors["bg"]
        )
        self.room_status_label.pack()
        
        # Leave room button (initially hidden)
        self.leave_button = tk.Button(
            self.status_frame,
            text="Leave Room",
            font=self.fonts["button"],
            bg=self.colors["secondary"],
            fg=self.colors["text_light"],
            relief="flat",
            borderwidth=0,
            command=self.leave_room,
            cursor="hand2"
        )
    
    def create_room_widgets(self) -> None:
        """Create widgets for the 3 game rooms."""
        for room_id in range(1, 4):
            room_frame = tk.Frame(
                self.rooms_frame,
                bg=self.colors["room_bg"],
                relief="solid",
                borderwidth=2
            )
            room_frame.pack(fill="x", pady=10, padx=20)
            
            # Room header
            header_frame = tk.Frame(room_frame, bg=self.colors["room_bg"])
            header_frame.pack(fill="x", padx=15, pady=(15, 10))
            
            room_title = tk.Label(
                header_frame,
                text=f"Room {room_id}",
                font=self.fonts["room_title"],
                fg=self.colors["text_dark"],
                bg=self.colors["room_bg"]
            )
            room_title.pack(side="left")
            
            # Join button
            join_button = tk.Button(
                header_frame,
                text="JOIN",
                font=self.fonts["button"],
                bg=self.colors["primary"],
                fg=self.colors["text_light"],
                relief="flat",
                borderwidth=0,
                command=lambda r=room_id: self.join_room(r),
                cursor="hand2"
            )
            join_button.pack(side="right")
            
            # Players info frame
            players_frame = tk.Frame(room_frame, bg=self.colors["room_bg"])
            players_frame.pack(fill="x", padx=15, pady=(0, 15))
            
            # Player slots
            player1_label = tk.Label(
                players_frame,
                text="Player 1: Empty",
                font=self.fonts["room_info"],
                fg=self.colors["secondary"],
                bg=self.colors["room_bg"]
            )
            player1_label.pack(anchor="w")
            
            player2_label = tk.Label(
                players_frame,
                text="Player 2: Empty",
                font=self.fonts["room_info"],
                fg=self.colors["secondary"],
                bg=self.colors["room_bg"]
            )
            player2_label.pack(anchor="w")
            
            # Store widget references
            self.room_widgets[room_id] = {
                "frame": room_frame,
                "join_button": join_button,
                "player1_label": player1_label,
                "player2_label": player2_label
            }
    
    def join_room(self, room_id: int) -> None:
        """
        Join a specific room.
        
        Args:
            room_id: ID of the room to join (1, 2, or 3)
        """
        if self.current_room is not None:
            PopupDialog.show_room_error(ErrorTypes.ALREADY_IN_ROOM)
            return
        
        try:
            response = requests.post(
                f"{self.server_url}/api/rooms/{room_id}/join",
                json={"username": self.username},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    self.current_room = room_id
                    self.update_status_display()
                    
                    # Check if game is starting
                    if data.get("game_starting"):
                        self.handle_game_start(data.get("game_data"))
                    else:
                        # Make sure polling is active for this user
                        if not self.polling_active:
                            self.start_room_polling()
                else:
                    error = data.get("error", "Unknown error")
                    if "full" in error.lower():
                        PopupDialog.show_room_error(ErrorTypes.ROOM_FULL)
                    else:
                        PopupDialog.show_room_error("room_error")
            else:
                PopupDialog.show_room_error(ErrorTypes.CONNECTION_LOST)
                
        except requests.RequestException:
            PopupDialog.show_room_error(ErrorTypes.CONNECTION_LOST)
        except Exception as e:
            PopupDialog.show_error("Error", f"Failed to join room: {str(e)}")
    
    def leave_room(self) -> None:
        """Leave the current room."""
        if self.current_room is None:
            return
        
        try:
            response = requests.post(
                f"{self.server_url}/api/rooms/{self.current_room}/leave",
                json={"username": self.username},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    self.current_room = None
                    self.update_status_display()
                    
        except requests.RequestException:
            PopupDialog.show_room_error(ErrorTypes.CONNECTION_LOST)
        except Exception as e:
            PopupDialog.show_error("Error", f"Failed to leave room: {str(e)}")
    

    
    def handle_game_start(self, game_data: Dict[str, Any]) -> None:
        """
        Handle game start event.
        
        Args:
            game_data: Game initialization data from server
        """
        self.stop_room_polling()
        if self.on_game_start:
            self.on_game_start(self.username, game_data)
    
    def update_status_display(self) -> None:
        """Update the current room status display."""
        if self.current_room is None:
            self.room_status_label.configure(
                text="Not in any room",
                fg=self.colors["secondary"]
            )
            self.leave_button.pack_forget()
        else:
            self.room_status_label.configure(
                text=f"In Room {self.current_room} - Waiting for players...",
                fg=self.colors["secondary"]
            )
            
            # Show leave button
            self.leave_button.pack()
    
    def update_room_display(self, rooms_data: Dict[str, Any]) -> None:
        """
        Update room display with current room information.
        
        Args:
            rooms_data: Room information from server
        """
        for room_id in range(1, 4):
            room_info = rooms_data.get(str(room_id), {})
            players = room_info.get("players", [])
            
            widgets = self.room_widgets[room_id]
            
            # Update player labels
            player1_text = f"Player 1: {players[0] if len(players) > 0 else 'Empty'}"
            player2_text = f"Player 2: {players[1] if len(players) > 1 else 'Empty'}"
            
            widgets["player1_label"].configure(text=player1_text)
            widgets["player2_label"].configure(text=player2_text)
            
            # Update join button state
            if len(players) >= 2:
                widgets["join_button"].configure(
                    text="FULL",
                    state="disabled",
                    bg=self.colors["secondary"]
                )
                widgets["frame"].configure(highlightbackground=self.colors["room_occupied"])
            else:
                widgets["join_button"].configure(
                    text="JOIN",
                    state="normal",
                    bg=self.colors["primary"]
                )
                widgets["frame"].configure(highlightbackground=self.colors["room_available"])
    
    def start_room_polling(self) -> None:
        """Start polling for room updates."""
        self.polling_active = True
        self.polling_thread = threading.Thread(target=self._poll_rooms, daemon=True)
        self.polling_thread.start()
    
    def stop_room_polling(self) -> None:
        """Stop polling for room updates."""
        self.polling_active = False
        if self.polling_thread:
            self.polling_thread.join(timeout=1.0)
    
    def destroy(self) -> None:
        """Destroy the lobby page and clean up resources."""
        self.stop_room_polling()
        
        # Cancel any scheduled callbacks
        if hasattr(self, 'scheduled_callbacks'):
            for callback_id in self.scheduled_callbacks:
                try:
                    self.root.after_cancel(callback_id)
                except (tk.TclError, AttributeError):
                    pass
            self.scheduled_callbacks.clear()
        
        # Destroy the main frame
        if hasattr(self, 'main_frame'):
            try:
                self.main_frame.destroy()
            except tk.TclError:
                pass
    
    def _poll_rooms(self) -> None:
        """Background thread function to poll room status."""
        while self.polling_active:
            try:
                response = requests.get(f"{self.server_url}/api/rooms", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data["success"]:
                        # Update UI in main thread
                        self.root.after(0, lambda: self.update_room_display(data["rooms"]))
                        
                        # Check for game start
                        if self.current_room:
                            room_data = data["rooms"].get(str(self.current_room), {})
                            if room_data.get("game_id"):
                                # Game has started for this room, get game data
                                game_data = {
                                    "game_id": room_data["game_id"],
                                    "room_id": self.current_room,
                                    "players": room_data["players"],
                                    "target_word": room_data.get("target_word")
                                }
                                self.root.after(0, lambda gd=game_data: self.handle_game_start(gd))
                                break
                            
            except requests.RequestException:
                pass  # Continue polling on network errors
            except Exception:
                pass  # Continue polling on other errors
            
            time.sleep(0.5)  # Poll every 0.5 seconds for faster game detection
    
    def logout(self) -> None:
        """Handle logout."""
        # Leave current room if in one
        if self.current_room:
            self.leave_room()
        
        # Stop polling
        self.stop_room_polling()
        
        # Call logout callback
        if self.on_logout:
            self.on_logout()
    
    def destroy(self) -> None:
        """Clean up the lobby page."""
        self.stop_room_polling()
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()

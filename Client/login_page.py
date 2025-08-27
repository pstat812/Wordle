"""
Login and Registration Page Module

This module provides the login and registration interface for the multiplayer Wordle game and single player game.
Users can either log in with existing credentials or register a new account.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import requests
from typing import Callable, Optional
from popup_dialog import PopupDialog, ErrorTypes


class LoginPage:
    """
    Login and registration page for user authentication.
    """
    
    def __init__(self, root: tk.Tk, server_url: str = "http://127.0.0.1:5000", 
                 on_login_success: Optional[Callable[[str], None]] = None,
                 on_single_player: Optional[Callable[[], None]] = None):
        """
        Initialize the login page.
        
        Args:
            root: Main tkinter window
            server_url: Server URL for authentication
            on_login_success: Callback function called when login succeeds
            on_single_player: Callback function called when single player is selected
        """
        self.root = root
        self.server_url = server_url
        self.on_login_success = on_login_success
        self.on_single_player = on_single_player
        
        # Track scheduled callbacks for cleanup
        self.scheduled_callbacks = []
        
        # UI setup
        self.setup_window()
        self.setup_colors()
        self.setup_fonts()
        self.create_widgets()
        
        # Focus on username field
        self.username_entry.focus_set()
    
    def setup_window(self) -> None:
        """Configure the main window for login page."""
        self.root.title("Wordle - Login")
        self.root.geometry("400x620")
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
            "input_bg": "#f8f9fa",
            "input_border": "#d3d6da",
            "button_hover": "#5a9a5a"
        }
    
    def setup_fonts(self) -> None:
        """Setup custom fonts."""
        self.fonts = {
            "title": tkFont.Font(family="Arial", size=28, weight="bold"),
            "subtitle": tkFont.Font(family="Arial", size=16),
            "label": tkFont.Font(family="Arial", size=12, weight="bold"),
            "input": tkFont.Font(family="Arial", size=12),
            "button": tkFont.Font(family="Arial", size=12, weight="bold"),
            "link": tkFont.Font(family="Arial", size=10, underline=True)
        }
    
    def create_widgets(self) -> None:
        """Create all UI widgets for the login page."""
        # Main container
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        # Title
        title_label = tk.Label(
            self.main_frame,
            text="WORDLE",
            font=self.fonts["title"],
            fg=self.colors["primary"],
            bg=self.colors["bg"]
        )
        title_label.pack(pady=(0, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            self.main_frame,
            text="Multiplayer Word Game",
            font=self.fonts["subtitle"],
            fg=self.colors["secondary"],
            bg=self.colors["bg"]
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Login form frame
        self.form_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        self.form_frame.pack(fill="x")
        
        # Username field
        username_label = tk.Label(
            self.form_frame,
            text="Username:",
            font=self.fonts["label"],
            fg=self.colors["text_dark"],
            bg=self.colors["bg"]
        )
        username_label.pack(anchor="w", pady=(0, 5))
        
        self.username_entry = tk.Entry(
            self.form_frame,
            font=self.fonts["input"],
            bg=self.colors["input_bg"],
            fg=self.colors["text_dark"],
            relief="solid",
            borderwidth=1,
            highlightthickness=2,
            highlightcolor=self.colors["primary"]
        )
        self.username_entry.pack(fill="x", pady=(0, 20), ipady=8)
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus_set())
        
        # Password field
        password_label = tk.Label(
            self.form_frame,
            text="Password:",
            font=self.fonts["label"],
            fg=self.colors["text_dark"],
            bg=self.colors["bg"]
        )
        password_label.pack(anchor="w", pady=(0, 5))
        
        self.password_entry = tk.Entry(
            self.form_frame,
            font=self.fonts["input"],
            bg=self.colors["input_bg"],
            fg=self.colors["text_dark"],
            relief="solid",
            borderwidth=1,
            highlightthickness=2,
            highlightcolor=self.colors["primary"],
            show="*"
        )
        self.password_entry.pack(fill="x", pady=(0, 30), ipady=8)
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        # Login button
        self.login_button = tk.Button(
            self.form_frame,
            text="LOGIN",
            font=self.fonts["button"],
            bg=self.colors["primary"],
            fg=self.colors["text_light"],
            relief="flat",
            borderwidth=0,
            command=self.login,
            cursor="hand2"
        )
        self.login_button.pack(fill="x", pady=(0, 15), ipady=12)
        self.login_button.bind('<Enter>', self.on_button_hover)
        self.login_button.bind('<Leave>', self.on_button_leave)
        
        # Register button
        self.register_button = tk.Button(
            self.form_frame,
            text="REGISTER",
            font=self.fonts["button"],
            bg=self.colors["secondary"],
            fg=self.colors["text_light"],
            relief="flat",
            borderwidth=0,
            command=self.register,
            cursor="hand2"
        )
        self.register_button.pack(fill="x", ipady=12)
        self.register_button.bind('<Enter>', self.on_register_button_hover)
        self.register_button.bind('<Leave>', self.on_register_button_leave)
        
        # Single Player button
        self.single_player_button = tk.Button(
            self.form_frame,
            text="SINGLE PLAYER",
            font=self.fonts["button"],
            bg=self.colors["accent"],
            fg=self.colors["text_light"],
            relief="flat",
            borderwidth=0,
            command=self.start_single_player,
            cursor="hand2"
        )
        self.single_player_button.pack(fill="x", pady=(15, 0), ipady=12)
        self.single_player_button.bind('<Enter>', self.on_single_player_hover)
        self.single_player_button.bind('<Leave>', self.on_single_player_leave)
        
        # Status label for feedback
        self.status_label = tk.Label(
            self.main_frame,
            text="",
            font=self.fonts["input"],
            fg=self.colors["secondary"],
            bg=self.colors["bg"]
        )
        self.status_label.pack(pady=(20, 0))
    
    def on_button_hover(self, event) -> None:
        """Handle login button hover effect."""
        self.login_button.configure(bg=self.colors["button_hover"])
    
    def on_button_leave(self, event) -> None:
        """Handle login button leave effect."""
        self.login_button.configure(bg=self.colors["primary"])
    
    def on_register_button_hover(self, event) -> None:
        """Handle register button hover effect."""
        self.register_button.configure(bg="#6a7c7e")
    
    def on_register_button_leave(self, event) -> None:
        """Handle register button leave effect."""
        self.register_button.configure(bg=self.colors["secondary"])
    
    def on_single_player_hover(self, event) -> None:
        """Handle single player button hover."""
        event.widget.configure(bg="#4caf50")  # Slightly darker accent
    
    def on_single_player_leave(self, event) -> None:
        """Handle single player button mouse leave."""
        event.widget.configure(bg=self.colors["accent"])
    
    def get_credentials(self) -> tuple[str, str]:
        """
        Get username and password from input fields.
        
        Returns:
            tuple: (username, password)
        """
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        return username, password
    
    def clear_fields(self) -> None:
        """Clear input fields."""
        try:
            if hasattr(self, 'username_entry') and self.username_entry.winfo_exists():
                self.username_entry.delete(0, tk.END)
            if hasattr(self, 'password_entry') and self.password_entry.winfo_exists():
                self.password_entry.delete(0, tk.END)
        except tk.TclError:
            # Widgets may have been destroyed
            pass
    
    def set_status(self, message: str, is_error: bool = False) -> None:
        """
        Set status message.
        
        Args:
            message: Status message to display
            is_error: Whether this is an error message
        """
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                color = "#d32f2f" if is_error else self.colors["secondary"]
                self.status_label.configure(text=message, fg=color)
                
                # Clear status after 3 seconds (track the callback safely)
                if message:  # Only schedule clearing if there's a message
                    callback_id = self.root.after(3000, self._safe_clear_status)
                    if hasattr(self, 'scheduled_callbacks'):
                        self.scheduled_callbacks.append(callback_id)
        except tk.TclError:
            # Widget may have been destroyed
            pass
    
    def _safe_clear_status(self) -> None:
        """Safely clear status label if it still exists."""
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text="")
        except tk.TclError:
            # Widget was destroyed, ignore
            pass
    
    def cleanup(self) -> None:
        """Clean up scheduled callbacks and widgets."""
        # Cancel all scheduled callbacks
        if hasattr(self, 'scheduled_callbacks'):
            for callback_id in self.scheduled_callbacks:
                try:
                    self.root.after_cancel(callback_id)
                except (tk.TclError, AttributeError):
                    # Callback may have already executed or root destroyed
                    pass
            self.scheduled_callbacks.clear()
        
        # Destroy the main frame
        if hasattr(self, 'main_frame'):
            try:
                self.main_frame.destroy()
            except tk.TclError:
                # Frame may have already been destroyed
                pass
    
    def destroy(self) -> None:
        """Destroy the login page and clean up resources."""
        self.cleanup()
    
    def disable_buttons(self) -> None:
        """Disable buttons during network requests."""
        try:
            if hasattr(self, 'login_button') and self.login_button.winfo_exists():
                self.login_button.configure(state="disabled", text="Logging in...")
            if hasattr(self, 'register_button') and self.register_button.winfo_exists():
                self.register_button.configure(state="disabled")
            if hasattr(self, 'single_player_button') and self.single_player_button.winfo_exists():
                self.single_player_button.configure(state="disabled")
        except tk.TclError:
            # Widgets may have been destroyed
            pass
    
    def enable_buttons(self) -> None:
        """Re-enable buttons after network requests."""
        try:
            if hasattr(self, 'login_button') and self.login_button.winfo_exists():
                self.login_button.configure(state="normal", text="LOGIN")
            if hasattr(self, 'register_button') and self.register_button.winfo_exists():
                self.register_button.configure(state="normal")
            if hasattr(self, 'single_player_button') and self.single_player_button.winfo_exists():
                self.single_player_button.configure(state="normal")
        except tk.TclError:
            # Widgets may have been destroyed
            pass
    
    def login(self) -> None:
        """Handle login button click."""
        username, password = self.get_credentials()
        
        # Validate input
        if not username or not password:
            PopupDialog.show_login_error(ErrorTypes.EMPTY_FIELDS)
            return
        
        # Disable UI during request
        self.disable_buttons()
        self.set_status("Logging in...")
        
        try:
            # Send login request to server
            response = requests.post(
                f"{self.server_url}/api/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    self.set_status("Login successful!")
                    # Call success callback
                    if self.on_login_success:
                        self.on_login_success(username)
                else:
                    error = data.get("error", "Unknown error")
                    if "password" in error.lower():
                        PopupDialog.show_login_error(ErrorTypes.WRONG_PASSWORD)
                    elif "not exist" in error.lower():
                        PopupDialog.show_login_error(ErrorTypes.USER_NOT_EXIST)
                    else:
                        PopupDialog.show_login_error(ErrorTypes.INVALID_CREDENTIALS)
            elif response.status_code == 401:
                # Authentication error - parse the error message
                try:
                    data = response.json()
                    error = data.get("error", "Authentication failed")
                    if "password" in error.lower() or "incorrect" in error.lower():
                        PopupDialog.show_login_error(ErrorTypes.WRONG_PASSWORD)
                    elif "not exist" in error.lower() or "does not exist" in error.lower():
                        PopupDialog.show_login_error(ErrorTypes.USER_NOT_EXIST)
                    else:
                        PopupDialog.show_login_error(ErrorTypes.INVALID_CREDENTIALS)
                except:
                    PopupDialog.show_login_error(ErrorTypes.INVALID_CREDENTIALS)
            elif response.status_code == 400:
                # Bad request - parse the error message
                try:
                    data = response.json()
                    error = data.get("error", "Bad request")
                    PopupDialog.show_error("Login Error", error)
                except:
                    PopupDialog.show_login_error(ErrorTypes.CONNECTION_ERROR)
            else:
                PopupDialog.show_login_error(ErrorTypes.CONNECTION_ERROR)
                
        except requests.RequestException:
            PopupDialog.show_login_error(ErrorTypes.CONNECTION_ERROR)
        except Exception as e:
            PopupDialog.show_error("Error", f"An unexpected error occurred: {str(e)}")
        finally:
            self.enable_buttons()
            self.set_status("")
    
    def register(self) -> None:
        """Handle register button click."""
        username, password = self.get_credentials()
        
        # Validate input
        if not username or not password:
            PopupDialog.show_login_error(ErrorTypes.EMPTY_FIELDS)
            return
        
        if len(username) < 3:
            PopupDialog.show_error("Invalid Input", "Username must be at least 3 characters long.")
            return
        
        if len(password) < 6:
            PopupDialog.show_error("Invalid Input", "Password must be at least 6 characters long.")
            return
        
        # Disable UI during request
        self.disable_buttons()
        self.set_status("Registering...")
        
        try:
            # Send registration request to server
            response = requests.post(
                f"{self.server_url}/api/auth/register",
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    self.set_status("Registration successful!")
                    PopupDialog.show_info("Success", "Account created successfully! You can now log in.")
                    self.clear_fields()
                    self.username_entry.focus_set()
                else:
                    error = data.get("error", "Unknown error")
                    if "already exists" in error.lower():
                        PopupDialog.show_login_error(ErrorTypes.USER_EXISTS)
                    else:
                        PopupDialog.show_error("Registration Error", error)
            elif response.status_code == 400:
                # Registration error - parse the error message
                try:
                    data = response.json()
                    error = data.get("error", "Registration failed")
                    if "already exists" in error.lower() or "username already" in error.lower():
                        PopupDialog.show_login_error(ErrorTypes.USER_EXISTS)
                    elif "password" in error.lower() and "6" in error:
                        PopupDialog.show_error("Registration Error", "Password must be at least 6 characters long")
                    elif "username" in error.lower() and "3" in error:
                        PopupDialog.show_error("Registration Error", "Username must be at least 3 characters long")
                    else:
                        PopupDialog.show_error("Registration Error", error)
                except:
                    PopupDialog.show_login_error(ErrorTypes.CONNECTION_ERROR)
            else:
                PopupDialog.show_login_error(ErrorTypes.CONNECTION_ERROR)
                
        except requests.RequestException:
            PopupDialog.show_login_error(ErrorTypes.CONNECTION_ERROR)
        except Exception as e:
            PopupDialog.show_error("Error", f"An unexpected error occurred: {str(e)}")
        finally:
            self.enable_buttons()
            self.set_status("")
    
    def start_single_player(self) -> None:
        """Handle single player button click."""
        # Cleanup before transitioning
        self.cleanup()
        # Call single player callback
        if self.on_single_player:
            self.on_single_player()
    
    def destroy(self) -> None:
        """Clean up the login page."""
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()

#!/usr/bin/env python3
"""
Wordle Game Application - Entry Point Module

This module serves as the main entry point for the Wordle game application.
It handles dependency validation, error management, and application bootstrapping
following defensive programming principles and graceful error handling patterns.

Architecture Overview:
    - Dependency injection pattern for GUI module
    - Fail-fast validation for required dependencies
    - Graceful degradation with fallback error reporting
    - Separation of concerns between CLI and GUI error handling

Author: Technical Assessment
Version: 1.0
"""

import sys
import tkinter as tk
from tkinter import messagebox
from typing import NoReturn


# Dependency injection: Import GUI module with error isolation
try:
    from wordle_gui import main as run_gui
except ImportError as import_error:
    print(f"Critical dependency error: {import_error}")
    print("Module wordle_gui not found. Ensure all game files are in the same directory.")
    sys.exit(1)


def validate_runtime_dependencies() -> bool:
    """
    Validates that all required runtime dependencies are available.
    
    This function implements defensive programming by checking critical
    dependencies before attempting to initialize the application.
    
    Returns:
        bool: True if all dependencies are satisfied, False otherwise
        
    Note:
        tkinter is typically bundled with Python installations but may
        be missing in some minimal distributions or Docker containers.
    """
    try:
        import tkinter as tk_validation
        # Verify tkinter can create a root window (deeper validation)
        test_root = tk_validation.Tk()
        test_root.withdraw()
        test_root.destroy()
        return True
    except (ImportError, tk.TclError) as dependency_error:
        print(f"Dependency validation failed: {dependency_error}")
        return False


def display_error_with_fallback(error_message: str, detailed_error: Exception) -> None:
    """
    Displays error messages with graceful fallback mechanisms.
    
    Implements a cascading error reporting strategy:
    1. Attempt GUI-based error dialog (preferred UX)
    2. Fall back to console output if GUI unavailable
    
    Args:
        error_message (str): User-friendly error description
        detailed_error (Exception): Technical error details for debugging
        
    Design Pattern:
        This follows the "graceful degradation" pattern, ensuring
        error information reaches the user regardless of system state.
    """
    console_message = f"Application Error: {error_message}\nTechnical Details: {detailed_error}"
    print(console_message)
    
    # Attempt GUI error reporting with exception isolation
    try:
        error_root = tk.Tk()
        error_root.withdraw()  # Hide root window to show only dialog
        messagebox.showerror(
            "Wordle Game - Application Error",
            f"{error_message}\n\nTechnical Details:\n{detailed_error}"
        )
        error_root.destroy()
    except Exception as gui_error:
        # GUI fallback failed - rely on console output
        print(f"GUI error reporting unavailable: {gui_error}")
        print("Error information displayed in console only.")


def bootstrap_application() -> NoReturn:
    """
    Bootstrap and launch the Wordle game application.
    
    This function orchestrates the complete application startup sequence:
    1. Dependency validation (fail-fast principle)
    2. Application initialization
    3. Error handling and user feedback
    4. Graceful shutdown on failure
    
    Raises:
        SystemExit: On critical errors that prevent application startup
        
    Design Patterns:
        - Template Method: Defines startup algorithm structure
        - Fail-Fast: Immediate validation prevents partial initialization
        - Exception Translation: Converts technical errors to user-friendly messages
    """
    print("Initializing Wordle Game Application...")
    
    # Phase 1: Pre-flight dependency validation
    if not validate_runtime_dependencies():
        error_message = (
            "Required dependencies are not available. "
            "Please ensure Python tkinter is properly installed."
        )
        print(f"Startup aborted: {error_message}")
        sys.exit(1)
    
    print("Dependency validation successful.")
    
    # Phase 2: Application launch with comprehensive error handling
    try:
        print("Launching graphical user interface...")
        run_gui()  # Delegate to GUI module
        print("Application terminated normally.")
        
    except Exception as startup_error:
        # Translate technical errors into user-actionable information
        user_message = (
            "The application failed to start due to an unexpected error. "
            "Please check your system configuration and try again."
        )
        
        display_error_with_fallback(user_message, startup_error)
        
        # Explicit failure exit code for automated testing/monitoring
        sys.exit(1)


if __name__ == "__main__":
    """
    Application entry point with proper module execution guard.
    
    This guard ensures the bootstrap function only executes when the module
    is run directly, not when imported. This follows Python best practices
    for module design and enables safe importability for testing.
    """
    bootstrap_application()
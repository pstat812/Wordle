#!/usr/bin/env python3
"""
Wordle Client Launcher

Simple launcher for the Wordle game client.
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
        from wordle_client import main as run_client
        print("Launching Wordle Game Client...")
        print("Make sure the server is running at http://127.0.0.1:5000")
        run_client()
    except ImportError as e:
        print(f"Error: Could not import client module: {e}")
        print("Please ensure all required files are in the Client directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

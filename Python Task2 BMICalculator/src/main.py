"""
Main Application Launcher for Human BMI Calculator & Health Tracker.

Oasis Infobyte (OIBSIP) Python Programming Internship - Task 2 (Advanced).
"""

import sys
import os

# Add root project directory to sys.path to enable smooth imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import messagebox
from src.gui import BMICalculatorApp


def main():
    """Start the GUI application."""
    try:
        root = tk.Tk()
        app = BMICalculatorApp(root)
        root.mainloop()
    except Exception as exc:
        try:
            messagebox.showerror(
                "Application Error",
                f"An unexpected error occurred while running the application:\n{exc}",
            )
        except Exception:
            print(f"Critical error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

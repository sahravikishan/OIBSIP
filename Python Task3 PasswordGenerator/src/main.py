"""
Application entry point for OIBSIP Task 3: Advanced Random Password Generator.
"""

from pathlib import Path
import sys
import tkinter as tk

# Ensure project root is in sys.path when running 'python src/main.py'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.gui import PasswordGeneratorGUI
except ModuleNotFoundError:
    from gui import PasswordGeneratorGUI


def main() -> None:
    """Initializes and runs the Tkinter application."""
    root = tk.Tk()
    app = PasswordGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

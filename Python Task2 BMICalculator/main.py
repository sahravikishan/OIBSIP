"""
Project Root Application Launcher for BMI Calculator & Health Tracker.

Allows starting the application directly via `python main.py` as well as `python src/main.py`.
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.main import main

if __name__ == "__main__":
    main()

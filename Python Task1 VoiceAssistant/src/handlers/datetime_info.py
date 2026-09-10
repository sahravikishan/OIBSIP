"""
Date and time handler — provides the current time and date
formatted as natural spoken sentences.
"""

from datetime import datetime


def handle_time() -> str:
    """Return the current time as a spoken sentence."""
    now = datetime.now()
    # Format: "3:45 PM" style for natural speech
    time_str = now.strftime("%I:%M %p").lstrip("0")
    return f"The current time is {time_str}."


def handle_date() -> str:
    """Return today's date as a spoken sentence."""
    now = datetime.now()
    # Format: "Tuesday, September 9, 2026"
    date_str = now.strftime("%A, %B %d, %Y")
    # Remove leading zero from day if strftime keeps it
    # (e.g., "September 09" → "September 9")
    date_str = date_str.replace(" 0", " ")
    return f"Today is {date_str}."

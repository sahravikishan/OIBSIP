"""
Greeting handler — responds to hello/hi/hey with time-appropriate greetings.
"""

import random
from datetime import datetime


def handle_greeting() -> str:
    """
    Generate a context-aware greeting based on the current time of day.
    Returns a varied response from a pool of options.
    """
    hour = datetime.now().hour

    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 17:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"

    responses = [
        f"{time_greeting}! How can I help you today?",
        f"{time_greeting}! What can I do for you?",
        f"Hey there! {time_greeting}. I'm ready to assist.",
        f"{time_greeting}! I'm your voice assistant. Ask me anything.",
        f"Hello! {time_greeting}. What would you like me to do?",
    ]

    return random.choice(responses)

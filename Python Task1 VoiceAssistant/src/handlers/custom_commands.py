"""
Custom commands handler — loads user-configurable commands from
config/custom_commands.json and executes safe predefined actions.

SECURITY: Only URL-opening actions are permitted. No shell commands
or arbitrary code execution from the configuration file.
"""

import json
import webbrowser
from pathlib import Path


_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "custom_commands.json"

# Loaded commands: {trigger_phrase: url}
_custom_commands: dict[str, str] = {}


def load_custom_commands() -> dict[str, str]:
    """
    Load custom commands from the JSON configuration file.

    Expected format:
    {
        "open github": "https://github.com/",
        "open gmail": "https://mail.google.com/"
    }

    Returns:
        Dictionary of {trigger_phrase: url}.
        Empty dict if the file is missing or invalid.
    """
    global _custom_commands

    if not _CONFIG_PATH.is_file():
        print("[CUSTOM COMMANDS] config/custom_commands.json not found. "
              "Custom commands are disabled.")
        _custom_commands = {}
        return _custom_commands

    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"[CUSTOM COMMANDS] Invalid JSON in custom_commands.json: {exc}")
        _custom_commands = {}
        return _custom_commands

    if not isinstance(raw, dict):
        print("[CUSTOM COMMANDS] custom_commands.json must be a JSON object "
              "(key-value pairs). Ignoring.")
        _custom_commands = {}
        return _custom_commands

    # Validate each entry: key must be a string, value must be a URL string
    validated = {}
    for phrase, url in raw.items():
        if not isinstance(phrase, str) or not isinstance(url, str):
            print(f"[CUSTOM COMMANDS] Skipping invalid entry: {phrase!r}")
            continue
        if not url.startswith(("http://", "https://")):
            print(f"[CUSTOM COMMANDS] Skipping non-URL value for '{phrase}': "
                  f"only http/https URLs are allowed for security.")
            continue
        validated[phrase.lower().strip()] = url.strip()

    _custom_commands = validated
    if validated:
        print(f"[CUSTOM COMMANDS] Loaded {len(validated)} custom commands.")
    return _custom_commands


def get_custom_commands() -> dict[str, str]:
    """Return the currently loaded custom commands."""
    return _custom_commands


def handle_custom_command(user_text: str) -> str | None:
    """
    Check if the user's text matches a custom command and execute it.

    Args:
        user_text: The user's spoken text (lowercased).

    Returns:
        A spoken confirmation if a command matched, or None if no match.
    """
    if not _custom_commands:
        return None

    text_lower = user_text.lower().strip()

    # Try exact match first
    if text_lower in _custom_commands:
        url = _custom_commands[text_lower]
        return _open_url(text_lower, url)

    # Try partial match — check if user text contains a command phrase
    for phrase, url in _custom_commands.items():
        if phrase in text_lower:
            return _open_url(phrase, url)

    return None


def _open_url(phrase: str, url: str) -> str:
    """Open a URL in the default browser and return confirmation."""
    try:
        webbrowser.open(url)
        return f"Opening {phrase} for you."
    except webbrowser.Error:
        return f"I couldn't open {phrase}. Please check your browser settings."

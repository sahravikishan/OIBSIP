"""
Configuration utility — loads environment variables from .env file
and provides safe access to secrets and settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# Resolve the project root (two levels up from this file: src/utils/config.py → project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env from project root if it exists
_dotenv_path = _PROJECT_ROOT / ".env"
if _dotenv_path.is_file():
    load_dotenv(_dotenv_path)


def get_env(key: str, default: str = "", required: bool = False) -> str:
    """
    Retrieve an environment variable by key.

    Args:
        key: The environment variable name.
        default: Fallback value if the variable is not set.
        required: If True, raises a warning message (does not crash)
                  when the variable is missing.

    Returns:
        The environment variable value, or the default.
    """
    value = os.environ.get(key, "").strip()
    if not value:
        if required:
            print(f"[CONFIG WARNING] Environment variable '{key}' is not set. "
                  f"Some features may not work. See .env.example for setup.")
        return default
    return value


def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return _PROJECT_ROOT


def validate_email_config() -> dict:
    """
    Check whether email environment variables are configured.
    Returns a dict with the values and a 'configured' boolean.
    """
    address = get_env("EMAIL_ADDRESS")
    password = get_env("EMAIL_PASSWORD")
    server = get_env("SMTP_SERVER", default="smtp.gmail.com")
    port = get_env("SMTP_PORT", default="587")

    configured = bool(address and password)

    return {
        "address": address,
        "password": password,
        "server": server,
        "port": int(port) if port.isdigit() else 587,
        "configured": configured,
    }


def validate_weather_config() -> dict:
    """
    Check whether the OpenWeatherMap API key is configured.
    Returns a dict with the key and a 'configured' boolean.
    """
    api_key = get_env("OPENWEATHER_API_KEY")
    return {
        "api_key": api_key,
        "configured": bool(api_key),
    }

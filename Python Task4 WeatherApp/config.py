"""
Configuration management for Weather App.
Handles loading and saving API keys and user preferences (e.g. default temperature unit).
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

CONFIG_FILE = Path(__file__).resolve().parent / "config.json"
ENV_KEY_NAME = "OPENWEATHER_API_KEY"

DEFAULT_CONFIG: Dict[str, Any] = {
    "api_key": "",
    "default_unit": "C",  # 'C' for Celsius, 'F' for Fahrenheit
    "theme": "dark",      # 'dark' or 'light'
    "last_city": "Pune",
    "use_demo_if_no_key": True
}


def load_env_file() -> None:
    """Simple parser for .env file in the workspace directory."""
    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and not os.environ.get(k):
                            os.environ[k] = v
        except Exception:
            pass


load_env_file()


def get_config() -> Dict[str, Any]:
    """Load configuration from config.json with fallback defaults."""
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    cfg.update(data)
        except Exception:
            pass

    # Environment variable has priority if set and non-empty
    env_key = os.environ.get(ENV_KEY_NAME, "").strip()
    if env_key:
        cfg["api_key"] = env_key

    return cfg


def save_config(updates: Dict[str, Any]) -> None:
    """Save configuration updates to config.json."""
    current = get_config()
    current.update(updates)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=4)
    except Exception as e:
        print(f"Warning: Could not save configuration: {e}")


def get_api_key() -> str:
    """Retrieve the OpenWeatherMap API key."""
    return get_config().get("api_key", "").strip()


def set_api_key(key: str) -> None:
    """Store the OpenWeatherMap API key."""
    save_config({"api_key": key.strip()})

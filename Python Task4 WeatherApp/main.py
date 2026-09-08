"""
Main Entry Point for the Real-Time Weather Application.
Allows running either the Advanced GUI (default) or Beginner CLI via `--cli`.
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="Real-Time Weather Application (GUI & CLI)")
    parser.add_argument("--cli", action="store_true", help="Launch command-line interface instead of GUI")
    parser.add_argument("city", nargs="?", help="Optional city name or ZIP code to look up in CLI mode")
    parser.add_argument("--set-key", help="Save OpenWeatherMap API key to config")

    args, unknown = parser.parse_known_args()

    if args.cli or args.city or args.set_key:
        from weather_cli import main as cli_main
        cli_main()
    else:
        try:
            from weather_gui import main as gui_main
            gui_main()
        except Exception as e:
            print(f"[!] Unable to launch GUI ({e}). Falling back to CLI mode...\n")
            from weather_cli import main as cli_main
            cli_main()


if __name__ == "__main__":
    main()

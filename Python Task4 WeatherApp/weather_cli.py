"""
Weather CLI - Beginner Tier Command-Line Interface.
Prompts for city name/ZIP code, validates input, fetches weather data,
and displays temperature (°C and °F), humidity, condition, and wind speed.
"""

import argparse
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import get_api_key, set_api_key
from weather_service import (
    fetch_weather_data,
    ValidationError,
    CityNotFoundError,
    InvalidApiKeyError,
    NetworkError,
    RateLimitError,
    WeatherAppError
)


def format_weather_output(weather_data) -> str:
    """Format weather details into an attractive CLI card."""
    curr = weather_data.current
    demo_tag = " (DEMO PREVIEW - No API key configured)" if curr.is_demo else ""
    country_part = f", {curr.country}" if curr.country else ""

    lines = [
        "=" * 50,
        f"  WEATHER REPORT: {curr.city.upper()}{country_part}{demo_tag}",
        "=" * 50,
        f"  Condition    : {curr.condition} ({curr.description})",
        f"  Temperature  : {curr.temp_c}°C  |  {curr.temp_f}°F",
        f"  Feels Like   : {curr.feels_like_c}°C  |  {curr.feels_like_f}°F",
        f"  Humidity     : {curr.humidity}%",
        f"  Wind Speed   : {curr.wind_speed_mps} m/s  ({curr.wind_speed_mph} mph)",
        f"  Pressure     : {curr.pressure_hpa} hPa",
        f"  Report Time  : {curr.formatted_time}",
        "=" * 50
    ]

    # Show 5-day outlook summary if available
    if weather_data.daily:
        lines.append("\n  5-Day Outlook:")
        lines.append("  " + "-" * 44)
        for day in weather_data.daily:
            lines.append(
                f"  {day.day_name:<8} {day.date_str:<8} {day.condition:<12} "
                f"{day.temp_min_c:>4.1f}°C / {day.temp_max_c:>4.1f}°C  ({day.temp_min_f:>4.1f}°F / {day.temp_max_f:>4.1f}°F)"
            )
        lines.append("  " + "-" * 44)

    return "\n".join(lines)


def fetch_and_display(query: str) -> bool:
    """Fetches and displays weather for a single query. Returns True if successful."""
    try:
        data = fetch_weather_data(query)
        print("\n" + format_weather_output(data) + "\n")
        return True
    except ValidationError as e:
        print(f"\n[!] Input Error: {e}\n")
    except CityNotFoundError as e:
        print(f"\n[!] Location Not Found: {e}\n")
    except InvalidApiKeyError as e:
        print(f"\n[!] API Key Error: {e}")
        print("    Tip: Register a free key at https://openweathermap.org/api and set it with:")
        print("         python weather_cli.py --set-key <YOUR_API_KEY>\n")
    except NetworkError as e:
        print(f"\n[!] Network Error: {e}\n")
    except RateLimitError as e:
        print(f"\n[!] Rate Limit Exceeded: {e}\n")
    except WeatherAppError as e:
        print(f"\n[!] Error: {e}\n")
    except Exception as e:
        print(f"\n[!] Unexpected error occurred: {e}\n")
    return False


def run_interactive():
    """Interactive loop prompting the user for city or ZIP code."""
    api_key = get_api_key()

    print("=" * 50)
    print("       Real-Time Weather App (CLI)")
    print("=" * 50)
    if not api_key:
        print("[Note] No OpenWeatherMap API key detected.")
        print("       Running in Demo Preview mode.")
        print("       To use live data: register at openweathermap.org")
        print("       and run: python weather_cli.py --set-key YOUR_KEY\n")
    else:
        print("[✓] OpenWeatherMap API key loaded.\n")

    print("Type a city name (e.g. 'London', 'Tokyo', 'Paris') or ZIP code.")
    print("Type 'q' or 'exit' to quit.\n")

    while True:
        try:
            city_input = input("Enter city name or ZIP code: ").strip()
            if not city_input:
                print("[!] Error: City name cannot be empty. Please try again.\n")
                continue

            if city_input.lower() in ("q", "quit", "exit"):
                print("Exiting Weather App. Goodbye!")
                break

            fetch_and_display(city_input)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Weather App. Goodbye!")
            break


def main(argv=None):
    parser = argparse.ArgumentParser(description="Real-Time Weather CLI Application")
    parser.add_argument("--cli", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("city", nargs="?", help="City name or ZIP code to look up")
    parser.add_argument("--set-key", help="Save OpenWeatherMap API key to config")
    parser.add_argument("--view-key", action="store_true", help="Display current configured API key (masked)")

    args = parser.parse_args(argv)

    if args.set_key:
        key = args.set_key.strip()
        set_api_key(key)
        print(f"[✓] OpenWeatherMap API key successfully saved to config.json ({key[:4]}...{key[-4:] if len(key) > 8 else ''})")
        return

    if args.view_key:
        key = get_api_key()
        if key:
            masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
            print(f"Current API Key: {masked}")
        else:
            print("No API Key configured. (Using Demo Mode)")
        return

    if args.city:
        success = fetch_and_display(args.city)
        if not success:
            sys.exit(1)
    else:
        run_interactive()


if __name__ == "__main__":
    main()

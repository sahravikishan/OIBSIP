"""
Weather handler — retrieves live weather data from the OpenWeatherMap API
and formats it as a natural spoken response.

API key is loaded from environment variables (never hard-coded).
"""

import requests

from src.utils.config import validate_weather_config


# OpenWeatherMap Current Weather endpoint
_OWM_URL = "https://api.openweathermap.org/data/2.5/weather"


def handle_weather(city: str) -> str:
    """
    Fetch current weather for the given city and return a spoken description.

    Args:
        city: City name (e.g., "Pune", "New York").

    Returns:
        A natural sentence describing the weather, or an error message.
    """
    if not city or not city.strip():
        return "I didn't catch which city you want the weather for. Could you say it again?"

    weather_cfg = validate_weather_config()
    if not weather_cfg["configured"]:
        return (
            "The weather service is not configured. Please set "
            "OPENWEATHER_API_KEY in your environment variables. "
            "You can get a free key at openweathermap.org."
        )

    # Build the API request
    params = {
        "q": city.strip(),
        "appid": weather_cfg["api_key"],
        "units": "metric",  # Celsius
    }

    try:
        response = requests.get(_OWM_URL, params=params, timeout=10)
    except requests.ConnectionError:
        return "I couldn't connect to the weather service. Please check your internet connection."
    except requests.Timeout:
        return "The weather service took too long to respond. Please try again."
    except requests.RequestException as exc:
        return f"An error occurred while fetching weather data: {exc}"

    # Handle HTTP errors
    if response.status_code == 401:
        return "The weather API key is invalid. Please check your OPENWEATHER_API_KEY."
    elif response.status_code == 404:
        return f"I couldn't find weather data for '{city}'. Please check the city name."
    elif response.status_code != 200:
        return f"The weather service returned an error (status {response.status_code})."

    # Parse the JSON response
    try:
        data = response.json()
    except ValueError:
        return "The weather service returned an unexpected response."

    return _format_weather_response(data, city)


def _format_weather_response(data: dict, city: str) -> str:
    """
    Convert raw OpenWeatherMap JSON into a natural spoken sentence.

    Extracts: temperature, condition description, humidity, wind speed.
    """
    try:
        temp = round(data["main"]["temp"])
        condition = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind_speed = round(data["wind"]["speed"] * 3.6)  # m/s → km/h
        city_name = data.get("name", city)

        return (
            f"The current temperature in {city_name} is {temp} degrees Celsius "
            f"with {condition}. "
            f"Humidity is at {humidity} percent, "
            f"and the wind speed is {wind_speed} kilometres per hour."
        )
    except (KeyError, IndexError, TypeError):
        return f"I received weather data for {city} but couldn't read it properly."

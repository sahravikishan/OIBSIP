"""
Weather Service Module for fetching, parsing, and caching weather data.
Supports OpenWeatherMap API (Current Weather and 5-Day/3-Hour Forecast),
IP-based auto-location detection, unit conversions, and icon management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import requests
from PIL import Image, ImageDraw

from config import get_api_key

# Endpoints
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
ICON_BASE_URL = "https://openweathermap.org/img/wn/{icon}@2x.png"
IPINFO_URL = "https://ipinfo.io/json"
IP_API_URL = "http://ip-api.com/json"

CACHE_DIR = Path(__file__).resolve().parent / ".cache" / "icons"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# --- Custom Exceptions ---

class WeatherAppError(Exception):
    """Base exception for Weather App."""
    pass


class ValidationError(WeatherAppError):
    """Raised when user input is empty or invalid."""
    pass


class CityNotFoundError(WeatherAppError):
    """Raised when the specified city or location is not found (404)."""
    pass


class InvalidApiKeyError(WeatherAppError):
    """Raised when the API key is missing or rejected (401)."""
    pass


class NetworkError(WeatherAppError):
    """Raised on connection failure, timeout, or DNS issues."""
    pass


class RateLimitError(WeatherAppError):
    """Raised when API rate limit is exceeded (429)."""
    pass


# --- Unit Conversion Helpers ---

def c_to_f(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return round((celsius * 9 / 5) + 32, 1)


def f_to_c(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return round((fahrenheit - 32) * 5 / 9, 1)


def mps_to_mph(mps: float) -> float:
    """Convert meters per second to miles per hour."""
    return round(mps * 2.23694, 1)


# --- Data Models ---

@dataclass
class CurrentWeather:
    city: str
    country: str
    temp_c: float
    temp_f: float
    feels_like_c: float
    feels_like_f: float
    humidity: int
    condition: str
    description: str
    wind_speed_mps: float
    wind_speed_mph: float
    pressure_hpa: int
    icon_code: str
    dt: int
    is_demo: bool = False

    @property
    def formatted_time(self) -> str:
        try:
            return datetime.fromtimestamp(self.dt, tz=timezone.utc).strftime("%A, %d %b %Y %H:%M UTC")
        except Exception:
            return datetime.now().strftime("%A, %d %b %Y %H:%M")


@dataclass
class HourlyForecastItem:
    time_str: str
    temp_c: float
    temp_f: float
    condition: str
    icon_code: str
    dt: int


@dataclass
class DailyForecastItem:
    day_name: str
    date_str: str
    temp_min_c: float
    temp_max_c: float
    temp_min_f: float
    temp_max_f: float
    condition: str
    icon_code: str


@dataclass
class WeatherData:
    current: CurrentWeather
    hourly: List[HourlyForecastItem] = field(default_factory=list)
    daily: List[DailyForecastItem] = field(default_factory=list)


# --- Demo Data Generator (For Testing or Key-less Preview) ---

def get_demo_weather(query: str) -> WeatherData:
    """Provides realistic offline mock weather data for preview/demonstration."""
    q_lower = query.strip().lower()
    city_configs = {
        "london": ("London", "GB", 16.5, 78, "Clouds", "scattered clouds", 4.2, 1014, "03d"),
        "new york": ("New York", "US", 21.0, 65, "Clear", "clear sky", 3.6, 1018, "01d"),
        "tokyo": ("Tokyo", "JP", 24.5, 82, "Rain", "light rain", 5.1, 1009, "10d"),
        "paris": ("Paris", "FR", 18.0, 70, "Clouds", "broken clouds", 3.8, 1016, "04d"),
        "mumbai": ("Mumbai", "IN", 30.0, 85, "Haze", "haze", 2.5, 1008, "50d"),
    }

    match_name = "Demo City"
    match_country = "GLOBAL"
    base_temp = 20.0
    humidity = 65
    condition = "Partly Cloudy"
    description = "scattered clouds"
    wind_speed = 3.5
    pressure = 1013
    icon = "02d"

    for k, v in city_configs.items():
        if k in q_lower:
            match_name, match_country, base_temp, humidity, condition, description, wind_speed, pressure, icon = v
            break
    else:
        match_name = query.strip().title()

    curr = CurrentWeather(
        city=match_name,
        country=match_country,
        temp_c=round(base_temp, 1),
        temp_f=c_to_f(base_temp),
        feels_like_c=round(base_temp - 0.5, 1),
        feels_like_f=c_to_f(base_temp - 0.5),
        humidity=humidity,
        condition=condition,
        description=description,
        wind_speed_mps=wind_speed,
        wind_speed_mph=mps_to_mph(wind_speed),
        pressure_hpa=pressure,
        icon_code=icon,
        dt=int(datetime.now().timestamp()),
        is_demo=True
    )

    # 6 hours ahead forecast
    hourly = []
    now_hour = datetime.now().hour
    for i in range(1, 7):
        h = (now_hour + i) % 24
        t_c = round(base_temp + (i * 0.4 if i <= 3 else -i * 0.3), 1)
        hourly.append(HourlyForecastItem(
            time_str=f"{h:02d}:00",
            temp_c=t_c,
            temp_f=c_to_f(t_c),
            condition=condition,
            icon_code=icon,
            dt=int(datetime.now().timestamp()) + (i * 3600)
        ))

    # 5-day forecast
    daily = []
    day_offsets = ["Today", "Tomorrow", "Wed", "Thu", "Fri"]
    for i, day in enumerate(day_offsets):
        min_c = round(base_temp - 4 + (i * 0.5), 1)
        max_c = round(base_temp + 3 + (i * 0.5), 1)
        daily.append(DailyForecastItem(
            day_name=day,
            date_str=f"+{i}d",
            temp_min_c=min_c,
            temp_max_c=max_c,
            temp_min_f=c_to_f(min_c),
            temp_max_f=c_to_f(max_c),
            condition=condition,
            icon_code=icon
        ))

    return WeatherData(current=curr, hourly=hourly, daily=daily)


# --- API Validation & Call Wrappers ---

def validate_location_query(query: str) -> str:
    """Validates and trims user query."""
    if not query or not query.strip():
        raise ValidationError("Location query cannot be empty. Please enter a city name or ZIP code.")
    cleaned = query.strip()
    if len(cleaned) < 2:
        raise ValidationError("Location query is too short. Please enter a valid city name or ZIP code.")
    return cleaned


def _request_openweathermap(url: str, params: Dict[str, Any], timeout: int = 8) -> Dict[str, Any]:
    """Execute HTTP GET to OpenWeatherMap with robust error handling."""
    try:
        response = requests.get(url, params=params, timeout=timeout)
    except requests.exceptions.Timeout:
        raise NetworkError("Request timed out. Please check your internet connection and try again.")
    except requests.exceptions.ConnectionError:
        raise NetworkError("Could not connect to OpenWeatherMap. Please check your network connection.")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"Network error occurred: {str(e)}")

    if response.status_code == 200:
        try:
            return response.json()
        except Exception:
            raise WeatherAppError("Invalid JSON response received from weather service.")

    # Error handling based on HTTP status codes
    if response.status_code == 401:
        raise InvalidApiKeyError(
            "API Key Not Active Yet: OpenWeatherMap newly created keys take 10 to 60 minutes after registration to activate. Please also verify that you clicked the confirmation link in your email."
        )
    elif response.status_code == 404:
        raise CityNotFoundError(
            f"Location '{params.get('q', 'specified')}' not found. Please check spelling or try adding a country code (e.g. 'London,UK')."
        )
    elif response.status_code == 429:
        raise RateLimitError("OpenWeatherMap API rate limit reached (60 calls/minute). Please wait a moment.")
    else:
        try:
            err_json = response.json()
            msg = err_json.get("message", f"HTTP {response.status_code}")
        except Exception:
            msg = f"HTTP {response.status_code}"
        raise WeatherAppError(f"Weather API error: {msg}")


def parse_current_weather(data: Dict[str, Any]) -> CurrentWeather:
    """Parse JSON from /weather endpoint into CurrentWeather dataclass."""
    main = data.get("main", {})
    weather_list = data.get("weather", [{}])
    weather_0 = weather_list[0] if weather_list else {}
    wind = data.get("wind", {})
    sys = data.get("sys", {})

    temp_c = round(float(main.get("temp", 0.0)), 1)
    feels_like_c = round(float(main.get("feels_like", temp_c)), 1)
    wind_mps = round(float(wind.get("speed", 0.0)), 1)

    return CurrentWeather(
        city=data.get("name", "Unknown"),
        country=sys.get("country", ""),
        temp_c=temp_c,
        temp_f=c_to_f(temp_c),
        feels_like_c=feels_like_c,
        feels_like_f=c_to_f(feels_like_c),
        humidity=int(main.get("humidity", 0)),
        condition=weather_0.get("main", "Clear"),
        description=weather_0.get("description", "").capitalize(),
        wind_speed_mps=wind_mps,
        wind_speed_mph=mps_to_mph(wind_mps),
        pressure_hpa=int(main.get("pressure", 1013)),
        icon_code=weather_0.get("icon", "01d"),
        dt=int(data.get("dt", datetime.now().timestamp())),
        is_demo=False
    )


def parse_forecast_data(data: Dict[str, Any]) -> Tuple[List[HourlyForecastItem], List[DailyForecastItem]]:
    """
    Parse JSON from /forecast endpoint (3-hour intervals over 5 days).
    Returns (hourly_items, daily_items).
    """
    items = data.get("list", [])
    if not items:
        return [], []

    # 1. Hourly Forecast: Next 6-9 hours (first 2-3 intervals)
    hourly: List[HourlyForecastItem] = []
    for item in items[:4]:  # up to next 9-12 hours
        dt = item.get("dt", 0)
        dt_obj = datetime.fromtimestamp(dt, tz=timezone.utc)
        time_str = dt_obj.strftime("%H:%M")

        temp_c = round(float(item.get("main", {}).get("temp", 0.0)), 1)
        weather_0 = item.get("weather", [{}])[0]

        hourly.append(HourlyForecastItem(
            time_str=time_str,
            temp_c=temp_c,
            temp_f=c_to_f(temp_c),
            condition=weather_0.get("main", "Clear"),
            icon_code=weather_0.get("icon", "01d"),
            dt=dt
        ))

    # 2. Daily Forecast: Aggregate 5 days (min/max temp, midday condition)
    days_dict: Dict[str, Dict[str, Any]] = {}
    for item in items:
        dt = item.get("dt", 0)
        dt_obj = datetime.fromtimestamp(dt, tz=timezone.utc)
        date_key = dt_obj.strftime("%Y-%m-%d")
        temp_c = float(item.get("main", {}).get("temp", 0.0))
        weather_0 = item.get("weather", [{}])[0]

        if date_key not in days_dict:
            days_dict[date_key] = {
                "day_name": dt_obj.strftime("%a"),
                "date_str": dt_obj.strftime("%b %d"),
                "temps": [temp_c],
                "conditions": [weather_0.get("main", "Clear")],
                "icons": [weather_0.get("icon", "01d")],
                "hours": [dt_obj.hour]
            }
        else:
            days_dict[date_key]["temps"].append(temp_c)
            days_dict[date_key]["conditions"].append(weather_0.get("main", "Clear"))
            days_dict[date_key]["icons"].append(weather_0.get("icon", "01d"))
            days_dict[date_key]["hours"].append(dt_obj.hour)

    daily: List[DailyForecastItem] = []
    # Take up to 5 days
    for date_key, info in list(days_dict.items())[:5]:
        min_c = round(min(info["temps"]), 1)
        max_c = round(max(info["temps"]), 1)

        # Pick icon closest to midday (12:00)
        best_idx = 0
        min_diff = 99
        for idx, hour in enumerate(info["hours"]):
            diff = abs(hour - 12)
            if diff < min_diff:
                min_diff = diff
                best_idx = idx

        daily.append(DailyForecastItem(
            day_name=info["day_name"],
            date_str=info["date_str"],
            temp_min_c=min_c,
            temp_max_c=max_c,
            temp_min_f=c_to_f(min_c),
            temp_max_f=c_to_f(max_c),
            condition=info["conditions"][best_idx],
            icon_code=info["icons"][best_idx]
        ))

    return hourly, daily


def fetch_weather_data(query: str, api_key: Optional[str] = None) -> WeatherData:
    """
    Primary service method to fetch complete weather data for a city or ZIP code.
    Raises ValidationError, InvalidApiKeyError, CityNotFoundError, NetworkError, WeatherAppError.
    """
    clean_query = validate_location_query(query)
    key = api_key or get_api_key()

    if not key:
        # If no key is set, we return demo data for testing, but mark it
        return get_demo_weather(clean_query)

    # 1. Fetch current weather (units=metric returns Celsius and m/s)
    current_params = {
        "q": clean_query,
        "appid": key,
        "units": "metric"
    }
    current_json = _request_openweathermap(CURRENT_WEATHER_URL, current_params)
    current_weather = parse_current_weather(current_json)

    # 2. Fetch 5-day / 3-hour forecast
    hourly_items: List[HourlyForecastItem] = []
    daily_items: List[DailyForecastItem] = []
    try:
        forecast_params = {
            "q": clean_query,
            "appid": key,
            "units": "metric"
        }
        forecast_json = _request_openweathermap(FORECAST_URL, forecast_params)
        hourly_items, daily_items = parse_forecast_data(forecast_json)
    except Exception:
        # If forecast fails but current succeeded, still provide current weather
        pass

    return WeatherData(current=current_weather, hourly=hourly_items, daily=daily_items)


# --- IP-based Location Auto-Detection ---

def detect_user_location() -> str:
    """
    Detect user's current city using ipinfo.io (free tier) with fallback to ip-api.com.
    Returns city name (e.g. 'San Francisco', 'Mumbai', 'London').
    """
    try:
        resp = requests.get(IPINFO_URL, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            city = data.get("city")
            if city:
                return city.strip()
    except Exception:
        pass

    # Fallback to ip-api
    try:
        resp = requests.get(IP_API_URL, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            city = data.get("city")
            if city:
                return city.strip()
    except Exception:
        pass

    raise NetworkError("Could not automatically detect location. Please type your city name manually.")


# --- Weather Icon Management ---

def create_fallback_icon(condition: str, size: Tuple[int, int] = (64, 64)) -> Image.Image:
    """Generates a clean colored weather symbol if icon download is unavailable."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = size
    cond = condition.lower()

    if "rain" in cond:
        # Blue rain circle
        draw.ellipse([w * 0.2, h * 0.2, w * 0.8, h * 0.8], fill=(70, 130, 200, 255))
        draw.line([w * 0.35, h * 0.65, w * 0.3, h * 0.85], fill=(200, 230, 255, 255), width=2)
        draw.line([w * 0.5, h * 0.65, w * 0.45, h * 0.85], fill=(200, 230, 255, 255), width=2)
        draw.line([w * 0.65, h * 0.65, w * 0.6, h * 0.85], fill=(200, 230, 255, 255), width=2)
    elif "cloud" in cond:
        # Grey cloud ellipse
        draw.ellipse([w * 0.15, h * 0.3, w * 0.65, h * 0.75], fill=(180, 195, 210, 255))
        draw.ellipse([w * 0.35, h * 0.2, w * 0.85, h * 0.7], fill=(210, 225, 240, 255))
    elif "snow" in cond:
        # White-blue snowflake star
        draw.line([w * 0.5, h * 0.2, w * 0.5, h * 0.8], fill=(200, 240, 255, 255), width=3)
        draw.line([w * 0.2, h * 0.5, w * 0.8, h * 0.5], fill=(200, 240, 255, 255), width=3)
    else:
        # Bright sun
        draw.ellipse([w * 0.2, h * 0.2, w * 0.8, h * 0.8], fill=(255, 195, 0, 255))

    return img


def get_weather_icon(icon_code: str, condition: str = "Clear", size: Tuple[int, int] = (64, 64)) -> Image.Image:
    """
    Downloads or retrieves cached weather icon from OpenWeatherMap.
    Falls back to generated graphical icon if network fails.
    """
    if not icon_code:
        return create_fallback_icon(condition, size)

    cache_file = CACHE_DIR / f"{icon_code}.png"
    if cache_file.exists():
        try:
            img = Image.open(cache_file).convert("RGBA")
            if img.size != size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            return img
        except Exception:
            pass

    # Attempt to download icon
    url = ICON_BASE_URL.format(icon=icon_code)
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            with open(cache_file, "wb") as f:
                f.write(resp.content)
            img = Image.open(cache_file).convert("RGBA")
            if img.size != size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            return img
    except Exception:
        pass

    return create_fallback_icon(condition, size)

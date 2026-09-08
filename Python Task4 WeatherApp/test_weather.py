"""
Comprehensive Unit Tests for Weather Application.
Tests conversions, validation, JSON response parsing, error handling, and mocking.
"""

import unittest
from unittest.mock import patch, MagicMock
import requests

from weather_service import (
    c_to_f,
    f_to_c,
    mps_to_mph,
    validate_location_query,
    parse_current_weather,
    parse_forecast_data,
    _request_openweathermap,
    detect_user_location,
    get_demo_weather,
    ValidationError,
    CityNotFoundError,
    InvalidApiKeyError,
    NetworkError,
    RateLimitError
)
import config


class TestWeatherConversions(unittest.TestCase):
    def test_c_to_f(self):
        self.assertEqual(c_to_f(0), 32.0)
        self.assertEqual(c_to_f(100), 212.0)
        self.assertEqual(c_to_f(-40), -40.0)
        self.assertEqual(c_to_f(25.5), 77.9)

    def test_f_to_c(self):
        self.assertEqual(f_to_c(32.0), 0.0)
        self.assertEqual(f_to_c(212.0), 100.0)
        self.assertEqual(f_to_c(-40.0), -40.0)

    def test_mps_to_mph(self):
        self.assertEqual(mps_to_mph(0), 0.0)
        self.assertEqual(mps_to_mph(10), 22.4)


class TestValidation(unittest.TestCase):
    def test_empty_query_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            validate_location_query("")
        with self.assertRaises(ValidationError):
            validate_location_query("   ")

    def test_too_short_query_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            validate_location_query("a")

    def test_valid_query(self):
        self.assertEqual(validate_location_query(" London "), "London")
        self.assertEqual(validate_location_query("90210"), "90210")


class TestWeatherParsing(unittest.TestCase):
    def setUp(self):
        self.mock_current_json = {
            "name": "Paris",
            "sys": {"country": "FR"},
            "main": {
                "temp": 18.4,
                "feels_like": 17.8,
                "humidity": 65,
                "pressure": 1016
            },
            "weather": [
                {
                    "main": "Clouds",
                    "description": "scattered clouds",
                    "icon": "03d"
                }
            ],
            "wind": {
                "speed": 3.6
            },
            "dt": 1694000000
        }

        self.mock_forecast_json = {
            "list": [
                {
                    "dt": 1694000000,
                    "main": {"temp": 20.0},
                    "weather": [{"main": "Clear", "icon": "01d"}]
                },
                {
                    "dt": 1694010800,
                    "main": {"temp": 22.0},
                    "weather": [{"main": "Clouds", "icon": "02d"}]
                },
                {
                    "dt": 1694021600,
                    "main": {"temp": 19.0},
                    "weather": [{"main": "Rain", "icon": "10d"}]
                },
                {
                    "dt": 1694086400,  # Next day
                    "main": {"temp": 15.0},
                    "weather": [{"main": "Rain", "icon": "10d"}]
                }
            ]
        }

    def test_parse_current_weather(self):
        parsed = parse_current_weather(self.mock_current_json)
        self.assertEqual(parsed.city, "Paris")
        self.assertEqual(parsed.country, "FR")
        self.assertEqual(parsed.temp_c, 18.4)
        self.assertEqual(parsed.temp_f, 65.1)
        self.assertEqual(parsed.feels_like_c, 17.8)
        self.assertEqual(parsed.humidity, 65)
        self.assertEqual(parsed.condition, "Clouds")
        self.assertEqual(parsed.description, "Scattered clouds")
        self.assertEqual(parsed.wind_speed_mps, 3.6)
        self.assertEqual(parsed.wind_speed_mph, 8.1)
        self.assertEqual(parsed.pressure_hpa, 1016)
        self.assertEqual(parsed.icon_code, "03d")
        self.assertFalse(parsed.is_demo)

    def test_parse_forecast_data(self):
        hourly, daily = parse_forecast_data(self.mock_forecast_json)
        self.assertGreater(len(hourly), 0)
        self.assertEqual(hourly[0].temp_c, 20.0)
        self.assertEqual(hourly[0].condition, "Clear")

        self.assertGreater(len(daily), 0)
        # Daily items should aggregate min/max
        first_day = daily[0]
        self.assertTrue(hasattr(first_day, "temp_min_c"))
        self.assertTrue(hasattr(first_day, "temp_max_c"))

    def test_demo_weather_generation(self):
        demo = get_demo_weather("Tokyo")
        self.assertEqual(demo.current.city, "Tokyo")
        self.assertTrue(demo.current.is_demo)
        self.assertEqual(len(demo.hourly), 6)
        self.assertEqual(len(demo.daily), 5)


class TestErrorHandling(unittest.TestCase):
    @patch("requests.get")
    def test_401_raises_invalid_api_key(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        with self.assertRaises(InvalidApiKeyError):
            _request_openweathermap("http://fakeurl", {"appid": "invalid"})

    @patch("requests.get")
    def test_404_raises_city_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        with self.assertRaises(CityNotFoundError):
            _request_openweathermap("http://fakeurl", {"q": "nonexistentcity"})

    @patch("requests.get")
    def test_429_raises_rate_limit(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp

        with self.assertRaises(RateLimitError):
            _request_openweathermap("http://fakeurl", {})

    @patch("requests.get")
    def test_timeout_raises_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Timed out")

        with self.assertRaises(NetworkError):
            _request_openweathermap("http://fakeurl", {})

    @patch("requests.get")
    def test_connection_error_raises_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed connection")

        with self.assertRaises(NetworkError):
            _request_openweathermap("http://fakeurl", {})


class TestAutoLocation(unittest.TestCase):
    @patch("requests.get")
    def test_detect_location_ipinfo_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"city": "Berlin", "country": "DE"}
        mock_get.return_value = mock_resp

        loc = detect_user_location()
        self.assertEqual(loc, "Berlin")

    @patch("requests.get")
    def test_detect_location_fallback_ip_api(self, mock_get):
        # First call fails (ipinfo), second succeeds (ip-api)
        resp_fail = MagicMock()
        resp_fail.status_code = 500

        resp_success = MagicMock()
        resp_success.status_code = 200
        resp_success.json.return_value = {"city": "Sydney"}

        mock_get.side_effect = [resp_fail, resp_success]

        loc = detect_user_location()
        self.assertEqual(loc, "Sydney")


if __name__ == "__main__":
    unittest.main()

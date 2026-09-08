# SkyCast - Real-Time Weather Application

A comprehensive Python Weather Application featuring both a **Beginner Tier** Command-Line Interface (CLI) and an **Advanced Tier** Graphical User Interface (GUI) powered by the OpenWeatherMap API.

---

## 🌟 Feature Checklist

### Beginner Tier (CLI)
- [x] **Location Query**: Interactive prompt for city name or ZIP code, plus command-line argument support (`python weather_cli.py "London"`).
- [x] **API Integration**: Real-time HTTP GET to OpenWeatherMap API and structured JSON parsing.
- [x] **Weather Metrics Display**:
  - Current Temperature in both **Celsius (°C)** and **Fahrenheit (°F)**
  - Humidity percentage (%)
  - Weather condition and detailed description (e.g., "Clouds (scattered clouds)")
  - Wind speed in **m/s** and **mph**
  - Atmospheric pressure (hPa)
- [x] **Robust Error Handling**:
  - City not found (HTTP 404)
  - Invalid / missing API key (HTTP 401)
  - Network timeouts and connection drops
  - Rate limiting (HTTP 429)
- [x] **Input Validation**: Rejects empty strings, whitespace, or excessively short queries with clear guidance.

### Advanced Tier (GUI)
- [x] **Modern Responsive GUI**: Custom-styled dark slate theme built using Python `tkinter` and `ttk`.
- [x] **Weather Icons**: Fetches and renders official OpenWeatherMap weather icons with local disk caching and offline vector fallbacks.
- [x] **Hourly Forecast Panel**: Shows forecast cards for the next 6–9 hours with timestamps, weather icons, conditions, and temperatures.
- [x] **Daily Forecast Panel**: Aggregates a 5-day forecast displaying day names, dates, weather condition icons, and daily min/max temperatures.
- [x] **Unit Toggle (°C / °F)**: Instant toggle button in the header; recalculates and updates the entire UI without refetching from the network.
- [x] **📍 IP-Based Auto-Detection**: Automatically detects the user's city via the `ipinfo.io` (or fallback `ip-api.com`) free API.
- [x] **In-GUI Error Notifications**: Visually distinct inline error banners inside the GUI (no crashes or terminal popups).
- [x] **Non-Blocking Architecture**: Background threading (`threading.Thread`) ensures the GUI stays smooth and responsive during API calls.
- [x] **API Key Settings Modal**: In-app dialog to input, update, or clear your OpenWeatherMap key, saved securely to `config.json`.
- [x] **Demo Preview Mode**: Fully functional offline demo preview mode for testing before registering an API key.

---

## 🛠 Tech Stack

- **Language**: Python 3.8+
- **HTTP Client**: `requests`
- **Image Processing**: `Pillow` (`PIL`) for downloading, resizing, and caching weather icons
- **GUI Framework**: `tkinter` & `ttk`
- **Testing**: `unittest` with mock responses
- **APIs**:
  - [OpenWeatherMap API](https://openweathermap.org/api) (Current Weather & 5-Day Forecast)
  - [ipinfo.io](https://ipinfo.io) (IP-based Geolocation)

---

## 📁 Project Structure

```
Python Task4 WeatherApp/
├── weather_service.py       # Core weather client, data models, icon cache & auto-detection
├── weather_gui.py           # Advanced Tier: Modern Tkinter GUI
├── weather_cli.py           # Beginner Tier: Interactive & CLI interface
├── main.py                  # Unified entry point (defaults to GUI, accepts --cli)
├── config.py                # Configuration & API key persistence (config.json / .env)
├── test_weather.py          # Unit tests with mocks for API, conversions & errors
├── requirements.txt         # Project dependencies (requests, Pillow)
└── README.md                # Documentation & User Guide
```

---

## 🚀 Getting Started

### 1. Prerequisites & Installation

Install the required Python packages:

```bash
pip install -r requirements.txt
```

*(Note: `tkinter` is included with standard Python distributions on Windows and macOS).*

---

### 2. Getting an OpenWeatherMap API Key (Free)

1. Sign up for a free account at [OpenWeatherMap](https://openweathermap.org/users/sign_up).
2. Go to your account profile and navigate to the **API keys** tab.
3. Copy your 32-character key.
4. You can configure it in any of the following ways:
   - **Through the GUI**: Launch `python main.py`, click **⚙ API Key** in the top right, paste the key, and click **Save Key**.
   - **Through the CLI**: Run `python weather_cli.py --set-key YOUR_API_KEY`.
   - **Via Environment Variable or `.env` file**:
     ```bash
     export OPENWEATHER_API_KEY="your_api_key_here"
     ```
     or create a `.env` file containing:
     ```env
     OPENWEATHER_API_KEY=your_api_key_here
     ```

> **Note**: If no API key is provided, SkyCast automatically operates in **Demo Preview Mode** so you can immediately explore the interface and features.

---

## 💻 Usage

### Running the Advanced GUI Application (Default)

```bash
python main.py
```
or:
```bash
python weather_gui.py
```

#### GUI Features Walkthrough:
1. **Search**: Enter any city or ZIP code (e.g., `New York`, `Tokyo`, `London`, `90210`) and press **Enter** or click **Get Weather**.
2. **Auto Detect**: Click **📍 Auto Detect** to determine your current city via your IP address.
3. **Unit Switcher**: Click the **Unit: °C / °F** button in the top right to instantly swap all temperature values.
4. **Settings**: Click **⚙ API Key** to configure or view your API key.

---

### Running the Beginner CLI Application

You can run the CLI interactively:
```bash
python main.py --cli
```
or:
```bash
python weather_cli.py
```

Or query a city directly in one command:
```bash
python main.py --cli Tokyo
# or
python weather_cli.py "San Francisco"
```

#### Example CLI Output:
```text
==================================================
  WEATHER REPORT: TOKYO, JP
==================================================
  Condition    : Rain (light rain)
  Temperature  : 24.5°C  |  76.1°F
  Feels Like   : 24.0°C  |  75.2°F
  Humidity     : 82%
  Wind Speed   : 5.1 m/s  (11.4 mph)
  Pressure     : 1009 hPa
  Report Time  : Monday, 07 Sep 2026 17:04 UTC
==================================================

  5-Day Outlook:
  --------------------------------------------
  Today    +0d      Rain         20.5°C / 27.5°C  (68.9°F / 81.5°F)
  Tomorrow +1d      Rain         21.0°C / 28.0°C  (69.8°F / 82.4°F)
  Wed      +2d      Rain         21.5°C / 28.5°C  (70.7°F / 83.3°F)
  Thu      +3d      Rain         22.0°C / 29.0°C  (71.6°F / 84.2°F)
  Fri      +4d      Rain         22.5°C / 29.5°C  (72.5°F / 85.1°F)
  --------------------------------------------
```

---

## 🧪 Running Unit Tests

To run the automated test suite verifying conversions, JSON response parsing, validation, and error classifications:

```bash
python -m unittest test_weather.py
```

Expected output:
```text
................
----------------------------------------------------------------------
Ran 16 tests in 0.012s

OK
```

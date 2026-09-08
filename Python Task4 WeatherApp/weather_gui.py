"""
Weather GUI - Advanced Tier Graphical User Interface.
Built with Tkinter and Pillow.
Features:
- Search by city name or ZIP code
- Automatic location detection via IP (ipinfo.io / ip-api)
- Unit toggle: Celsius (°C) and Fahrenheit (°F) with instant re-render
- Real-time weather condition icons fetched from OpenWeatherMap
- Hourly forecast panel (next 6-9 hours)
- 5-Day daily forecast panel
- In-GUI error and status banners (no terminal crashes)
- Settings modal for saving and managing OpenWeatherMap API key
- Non-blocking background threads for snappy, responsive UI
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict
from PIL import Image, ImageTk

from config import get_api_key, set_api_key, get_config, save_config
from weather_service import (
    WeatherData,
    fetch_weather_data,
    detect_user_location,
    get_weather_icon,
    ValidationError,
    CityNotFoundError,
    InvalidApiKeyError,
    NetworkError,
    RateLimitError,
    WeatherAppError
)

# --- Color Palette (Modern Dark Slate Theme) ---
BG_COLOR = "#0F172A"         # Slate 900
PANEL_BG = "#1E293B"         # Slate 800
CARD_BG = "#334155"          # Slate 700
CARD_HOVER = "#475569"       # Slate 600
ACCENT_BLUE = "#38BDF8"      # Sky 400
ACCENT_CYAN = "#06B6D4"      # Cyan 500
TEXT_MAIN = "#F8FAFC"        # Slate 50
TEXT_MUTED = "#94A3B8"       # Slate 400
ERROR_BG = "#7F1D1D"         # Red 900
ERROR_TEXT = "#FCA5A5"       # Red 300
SUCCESS_BG = "#14532D"       # Green 900
SUCCESS_TEXT = "#86EFAC"     # Green 300
BORDER_COLOR = "#475569"     # Slate 600


class WeatherAppGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SkyCast - Real-Time Weather Application")
        self.root.geometry("820x860")
        self.root.minsize(760, 780)
        self.root.configure(bg=BG_COLOR)

        # State
        self.current_unit = get_config().get("default_unit", "C")
        self.weather_data: Optional[WeatherData] = None
        self.icon_photo_cache: Dict[str, ImageTk.PhotoImage] = {}
        self.is_loading = False

        # Configure custom TTK styles
        self._setup_styles()

        # Build UI
        self._build_header()
        self._build_search_bar()
        self._build_notification_banner()
        self._build_main_content()
        self._build_footer()

        # Auto-load initial weather
        last_city = get_config().get("last_city", "London")
        self.city_entry.insert(0, last_city)
        self.root.after(100, lambda: self.search_weather(last_city))

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", thickness=4, troughcolor=BG_COLOR, background=ACCENT_BLUE)

    def _build_header(self):
        header_frame = tk.Frame(self.root, bg=BG_COLOR)
        header_frame.pack(fill="x", padx=25, pady=(18, 10))

        # Title & Subtitle
        title_box = tk.Frame(header_frame, bg=BG_COLOR)
        title_box.pack(side="left")

        title_lbl = tk.Label(
            title_box,
            text="⛅ SkyCast Weather",
            font=("Segoe UI", 20, "bold"),
            fg=TEXT_MAIN,
            bg=BG_COLOR
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            title_box,
            text="Live conditions, hourly timeline & 5-day forecasts",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_COLOR
        )
        subtitle_lbl.pack(anchor="w")

        # Right Controls: Unit Toggle & Settings
        controls_box = tk.Frame(header_frame, bg=BG_COLOR)
        controls_box.pack(side="right", pady=4)

        # Unit Toggle Button
        self.unit_btn = tk.Button(
            controls_box,
            text=f"Unit: °{self.current_unit}",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_MAIN,
            bg=CARD_BG,
            activebackground=CARD_HOVER,
            activeforeground=TEXT_MAIN,
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.toggle_unit
        )
        self.unit_btn.pack(side="left", padx=6)

        # Settings Button
        settings_btn = tk.Button(
            controls_box,
            text="⚙ API Key",
            font=("Segoe UI", 10),
            fg=TEXT_MAIN,
            bg=CARD_BG,
            activebackground=CARD_HOVER,
            activeforeground=TEXT_MAIN,
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.open_settings_modal
        )
        settings_btn.pack(side="left")

    def _build_search_bar(self):
        search_frame = tk.Frame(self.root, bg=PANEL_BG, bd=1, relief="solid")
        search_frame.pack(fill="x", padx=25, pady=8)

        inner_frame = tk.Frame(search_frame, bg=PANEL_BG)
        inner_frame.pack(fill="x", padx=10, pady=8)

        # Search Icon Label
        icon_lbl = tk.Label(inner_frame, text="🔍", font=("Segoe UI", 12), bg=PANEL_BG, fg=TEXT_MUTED)
        icon_lbl.pack(side="left", padx=(4, 8))

        # Entry
        self.city_entry = tk.Entry(
            inner_frame,
            font=("Segoe UI", 12),
            bg=CARD_BG,
            fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            relief="flat",
            bd=5
        )
        self.city_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.city_entry.bind("<Return>", lambda event: self.on_search_clicked())

        # Search Button
        self.search_btn = tk.Button(
            inner_frame,
            text="Get Weather",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_BLUE,
            fg="#0F172A",
            activebackground=ACCENT_CYAN,
            relief="flat",
            padx=16,
            pady=5,
            cursor="hand2",
            command=self.on_search_clicked
        )
        self.search_btn.pack(side="left", padx=4)

        # Auto Detect Button
        self.auto_btn = tk.Button(
            inner_frame,
            text="📍 Auto Detect",
            font=("Segoe UI", 10),
            bg=CARD_BG,
            fg=TEXT_MAIN,
            activebackground=CARD_HOVER,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.on_auto_detect_clicked
        )
        self.auto_btn.pack(side="left", padx=4)

    def _build_notification_banner(self):
        """In-GUI Alert & Status notification panel."""
        self.banner_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.banner_frame.pack(fill="x", padx=25, pady=(2, 6))

        self.banner_lbl = tk.Label(
            self.banner_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            wraplength=740,
            justify="left",
            padx=12,
            pady=6
        )

    def show_banner(self, message: str, is_error: bool = False, is_info: bool = False):
        self.banner_lbl.config(
            text=message,
            bg=ERROR_BG if is_error else (PANEL_BG if is_info else SUCCESS_BG),
            fg=ERROR_TEXT if is_error else (ACCENT_BLUE if is_info else SUCCESS_TEXT)
        )
        self.banner_lbl.pack(fill="x")

    def hide_banner(self):
        self.banner_lbl.pack_forget()

    def _build_main_content(self):
        # Scrollable container or structured frames
        self.content_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.content_frame.pack(fill="both", expand=True, padx=25, pady=4)

        # 1. Current Weather Hero Card
        self.hero_card = tk.Frame(self.content_frame, bg=PANEL_BG, bd=1, relief="solid")
        self.hero_card.pack(fill="x", pady=(0, 10))

        # Hero Inner Content
        hero_inner = tk.Frame(self.hero_card, bg=PANEL_BG)
        hero_inner.pack(fill="x", padx=20, pady=16)

        # Top section of hero: City & Date
        hero_header = tk.Frame(hero_inner, bg=PANEL_BG)
        hero_header.pack(fill="x")

        self.location_lbl = tk.Label(
            hero_header,
            text="Ready to search",
            font=("Segoe UI", 19, "bold"),
            fg=TEXT_MAIN,
            bg=PANEL_BG
        )
        self.location_lbl.pack(side="left")

        self.demo_badge_lbl = tk.Label(
            hero_header,
            text="DEMO PREVIEW",
            font=("Segoe UI", 8, "bold"),
            bg="#854D0E",
            fg="#FEF08A",
            padx=6,
            pady=2
        )

        self.date_lbl = tk.Label(
            hero_header,
            text="",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=PANEL_BG
        )
        self.date_lbl.pack(side="right")

        # Middle section: Icon + Big Temperature + Condition
        temp_row = tk.Frame(hero_inner, bg=PANEL_BG)
        temp_row.pack(fill="x", pady=12)

        self.icon_lbl = tk.Label(temp_row, bg=PANEL_BG)
        self.icon_lbl.pack(side="left", padx=(0, 15))

        temp_col = tk.Frame(temp_row, bg=PANEL_BG)
        temp_col.pack(side="left")

        self.temp_lbl = tk.Label(
            temp_col,
            text="--°",
            font=("Segoe UI", 38, "bold"),
            fg=TEXT_MAIN,
            bg=PANEL_BG
        )
        self.temp_lbl.pack(anchor="w")

        self.condition_lbl = tk.Label(
            temp_col,
            text="Enter a city to view current conditions",
            font=("Segoe UI", 12),
            fg=ACCENT_BLUE,
            bg=PANEL_BG
        )
        self.condition_lbl.pack(anchor="w")

        # Bottom section: 4 Metric Cards (Feels like, Humidity, Wind, Pressure)
        metrics_grid = tk.Frame(hero_inner, bg=PANEL_BG)
        metrics_grid.pack(fill="x", pady=(12, 4))
        metrics_grid.columnconfigure(0, weight=1)
        metrics_grid.columnconfigure(1, weight=1)
        metrics_grid.columnconfigure(2, weight=1)
        metrics_grid.columnconfigure(3, weight=1)

        self.card_feels = self._create_metric_box(metrics_grid, 0, "🌡️ Feels Like", "--")
        self.card_humidity = self._create_metric_box(metrics_grid, 1, "💧 Humidity", "--")
        self.card_wind = self._create_metric_box(metrics_grid, 2, "💨 Wind Speed", "--")
        self.card_pressure = self._create_metric_box(metrics_grid, 3, "⏱️ Pressure", "--")

        # 2. Hourly Forecast (Next 6-9 Hours)
        hourly_section = tk.Frame(self.content_frame, bg=BG_COLOR)
        hourly_section.pack(fill="x", pady=(4, 10))

        hourly_title = tk.Label(
            hourly_section,
            text="🕒 Hourly Forecast (Next Hours)",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT_MAIN,
            bg=BG_COLOR
        )
        hourly_title.pack(anchor="w", pady=(0, 6))

        self.hourly_container = tk.Frame(hourly_section, bg=BG_COLOR)
        self.hourly_container.pack(fill="x")

        # 3. 5-Day Forecast
        daily_section = tk.Frame(self.content_frame, bg=BG_COLOR)
        daily_section.pack(fill="both", expand=True)

        daily_title = tk.Label(
            daily_section,
            text="📅 5-Day Daily Outlook",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT_MAIN,
            bg=BG_COLOR
        )
        daily_title.pack(anchor="w", pady=(0, 6))

        self.daily_container = tk.Frame(daily_section, bg=BG_COLOR)
        self.daily_container.pack(fill="both", expand=True)

    def _create_metric_box(self, parent, col: int, label_text: str, default_val: str) -> tk.Label:
        box = tk.Frame(parent, bg=CARD_BG, bd=1, relief="flat", padx=10, pady=8)
        box.grid(row=0, column=col, padx=4, sticky="nsew")

        title = tk.Label(box, text=label_text, font=("Segoe UI", 8), fg=TEXT_MUTED, bg=CARD_BG)
        title.pack(anchor="center")

        val_lbl = tk.Label(box, text=default_val, font=("Segoe UI", 11, "bold"), fg=TEXT_MAIN, bg=CARD_BG)
        val_lbl.pack(anchor="center", pady=(2, 0))
        return val_lbl

    def _build_footer(self):
        footer_frame = tk.Frame(self.root, bg=BG_COLOR)
        footer_frame.pack(fill="x", padx=25, pady=(4, 12))

        self.status_lbl = tk.Label(
            footer_frame,
            text="Powered by OpenWeatherMap API",
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=BG_COLOR
        )
        self.status_lbl.pack(side="left")

        version_lbl = tk.Label(
            footer_frame,
            text="Advanced Tier v1.0",
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=BG_COLOR
        )
        version_lbl.pack(side="right")

    # --- Unit Toggle & Re-rendering ---

    def toggle_unit(self):
        """Toggle between Celsius and Fahrenheit and refresh UI immediately."""
        self.current_unit = "F" if self.current_unit == "C" else "C"
        self.unit_btn.config(text=f"Unit: °{self.current_unit}")
        save_config({"default_unit": self.current_unit})

        if self.weather_data:
            self._render_weather_data()

    # --- Search & Network Call Management ---

    def on_search_clicked(self):
        query = self.city_entry.get().strip()
        self.search_weather(query)

    def on_auto_detect_clicked(self):
        if self.is_loading:
            return

        self.is_loading = True
        self.auto_btn.config(state="disabled", text="📍 Detecting...")
        self.show_banner("Detecting location via IP...", is_info=True)

        def worker():
            try:
                city = detect_user_location()
                self.root.after(0, lambda: self._on_location_detected(city))
            except Exception as e:
                self.root.after(0, lambda: self._on_location_detect_failed(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_location_detected(self, city: str):
        self.is_loading = False
        self.auto_btn.config(state="normal", text="📍 Auto Detect")
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city)
        self.search_weather(city)

    def _on_location_detect_failed(self, err_msg: str):
        self.is_loading = False
        self.auto_btn.config(state="normal", text="📍 Auto Detect")
        self.show_banner(f"Auto-detection failed: {err_msg}", is_error=True)

    def search_weather(self, query: str):
        if self.is_loading:
            return

        if not query or not query.strip():
            self.show_banner("Input validation error: Please enter a city name or ZIP code.", is_error=True)
            return

        self.is_loading = True
        self.search_btn.config(state="disabled", text="Fetching...")
        self.show_banner(f"Fetching weather data for '{query}'...", is_info=True)

        def worker():
            try:
                data = fetch_weather_data(query)
                self.root.after(0, lambda: self._on_fetch_success(data, query))
            except ValidationError as e:
                self.root.after(0, lambda: self._on_fetch_error(f"Validation Error: {str(e)}"))
            except CityNotFoundError as e:
                self.root.after(0, lambda: self._on_fetch_error(str(e)))
            except InvalidApiKeyError as e:
                self.root.after(0, lambda: self._on_fetch_error(
                    f"{str(e)} Click '⚙ API Key' in the header to enter your free OpenWeatherMap key."
                ))
            except NetworkError as e:
                self.root.after(0, lambda: self._on_fetch_error(f"Network Error: {str(e)}"))
            except RateLimitError as e:
                self.root.after(0, lambda: self._on_fetch_error(str(e)))
            except WeatherAppError as e:
                self.root.after(0, lambda: self._on_fetch_error(f"Weather Error: {str(e)}"))
            except Exception as e:
                self.root.after(0, lambda: self._on_fetch_error(f"Unexpected error: {str(e)}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_fetch_success(self, data: WeatherData, query: str):
        self.is_loading = False
        self.search_btn.config(state="normal", text="Get Weather")
        self.weather_data = data
        save_config({"last_city": query})

        if data.current.is_demo:
            self.show_banner(
                "Running in DEMO Preview mode (no API key configured). Set your free key under '⚙ API Key' for real-time live data.",
                is_info=True
            )
        else:
            self.hide_banner()

        self._render_weather_data()

    def _on_fetch_error(self, message: str):
        self.is_loading = False
        self.search_btn.config(state="normal", text="Get Weather")
        self.show_banner(message, is_error=True)

    # --- UI Rendering ---

    def _render_weather_data(self):
        if not self.weather_data:
            return

        curr = self.weather_data.current
        is_f = (self.current_unit == "F")

        # 1. Location & Demo Badge
        country_part = f", {curr.country}" if curr.country else ""
        self.location_lbl.config(text=f"{curr.city}{country_part}")
        self.date_lbl.config(text=curr.formatted_time)

        if curr.is_demo:
            self.demo_badge_lbl.pack(side="left", padx=(10, 0))
        else:
            self.demo_badge_lbl.pack_forget()

        # 2. Main Temperature & Condition
        temp_val = curr.temp_f if is_f else curr.temp_c
        self.temp_lbl.config(text=f"{temp_val:.1f}°{self.current_unit}")
        self.condition_lbl.config(text=f"{curr.condition} • {curr.description}")

        # 3. Metrics
        feels_val = curr.feels_like_f if is_f else curr.feels_like_c
        self.card_feels.config(text=f"{feels_val:.1f}°{self.current_unit}")
        self.card_humidity.config(text=f"{curr.humidity}%")

        if is_f:
            self.card_wind.config(text=f"{curr.wind_speed_mph} mph")
        else:
            self.card_wind.config(text=f"{curr.wind_speed_mps} m/s")

        self.card_pressure.config(text=f"{curr.pressure_hpa} hPa")

        # 4. Weather Icon for Current Condition
        self._load_icon_async(curr.icon_code, curr.condition, (90, 90), self.icon_lbl)

        # 5. Render Hourly Cards
        self._render_hourly_panel()

        # 6. Render Daily Cards
        self._render_daily_panel()

    def _load_icon_async(self, icon_code: str, condition: str, size, target_lbl: tk.Label):
        cache_key = f"{icon_code}_{size[0]}x{size[1]}"
        if cache_key in self.icon_photo_cache:
            target_lbl.config(image=self.icon_photo_cache[cache_key])
            return

        def worker():
            pil_img = get_weather_icon(icon_code, condition, size)
            photo = ImageTk.PhotoImage(pil_img)
            self.icon_photo_cache[cache_key] = photo

            def update_lbl():
                if target_lbl.winfo_exists():
                    target_lbl.config(image=photo)
            self.root.after(0, update_lbl)

        threading.Thread(target=worker, daemon=True).start()

    def _render_hourly_panel(self):
        # Clear existing cards
        for widget in self.hourly_container.winfo_children():
            widget.destroy()

        if not self.weather_data or not self.weather_data.hourly:
            empty_lbl = tk.Label(
                self.hourly_container,
                text="Hourly forecast details unavailable.",
                font=("Segoe UI", 9),
                fg=TEXT_MUTED,
                bg=BG_COLOR
            )
            empty_lbl.pack(anchor="w")
            return

        is_f = (self.current_unit == "F")

        # Show up to 4 intervals (covers next 6 to 12 hours)
        items = self.weather_data.hourly[:4]
        for item in items:
            card = tk.Frame(self.hourly_container, bg=PANEL_BG, bd=1, relief="solid", padx=10, pady=8)
            card.pack(side="left", fill="both", expand=True, padx=4)

            time_lbl = tk.Label(card, text=item.time_str, font=("Segoe UI", 9, "bold"), fg=TEXT_MUTED, bg=PANEL_BG)
            time_lbl.pack(anchor="center")

            icon_lbl = tk.Label(card, bg=PANEL_BG)
            icon_lbl.pack(anchor="center", pady=2)
            self._load_icon_async(item.icon_code, item.condition, (42, 42), icon_lbl)

            temp_val = item.temp_f if is_f else item.temp_c
            temp_lbl = tk.Label(card, text=f"{temp_val:.1f}°", font=("Segoe UI", 11, "bold"), fg=TEXT_MAIN, bg=PANEL_BG)
            temp_lbl.pack(anchor="center")

            cond_lbl = tk.Label(card, text=item.condition, font=("Segoe UI", 8), fg=ACCENT_BLUE, bg=PANEL_BG)
            cond_lbl.pack(anchor="center")

    def _render_daily_panel(self):
        for widget in self.daily_container.winfo_children():
            widget.destroy()

        if not self.weather_data or not self.weather_data.daily:
            empty_lbl = tk.Label(
                self.daily_container,
                text="5-day forecast details unavailable.",
                font=("Segoe UI", 9),
                fg=TEXT_MUTED,
                bg=BG_COLOR
            )
            empty_lbl.pack(anchor="w")
            return

        is_f = (self.current_unit == "F")
        days = self.weather_data.daily[:5]

        for day in days:
            row = tk.Frame(self.daily_container, bg=PANEL_BG, bd=1, relief="solid", padx=14, pady=6)
            row.pack(fill="x", pady=3)

            day_lbl = tk.Label(row, text=day.day_name, font=("Segoe UI", 10, "bold"), fg=TEXT_MAIN, bg=PANEL_BG, width=10, anchor="w")
            day_lbl.pack(side="left")

            date_lbl = tk.Label(row, text=day.date_str, font=("Segoe UI", 9), fg=TEXT_MUTED, bg=PANEL_BG, width=8, anchor="w")
            date_lbl.pack(side="left")

            icon_lbl = tk.Label(row, bg=PANEL_BG)
            icon_lbl.pack(side="left", padx=10)
            self._load_icon_async(day.icon_code, day.condition, (32, 32), icon_lbl)

            cond_lbl = tk.Label(row, text=day.condition, font=("Segoe UI", 9), fg=TEXT_MAIN, bg=PANEL_BG, width=16, anchor="w")
            cond_lbl.pack(side="left")

            min_val = day.temp_min_f if is_f else day.temp_min_c
            max_val = day.temp_max_f if is_f else day.temp_max_c
            temp_range = f"{min_val:.1f}° / {max_val:.1f}°{self.current_unit}"

            temps_lbl = tk.Label(row, text=temp_range, font=("Segoe UI", 10, "bold"), fg=ACCENT_BLUE, bg=PANEL_BG)
            temps_lbl.pack(side="right")

    # --- Settings / API Key Modal ---

    def open_settings_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("OpenWeatherMap API Key Settings")
        modal.geometry("540x360")
        modal.resizable(False, False)
        modal.configure(bg=BG_COLOR)
        modal.transient(self.root)
        modal.grab_set()

        inner = tk.Frame(modal, bg=BG_COLOR, padx=25, pady=20)
        inner.pack(fill="both", expand=True)

        title = tk.Label(
            inner,
            text="API Configuration",
            font=("Segoe UI", 14, "bold"),
            fg=TEXT_MAIN,
            bg=BG_COLOR
        )
        title.pack(anchor="w")

        info_text = (
            "To get live real-time weather and forecasts:\n"
            "1. Register free at: https://openweathermap.org/api\n"
            "2. Copy your 32-character API key from your profile.\n"
            "3. Paste it below and click 'Save Key'.\n"
            "(If left blank, the app will run in Demo Preview mode)."
        )
        info_lbl = tk.Label(
            inner,
            text=info_text,
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_COLOR,
            justify="left"
        )
        info_lbl.pack(anchor="w", pady=(8, 15))

        # API Key entry
        key_lbl = tk.Label(inner, text="API Key:", font=("Segoe UI", 9, "bold"), fg=TEXT_MAIN, bg=BG_COLOR)
        key_lbl.pack(anchor="w")

        current_key = get_api_key()
        key_entry = tk.Entry(
            inner,
            font=("Segoe UI", 10),
            bg=CARD_BG,
            fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            relief="flat",
            bd=5
        )
        key_entry.pack(fill="x", pady=(4, 15))
        key_entry.insert(0, current_key)

        # Action Buttons
        btn_box = tk.Frame(inner, bg=BG_COLOR)
        btn_box.pack(fill="x", pady=10)

        def save_and_close():
            new_key = key_entry.get().strip()
            set_api_key(new_key)
            modal.destroy()
            self.show_banner(
                "API key updated successfully. Refreshing weather..." if new_key else "API key cleared. Reverted to Demo mode.",
                is_info=True
            )
            # Re-fetch current city
            if self.city_entry.get().strip():
                self.search_weather(self.city_entry.get().strip())

        save_btn = tk.Button(
            btn_box,
            text="Save Key",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_BLUE,
            fg="#0F172A",
            activebackground=ACCENT_CYAN,
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=save_and_close
        )
        save_btn.pack(side="left", padx=(0, 8))

        cancel_btn = tk.Button(
            btn_box,
            text="Cancel",
            font=("Segoe UI", 10),
            bg=CARD_BG,
            fg=TEXT_MAIN,
            activebackground=CARD_HOVER,
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=modal.destroy
        )
        cancel_btn.pack(side="left")


def main():
    root = tk.Tk()
    app = WeatherAppGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

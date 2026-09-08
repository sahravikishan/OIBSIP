"""
Weather GUI - Advanced Tier Graphical User Interface.
Built with Tkinter and Pillow.

Features:
- Search by city name or ZIP code
- Automatic location detection via IP (ipinfo.io / ip-api)
- Unit toggle: Celsius (°C) and Fahrenheit (°F) with instant re-render
- Theme toggle: Enhanced Dark Mode (Obsidian & Neon Glow) & Light Mode (Clean Azure)
- Dynamic Weather Ambience: Canvas particle animations matching live conditions (Rain, Snow, Clouds, Clear)
- Real-Time Digital Clock: Live ticking clock with UTC and local time updates
- Live Radar Pulsing Badge: Animated breathing status indicators (LIVE DATA vs DEMO PREVIEW)
- Interactive Hover Glow: Elevated interactive animations on all cards, forecast rows, and buttons
- Custom vector-quality graphical icons for all UI controls (no emojis used)
- Hourly forecast panel (next 6-9 hours) with timestamps and temperature cards
- 5-Day daily forecast panel with min/max temperature range bars and condition badges
- In-GUI error and status banners (no terminal crashes)
- Settings modal for saving and managing OpenWeatherMap API key
- Non-blocking background threads for snappy, responsive UI
"""

import math
import random
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional, Dict, Tuple, List, Any
from PIL import Image, ImageTk

from config import get_api_key, set_api_key, get_config, save_config
from icon_assets import create_icon
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

# --- Dual Theme Palettes with Elevated Dark Mode ---
THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "name": "dark",
        "toggle_label": "Light",
        "bg": "#090D16",            # Deep Obsidian Navy
        "panel_bg": "#131C2E",      # Elevated Slate Surface
        "panel_border": "#23334D",  # Subtle Border
        "panel_hover_border": "#38BDF8", # Glowing Cyan Accent on Hover
        "card_bg": "#101826",       # Inner Card Background
        "card_hover": "#1C2A40",    # Card Hover Surface
        "card_surface": "#162035",  # Hourly / Daily Card Surfaces
        "accent": "#38BDF8",        # Vivid Neon Sky Blue
        "accent_hover": "#7DD3FC",  # Luminous Sky
        "accent_text": "#090D16",   # Deep Contrast Text on Accent
        "text_main": "#F8FAFC",     # Crisp White Text
        "text_muted": "#94A3B8",    # Muted Slate Text
        "text_subtle": "#64748B",   # Secondary Label Text
        "input_bg": "#0B111E",      # Deep Input Field
        "input_fg": "#F8FAFC",
        "btn_bg": "#1A263B",        # Polished Dark Button
        "btn_fg": "#F1F5F9",
        "btn_border": "#2D405E",
        "btn_hover": "#253754",     # Button Hover Glow
        "btn_hover_border": "#38BDF8",
        "badge_demo_bg": "#451A03", # Translucent Deep Amber
        "badge_demo_border": "#D97706",
        "badge_demo_fg": "#FDE68A", # Warm Gold
        "badge_live_bg": "#042F2E", # Translucent Deep Emerald
        "badge_live_border": "#059669",
        "badge_live_fg": "#6EE7B7", # Luminous Mint
        "metric_box_bg": "#121A29", # Metric Card Surface
        "metric_hover_bg": "#1A263B",
        "ambience_bg": "#0C1422",   # Particle Canvas Background
        "error_bg": "#7F1D1D",
        "error_text": "#FCA5A5",
        "info_bg": "#131C2E",
        "info_text": "#38BDF8",
        "success_bg": "#14532D",
        "success_text": "#86EFAC",
    },
    "light": {
        "name": "light",
        "toggle_label": "Dark",
        "bg": "#F8FAFC",            # Clean Soft Slate
        "panel_bg": "#FFFFFF",      # Pure White Container
        "panel_border": "#E2E8F0",  # Delicate Border
        "panel_hover_border": "#0284C7",
        "card_bg": "#F1F5F9",       # Soft Off-White Card Surface
        "card_hover": "#E2E8F0",
        "card_surface": "#FFFFFF",  # Hourly / Daily Card Surfaces
        "accent": "#0284C7",        # Ocean Azure
        "accent_hover": "#0369A1",
        "accent_text": "#FFFFFF",   # Crisp White on Accent
        "text_main": "#0F172A",     # Deep Slate Navy
        "text_muted": "#64748B",    # Slate 500
        "text_subtle": "#94A3B8",
        "input_bg": "#F8FAFC",
        "input_fg": "#0F172A",
        "btn_bg": "#F1F5F9",
        "btn_fg": "#0F172A",
        "btn_border": "#CBD5E1",
        "btn_hover": "#E2E8F0",
        "btn_hover_border": "#0284C7",
        "badge_demo_bg": "#FEF3C7",
        "badge_demo_border": "#F59E0B",
        "badge_demo_fg": "#92400E",
        "badge_live_bg": "#D1FAE5",
        "badge_live_border": "#10B981",
        "badge_live_fg": "#065F46",
        "metric_box_bg": "#F8FAFC",
        "metric_hover_bg": "#EDF2F7",
        "ambience_bg": "#F1F5F9",
        "error_bg": "#FEE2E2",
        "error_text": "#991B1B",
        "info_bg": "#E0F2FE",
        "info_text": "#0369A1",
        "success_bg": "#DCFCE7",
        "success_text": "#166534",
    }
}


class WeatherAppGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SkyCast - Real-Time Weather Application")
        self.root.geometry("860x780")
        self.root.minsize(780, 560)

        # Load preferences
        config = get_config()
        self.current_unit = config.get("default_unit", "C")
        self.theme_name = config.get("theme", "dark")
        if self.theme_name not in THEMES:
            self.theme_name = "dark"
        self.t = THEMES[self.theme_name]

        self.root.configure(bg=self.t["bg"])

        # State
        self.weather_data: Optional[WeatherData] = None
        self.icon_photo_cache: Dict[str, ImageTk.PhotoImage] = {}
        self.ui_photos: Dict[str, ImageTk.PhotoImage] = {}
        self.is_loading = False
        self.pulse_state = False
        self.active_tab = "all"  # 'all', 'hourly', 'daily'

        # Particle Animation Engine state
        self.particles: List[Dict[str, Any]] = []
        self.current_weather_type = "clear"  # 'clear', 'rain', 'clouds', 'snow'
        self.anim_running = True

        # Build UI
        self._build_header()
        self._build_search_bar()
        self._build_notification_banner()
        self._build_nav_tabs()
        self._build_main_content()
        self._build_footer()

        # Apply initial theme
        self.apply_theme()

        # Start Dynamic Background Loops
        self._init_particles()
        self._tick_ambience()
        self._tick_clock_and_pulse()

        # Auto-load initial weather
        last_city = config.get("last_city", "London")
        self.city_entry.insert(0, last_city)
        self.root.after(100, lambda: self.search_weather(last_city))

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.anim_running = False
        self.root.destroy()

    # --- UI Graphical Icon Manager ---

    def get_ui_photo(self, name: str, color_hex: str, size: Tuple[int, int] = (20, 20)) -> ImageTk.PhotoImage:
        """Returns or creates a cached PhotoImage for a graphical icon with exact theme color."""
        cache_key = f"{name}_{color_hex}_{size[0]}x{size[1]}"
        if cache_key not in self.ui_photos:
            pil_img = create_icon(name, color_hex, size)
            self.ui_photos[cache_key] = ImageTk.PhotoImage(pil_img)
        return self.ui_photos[cache_key]

    # --- Interactive Hover Glow Helper ---

    def _bind_hover_effect(self, widget, default_bg, hover_bg, default_border=None, hover_border=None):
        """Binds responsive hover glow and elevation effect to any interactive widget."""
        def on_enter(event):
            try:
                if widget.winfo_exists():
                    widget.configure(bg=hover_bg)
                    if hover_border and "highlightbackground" in widget.keys():
                        widget.configure(highlightbackground=hover_border)
            except Exception:
                pass

        def on_leave(event):
            try:
                if widget.winfo_exists():
                    widget.configure(bg=default_bg)
                    if default_border and "highlightbackground" in widget.keys():
                        widget.configure(highlightbackground=default_border)
            except Exception:
                pass

        widget.bind("<Enter>", on_enter, add="+")
        widget.bind("<Leave>", on_leave, add="+")

    # --- Theme Switching Engine ---

    def toggle_theme(self):
        """Switches between Dark and Light mode instantly."""
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.t = THEMES[self.theme_name]
        save_config({"theme": self.theme_name})
        self.apply_theme()

        # Re-render weather if data exists so forecast cards match the new theme
        if self.weather_data:
            self._render_weather_data()

    def apply_theme(self):
        """Applies colors and graphical icons from current theme palette across all widgets."""
        t = self.t

        # Root Window
        self.root.configure(bg=t["bg"])

        # Header section
        self.header_frame.configure(bg=t["bg"])
        self.title_box.configure(bg=t["bg"])
        self.logo_lbl.configure(
            bg=t["bg"],
            image=self.get_ui_photo("logo", t["accent"], (34, 34))
        )
        self.title_lbl.configure(bg=t["bg"], fg=t["text_main"])
        self.subtitle_lbl.configure(bg=t["bg"], fg=t["text_muted"])
        self.controls_box.configure(bg=t["bg"])

        # Header Buttons with Graphical Icons and Dark Mode borders
        theme_icon_name = "sun" if self.theme_name == "dark" else "moon"
        self.theme_btn.configure(
            text=f" {t['toggle_label']}",
            image=self.get_ui_photo(theme_icon_name, t["btn_fg"], (16, 16)),
            compound="left",
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            highlightbackground=t["btn_border"],
            highlightcolor=t["btn_hover_border"],
            activebackground=t["btn_hover"],
            activeforeground=t["btn_fg"]
        )
        self._bind_hover_effect(self.theme_btn, t["btn_bg"], t["btn_hover"], t["btn_border"], t["btn_hover_border"])

        self.unit_btn.configure(
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            highlightbackground=t["btn_border"],
            highlightcolor=t["btn_hover_border"],
            activebackground=t["btn_hover"],
            activeforeground=t["btn_fg"]
        )
        self._bind_hover_effect(self.unit_btn, t["btn_bg"], t["btn_hover"], t["btn_border"], t["btn_hover_border"])

        self.settings_btn.configure(
            text=" API Key",
            image=self.get_ui_photo("gear", t["btn_fg"], (16, 16)),
            compound="left",
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            highlightbackground=t["btn_border"],
            highlightcolor=t["btn_hover_border"],
            activebackground=t["btn_hover"],
            activeforeground=t["btn_fg"]
        )
        self._bind_hover_effect(self.settings_btn, t["btn_bg"], t["btn_hover"], t["btn_border"], t["btn_hover_border"])

        # Search Bar
        self.search_frame.configure(bg=t["panel_bg"], highlightbackground=t["panel_border"])
        self.search_inner.configure(bg=t["panel_bg"])
        self.search_icon_lbl.configure(
            bg=t["panel_bg"],
            image=self.get_ui_photo("search", t["text_muted"], (18, 18))
        )
        self.city_entry.configure(
            bg=t["input_bg"],
            fg=t["input_fg"],
            insertbackground=t["text_main"],
            highlightbackground=t["panel_border"],
            highlightcolor=t["accent"]
        )
        self.search_btn.configure(
            bg=t["accent"],
            fg=t["accent_text"],
            activebackground=t["accent_hover"],
            activeforeground=t["accent_text"]
        )
        self._bind_hover_effect(self.search_btn, t["accent"], t["accent_hover"])

        self.auto_btn.configure(
            text=" Auto Detect",
            image=self.get_ui_photo("location", t["btn_fg"], (16, 16)),
            compound="left",
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            highlightbackground=t["btn_border"],
            activebackground=t["btn_hover"],
            activeforeground=t["btn_fg"]
        )
        self._bind_hover_effect(self.auto_btn, t["btn_bg"], t["btn_hover"], t["btn_border"], t["btn_hover_border"])

        # Notification Banner container
        self.banner_frame.configure(bg=t["bg"])

        # Nav Tabs Bar
        if hasattr(self, "nav_tabs_frame"):
            self.nav_tabs_frame.configure(bg=t["bg"])
            self._update_tab_styles()

        # Main Scrollable Container & Canvas
        if hasattr(self, "scroll_container"):
            self.scroll_container.configure(bg=t["bg"])
            self.scroll_canvas.configure(bg=t["bg"])
        self.content_frame.configure(bg=t["bg"])

        # Hero Card & Ambience Canvas
        self.hero_card.configure(bg=t["panel_bg"], highlightbackground=t["panel_border"])
        self.ambience_canvas.configure(bg=t["ambience_bg"], highlightbackground=t["panel_border"])
        self.hero_inner.configure(bg=t["panel_bg"])
        self.hero_header.configure(bg=t["panel_bg"])
        self.location_lbl.configure(bg=t["panel_bg"], fg=t["text_main"])
        self.date_lbl.configure(bg=t["panel_bg"], fg=t["text_muted"])

        # Hero Temperature & Condition
        self.temp_row.configure(bg=t["panel_bg"])
        self.icon_lbl.configure(bg=t["panel_bg"])
        self.temp_col.configure(bg=t["panel_bg"])
        self.temp_lbl.configure(bg=t["panel_bg"], fg=t["text_main"])
        self.condition_lbl.configure(bg=t["panel_bg"], fg=t["accent"])

        # Metric Cards Grid with Graphical Icons & Hover Glow
        self.metrics_grid.configure(bg=t["panel_bg"])
        metric_configs = [
            ("thermometer", "FEELS LIKE"),
            ("droplet", "HUMIDITY"),
            ("wind", "WIND SPEED"),
            ("barometer", "PRESSURE")
        ]
        for idx, (box, header_line, icon_lbl, title_lbl, val_lbl) in enumerate(self.metric_widgets):
            icon_name, metric_title = metric_configs[idx]
            box.configure(bg=t["metric_box_bg"], highlightbackground=t["panel_border"])
            header_line.configure(bg=t["metric_box_bg"])
            icon_lbl.configure(
                bg=t["metric_box_bg"],
                image=self.get_ui_photo(icon_name, t["accent"], (18, 18))
            )
            title_lbl.configure(bg=t["metric_box_bg"], fg=t["text_muted"], text=metric_title)
            val_lbl.configure(bg=t["metric_box_bg"], fg=t["text_main"])

            # Attach interactive hover elevation
            self._bind_hover_effect(box, t["metric_box_bg"], t["metric_hover_bg"], t["panel_border"], t["panel_hover_border"])

        # Hourly Section with Clock Icon
        self.hourly_section.configure(bg=t["bg"])
        self.hourly_title.configure(
            bg=t["bg"],
            fg=t["text_main"],
            image=self.get_ui_photo("clock", t["accent"], (16, 16)),
            compound="left",
            text=" Hourly Timeline (Next Hours)"
        )
        self.hourly_container.configure(bg=t["bg"])

        # Daily Section with Calendar Icon
        self.daily_section.configure(bg=t["bg"])
        self.daily_title.configure(
            bg=t["bg"],
            fg=t["text_main"],
            image=self.get_ui_photo("calendar", t["accent"], (16, 16)),
            compound="left",
            text=" 5-Day Daily Outlook"
        )
        self.daily_container.configure(bg=t["bg"])

        # Footer
        self.footer_frame.configure(bg=t["bg"])
        self.status_lbl.configure(bg=t["bg"], fg=t["text_muted"])
        self.live_clock_lbl.configure(bg=t["bg"], fg=t["text_muted"])
        self.version_lbl.configure(bg=t["bg"], fg=t["accent"])

    # --- UI Construction ---

    def _build_header(self):
        self.header_frame = tk.Frame(self.root, bg=self.t["bg"])
        self.header_frame.pack(fill="x", padx=24, pady=(16, 8))

        # Title & Subtitle Box
        self.title_box = tk.Frame(self.header_frame, bg=self.t["bg"])
        self.title_box.pack(side="left")

        # Logo and Title row
        title_row = tk.Frame(self.title_box, bg=self.t["bg"])
        title_row.pack(anchor="w")

        self.logo_lbl = tk.Label(title_row, bg=self.t["bg"])
        self.logo_lbl.pack(side="left", padx=(0, 10))

        self.title_lbl = tk.Label(
            title_row,
            text="SkyCast Weather",
            font=("Segoe UI", 20, "bold"),
            fg=self.t["text_main"],
            bg=self.t["bg"]
        )
        self.title_lbl.pack(side="left")

        self.subtitle_lbl = tk.Label(
            self.title_box,
            text="Real-Time Weather Intelligence • Hourly & 5-Day Forecasts",
            font=("Segoe UI", 9),
            fg=self.t["text_muted"],
            bg=self.t["bg"]
        )
        self.subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # Right Controls (Theme Toggle, Unit Toggle, Settings)
        self.controls_box = tk.Frame(self.header_frame, bg=self.t["bg"])
        self.controls_box.pack(side="right", pady=4)

        # Theme Toggle Button
        self.theme_btn = tk.Button(
            self.controls_box,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            highlightthickness=1,
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.toggle_theme
        )
        self.theme_btn.pack(side="left", padx=4)

        # Unit Toggle Button
        self.unit_btn = tk.Button(
            self.controls_box,
            text=f"°{self.current_unit}",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            highlightthickness=1,
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.toggle_unit
        )
        self.unit_btn.pack(side="left", padx=4)

        # Settings Button
        self.settings_btn = tk.Button(
            self.controls_box,
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            highlightthickness=1,
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.open_settings_modal
        )
        self.settings_btn.pack(side="left", padx=4)

    def _build_search_bar(self):
        self.search_frame = tk.Frame(
            self.root,
            bg=self.t["panel_bg"],
            highlightthickness=1,
            highlightbackground=self.t["panel_border"]
        )
        self.search_frame.pack(fill="x", padx=24, pady=8)

        self.search_inner = tk.Frame(self.search_frame, bg=self.t["panel_bg"])
        self.search_inner.pack(fill="x", padx=10, pady=8)

        self.search_icon_lbl = tk.Label(
            self.search_inner,
            bg=self.t["panel_bg"]
        )
        self.search_icon_lbl.pack(side="left", padx=(4, 8))

        # Search Entry Field
        self.city_entry = tk.Entry(
            self.search_inner,
            font=("Segoe UI", 11),
            bg=self.t["input_bg"],
            fg=self.t["input_fg"],
            insertbackground=self.t["text_main"],
            relief="flat",
            bd=5,
            highlightthickness=1,
            highlightbackground=self.t["panel_border"]
        )
        self.city_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.city_entry.bind("<Return>", lambda event: self.on_search_clicked())

        # Get Weather Button
        self.search_btn = tk.Button(
            self.search_inner,
            text="Get Weather",
            font=("Segoe UI", 10, "bold"),
            bg=self.t["accent"],
            fg=self.t["accent_text"],
            activebackground=self.t["accent_hover"],
            relief="flat",
            bd=0,
            padx=18,
            pady=6,
            cursor="hand2",
            command=self.on_search_clicked
        )
        self.search_btn.pack(side="left", padx=4)

        # Auto Detect Button
        self.auto_btn = tk.Button(
            self.search_inner,
            font=("Segoe UI", 10),
            bg=self.t["btn_bg"],
            fg=self.t["btn_fg"],
            activebackground=self.t["btn_hover"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.on_auto_detect_clicked
        )
        self.auto_btn.pack(side="left", padx=4)

    def _build_notification_banner(self):
        self.banner_frame = tk.Frame(self.root, bg=self.t["bg"])
        self.banner_frame.pack(fill="x", padx=24, pady=(2, 6))

        self.banner_lbl = tk.Label(
            self.banner_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            wraplength=780,
            justify="left",
            padx=14,
            pady=7
        )

    def show_banner(self, message: str, is_error: bool = False, is_info: bool = False):
        t = self.t
        self.banner_lbl.config(
            text=message,
            bg=t["error_bg"] if is_error else (t["info_bg"] if is_info else t["success_bg"]),
            fg=t["error_text"] if is_error else (t["info_text"] if is_info else t["success_text"])
        )
        self.banner_lbl.pack(fill="x")

    def hide_banner(self):
        self.banner_lbl.pack_forget()

    def _build_nav_tabs(self):
        """Segmented navigation tabs allowing user to view All, Hourly, or 5-Day forecast."""
        self.nav_tabs_frame = tk.Frame(self.root, bg=self.t["bg"])
        self.nav_tabs_frame.pack(fill="x", padx=24, pady=(2, 6))

        nav_inner = tk.Frame(self.nav_tabs_frame, bg=self.t["bg"])
        nav_inner.pack(side="left")

        # Tab: Overview (All)
        self.tab_all_btn = tk.Button(
            nav_inner,
            text=" Overview (All)",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            highlightthickness=1,
            padx=14,
            pady=5,
            cursor="hand2",
            command=lambda: self.select_tab("all")
        )
        self.tab_all_btn.pack(side="left", padx=(0, 6))

        # Tab: Hourly (Next Hours)
        self.tab_hourly_btn = tk.Button(
            nav_inner,
            text=" Hourly Forecast",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            highlightthickness=1,
            padx=14,
            pady=5,
            cursor="hand2",
            command=lambda: self.select_tab("hourly")
        )
        self.tab_hourly_btn.pack(side="left", padx=(0, 6))

        # Tab: 5-Day Outlook (Daily)
        self.tab_daily_btn = tk.Button(
            nav_inner,
            text=" 5-Day Outlook",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            highlightthickness=1,
            padx=14,
            pady=5,
            cursor="hand2",
            command=lambda: self.select_tab("daily")
        )
        self.tab_daily_btn.pack(side="left")

        # Right tip label
        scroll_tip = tk.Label(
            self.nav_tabs_frame,
            text="Tip: Scroll with mouse wheel or select tabs",
            font=("Segoe UI", 8),
            fg=self.t["text_subtle"],
            bg=self.t["bg"]
        )
        scroll_tip.pack(side="right", pady=4)

    def select_tab(self, tab_name: str):
        """Switches visible view sections between All, Hourly, and 5-Day Outlook."""
        self.active_tab = tab_name
        self._update_tab_styles()

        if not hasattr(self, "hero_card") or not hasattr(self, "scroll_canvas"):
            return

        if tab_name == "all":
            self.hero_card.pack(fill="x", pady=(0, 10))
            self.hourly_section.pack(fill="x", pady=(4, 8))
            self.daily_section.pack(fill="both", expand=True, pady=(4, 10))
            self.scroll_canvas.yview_moveto(0)
        elif tab_name == "hourly":
            self.hero_card.pack(fill="x", pady=(0, 10))
            self.hourly_section.pack(fill="x", pady=(4, 8))
            self.daily_section.pack_forget()
            self.scroll_canvas.yview_moveto(0)
        elif tab_name == "daily":
            self.hero_card.pack(fill="x", pady=(0, 10))
            self.hourly_section.pack_forget()
            self.daily_section.pack(fill="both", expand=True, pady=(4, 10))
            self.scroll_canvas.yview_moveto(0)

        self.root.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _update_tab_styles(self):
        """Updates active tab highlight colors according to active theme."""
        t = self.t
        tabs = [
            ("all", self.tab_all_btn),
            ("hourly", self.tab_hourly_btn),
            ("daily", self.tab_daily_btn)
        ]
        for name, btn in tabs:
            if self.active_tab == name:
                btn.configure(
                    bg=t["accent"],
                    fg=t["accent_text"],
                    highlightbackground=t["accent"],
                    activebackground=t["accent_hover"],
                    activeforeground=t["accent_text"]
                )
            else:
                btn.configure(
                    bg=t["btn_bg"],
                    fg=t["btn_fg"],
                    highlightbackground=t["btn_border"],
                    activebackground=t["btn_hover"],
                    activeforeground=t["btn_fg"]
                )

    def _build_main_content(self):
        """Builds scrollable main canvas with vertical scrollbar and mouse-wheel support."""
        self.scroll_container = tk.Frame(self.root, bg=self.t["bg"])
        self.scroll_container.pack(fill="both", expand=True, padx=(24, 8), pady=2)

        # Scroll Canvas
        self.scroll_canvas = tk.Canvas(
            self.scroll_container,
            bg=self.t["bg"],
            bd=0,
            highlightthickness=0
        )

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.scroll_container,
            orient="vertical",
            command=self.scroll_canvas.yview
        )
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y", padx=(2, 0))
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        # Inner content frame placed on canvas
        self.content_frame = tk.Frame(self.scroll_canvas, bg=self.t["bg"])
        self.canvas_window = self.scroll_canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw"
        )

        # Dynamic resizing bindings
        def on_frame_configure(event):
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

        def on_canvas_configure(event):
            # Keep content_frame width matching canvas width minus margin
            self.scroll_canvas.itemconfig(self.canvas_window, width=event.width)

        self.content_frame.bind("<Configure>", on_frame_configure)
        self.scroll_canvas.bind("<Configure>", on_canvas_configure)

        # Mouse wheel scrolling bindings (Windows + Linux)
        def _on_mousewheel(event):
            if not self.root.winfo_exists():
                return
            if event.delta:
                self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                self.scroll_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.scroll_canvas.yview_scroll(1, "units")

        self.root.bind_all("<MouseWheel>", _on_mousewheel)
        self.root.bind_all("<Button-4>", _on_mousewheel)
        self.root.bind_all("<Button-5>", _on_mousewheel)

        # 1. Current Weather Hero Card Container
        self.hero_card = tk.Frame(
            self.content_frame,
            bg=self.t["panel_bg"],
            highlightthickness=1,
            highlightbackground=self.t["panel_border"]
        )
        self.hero_card.pack(fill="x", pady=(0, 10))

        # Dynamic Weather Ambience Header Canvas (Animated Particles matching Live Condition)
        self.ambience_canvas = tk.Canvas(
            self.hero_card,
            height=36,
            bg=self.t["ambience_bg"],
            bd=0,
            highlightthickness=0
        )
        self.ambience_canvas.pack(fill="x")

        self.hero_inner = tk.Frame(self.hero_card, bg=self.t["panel_bg"])
        self.hero_inner.pack(fill="x", padx=20, pady=(8, 14))

        # Top section: Location & Badge & Date
        self.hero_header = tk.Frame(self.hero_inner, bg=self.t["panel_bg"])
        self.hero_header.pack(fill="x")

        self.location_lbl = tk.Label(
            self.hero_header,
            text="Ready to search",
            font=("Segoe UI", 18, "bold"),
            fg=self.t["text_main"],
            bg=self.t["panel_bg"]
        )
        self.location_lbl.pack(side="left")

        # Modern Status Pill Badge with animated breathing dot
        self.status_badge_lbl = tk.Label(
            self.hero_header,
            text="",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            bd=0,
            highlightthickness=1,
            padx=10,
            pady=3
        )

        self.date_lbl = tk.Label(
            self.hero_header,
            text="",
            font=("Segoe UI", 9),
            fg=self.t["text_muted"],
            bg=self.t["panel_bg"]
        )
        self.date_lbl.pack(side="right")

        # Middle section: Weather Icon + Large Temperature + Condition text
        self.temp_row = tk.Frame(self.hero_inner, bg=self.t["panel_bg"])
        self.temp_row.pack(fill="x", pady=6)

        self.icon_lbl = tk.Label(self.temp_row, bg=self.t["panel_bg"])
        self.icon_lbl.pack(side="left", padx=(0, 16))

        self.temp_col = tk.Frame(self.temp_row, bg=self.t["panel_bg"])
        self.temp_col.pack(side="left")

        self.temp_lbl = tk.Label(
            self.temp_col,
            text="--°",
            font=("Segoe UI", 36, "bold"),
            fg=self.t["text_main"],
            bg=self.t["panel_bg"]
        )
        self.temp_lbl.pack(anchor="w")

        self.condition_lbl = tk.Label(
            self.temp_col,
            text="Enter a city to view current conditions",
            font=("Segoe UI", 11),
            fg=self.t["accent"],
            bg=self.t["panel_bg"]
        )
        self.condition_lbl.pack(anchor="w")

        # Bottom section: 4 Metric Cards (Feels Like, Humidity, Wind, Pressure)
        self.metrics_grid = tk.Frame(self.hero_inner, bg=self.t["panel_bg"])
        self.metrics_grid.pack(fill="x", pady=(8, 2))
        self.metrics_grid.columnconfigure(0, weight=1)
        self.metrics_grid.columnconfigure(1, weight=1)
        self.metrics_grid.columnconfigure(2, weight=1)
        self.metrics_grid.columnconfigure(3, weight=1)

        self.metric_widgets = []
        self.card_feels = self._create_metric_box(self.metrics_grid, 0, "thermometer", "FEELS LIKE", "--")
        self.card_humidity = self._create_metric_box(self.metrics_grid, 1, "droplet", "HUMIDITY", "--")
        self.card_wind = self._create_metric_box(self.metrics_grid, 2, "wind", "WIND SPEED", "--")
        self.card_pressure = self._create_metric_box(self.metrics_grid, 3, "barometer", "PRESSURE", "--")

        # 2. Hourly Forecast Section
        self.hourly_section = tk.Frame(self.content_frame, bg=self.t["bg"])
        self.hourly_section.pack(fill="x", pady=(4, 8))

        self.hourly_title = tk.Label(
            self.hourly_section,
            font=("Segoe UI", 11, "bold"),
            fg=self.t["text_main"],
            bg=self.t["bg"]
        )
        self.hourly_title.pack(anchor="w", pady=(0, 6))

        self.hourly_container = tk.Frame(self.hourly_section, bg=self.t["bg"])
        self.hourly_container.pack(fill="x")

        # 3. 5-Day Forecast Section
        self.daily_section = tk.Frame(self.content_frame, bg=self.t["bg"])
        self.daily_section.pack(fill="both", expand=True, pady=(4, 10))

        self.daily_title = tk.Label(
            self.daily_section,
            font=("Segoe UI", 11, "bold"),
            fg=self.t["text_main"],
            bg=self.t["bg"]
        )
        self.daily_title.pack(anchor="w", pady=(0, 6))

        self.daily_container = tk.Frame(self.daily_section, bg=self.t["bg"])
        self.daily_container.pack(fill="both", expand=True)

    def _create_metric_box(self, parent, col: int, icon_name: str, label_text: str, default_val: str) -> tk.Label:
        box = tk.Frame(
            parent,
            bg=self.t["metric_box_bg"],
            highlightthickness=1,
            highlightbackground=self.t["panel_border"],
            padx=10,
            pady=8
        )
        box.grid(row=0, column=col, padx=4, sticky="nsew")

        header_line = tk.Frame(box, bg=self.t["metric_box_bg"])
        header_line.pack(anchor="center")

        icon_lbl = tk.Label(
            header_line,
            bg=self.t["metric_box_bg"],
            image=self.get_ui_photo(icon_name, self.t["accent"], (16, 16))
        )
        icon_lbl.pack(side="left", padx=(0, 4))

        title = tk.Label(header_line, text=label_text, font=("Segoe UI", 8, "bold"), fg=self.t["text_muted"], bg=self.t["metric_box_bg"])
        title.pack(side="left")

        val_lbl = tk.Label(box, text=default_val, font=("Segoe UI", 11, "bold"), fg=self.t["text_main"], bg=self.t["metric_box_bg"])
        val_lbl.pack(anchor="center", pady=(4, 0))

        self.metric_widgets.append((box, header_line, icon_lbl, title, val_lbl))
        return val_lbl

    def _build_footer(self):
        self.footer_frame = tk.Frame(self.root, bg=self.t["bg"])
        self.footer_frame.pack(fill="x", padx=24, pady=(4, 12))

        self.status_lbl = tk.Label(
            self.footer_frame,
            text="Powered by OpenWeatherMap API",
            font=("Segoe UI", 8),
            fg=self.t["text_muted"],
            bg=self.t["bg"]
        )
        self.status_lbl.pack(side="left")

        self.live_clock_lbl = tk.Label(
            self.footer_frame,
            text="",
            font=("Segoe UI", 8),
            fg=self.t["text_muted"],
            bg=self.t["bg"]
        )
        self.live_clock_lbl.pack(side="left", padx=16)

        self.version_lbl = tk.Label(
            self.footer_frame,
            text="SkyCast v2.5 • Dynamic Edition",
            font=("Segoe UI", 8, "bold"),
            fg=self.t["accent"],
            bg=self.t["bg"]
        )
        self.version_lbl.pack(side="right")

    # --- Dynamic Weather Ambience & Particle System ---

    def _init_particles(self):
        """Initializes particle pool for ambient weather animations."""
        self.particles.clear()
        self.ambience_canvas.delete("all")
        width = 800
        height = 40

        for _ in range(25):
            self.particles.append({
                "x": random.uniform(0, width),
                "y": random.uniform(0, height),
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(1.2, 3.0),
                "size": random.uniform(1.5, 3.5),
                "alpha": random.uniform(0.3, 0.9),
                "id": None
            })

    def _set_weather_ambience(self, condition: str):
        """Adapts dynamic particle animation mode based on current weather condition."""
        cond = condition.lower()
        if "rain" in cond or "drizzle" in cond or "thunder" in cond:
            self.current_weather_type = "rain"
        elif "snow" in cond:
            self.current_weather_type = "snow"
        elif "cloud" in cond or "mist" in cond or "fog" in cond or "haze" in cond:
            self.current_weather_type = "clouds"
        else:
            self.current_weather_type = "clear"

        # Re-initialize particles for the selected type
        self.particles.clear()
        self.ambience_canvas.delete("all")
        width = max(self.ambience_canvas.winfo_width(), 800)
        height = 40

        count = 28 if self.current_weather_type in ("rain", "snow") else 16
        for _ in range(count):
            if self.current_weather_type == "rain":
                self.particles.append({
                    "x": random.uniform(0, width),
                    "y": random.uniform(0, height),
                    "vx": random.uniform(-0.4, 0.2),
                    "vy": random.uniform(3.5, 6.0),
                    "len": random.uniform(6, 12),
                    "id": None
                })
            elif self.current_weather_type == "snow":
                self.particles.append({
                    "x": random.uniform(0, width),
                    "y": random.uniform(0, height),
                    "vx": random.uniform(-0.6, 0.6),
                    "vy": random.uniform(0.8, 1.8),
                    "size": random.uniform(2, 4),
                    "phase": random.uniform(0, math.pi * 2),
                    "id": None
                })
            elif self.current_weather_type == "clouds":
                self.particles.append({
                    "x": random.uniform(0, width),
                    "y": random.uniform(8, height - 8),
                    "vx": random.uniform(0.3, 0.7),
                    "w": random.uniform(40, 80),
                    "h": random.uniform(14, 22),
                    "id": None
                })
            else:  # Clear / Radiant ambient dust
                self.particles.append({
                    "x": random.uniform(0, width),
                    "y": random.uniform(0, height),
                    "vx": random.uniform(-0.3, 0.3),
                    "vy": random.uniform(-0.4, 0.4),
                    "size": random.uniform(1.5, 3.0),
                    "phase": random.uniform(0, math.pi * 2),
                    "id": None
                })

    def _tick_ambience(self):
        """Runs the 30 FPS ambient particle animation loop."""
        if not self.anim_running or not self.root.winfo_exists():
            return

        try:
            width = max(self.ambience_canvas.winfo_width(), 800)
            height = 40
            t = self.t

            rain_color = "#38BDF8" if self.theme_name == "dark" else "#0284C7"
            snow_color = "#E0F2FE" if self.theme_name == "dark" else "#BAE6FD"
            cloud_color = "#1E293B" if self.theme_name == "dark" else "#E2E8F0"
            sun_beam = "#FDE047" if self.theme_name == "dark" else "#F59E0B"

            for p in self.particles:
                if self.current_weather_type == "rain":
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    if p["y"] > height:
                        p["y"] = 0
                        p["x"] = random.uniform(0, width)
                    if p["id"] is None:
                        p["id"] = self.ambience_canvas.create_line(
                            p["x"], p["y"], p["x"] + p["vx"] * 2, p["y"] + p["len"],
                            fill=rain_color, width=1
                        )
                    else:
                        self.ambience_canvas.coords(
                            p["id"], p["x"], p["y"], p["x"] + p["vx"] * 2, p["y"] + p["len"]
                        )
                        self.ambience_canvas.itemconfig(p["id"], fill=rain_color)

                elif self.current_weather_type == "snow":
                    p["phase"] += 0.05
                    p["x"] += p["vx"] + math.sin(p["phase"]) * 0.4
                    p["y"] += p["vy"]
                    if p["y"] > height:
                        p["y"] = 0
                        p["x"] = random.uniform(0, width)
                    s = p["size"]
                    if p["id"] is None:
                        p["id"] = self.ambience_canvas.create_oval(
                            p["x"] - s, p["y"] - s, p["x"] + s, p["y"] + s,
                            fill=snow_color, outline=""
                        )
                    else:
                        self.ambience_canvas.coords(
                            p["id"], p["x"] - s, p["y"] - s, p["x"] + s, p["y"] + s
                        )
                        self.ambience_canvas.itemconfig(p["id"], fill=snow_color)

                elif self.current_weather_type == "clouds":
                    p["x"] += p["vx"]
                    if p["x"] - p["w"] > width:
                        p["x"] = -p["w"]
                    if p["id"] is None:
                        p["id"] = self.ambience_canvas.create_oval(
                            p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"],
                            fill=cloud_color, outline=""
                        )
                    else:
                        self.ambience_canvas.coords(
                            p["id"], p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"]
                        )
                        self.ambience_canvas.itemconfig(p["id"], fill=cloud_color)

                else:  # Clear
                    p["phase"] += 0.04
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    if p["x"] < 0: p["x"] = width
                    if p["x"] > width: p["x"] = 0
                    if p["y"] < 0: p["y"] = height
                    if p["y"] > height: p["y"] = 0
                    s = p["size"] * (0.8 + 0.3 * math.sin(p["phase"]))
                    if p["id"] is None:
                        p["id"] = self.ambience_canvas.create_oval(
                            p["x"] - s, p["y"] - s, p["x"] + s, p["y"] + s,
                            fill=sun_beam, outline=""
                        )
                    else:
                        self.ambience_canvas.coords(
                            p["id"], p["x"] - s, p["y"] - s, p["x"] + s, p["y"] + s
                        )
                        self.ambience_canvas.itemconfig(p["id"], fill=sun_beam)
        except Exception:
            pass

        if self.anim_running and self.root.winfo_exists():
            self.root.after(35, self._tick_ambience)

    # --- Live Clock & Status Radar Pulsing Engine ---

    def _tick_clock_and_pulse(self):
        """Updates live digital clock and pulses the status radar indicator every 1000ms."""
        if not self.anim_running or not self.root.winfo_exists():
            return

        try:
            # 1. Update Live Digital Clock
            now_str = datetime.now().strftime("%I:%M:%S %p • %a, %b %d")
            self.live_clock_lbl.config(text=f"Live Time: {now_str}")

            # 2. Breathing / Pulsing effect on Status Badge
            if self.weather_data and self.status_badge_lbl.winfo_exists():
                self.pulse_state = not self.pulse_state
                curr = self.weather_data.current
                t = self.t
                if curr.is_demo:
                    dot_color = t["badge_demo_fg"] if self.pulse_state else t["text_muted"]
                    self.status_badge_lbl.config(
                        image=self.get_ui_photo("dot", dot_color, (10, 10))
                    )
                else:
                    dot_color = t["badge_live_fg"] if self.pulse_state else "#047857"
                    self.status_badge_lbl.config(
                        image=self.get_ui_photo("dot", dot_color, (10, 10))
                    )
        except Exception:
            pass

        if self.anim_running and self.root.winfo_exists():
            self.root.after(1000, self._tick_clock_and_pulse)

    # --- Unit Toggle & Re-rendering ---

    def toggle_unit(self):
        """Toggle between Celsius and Fahrenheit and refresh UI immediately."""
        self.current_unit = "F" if self.current_unit == "C" else "C"
        self.unit_btn.config(text=f"°{self.current_unit}")
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
        self.auto_btn.config(state="disabled", text=" Detecting...")
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
        self.auto_btn.config(state="normal", text=" Auto Detect")
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city)
        self.search_weather(city)

    def _on_location_detect_failed(self, err_msg: str):
        self.is_loading = False
        self.auto_btn.config(state="normal", text=" Auto Detect")
        self.show_banner(f"Auto-detection failed: {err_msg}", is_error=True)

    def search_weather(self, query: str):
        if self.is_loading:
            return

        if not query or not query.strip():
            self.show_banner("Input validation error: Please enter a city name or ZIP code.", is_error=True)
            return

        self.is_loading = True
        self.search_btn.config(state="disabled", text="Fetching...")
        self.show_banner(f"Fetching live weather for '{query}'...", is_info=True)

        def worker():
            try:
                data = fetch_weather_data(query)
                self.root.after(0, lambda: self._on_fetch_success(data, query))
            except ValidationError as e:
                self.root.after(0, lambda: self._on_fetch_error(f"Validation Error: {str(e)}"))
            except CityNotFoundError as e:
                self.root.after(0, lambda: self._on_fetch_error(str(e)))
            except InvalidApiKeyError as e:
                err_msg = str(e) if (str(e) and str(e) != "None") else "API Key Not Active Yet: OpenWeatherMap keys take 10 to 60 minutes after signup to activate."
                self.root.after(0, lambda: self._on_fetch_error(err_msg))
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

        # Update dynamic particle ambience to match current weather
        self._set_weather_ambience(data.current.condition)

        if data.current.is_demo:
            self.show_banner(
                "Running in DEMO Preview mode (no API key configured). Set your free key under 'API Key' for real-time live data.",
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

        t = self.t
        curr = self.weather_data.current
        is_f = (self.current_unit == "F")

        # 1. Location & Status Badge with clean graphical dot and glowing borders
        country_part = f", {curr.country}" if curr.country else ""
        self.location_lbl.config(text=f"{curr.city}{country_part}", fg=t["text_main"], bg=t["panel_bg"])
        self.date_lbl.config(text=curr.formatted_time, fg=t["text_muted"], bg=t["panel_bg"])

        if curr.is_demo:
            dot_photo = self.get_ui_photo("dot", t["badge_demo_fg"], (10, 10))
            self.status_badge_lbl.config(
                text=" DEMO PREVIEW",
                image=dot_photo,
                compound="left",
                bg=t["badge_demo_bg"],
                fg=t["badge_demo_fg"],
                highlightbackground=t["badge_demo_border"]
            )
        else:
            dot_photo = self.get_ui_photo("dot", t["badge_live_fg"], (10, 10))
            self.status_badge_lbl.config(
                text=" LIVE DATA",
                image=dot_photo,
                compound="left",
                bg=t["badge_live_bg"],
                fg=t["badge_live_fg"],
                highlightbackground=t["badge_live_border"]
            )
        self.status_badge_lbl.pack(side="left", padx=(10, 0))

        # 2. Main Temperature & Condition
        temp_val = curr.temp_f if is_f else curr.temp_c
        self.temp_lbl.config(text=f"{temp_val:.1f}°{self.current_unit}", fg=t["text_main"], bg=t["panel_bg"])
        self.condition_lbl.config(text=f"{curr.condition} • {curr.description}", fg=t["accent"], bg=t["panel_bg"])

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

        # 5. Render Hourly Cards with dynamic hover
        self._render_hourly_panel()

        # 6. Render Daily Cards with dynamic hover
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
        for widget in self.hourly_container.winfo_children():
            widget.destroy()

        t = self.t
        if not self.weather_data or not self.weather_data.hourly:
            empty_lbl = tk.Label(
                self.hourly_container,
                text="Hourly forecast details unavailable.",
                font=("Segoe UI", 9),
                fg=t["text_muted"],
                bg=t["bg"]
            )
            empty_lbl.pack(anchor="w")
            return

        is_f = (self.current_unit == "F")

        # Show up to 4 intervals (covers next 6 to 12 hours)
        items = self.weather_data.hourly[:4]
        for item in items:
            card = tk.Frame(
                self.hourly_container,
                bg=t["card_surface"],
                highlightthickness=1,
                highlightbackground=t["panel_border"],
                padx=10,
                pady=8
            )
            card.pack(side="left", fill="both", expand=True, padx=4)

            time_lbl = tk.Label(card, text=item.time_str, font=("Segoe UI", 9, "bold"), fg=t["text_muted"], bg=t["card_surface"])
            time_lbl.pack(anchor="center")

            icon_lbl = tk.Label(card, bg=t["card_surface"])
            icon_lbl.pack(anchor="center", pady=2)
            self._load_icon_async(item.icon_code, item.condition, (42, 42), icon_lbl)

            temp_val = item.temp_f if is_f else item.temp_c
            temp_lbl = tk.Label(card, text=f"{temp_val:.1f}°", font=("Segoe UI", 11, "bold"), fg=t["text_main"], bg=t["card_surface"])
            temp_lbl.pack(anchor="center")

            cond_lbl = tk.Label(card, text=item.condition, font=("Segoe UI", 8), fg=t["accent"], bg=t["card_surface"])
            cond_lbl.pack(anchor="center")

            # Dynamic Hover Elevation & Glow
            self._bind_hover_effect(card, t["card_surface"], t["card_hover"], t["panel_border"], t["panel_hover_border"])

    def _render_daily_panel(self):
        for widget in self.daily_container.winfo_children():
            widget.destroy()

        t = self.t
        if not self.weather_data or not self.weather_data.daily:
            empty_lbl = tk.Label(
                self.daily_container,
                text="5-day forecast details unavailable.",
                font=("Segoe UI", 9),
                fg=t["text_muted"],
                bg=t["bg"]
            )
            empty_lbl.pack(anchor="w")
            return

        is_f = (self.current_unit == "F")
        days = self.weather_data.daily[:5]

        for day in days:
            row = tk.Frame(
                self.daily_container,
                bg=t["card_surface"],
                highlightthickness=1,
                highlightbackground=t["panel_border"],
                padx=14,
                pady=6
            )
            row.pack(fill="x", pady=3)

            day_lbl = tk.Label(row, text=day.day_name, font=("Segoe UI", 10, "bold"), fg=t["text_main"], bg=t["card_surface"], width=10, anchor="w")
            day_lbl.pack(side="left")

            date_lbl = tk.Label(row, text=day.date_str, font=("Segoe UI", 9), fg=t["text_muted"], bg=t["card_surface"], width=8, anchor="w")
            date_lbl.pack(side="left")

            icon_lbl = tk.Label(row, bg=t["card_surface"])
            icon_lbl.pack(side="left", padx=10)
            self._load_icon_async(day.icon_code, day.condition, (32, 32), icon_lbl)

            cond_lbl = tk.Label(row, text=day.condition, font=("Segoe UI", 9), fg=t["text_main"], bg=t["card_surface"], width=16, anchor="w")
            cond_lbl.pack(side="left")

            min_val = day.temp_min_f if is_f else day.temp_min_c
            max_val = day.temp_max_f if is_f else day.temp_max_c
            temp_range = f"{min_val:.1f}° / {max_val:.1f}°{self.current_unit}"

            temps_lbl = tk.Label(row, text=temp_range, font=("Segoe UI", 10, "bold"), fg=t["accent"], bg=t["card_surface"])
            temps_lbl.pack(side="right")

            # Dynamic Hover Elevation & Glow
            self._bind_hover_effect(row, t["card_surface"], t["card_hover"], t["panel_border"], t["panel_hover_border"])

    # --- Settings / API Key Modal ---

    def open_settings_modal(self):
        t = self.t
        modal = tk.Toplevel(self.root)
        modal.title("OpenWeatherMap API Key Settings")
        modal.geometry("540x370")
        modal.resizable(False, False)
        modal.configure(bg=t["bg"])
        modal.transient(self.root)
        modal.grab_set()

        inner = tk.Frame(modal, bg=t["bg"], padx=25, pady=20)
        inner.pack(fill="both", expand=True)

        header_box = tk.Frame(inner, bg=t["bg"])
        header_box.pack(fill="x")

        gear_icon_lbl = tk.Label(
            header_box,
            bg=t["bg"],
            image=self.get_ui_photo("gear", t["accent"], (20, 20))
        )
        gear_icon_lbl.pack(side="left", padx=(0, 8))

        title = tk.Label(
            header_box,
            text="API Configuration",
            font=("Segoe UI", 14, "bold"),
            fg=t["text_main"],
            bg=t["bg"]
        )
        title.pack(side="left")

        info_text = (
            "To get live real-time weather and forecasts:\n"
            "1. Register free at: https://openweathermap.org/api\n"
            "2. Confirm your email address (check your inbox/spam).\n"
            "3. Copy your 32-character API key and paste below.\n\n"
            "IMPORTANT: Brand new OpenWeatherMap keys take 10 to 60 minutes\n"
            "after signup to activate on their servers! (Error 401 until active)."
        )
        info_lbl = tk.Label(
            inner,
            text=info_text,
            font=("Segoe UI", 9),
            fg=t["text_muted"],
            bg=t["bg"],
            justify="left"
        )
        info_lbl.pack(anchor="w", pady=(8, 12))

        key_lbl = tk.Label(inner, text="API Key:", font=("Segoe UI", 9, "bold"), fg=t["text_main"], bg=t["bg"])
        key_lbl.pack(anchor="w")

        current_key = get_api_key()
        key_entry = tk.Entry(
            inner,
            font=("Segoe UI", 10),
            bg=t["input_bg"],
            fg=t["input_fg"],
            insertbackground=t["text_main"],
            relief="flat",
            bd=5,
            highlightthickness=1,
            highlightbackground=t["panel_border"]
        )
        key_entry.pack(fill="x", pady=(4, 8))
        key_entry.insert(0, current_key)

        # Inline status label for testing key
        test_status_lbl = tk.Label(
            inner,
            text="",
            font=("Segoe UI", 8, "bold"),
            fg=t["accent"],
            bg=t["bg"],
            wraplength=480,
            justify="left"
        )
        test_status_lbl.pack(anchor="w", pady=(0, 8))

        btn_box = tk.Frame(inner, bg=t["bg"])
        btn_box.pack(fill="x", pady=6)

        def test_key_online():
            candidate_key = key_entry.get().strip()
            if not candidate_key:
                test_status_lbl.config(text="Please enter an API key above to test.", fg=t["error_text"])
                return

            test_status_lbl.config(text="Contacting OpenWeatherMap servers...", fg=t["accent"])

            def worker():
                import requests
                try:
                    r = requests.get(
                        "https://api.openweathermap.org/data/2.5/weather",
                        params={"q": "London", "appid": candidate_key},
                        timeout=5
                    )
                    if r.status_code == 200:
                        msg = "[ACTIVE] Key is verified and working! You can click 'Save Key'."
                        color = t["badge_live_fg"]
                    elif r.status_code == 401:
                        msg = "[NOT ACTIVE YET] OpenWeatherMap returned 401.\nNew keys take 10-60 mins to activate. Also ensure you verified your email."
                        color = t["badge_demo_fg"]
                    else:
                        msg = f"Server response: HTTP {r.status_code}"
                        color = t["error_text"]
                except Exception as ex:
                    msg = f"Network test failed: {ex}"
                    color = t["error_text"]

                modal.after(0, lambda: test_status_lbl.config(text=msg, fg=color))

            threading.Thread(target=worker, daemon=True).start()

        def save_and_close():
            new_key = key_entry.get().strip()
            set_api_key(new_key)
            modal.destroy()
            self.show_banner(
                "API key updated. Fetching weather..." if new_key else "API key cleared. Reverted to Demo mode.",
                is_info=True
            )
            if self.city_entry.get().strip():
                self.search_weather(self.city_entry.get().strip())

        save_btn = tk.Button(
            btn_box,
            text="Save Key",
            font=("Segoe UI", 10, "bold"),
            bg=t["accent"],
            fg=t["accent_text"],
            activebackground=t["accent_hover"],
            relief="flat",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=save_and_close
        )
        save_btn.pack(side="left", padx=(0, 8))
        self._bind_hover_effect(save_btn, t["accent"], t["accent_hover"])

        test_btn = tk.Button(
            btn_box,
            text="Test Key",
            font=("Segoe UI", 9, "bold"),
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            activebackground=t["btn_hover"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            padx=12,
            pady=6,
            cursor="hand2",
            command=test_key_online
        )
        test_btn.pack(side="left", padx=(0, 8))
        self._bind_hover_effect(test_btn, t["btn_bg"], t["btn_hover"], t["btn_border"], t["btn_hover_border"])

        cancel_btn = tk.Button(
            btn_box,
            text="Cancel",
            font=("Segoe UI", 10),
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            activebackground=t["btn_hover"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            padx=14,
            pady=6,
            cursor="hand2",
            command=modal.destroy
        )
        cancel_btn.pack(side="left")
        self._bind_hover_effect(cancel_btn, t["btn_bg"], t["btn_hover"], t["btn_border"], t["btn_hover_border"])


def main():
    root = tk.Tk()
    app = WeatherAppGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

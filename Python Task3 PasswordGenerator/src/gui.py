"""
GUI implementation for the Advanced Random Password Generator.
Built with Tkinter, featuring a responsive two-column layout,
switchable Golden Light and Golden Dark themes, 3x enlarged custom checkboxes,
synchronized controls, strength visualization, clipboard integration,
and session-only memory history.
"""

from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Deque, Dict, Any, Tuple

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

try:
    from src.password_generator import (
        PasswordCriteria,
        ValidationError,
        generate_secure_password,
        MIN_PASSWORD_LENGTH,
        MAX_PASSWORD_LENGTH,
    )
    from src.strength import assess_password_strength, StrengthAssessment
except ModuleNotFoundError:
    from password_generator import (
        PasswordCriteria,
        ValidationError,
        generate_secure_password,
        MIN_PASSWORD_LENGTH,
        MAX_PASSWORD_LENGTH,
    )
    from strength import assess_password_strength, StrengthAssessment


# ==========================================
# THEME DEFINITIONS: GOLDEN LIGHT & DARK
# ==========================================

THEME_LIGHT: Dict[str, str] = {
    "name": "light",
    "bg_main": "#f8f6f0",         # Warm ivory / soft alabaster
    "bg_card": "#ffffff",         # Crisp clean white card surface
    "bg_input": "#fdf8ee",        # Warm champagne container
    "border": "#e7dfcb",          # Soft golden-sand border
    "text_main": "#1c1917",       # Dark stone charcoal (high legibility)
    "text_muted": "#78716c",      # Warm neutral stone
    "accent_primary": "#d97706",  # Rich warm golden amber
    "accent_hover": "#b45309",    # Deep bronze gold
    "accent_secondary": "#b45309",# Deep warm amber for headers
    "accent_success": "#15803d",  # Forest emerald green
    "accent_danger": "#dc2626",   # Deep coral red
    "accent_warn": "#d97706",     # Warm amber
    "btn_text": "#ffffff",        # Crisp white bold text on golden buttons
    "entry_fg": "#92400e",        # Deep golden amber monospace text
    "entry_bg": "#fdf8ee",
    "history_row_bg": "#f9f5ed",
    "text_dark": "#12100b",
    "toggle_btn_text": "🌙 Dark Theme",
}

THEME_DARK: Dict[str, str] = {
    "name": "dark",
    "bg_main": "#12100b",         # Deep obsidian with golden-amber undertone
    "bg_card": "#1c1810",         # Warm dark bronze surface
    "bg_input": "#292316",        # Elevated dark amber container
    "border": "#4a3e20",          # Subtle bronze border
    "text_main": "#fef9c3",       # Warm pale golden-cream
    "text_muted": "#a89f81",      # Warm golden-sand
    "accent_primary": "#f59e0b",  # Radiant pure gold
    "accent_hover": "#d97706",    # Burnished gold
    "accent_secondary": "#fbbf24",# Bright yellow gold
    "accent_success": "#84cc16",  # Lime-gold green
    "accent_danger": "#f87171",   # Warm coral red
    "accent_warn": "#eab308",     # Golden yellow
    "btn_text": "#12100b",        # Dark text on bright gold
    "entry_fg": "#fbbf24",        # Bright gold monospace text
    "entry_bg": "#292316",
    "history_row_bg": "#292316",
    "text_dark": "#12100b",
    "toggle_btn_text": "☀️ Light Theme",
}

# Backwards-compatible exports (defaulting to Light Theme)
BG_MAIN = THEME_LIGHT["bg_main"]
BG_CARD = THEME_LIGHT["bg_card"]
BG_INPUT = THEME_LIGHT["bg_input"]
TEXT_MAIN = THEME_LIGHT["text_main"]
TEXT_MUTED = THEME_LIGHT["text_muted"]
TEXT_DARK = THEME_LIGHT["text_main"]
ACCENT_PRIMARY = THEME_LIGHT["accent_primary"]
ACCENT_HOVER = THEME_LIGHT["accent_hover"]
ACCENT_SECONDARY = THEME_LIGHT["accent_secondary"]
ACCENT_SUCCESS = THEME_LIGHT["accent_success"]
ACCENT_DANGER = THEME_LIGHT["accent_danger"]
ACCENT_WARN = THEME_LIGHT["accent_warn"]
BORDER_COLOR = THEME_LIGHT["border"]

# 3x Checkbox Icon Box Size
CHECKBOX_BOX_SIZE = 28


def render_checkbox_ppms(size: int, theme: Dict[str, str]) -> Tuple[bytes, bytes]:
    """
    Renders pixel-perfect 3x checkbox icons (unchecked and checked)
    in PPM binary format, fully compatible with Tk PhotoImage.
    """
    def h2rgb(hex_str: str) -> Tuple[int, int, int]:
        h = hex_str.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    bg_card_rgb = h2rgb(theme["bg_card"])
    border_rgb = h2rgb(theme["accent_primary"])

    # Checked state colors
    if theme["name"] == "light":
        fill_checked_rgb = h2rgb(theme["accent_primary"])
        tick_rgb = (255, 255, 255)  # Crisp white tick on amber
    else:
        fill_checked_rgb = h2rgb(theme["accent_primary"])
        tick_rgb = h2rgb(theme["text_dark"])  # Dark tick on gold

    # UNCHECKED BOX
    u_data = bytearray()
    for y in range(size):
        for x in range(size):
            # Smooth rounded corners
            is_corner_transparent = (
                (x == 0 and (y == 0 or y == size - 1)) or
                (x == size - 1 and (y == 0 or y == size - 1))
            )
            if is_corner_transparent:
                u_data.extend(bg_card_rgb)
            elif x < 2 or x >= size - 2 or y < 2 or y >= size - 2:
                u_data.extend(border_rgb)
            else:
                u_data.extend(bg_card_rgb)

    # CHECKED BOX
    c_data = bytearray()
    for y in range(size):
        for x in range(size):
            is_corner_transparent = (
                (x == 0 and (y == 0 or y == size - 1)) or
                (x == size - 1 and (y == 0 or y == size - 1))
            )
            if is_corner_transparent:
                c_data.extend(bg_card_rgb)
            else:
                # 3px thick checkmark line segments:
                # Downstroke: x in 7..12, y = x + 8
                # Upstroke: x in 12..22, y = 32 - x
                is_tick = False
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        px, py = x + ox, y + oy
                        if 7 <= px <= 12 and abs(py - (px + 8)) <= 1:
                            is_tick = True
                        elif 12 <= px <= 22 and abs(py - (32 - px)) <= 1:
                            is_tick = True

                if is_tick:
                    c_data.extend(tick_rgb)
                else:
                    c_data.extend(fill_checked_rgb)

    hdr = f"P6\n{size} {size}\n255\n".encode("ascii")
    return hdr + bytes(u_data), hdr + bytes(c_data)


class PasswordGeneratorGUI:
    """Main Tkinter GUI Controller and View supporting Light & Dark themes."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Advanced Random Password Generator - OIBSIP Task 3")
        self.root.geometry("980x680")
        self.root.minsize(920, 640)

        # Active Theme (defaulting to Golden Light Theme)
        self.is_dark_theme: bool = False
        self.theme: Dict[str, str] = THEME_LIGHT
        self.root.configure(bg=self.theme["bg_main"])

        # In-memory session history (strictly ephemeral, max 5 items)
        self.session_history: Deque[str] = deque(maxlen=5)
        self.history_mask_state: bool = True  # Hidden by default for shoulder-surfing safety

        # State Variables
        self.var_length = tk.IntVar(value=16)
        self.var_uppercase = tk.BooleanVar(value=True)
        self.var_lowercase = tk.BooleanVar(value=True)
        self.var_digits = tk.BooleanVar(value=True)
        self.var_symbols = tk.BooleanVar(value=True)
        self.var_exclude_ambiguous = tk.BooleanVar(value=False)
        self.var_auto_copy = tk.BooleanVar(value=True)

        self.current_password = ""
        self.last_assessment: Optional[StrengthAssessment] = None

        # Generate initial 3x checkbox icons
        u_ppm, c_ppm = render_checkbox_ppms(CHECKBOX_BOX_SIZE, self.theme)
        self.img_unchecked = tk.PhotoImage(data=u_ppm)
        self.img_checked = tk.PhotoImage(data=c_ppm)

        self._configure_styles()
        self._build_ui()
        self._update_length_label(16)

    def _configure_styles(self) -> None:
        """Configures ttk widget styling for active theme."""
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Progressbar styling
        self.style.configure(
            "Strength.Horizontal.TProgressbar",
            troughcolor=self.theme["bg_input"],
            bordercolor=self.theme["bg_input"],
            lightcolor=self.theme["accent_primary"],
            darkcolor=self.theme["accent_primary"],
            background=self.theme["accent_primary"],
            thickness=10
        )

    def _build_ui(self) -> None:
        """Constructs all GUI containers and widgets in a responsive two-column layout."""
        t = self.theme

        # Main container with outer padding
        self.main_frame = tk.Frame(self.root, bg=t["bg_main"], padx=20, pady=16)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # --- HEADER SECTION (3-column symmetrical grid for exact dead-center alignment) ---
        self.header_frame = tk.Frame(self.main_frame, bg=t["bg_main"])
        self.header_frame.pack(fill=tk.X, pady=(0, 12))
        self.header_frame.grid_columnconfigure(0, weight=1, uniform="hdr_side")
        self.header_frame.grid_columnconfigure(1, weight=3, uniform="hdr_center")
        self.header_frame.grid_columnconfigure(2, weight=1, uniform="hdr_side")

        # Left spacer to guarantee perfect symmetrical centering of the title
        self.header_left = tk.Frame(self.header_frame, bg=t["bg_main"])
        self.header_left.grid(row=0, column=0, sticky="nsew")

        self.header_center = tk.Frame(self.header_frame, bg=t["bg_main"])
        self.header_center.grid(row=0, column=1, sticky="n")

        self.title_label = tk.Label(
            self.header_center,
            text="Random Password Generator",
            font=("Segoe UI", 18, "bold"),
            bg=t["bg_main"],
            fg=t["accent_secondary"]
        )
        self.title_label.pack(anchor="center")

        self.subtitle_label = tk.Label(
            self.header_center,
            text="Cryptographically secure generation via Python secrets",
            font=("Segoe UI", 11),
            bg=t["bg_main"],
            fg=t["text_muted"]
        )
        self.subtitle_label.pack(anchor="center", pady=(3, 0))

        # Theme toggle button in header (fixed width=16 so width NEVER shifts between modes)
        self.btn_theme_toggle = tk.Button(
            self.header_frame,
            text=t["toggle_btn_text"],
            font=("Segoe UI", 11, "bold"),
            bg=t["bg_card"],
            fg=t["accent_primary"],
            activebackground=t["bg_input"],
            activeforeground=t["accent_secondary"],
            relief=tk.FLAT,
            cursor="hand2",
            width=16,
            pady=5,
            command=self.toggle_theme
        )
        self.btn_theme_toggle.grid(row=0, column=2, sticky="e")

        # --- TWO-COLUMN BODY CONTAINER ---
        self.cols_container = tk.Frame(self.main_frame, bg=t["bg_main"])
        self.cols_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.cols_container.grid_columnconfigure(0, weight=1, uniform="col")
        self.cols_container.grid_columnconfigure(1, weight=1, uniform="col")
        self.cols_container.grid_rowconfigure(0, weight=1)

        # ==========================================
        # LEFT COLUMN: PASSWORD CONFIGURATION
        # ==========================================
        self.left_card = tk.Frame(self.cols_container, bg=t["bg_card"], padx=18, pady=16, relief=tk.FLAT, bd=1)
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Left Column Title
        self.left_title_label = tk.Label(
            self.left_card,
            text="Password Configuration",
            font=("Segoe UI", 15, "bold"),
            bg=t["bg_card"],
            fg=t["accent_secondary"]
        )
        self.left_title_label.pack(anchor="w", pady=(0, 12))

        # 1. Password Length
        self.length_header_frame = tk.Frame(self.left_card, bg=t["bg_card"])
        self.length_header_frame.pack(fill=tk.X, pady=(0, 4))

        self.lbl_length_title = tk.Label(
            self.length_header_frame,
            text="Password Length:",
            font=("Segoe UI", 13, "bold"),
            bg=t["bg_card"],
            fg=t["text_main"]
        )
        self.lbl_length_title.pack(side=tk.LEFT)

        self.length_display = tk.Label(
            self.length_header_frame,
            text="16",
            font=("Segoe UI", 13, "bold"),
            bg=t["bg_input"],
            fg=t["accent_primary"],
            padx=10,
            pady=3,
            relief=tk.FLAT
        )
        self.length_display.pack(side=tk.RIGHT)

        self.slider_frame = tk.Frame(self.left_card, bg=t["bg_card"])
        self.slider_frame.pack(fill=tk.X, pady=(0, 14))

        self.slider = tk.Scale(
            self.slider_frame,
            from_=MIN_PASSWORD_LENGTH,
            to=64,
            orient=tk.HORIZONTAL,
            command=self._on_slider_changed,
            showvalue=0,
            bg=t["bg_card"],
            fg=t["text_main"],
            troughcolor=t["bg_input"],
            activebackground=t["accent_primary"],
            highlightthickness=0,
            bd=0
        )
        self.slider.set(16)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.spinbox = tk.Spinbox(
            self.slider_frame,
            from_=MIN_PASSWORD_LENGTH,
            to=MAX_PASSWORD_LENGTH,
            command=self._on_spinbox_changed,
            width=5,
            font=("Segoe UI", 13, "bold"),
            bg=t["bg_input"],
            fg=t["entry_fg"],
            buttonbackground=t["bg_card"],
            relief=tk.FLAT,
            justify=tk.CENTER
        )
        self.spinbox.delete(0, tk.END)
        self.spinbox.insert(0, "16")
        self.spinbox.pack(side=tk.RIGHT)
        self.spinbox.bind("<KeyRelease>", self._on_spinbox_key)

        # 2. Character Types (with 3x Checkboxes & Larger Font)
        self.char_types_header = tk.Frame(self.left_card, bg=t["bg_card"])
        self.char_types_header.pack(anchor="w", pady=(0, 6))

        self.lbl_char_types = tk.Label(
            self.char_types_header,
            text="Character Types",
            font=("Segoe UI", 13, "bold"),
            bg=t["bg_card"],
            fg=t["text_main"]
        )
        self.lbl_char_types.pack(anchor="w")

        self.lbl_char_types_sub = tk.Label(
            self.char_types_header,
            text="(minimum 2 required)",
            font=("Segoe UI", 10),
            bg=t["bg_card"],
            fg=t["text_muted"]
        )
        self.lbl_char_types_sub.pack(anchor="w")

        self.types_frame = tk.Frame(self.left_card, bg=t["bg_card"])
        self.types_frame.pack(fill=tk.X, pady=(0, 10))
        self.types_frame.grid_columnconfigure(0, weight=1, uniform="type_col")
        self.types_frame.grid_columnconfigure(1, weight=1, uniform="type_col")

        # 3x Custom Enlarged Checkboxes (28x28px indicator + 13pt bold font)
        self.cb_upper = tk.Checkbutton(
            self.types_frame,
            text="  Uppercase (A-Z)",
            variable=self.var_uppercase,
            image=self.img_unchecked,
            selectimage=self.img_checked,
            compound="left",
            indicatoron=False,
            font=("Segoe UI", 13, "bold"),
            bg=t["bg_card"],
            fg=t["text_main"],
            activebackground=t["bg_card"],
            activeforeground=t["accent_secondary"],
            selectcolor=t["bg_card"],
            bd=0,
            cursor="hand2",
            anchor="w"
        )
        self.cb_upper.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)

        self.cb_lower = tk.Checkbutton(
            self.types_frame,
            text="  Lowercase (a-z)",
            variable=self.var_lowercase,
            image=self.img_unchecked,
            selectimage=self.img_checked,
            compound="left",
            indicatoron=False,
            font=("Segoe UI", 13, "bold"),
            bg=t["bg_card"],
            fg=t["text_main"],
            activebackground=t["bg_card"],
            activeforeground=t["accent_secondary"],
            selectcolor=t["bg_card"],
            bd=0,
            cursor="hand2",
            anchor="w"
        )
        self.cb_lower.grid(row=0, column=1, sticky="w", pady=6)

        self.cb_digits = tk.Checkbutton(
            self.types_frame,
            text="  Numbers (0-9)",
            variable=self.var_digits,
            image=self.img_unchecked,
            selectimage=self.img_checked,
            compound="left",
            indicatoron=False,
            font=("Segoe UI", 13, "bold"),
            bg=t["bg_card"],
            fg=t["text_main"],
            activebackground=t["bg_card"],
            activeforeground=t["accent_secondary"],
            selectcolor=t["bg_card"],
            bd=0,
            cursor="hand2",
            anchor="w"
        )
        self.cb_digits.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)

        self.cb_symbols = tk.Checkbutton(
            self.types_frame,
            text="  Symbols (!@#$%)",
            variable=self.var_symbols,
            image=self.img_unchecked,
            selectimage=self.img_checked,
            compound="left",
            indicatoron=False,
            font=("Segoe UI", 13, "bold"),
            bg=t["bg_card"],
            fg=t["text_main"],
            activebackground=t["bg_card"],
            activeforeground=t["accent_secondary"],
            selectcolor=t["bg_card"],
            bd=0,
            cursor="hand2",
            anchor="w"
        )
        self.cb_symbols.grid(row=1, column=1, sticky="w", pady=6)

        # 3. Ambiguous Characters (3x Checkbox + 12pt bold font)
        self.cb_ambiguous = tk.Checkbutton(
            self.left_card,
            text="  Exclude ambiguous characters (0, O, 1, l, I, |)",
            variable=self.var_exclude_ambiguous,
            image=self.img_unchecked,
            selectimage=self.img_checked,
            compound="left",
            indicatoron=False,
            font=("Segoe UI", 12, "bold"),
            bg=t["bg_card"],
            fg=t["text_main"],
            activebackground=t["bg_card"],
            activeforeground=t["accent_secondary"],
            selectcolor=t["bg_card"],
            bd=0,
            cursor="hand2",
            anchor="w"
        )
        self.cb_ambiguous.pack(anchor="w", pady=(8, 0))

        # Flexible spacer pushing generate button to the bottom of the left column
        self.left_spacer = tk.Frame(self.left_card, bg=t["bg_card"])
        self.left_spacer.pack(fill=tk.BOTH, expand=True)

        # 4. Generate Password Button (80-90% width of left column, centered horizontally)
        self.btn_container = tk.Frame(self.left_card, bg=t["bg_card"])
        self.btn_container.pack(fill=tk.X, pady=(16, 6))

        self.btn_generate = tk.Button(
            self.btn_container,
            text="⚡ GENERATE PASSWORD",
            font=("Segoe UI", 12, "bold"),
            bg=t["accent_primary"],
            fg=t["btn_text"],
            activebackground=t["accent_hover"],
            activeforeground=t["btn_text"],
            relief=tk.FLAT,
            cursor="hand2",
            pady=12,
            command=self.generate_password_action
        )
        self.btn_generate.pack(fill=tk.X, padx=16)

        # ==========================================
        # RIGHT COLUMN: GENERATED PASSWORD
        # ==========================================
        self.right_card = tk.Frame(self.cols_container, bg=t["bg_card"], padx=18, pady=16, relief=tk.FLAT, bd=1)
        self.right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Right Column Title
        self.right_title_label = tk.Label(
            self.right_card,
            text="Generated Password",
            font=("Segoe UI", 15, "bold"),
            bg=t["bg_card"],
            fg=t["accent_secondary"]
        )
        self.right_title_label.pack(anchor="w", pady=(0, 10))

        # 1. Password Display Field & 2. Copy Button
        self.display_frame = tk.Frame(self.right_card, bg=t["bg_input"], padx=10, pady=8)
        self.display_frame.pack(fill=tk.X, pady=(0, 6))

        self.password_entry = tk.Entry(
            self.display_frame,
            font=("Consolas", 14, "bold"),
            bg=t["entry_bg"],
            fg=t["entry_fg"],
            readonlybackground=t["entry_bg"],
            disabledbackground=t["entry_bg"],
            relief=tk.FLAT,
            bd=0,
            insertbackground=t["accent_primary"]
        )
        self.password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 8))
        self.password_entry.insert(0, "Click Generate on left")
        self.password_entry.configure(state="readonly")

        self.btn_copy = tk.Button(
            self.display_frame,
            text="📋 Copy",
            font=("Segoe UI", 11, "bold"),
            bg=t["accent_primary"],
            fg=t["btn_text"],
            activebackground=t["accent_hover"],
            activeforeground=t["btn_text"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.copy_current_password
        )
        self.btn_copy.pack(side=tk.RIGHT)

        # 3. Password Strength
        self.strength_frame = tk.Frame(self.right_card, bg=t["bg_card"])
        self.strength_frame.pack(fill=tk.X, pady=(4, 2))

        self.strength_top_row = tk.Frame(self.strength_frame, bg=t["bg_card"])
        self.strength_top_row.pack(fill=tk.X, pady=(0, 4))

        self.lbl_strength_title = tk.Label(
            self.strength_top_row,
            text="Strength:",
            font=("Segoe UI", 11, "bold"),
            bg=t["bg_card"],
            fg=t["text_muted"]
        )
        self.lbl_strength_title.pack(side=tk.LEFT)

        self.lbl_strength_level = tk.Label(
            self.strength_top_row,
            text="Ready",
            font=("Segoe UI", 11, "bold"),
            bg=t["bg_card"],
            fg=t["text_muted"]
        )
        self.lbl_strength_level.pack(side=tk.LEFT, padx=(6, 0))

        self.lbl_entropy = tk.Label(
            self.strength_top_row,
            text="",
            font=("Segoe UI", 10),
            bg=t["bg_card"],
            fg=t["text_muted"]
        )
        self.lbl_entropy.pack(side=tk.RIGHT)

        self.strength_canvas = tk.Canvas(
            self.strength_frame,
            height=10,
            bg=t["bg_input"],
            highlightthickness=0,
            bd=0
        )
        self.strength_canvas.pack(fill=tk.X, pady=(2, 4))
        self.strength_canvas.bind("<Configure>", self._redraw_strength_bar)

        # 4. Generation Status (underneath strength indicator)
        self.lbl_status = tk.Label(
            self.right_card,
            text="",
            font=("Segoe UI", 11),
            bg=t["bg_card"],
            fg=t["accent_success"]
        )
        self.lbl_status.pack(anchor="w", pady=(0, 8))

        # 5. Session History (Last 5 - RAM Only)
        self.history_header = tk.Frame(self.right_card, bg=t["bg_card"])
        self.history_header.pack(fill=tk.X, pady=(4, 6))

        self.lbl_history_title = tk.Label(
            self.history_header,
            text="Session History (Last 5 - RAM Only)",
            font=("Segoe UI", 13, "bold"),
            bg=t["bg_card"],
            fg=t["accent_secondary"]
        )
        self.lbl_history_title.pack(side=tk.LEFT)

        self.btn_toggle_mask = tk.Button(
            self.history_header,
            text="👁 Unmask",
            font=("Segoe UI", 10, "bold"),
            bg=t["bg_input"],
            fg=t["text_main"],
            activebackground=t["bg_card"],
            activeforeground=t["accent_secondary"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=9,
            pady=3,
            command=self.toggle_history_mask
        )
        self.btn_toggle_mask.pack(side=tk.RIGHT)

        self.history_container = tk.Frame(self.right_card, bg=t["bg_card"])
        self.history_container.pack(fill=tk.BOTH, expand=True)
        self._refresh_history_ui()

        # ==========================================
        # BOTTOM ACTION BAR
        # ==========================================
        self.footer_frame = tk.Frame(self.main_frame, bg=t["bg_main"])
        self.footer_frame.pack(fill=tk.X, pady=(8, 0))

        self.btn_reset = tk.Button(
            self.footer_frame,
            text="↺ Reset Defaults",
            font=("Segoe UI", 11, "bold"),
            bg=t["bg_card"],
            fg=t["text_muted"],
            activebackground=t["bg_input"],
            activeforeground=t["accent_secondary"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=16,
            pady=6,
            command=self.reset_defaults
        )
        self.btn_reset.pack(side=tk.LEFT)

        self.btn_clear_hist = tk.Button(
            self.footer_frame,
            text="Clear History",
            font=("Segoe UI", 11, "bold"),
            bg=t["bg_card"],
            fg=t["text_muted"],
            activebackground=t["bg_input"],
            activeforeground=t["accent_secondary"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=16,
            pady=6,
            command=self.clear_history
        )
        self.btn_clear_hist.pack(side=tk.LEFT, padx=(12, 0))

        self.btn_exit = tk.Button(
            self.footer_frame,
            text="Exit",
            font=("Segoe UI", 11, "bold"),
            bg=t["bg_card"],
            fg=t["accent_danger"],
            activebackground=t["bg_input"],
            activeforeground=t["accent_danger"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=6,
            command=self.root.destroy
        )
        self.btn_exit.pack(side=tk.RIGHT)

    def toggle_theme(self) -> None:
        """Toggles between Golden Light Theme and Golden Dark Theme."""
        self.is_dark_theme = not self.is_dark_theme
        self.theme = THEME_DARK if self.is_dark_theme else THEME_LIGHT
        self._apply_theme()

    def _apply_theme(self) -> None:
        """Applies the current theme colors across all widgets and redraws UI."""
        t = self.theme
        self.root.configure(bg=t["bg_main"])
        self.main_frame.configure(bg=t["bg_main"])
        self.header_frame.configure(bg=t["bg_main"])
        self.header_left.configure(bg=t["bg_main"])
        self.header_center.configure(bg=t["bg_main"])
        self.title_label.configure(bg=t["bg_main"], fg=t["accent_secondary"])
        self.subtitle_label.configure(bg=t["bg_main"], fg=t["text_muted"])
        self.btn_theme_toggle.configure(
            text=t["toggle_btn_text"],
            bg=t["bg_card"],
            fg=t["accent_primary"],
            activebackground=t["bg_input"],
            activeforeground=t["accent_secondary"]
        )

        self.cols_container.configure(bg=t["bg_main"])
        self.left_card.configure(bg=t["bg_card"])
        self.left_title_label.configure(bg=t["bg_card"], fg=t["accent_secondary"])

        self.length_header_frame.configure(bg=t["bg_card"])
        self.lbl_length_title.configure(bg=t["bg_card"], fg=t["text_main"])
        self.length_display.configure(bg=t["bg_input"], fg=t["accent_primary"])

        self.slider_frame.configure(bg=t["bg_card"])
        self.slider.configure(
            bg=t["bg_card"],
            fg=t["text_main"],
            troughcolor=t["bg_input"],
            activebackground=t["accent_primary"]
        )
        self.spinbox.configure(
            bg=t["bg_input"],
            fg=t["entry_fg"],
            buttonbackground=t["bg_card"]
        )

        self.char_types_header.configure(bg=t["bg_card"])
        self.lbl_char_types.configure(bg=t["bg_card"], fg=t["text_main"])
        self.lbl_char_types_sub.configure(bg=t["bg_card"], fg=t["text_muted"])
        self.types_frame.configure(bg=t["bg_card"])

        # Dynamically update 3x checkbox icons for current theme
        u_ppm, c_ppm = render_checkbox_ppms(CHECKBOX_BOX_SIZE, t)
        self.img_unchecked.configure(data=u_ppm)
        self.img_checked.configure(data=c_ppm)

        for cb in (self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symbols, self.cb_ambiguous):
            cb.configure(
                bg=t["bg_card"],
                fg=t["text_main"],
                activebackground=t["bg_card"],
                activeforeground=t["accent_secondary"],
                selectcolor=t["bg_card"]
            )

        self.left_spacer.configure(bg=t["bg_card"])
        self.btn_container.configure(bg=t["bg_card"])
        self.btn_generate.configure(
            bg=t["accent_primary"],
            fg=t["btn_text"],
            activebackground=t["accent_hover"],
            activeforeground=t["btn_text"]
        )

        # Right column
        self.right_card.configure(bg=t["bg_card"])
        self.right_title_label.configure(bg=t["bg_card"], fg=t["accent_secondary"])
        self.display_frame.configure(bg=t["bg_input"])
        self.password_entry.configure(
            bg=t["entry_bg"],
            fg=t["entry_fg"],
            readonlybackground=t["entry_bg"],
            disabledbackground=t["entry_bg"],
            insertbackground=t["accent_primary"]
        )
        self.btn_copy.configure(
            bg=t["accent_primary"],
            fg=t["btn_text"],
            activebackground=t["accent_hover"],
            activeforeground=t["btn_text"]
        )

        self.strength_frame.configure(bg=t["bg_card"])
        self.strength_top_row.configure(bg=t["bg_card"])
        self.lbl_strength_title.configure(bg=t["bg_card"], fg=t["text_muted"])
        self.lbl_strength_level.configure(bg=t["bg_card"])
        self.lbl_entropy.configure(bg=t["bg_card"], fg=t["text_muted"])
        self.strength_canvas.configure(bg=t["bg_input"])

        self.lbl_status.configure(bg=t["bg_card"])

        self.history_header.configure(bg=t["bg_card"])
        self.lbl_history_title.configure(bg=t["bg_card"], fg=t["accent_secondary"])
        self.btn_toggle_mask.configure(
            bg=t["bg_input"],
            fg=t["text_main"],
            activebackground=t["bg_card"],
            activeforeground=t["accent_secondary"]
        )
        self.history_container.configure(bg=t["bg_card"])

        # Footer
        self.footer_frame.configure(bg=t["bg_main"])
        self.btn_reset.configure(
            bg=t["bg_card"],
            fg=t["text_muted"],
            activebackground=t["bg_input"],
            activeforeground=t["accent_secondary"]
        )
        self.btn_clear_hist.configure(
            bg=t["bg_card"],
            fg=t["text_muted"],
            activebackground=t["bg_input"],
            activeforeground=t["accent_secondary"]
        )
        self.btn_exit.configure(
            bg=t["bg_card"],
            fg=t["accent_danger"],
            activebackground=t["bg_input"],
            activeforeground=t["accent_danger"]
        )

        self._redraw_strength_bar()
        self._refresh_history_ui()

    # --- EVENT HANDLERS & SYNCHRONIZATION ---

    def _on_slider_changed(self, value: str) -> None:
        val = int(float(value))
        self.spinbox.delete(0, tk.END)
        self.spinbox.insert(0, str(val))
        self._update_length_label(val)

    def _on_spinbox_changed(self) -> None:
        try:
            val = int(self.spinbox.get())
            self._update_length_label(val)
            if MIN_PASSWORD_LENGTH <= val <= 64:
                self.slider.set(val)
        except ValueError:
            pass

    def _on_spinbox_key(self, event=None) -> None:
        try:
            val = int(self.spinbox.get())
            self._update_length_label(val)
            if MIN_PASSWORD_LENGTH <= val <= 64:
                self.slider.set(val)
        except ValueError:
            pass

    def _update_length_label(self, length: int) -> None:
        self.length_display.configure(text=str(length))

    # --- ACTIONS ---

    def generate_password_action(self) -> None:
        """Collects criteria, validates, generates password, copies, and updates UI."""
        raw_length = self.spinbox.get().strip()
        try:
            length = int(raw_length)
        except ValueError:
            messagebox.showerror(
                "Invalid Length",
                "Password length must be a valid integer."
            )
            return

        criteria = PasswordCriteria(
            length=length,
            include_uppercase=self.var_uppercase.get(),
            include_lowercase=self.var_lowercase.get(),
            include_digits=self.var_digits.get(),
            include_symbols=self.var_symbols.get(),
            exclude_ambiguous=self.var_exclude_ambiguous.get()
        )

        try:
            new_password = generate_secure_password(criteria)
        except ValidationError as err:
            messagebox.showwarning("Validation Error", str(err))
            return
        except Exception as err:
            messagebox.showerror("Generation Error", f"An unexpected error occurred: {err}")
            return

        self.current_password = new_password

        # Update entry display
        self.password_entry.configure(state="normal")
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, new_password)
        self.password_entry.configure(state="readonly")

        # Update Strength Assessment
        assessment = assess_password_strength(new_password)
        self._update_strength_display(assessment)

        # Update History (sliding window of max 5)
        self.session_history.append(new_password)
        self._refresh_history_ui()

        # Automatic Clipboard Copy
        copied = self._perform_clipboard_copy(new_password)
        if copied:
            self._set_status("✓ Generated and copied to clipboard!", self.theme["accent_success"])
        else:
            self._set_status("✓ Password generated (clipboard copy unavailable)", self.theme["accent_warn"])

    def _perform_clipboard_copy(self, text: str) -> bool:
        """Copies text to clipboard using pyperclip with Tkinter fallback."""
        success = False
        if HAS_PYPERCLIP:
            try:
                pyperclip.copy(text)
                success = True
            except Exception:
                success = False

        # Fallback to Tkinter native clipboard if pyperclip failed
        if not success:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.root.update()  # Required on some window managers
                success = True
            except Exception:
                success = False

        return success

    def copy_current_password(self) -> None:
        """Manual copy button handler."""
        if not self.current_password:
            self._set_status("No password generated to copy.", self.theme["accent_warn"])
            return

        if self._perform_clipboard_copy(self.current_password):
            self._set_status("✓ Password copied to clipboard!", self.theme["accent_success"])
        else:
            self._set_status("Failed to copy to clipboard.", self.theme["accent_danger"])

    def _update_strength_display(self, assessment: StrengthAssessment) -> None:
        """Updates the strength label and visual meter."""
        self.last_assessment = assessment
        self.lbl_strength_level.configure(
            text=assessment.level,
            fg=assessment.color_hex
        )
        self.lbl_entropy.configure(
            text=f"~{assessment.entropy_bits} bits entropy"
        )
        self._redraw_strength_bar()

    def _redraw_strength_bar(self, event=None) -> None:
        """Redraws the strength bar proportionally to canvas width."""
        if not hasattr(self, "last_assessment") or not self.last_assessment:
            return
        width = self.strength_canvas.winfo_width()
        height = self.strength_canvas.winfo_height()
        if width <= 1:
            width = 360
        if height <= 1:
            height = 10
        self.strength_canvas.delete("all")
        fill_width = int((self.last_assessment.score / 100.0) * width)
        self.strength_canvas.create_rectangle(
            0, 0, fill_width, height,
            fill=self.last_assessment.color_hex,
            width=0
        )

    def toggle_history_mask(self) -> None:
        """Toggles masking of passwords in history view for shoulder-surfing protection."""
        self.history_mask_state = not self.history_mask_state
        self.btn_toggle_mask.configure(
            text="👁 Unmask" if self.history_mask_state else "🔒 Mask"
        )
        self._refresh_history_ui()

    def _refresh_history_ui(self) -> None:
        """Re-renders the session history list."""
        for widget in self.history_container.winfo_children():
            widget.destroy()

        t = self.theme

        if not self.session_history:
            empty_lbl = tk.Label(
                self.history_container,
                text="No passwords generated yet in this session.",
                font=("Segoe UI", 11, "italic"),
                bg=t["bg_card"],
                fg=t["text_muted"]
            )
            empty_lbl.pack(anchor="w", pady=10)
            return

        # Render list in reverse chronological order (newest first)
        for idx, pwd in enumerate(reversed(self.session_history), start=1):
            row = tk.Frame(self.history_container, bg=t["history_row_bg"], pady=4, padx=8)
            row.pack(fill=tk.X, pady=2)

            num_lbl = tk.Label(
                row,
                text=f"{idx}.",
                font=("Consolas", 11, "bold"),
                bg=t["history_row_bg"],
                fg=t["text_muted"],
                width=3,
                anchor="w"
            )
            num_lbl.pack(side=tk.LEFT)

            display_pwd = "•" * len(pwd) if self.history_mask_state else pwd
            val_lbl = tk.Label(
                row,
                text=display_pwd,
                font=("Consolas", 12),
                bg=t["history_row_bg"],
                fg=t["text_main"],
                anchor="w"
            )
            val_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

            # Copy button for individual history item
            btn_copy_item = tk.Button(
                row,
                text="Copy",
                font=("Segoe UI", 10, "bold"),
                bg=t["bg_card"],
                fg=t["accent_primary"],
                activebackground=t["bg_input"],
                activeforeground=t["accent_secondary"],
                relief=tk.FLAT,
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda p=pwd: self._copy_history_item(p)
            )
            btn_copy_item.pack(side=tk.RIGHT)

    def _copy_history_item(self, pwd: str) -> None:
        """Copies a specific history item."""
        if self._perform_clipboard_copy(pwd):
            self._set_status("✓ History item copied to clipboard!", self.theme["accent_success"])
        else:
            self._set_status("Failed to copy history item.", self.theme["accent_danger"])

    def clear_history(self) -> None:
        """Clears the session-only in-memory history."""
        self.session_history.clear()
        self._refresh_history_ui()
        self._set_status("Session history cleared.", self.theme["text_muted"])

    def reset_defaults(self) -> None:
        """Resets all controls back to default configurations."""
        self.var_length.set(16)
        self.slider.set(16)
        self.spinbox.delete(0, tk.END)
        self.spinbox.insert(0, "16")
        self.var_uppercase.set(True)
        self.var_lowercase.set(True)
        self.var_digits.set(True)
        self.var_symbols.set(True)
        self.var_exclude_ambiguous.set(False)
        self._update_length_label(16)
        self._set_status("Reset to default configuration.", self.theme["text_muted"])

    def _set_status(self, message: str, color: str) -> None:
        """Updates transient status label."""
        self.lbl_status.configure(text=message, fg=color)

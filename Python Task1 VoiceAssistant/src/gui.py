"""
Nova Voice Assistant — Tkinter GUI Presentation Layer

This module provides a modern desktop interface for the voice assistant.
It acts strictly as an interface layer, reusing the existing core logic:
- voice_io (listen, speak)
- intent_engine (NLP intent classification)
- dispatcher (routing to handlers)
- reminders, weather, email, knowledge, custom commands

All background tasks (listening, network APIs, TTS) execute in worker
threads to ensure the Tkinter UI never freezes.
"""

import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime

# Ensure project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.voice_io import speak as base_speak, listen as base_listen
from src.intent_engine import IntentEngine
from src.dispatcher import dispatch
from src.handlers.custom_commands import load_custom_commands
from src.handlers.reminders import cancel_all_reminders


# ── Color Palette (Modern Dark / Slate Theme) ──────────────────────
BG_DARK = "#181825"        # Main window background
BG_CARD = "#1e1e2e"        # Frame / Card background
BG_CHAT = "#11111b"        # Conversation log background
TEXT_PRIMARY = "#cdd6f4"   # Main text color
TEXT_MUTED = "#a6adc8"     # Secondary / timestamp text
ACCENT_BLUE = "#89b4fa"    # Accent / header color
ACCENT_GREEN = "#a6e3a1"   # Ready / active color
ACCENT_RED = "#f38ba8"     # Exit / error color
ACCENT_YELLOW = "#f9e2af"  # Processing / warning color
ACCENT_PURPLE = "#cba6f7"  # Listening indicator color
BTN_BG = "#313244"         # Quick button background
BTN_HOVER = "#45475a"      # Quick button hover color
USER_TAG_COLOR = "#89dceb" # User speech tag color
NOVA_TAG_COLOR = "#cba6f7" # Assistant speech tag color


class NovaVoiceAssistantGUI:
    """
    Tkinter desktop application for Nova Voice Assistant.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Nova Voice Assistant")
        self.root.geometry("620x720")
        self.root.minsize(500, 600)
        self.root.configure(bg=BG_DARK)

        # Execution lock to prevent overlapping voice queries
        self._is_busy = False
        self._busy_lock = threading.Lock()

        # Initialize existing core engine components
        load_custom_commands()
        self.intent_engine = IntentEngine()

        # Build UI layout
        self._setup_ui()

        # Safe shutdown handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Initial welcome message in GUI
        self.append_conversation(
            "NOVA",
            "Hello! I'm Nova, your voice assistant. Click 'Start Listening' or use quick commands to begin.",
            status="Ready"
        )

    # ── UI Construction ──────────────────────────────────────────────

    def _setup_ui(self) -> None:
        """Create and lay out all Tkinter widgets."""

        # 1. Header Frame
        header_frame = tk.Frame(self.root, bg=BG_CARD, pady=12, padx=16)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_label = tk.Label(
            header_frame,
            text="NOVA VOICE ASSISTANT",
            font=("Segoe UI", 16, "bold"),
            fg=ACCENT_BLUE,
            bg=BG_CARD
        )
        title_label.pack(anchor=tk.CENTER)

        subtitle_label = tk.Label(
            header_frame,
            text="Natural Language Desktop Assistant",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_CARD
        )
        subtitle_label.pack(anchor=tk.CENTER, pady=(2, 6))

        # Status Badge Frame
        status_bar = tk.Frame(header_frame, bg=BG_CARD)
        status_bar.pack(anchor=tk.CENTER, pady=(4, 0))

        self.status_dot = tk.Label(
            status_bar,
            text="●",
            font=("Segoe UI", 12),
            fg=ACCENT_GREEN,
            bg=BG_CARD
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 6))

        self.status_label = tk.Label(
            status_bar,
            text="Ready",
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_GREEN,
            bg=BG_CARD
        )
        self.status_label.pack(side=tk.LEFT)

        # 2. Conversation History Display (Scrollable)
        chat_container = tk.Frame(self.root, bg=BG_DARK, padx=16, pady=10)
        chat_container.pack(fill=tk.BOTH, expand=True)

        chat_frame = tk.Frame(chat_container, bg=BG_CHAT, bd=1, relief=tk.SOLID)
        chat_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_history = tk.Text(
            chat_frame,
            wrap=tk.WORD,
            bg=BG_CHAT,
            fg=TEXT_PRIMARY,
            font=("Consolas", 10),
            padx=14,
            pady=12,
            bd=0,
            highlightthickness=0,
            cursor="arrow"
        )
        scrollbar = tk.Scrollbar(chat_frame, command=self.chat_history.yview)
        self.chat_history.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Text styles / formatting tags
        self.chat_history.tag_configure("user_header", font=("Segoe UI", 10, "bold"), foreground=USER_TAG_COLOR)
        self.chat_history.tag_configure("nova_header", font=("Segoe UI", 10, "bold"), foreground=NOVA_TAG_COLOR)
        self.chat_history.tag_configure("time_header", font=("Segoe UI", 8), foreground=TEXT_MUTED)
        self.chat_history.tag_configure("user_body", font=("Segoe UI", 10), foreground=TEXT_PRIMARY, lmargin1=18, lmargin2=18)
        self.chat_history.tag_configure("nova_body", font=("Segoe UI", 10), foreground=TEXT_PRIMARY, lmargin1=18, lmargin2=18)
        self.chat_history.tag_configure("error_body", font=("Segoe UI", 10, "italic"), foreground=ACCENT_RED, lmargin1=18, lmargin2=18)
        self.chat_history.tag_configure("separator", font=("Segoe UI", 5), foreground=BG_CARD)

        self.chat_history.config(state=tk.DISABLED)

        # 3. Primary Microphone Action Button
        action_frame = tk.Frame(self.root, bg=BG_DARK, pady=10, padx=16)
        action_frame.pack(fill=tk.X)

        self.mic_btn = tk.Button(
            action_frame,
            text="🎙  Start Listening",
            font=("Segoe UI", 12, "bold"),
            bg="#3b82f6",
            fg="#ffffff",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.start_listening_thread
        )
        self.mic_btn.pack(fill=tk.X)

        # 4. Quick-Action Buttons Frame
        quick_frame = tk.Frame(self.root, bg=BG_DARK, padx=16, pady=4)
        quick_frame.pack(fill=tk.X)

        quick_buttons = [
            ("⏰ Time", lambda: self.trigger_text_query("what is the current time")),
            ("⛅ Weather", lambda: self.trigger_text_query("what is the weather in Delhi")),
            ("🔍 Search", lambda: self.trigger_text_query("search for Python tutorials")),
            ("❓ Help", self.show_help),
            ("🗑 Clear", self.clear_conversation),
            ("❌ Exit", self.on_exit),
        ]

        for idx, (label, cmd) in enumerate(quick_buttons):
            # Styling specific buttons
            btn_fg = ACCENT_RED if "Exit" in label else (ACCENT_YELLOW if "Clear" in label else TEXT_PRIMARY)
            btn = tk.Button(
                quick_frame,
                text=label,
                font=("Segoe UI", 9),
                bg=BTN_BG,
                fg=btn_fg,
                activebackground=BTN_HOVER,
                activeforeground=btn_fg,
                relief=tk.FLAT,
                bd=0,
                padx=8,
                pady=6,
                cursor="hand2",
                command=cmd
            )
            btn.grid(row=0, column=idx, padx=4, pady=2, sticky="ew")
            quick_frame.grid_columnconfigure(idx, weight=1)

        # 5. Footer / Status Text
        footer_frame = tk.Frame(self.root, bg=BG_CARD, padx=16, pady=6)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(8, 0))

        self.footer_status = tk.Label(
            footer_frame,
            text="Assistant active • All systems operational",
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=BG_CARD
        )
        self.footer_status.pack(side=tk.LEFT)

        author_label = tk.Label(
            footer_frame,
            text="OIBSIP Task 1",
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=BG_CARD
        )
        author_label.pack(side=tk.RIGHT)

    # ── State and Status Helpers ─────────────────────────────────────

    def set_status(self, status: str) -> None:
        """Update the status indicator badge with appropriate colors."""
        color_map = {
            "Ready": ACCENT_GREEN,
            "Listening...": ACCENT_PURPLE,
            "Processing...": ACCENT_YELLOW,
            "Speaking...": ACCENT_BLUE,
            "Error": ACCENT_RED,
        }
        color = color_map.get(status, ACCENT_GREEN)

        def _update():
            self.status_label.config(text=status, fg=color)
            self.status_dot.config(fg=color)
            if status == "Listening...":
                self.mic_btn.config(
                    text="🔴  Listening... Speak now",
                    bg="#dc2626",
                    state=tk.DISABLED
                )
            elif status == "Processing...":
                self.mic_btn.config(
                    text="⏳  Processing intent...",
                    bg="#ca8a04",
                    state=tk.DISABLED
                )
            elif status == "Speaking...":
                self.mic_btn.config(
                    text="🔊  Speaking response...",
                    bg="#2563eb",
                    state=tk.DISABLED
                )
            elif status == "Ready":
                self.mic_btn.config(
                    text="🎙  Start Listening",
                    bg="#3b82f6",
                    state=tk.NORMAL
                )
            elif status == "Error":
                self.mic_btn.config(
                    text="🎙  Start Listening",
                    bg="#3b82f6",
                    state=tk.NORMAL
                )

        self.root.after(0, _update)

    def append_conversation(self, sender: str, message: str, is_error: bool = False, status: str = None) -> None:
        """Safely append user or assistant messages to the scrollable text widget."""
        timestamp = datetime.now().strftime("%I:%M %p")

        def _append():
            self.chat_history.config(state=tk.NORMAL)

            # Add sender tag and timestamp
            if sender.upper() == "YOU":
                self.chat_history.insert(tk.END, f"YOU ", "user_header")
                self.chat_history.insert(tk.END, f"({timestamp})\n", "time_header")
                self.chat_history.insert(tk.END, f"{message}\n\n", "user_body")
            else:
                self.chat_history.insert(tk.END, f"NOVA ", "nova_header")
                self.chat_history.insert(tk.END, f"({timestamp})\n", "time_header")
                tag = "error_body" if is_error else "nova_body"
                self.chat_history.insert(tk.END, f"{message}\n\n", tag)

            # Auto-scroll to latest
            self.chat_history.see(tk.END)
            self.chat_history.config(state=tk.DISABLED)

            if status:
                self.set_status(status)

        self.root.after(0, _append)

    # ── Voice Engine Integration (Non-blocking) ──────────────────────

    def _gui_speak(self, text: str) -> None:
        """
        Wrapped TTS function passed to dispatcher and reminders.
        Updates GUI conversation history and status, then speaks aloud via pyttsx3.
        """
        if not text:
            return
        self.set_status("Speaking...")
        self.append_conversation("NOVA", text)
        base_speak(text)

    def _gui_listen(self, timeout: int = 6, phrase_time_limit: int = 12) -> str | None:
        """
        Wrapped STT function passed to dispatcher for interactive flows (like email).
        Updates status to listening while mic is active.
        """
        self.set_status("Listening...")
        text = base_listen(timeout=timeout, phrase_time_limit=phrase_time_limit)
        return text

    def start_listening_thread(self) -> None:
        """Triggered by the microphone button; runs voice cycle in background."""
        with self._busy_lock:
            if self._is_busy:
                return
            self._is_busy = True

        worker = threading.Thread(target=self._run_voice_interaction, daemon=True)
        worker.start()

    def _run_voice_interaction(self) -> None:
        """
        Background worker that runs the full voice interaction pipeline:
        listen -> display YOU -> classify -> dispatch -> display NOVA -> speak.
        """
        try:
            self.set_status("Listening...")
            user_text = base_listen(timeout=6, phrase_time_limit=12)

            if user_text is None:
                self.set_status("Error")
                self.append_conversation(
                    "NOVA",
                    "I didn't catch that or microphone timed out. Please click 'Start Listening' and try again.",
                    is_error=True
                )
                self._gui_speak("I didn't catch that. Could you please repeat?")
                return

            # Display recognized speech in GUI
            self.set_status("Processing...")
            self.append_conversation("YOU", user_text)

            # NLP intent classification
            intent, confidence = self.intent_engine.classify(user_text)

            if intent == "exit":
                self._gui_speak("Goodbye! Have a great day.")
                self.root.after(500, self.root.destroy)
                return

            # Dispatch intent to existing handlers
            response = dispatch(
                intent=intent,
                confidence=confidence,
                raw_text=user_text,
                intent_engine=self.intent_engine,
                listen_fn=self._gui_listen,
                speak_fn=self._gui_speak,
            )

            # If response returned (not already spoken inside interactive flow), speak it
            if response:
                self._gui_speak(response)

        except Exception as exc:
            self.set_status("Error")
            err_msg = f"An unexpected error occurred: {exc}"
            self.append_conversation("NOVA", err_msg, is_error=True)
            self._gui_speak("Something went wrong on my end. Let's try again.")

        finally:
            with self._busy_lock:
                self._is_busy = False
            self.set_status("Ready")

    def trigger_text_query(self, query: str) -> None:
        """
        Enables quick-action buttons to feed commands directly into the existing
        NLP engine and dispatcher without bypassing any logic.
        """
        with self._busy_lock:
            if self._is_busy:
                return
            self._is_busy = True

        def _worker():
            try:
                self.set_status("Processing...")
                self.append_conversation("YOU", query)

                intent, confidence = self.intent_engine.classify(query)

                if intent == "exit":
                    self._gui_speak("Goodbye! Have a great day.")
                    self.root.after(500, self.root.destroy)
                    return

                response = dispatch(
                    intent=intent,
                    confidence=confidence,
                    raw_text=query,
                    intent_engine=self.intent_engine,
                    listen_fn=self._gui_listen,
                    speak_fn=self._gui_speak,
                )

                if response:
                    self._gui_speak(response)

            except Exception as exc:
                self.set_status("Error")
                self.append_conversation("NOVA", f"Error: {exc}", is_error=True)
                self._gui_speak("Something went wrong processing that request.")

            finally:
                with self._busy_lock:
                    self._is_busy = False
                self.set_status("Ready")

        threading.Thread(target=_worker, daemon=True).start()

    # ── Quick Actions ────────────────────────────────────────────────

    def clear_conversation(self) -> None:
        """Clears the chat history widget."""
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.config(state=tk.DISABLED)
        self.append_conversation("NOVA", "Conversation cleared. Ready for your next command.")

    def show_help(self) -> None:
        """Displays supported features and example voice commands."""
        help_text = (
            "Supported Voice Commands:\n\n"
            "• Greet: 'Hello', 'Good morning', 'Hey assistant'\n"
            "• Time & Date: 'What time is it?', 'What is today's date?'\n"
            "• Web Search: 'Search for Python decorators', 'Look up machine learning'\n"
            "• Weather: 'What's the weather in Pune?', 'Temperature in Mumbai'\n"
            "• Reminders: 'Remind me in 30 seconds to check the oven'\n"
            "• General Knowledge: 'What is Python?', 'What is the capital of France?'\n"
            "• Custom Commands: 'Open GitHub', 'Open YouTube', 'Open Gmail'\n"
            "• Email: 'Send an email' (requires .env configuration)\n"
            "• Exit: 'Exit', 'Quit', 'Goodbye'\n"
        )
        self.append_conversation("NOVA", help_text)

    def on_exit(self) -> None:
        """Gracefully cancels reminders and closes the window."""
        try:
            cancel_all_reminders()
        except Exception:
            pass
        self.root.destroy()


def launch_gui() -> None:
    """Launch the Nova Voice Assistant Tkinter GUI."""
    root = tk.Tk()
    app = NovaVoiceAssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()

"""
Reminder handler — schedules timed reminders using background threads.

Reminders run in the background via threading.Timer so the main
assistant loop continues accepting commands while waiting.
"""

import threading
from datetime import datetime, timedelta

# Active reminders tracked for status reporting
_active_reminders: list[dict] = []
_reminder_lock = threading.Lock()


def handle_reminder(
    seconds: int | None,
    message: str,
    speak_fn,
) -> str:
    """
    Schedule a timed reminder that will speak an alert after the given duration.

    Args:
        seconds: How many seconds from now to fire the reminder.
                 None if duration could not be parsed.
        message: What to remind the user about.
        speak_fn: The TTS function to call when the reminder fires.

    Returns:
        Confirmation or error message.
    """
    if seconds is None or seconds <= 0:
        return (
            "I couldn't understand the duration for the reminder. "
            "Please say something like 'remind me in 5 minutes to take a break'."
        )

    # Cap at 24 hours to prevent accidentally huge timers
    max_seconds = 86400
    if seconds > max_seconds:
        return "I can only set reminders up to 24 hours. Please choose a shorter duration."

    # Build a human-readable duration string
    duration_text = _format_duration(seconds)
    fire_time = datetime.now() + timedelta(seconds=seconds)

    # Create the reminder info record
    reminder_info = {
        "message": message,
        "seconds": seconds,
        "fire_time": fire_time.strftime("%I:%M %p"),
        "timer": None,
        "fired": False,
    }

    # Define the callback
    def _on_reminder():
        reminder_info["fired"] = True
        alert = f"Reminder: {message}!"
        print(f"\n[REMINDER ALERT] {alert}")
        speak_fn(alert)
        # Clean up
        with _reminder_lock:
            if reminder_info in _active_reminders:
                _active_reminders.remove(reminder_info)

    # Start the background timer
    timer = threading.Timer(seconds, _on_reminder)
    timer.daemon = True  # Ensure it doesn't block program exit
    reminder_info["timer"] = timer

    with _reminder_lock:
        _active_reminders.append(reminder_info)

    timer.start()

    return (
        f"Got it. I'll remind you to {message} in {duration_text}, "
        f"around {reminder_info['fire_time']}."
    )


def get_active_reminders() -> list[dict]:
    """Return a snapshot of currently active (unfired) reminders."""
    with _reminder_lock:
        return [r for r in _active_reminders if not r["fired"]]


def cancel_all_reminders() -> None:
    """Cancel all pending reminders (used during shutdown)."""
    with _reminder_lock:
        for reminder in _active_reminders:
            timer = reminder.get("timer")
            if timer and not reminder["fired"]:
                timer.cancel()
        _active_reminders.clear()


def _format_duration(seconds: int) -> str:
    """Convert a duration in seconds into a readable string."""
    if seconds < 60:
        unit = "second" if seconds == 1 else "seconds"
        return f"{seconds} {unit}"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining = seconds % 60
        parts = []
        if minutes:
            parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")
        if remaining:
            parts.append(f"{remaining} {'second' if remaining == 1 else 'seconds'}")
        return " and ".join(parts)
    else:
        hours = seconds // 3600
        remaining_min = (seconds % 3600) // 60
        parts = []
        if hours:
            parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
        if remaining_min:
            parts.append(f"{remaining_min} {'minute' if remaining_min == 1 else 'minutes'}")
        return " and ".join(parts)

"""
Dispatcher — routes classified intents to the appropriate handler
functions and returns spoken responses.

This module decouples intent classification from action execution,
making it easy to add new intents without modifying existing handlers.
"""

from src.handlers.greetings import handle_greeting
from src.handlers.datetime_info import handle_time, handle_date
from src.handlers.web_search import handle_search
from src.handlers.email_sender import collect_email_details_flow
from src.handlers.weather import handle_weather
from src.handlers.reminders import handle_reminder
from src.handlers.knowledge import handle_knowledge
from src.handlers.custom_commands import handle_custom_command


def dispatch(intent: str, confidence: float, raw_text: str,
             intent_engine, listen_fn, speak_fn) -> str | None:
    """
    Route the classified intent to the correct handler.

    Args:
        intent: The classified intent name (e.g., 'greeting', 'weather').
        confidence: The classification confidence score.
        raw_text: The original user text (used for entity extraction).
        intent_engine: The IntentEngine instance (for entity extraction).
        listen_fn: The voice listen function (for interactive flows).
        speak_fn: The voice speak function (for interactive flows).

    Returns:
        Response text to speak, or None for exit intent.
    """
    # ── Check custom commands first (they can overlap with other intents)
    if intent == "custom_command":
        custom_result = handle_custom_command(raw_text)
        if custom_result:
            return custom_result
        # If no custom command matched, treat as unknown
        return "I don't recognise that command. You can add custom commands in config/custom_commands.json."

    # ── Route to handlers ────────────────────────────────────────────
    if intent == "greeting":
        return handle_greeting()

    elif intent == "time":
        return handle_time()

    elif intent == "date":
        return handle_date()

    elif intent == "web_search":
        query = intent_engine.extract_search_query(raw_text)
        return handle_search(query)

    elif intent == "send_email":
        # Email uses an interactive multi-step flow
        collect_email_details_flow(listen_fn, speak_fn)
        return None  # Response already spoken inside the flow

    elif intent == "weather":
        city = intent_engine.extract_city(raw_text)
        if not city:
            speak_fn("Which city would you like the weather for?")
            city_response = listen_fn(timeout=6, phrase_time_limit=8)
            if city_response:
                city = city_response.strip().title()
            else:
                return "I didn't catch the city name. Please try again."
        return handle_weather(city)

    elif intent == "reminder":
        seconds, message = intent_engine.extract_reminder(raw_text)
        return handle_reminder(seconds, message, speak_fn)

    elif intent == "general_knowledge":
        return handle_knowledge(raw_text)

    elif intent == "exit":
        return None  # Caller checks for exit intent separately

    elif intent == "unknown":
        return (
            "I'm not sure I understood that. Could you please rephrase? "
            "You can ask me about the time, weather, set reminders, "
            "search the web, send emails, or ask general-knowledge questions."
        )

    else:
        return f"I recognised your intent as '{intent}' but I don't have a handler for it yet."

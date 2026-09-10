"""
Unit tests for the IntentEngine — verifies that the NLTK-based
bag-of-stems cosine similarity classifier correctly maps varied
phrasings to the expected intents.

Run with:  python -m pytest tests/test_intent_engine.py -v
"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.intent_engine import IntentEngine


# Shared engine instance (building the model is deterministic)
_engine = IntentEngine()


def _assert_intent(text: str, expected_intent: str):
    """Helper: classify text and assert the intent matches."""
    intent, confidence = _engine.classify(text)
    assert intent == expected_intent, (
        f"Input: {text!r}\n"
        f"Expected intent: {expected_intent}\n"
        f"Got: {intent} (confidence={confidence:.3f})"
    )


# ── Greeting tests ──────────────────────────────────────────────────

class TestGreetingIntent:
    def test_hello(self):
        _assert_intent("hello", "greeting")

    def test_hi_there(self):
        _assert_intent("hi there", "greeting")

    def test_hey_assistant(self):
        _assert_intent("hey assistant", "greeting")

    def test_good_morning(self):
        _assert_intent("good morning", "greeting")

    def test_howdy(self):
        _assert_intent("howdy", "greeting")


# ── Time tests ──────────────────────────────────────────────────────

class TestTimeIntent:
    def test_what_time(self):
        _assert_intent("what time is it", "time")

    def test_current_time(self):
        _assert_intent("tell me the current time", "time")

    def test_time_now(self):
        _assert_intent("what time do we have", "time")

    def test_time_variation(self):
        _assert_intent("can you tell me the time please", "time")


# ── Date tests ──────────────────────────────────────────────────────

class TestDateIntent:
    def test_todays_date(self):
        _assert_intent("what is today's date", "date")

    def test_date_today(self):
        _assert_intent("what's the date today", "date")

    def test_which_day(self):
        _assert_intent("what day is it", "date")

    def test_current_date(self):
        _assert_intent("tell me the current date", "date")


# ── Web search tests ───────────────────────────────────────────────

class TestSearchIntent:
    def test_search_for(self):
        _assert_intent("search for python decorators", "web_search")

    def test_look_up(self):
        _assert_intent("look up machine learning", "web_search")

    def test_google_something(self):
        _assert_intent("google artificial intelligence", "web_search")

    def test_search_internet(self):
        _assert_intent("i want you to search the internet for python", "web_search")


# ── Email tests ─────────────────────────────────────────────────────

class TestEmailIntent:
    def test_send_email(self):
        _assert_intent("send an email", "send_email")

    def test_compose_email(self):
        _assert_intent("compose an email", "send_email")

    def test_write_email(self):
        _assert_intent("i want to send an email", "send_email")


# ── Weather tests ───────────────────────────────────────────────────

class TestWeatherIntent:
    def test_weather_in_city(self):
        _assert_intent("what's the weather in pune", "weather")

    def test_temperature(self):
        _assert_intent("how hot is it in delhi", "weather")

    def test_weather_forecast(self):
        _assert_intent("weather forecast for london", "weather")


# ── Reminder tests ──────────────────────────────────────────────────

class TestReminderIntent:
    def test_remind_me(self):
        _assert_intent("remind me in ten minutes to drink water", "reminder")

    def test_set_reminder(self):
        _assert_intent("set a reminder for thirty seconds", "reminder")

    def test_alert_me(self):
        _assert_intent("alert me in one hour", "reminder")


# ── Knowledge tests ─────────────────────────────────────────────────

class TestKnowledgeIntent:
    def test_what_is(self):
        _assert_intent("what is python", "general_knowledge")

    def test_capital(self):
        _assert_intent("what is the capital of france", "general_knowledge")

    def test_who_invented(self):
        _assert_intent("who invented the telephone", "general_knowledge")


# ── Exit tests ──────────────────────────────────────────────────────

class TestExitIntent:
    def test_exit(self):
        _assert_intent("exit", "exit")

    def test_goodbye(self):
        _assert_intent("goodbye", "exit")

    def test_quit(self):
        _assert_intent("quit", "exit")

    def test_bye(self):
        _assert_intent("bye", "exit")


# ── Entity extraction tests ────────────────────────────────────────

class TestEntityExtraction:
    def test_search_query_extraction(self):
        query = _engine.extract_search_query("search for python decorators")
        assert "python" in query.lower()
        assert "decorator" in query.lower()

    def test_city_extraction_in_pattern(self):
        city = _engine.extract_city("what's the weather in pune")
        assert city.lower() == "pune"

    def test_city_extraction_for_pattern(self):
        city = _engine.extract_city("weather forecast for london")
        assert city.lower() == "london"

    def test_reminder_extraction_minutes(self):
        seconds, message = _engine.extract_reminder(
            "remind me in 10 minutes to drink water"
        )
        assert seconds == 600
        assert "drink water" in message

    def test_reminder_extraction_seconds(self):
        seconds, message = _engine.extract_reminder(
            "set a reminder for 30 seconds to check the oven"
        )
        assert seconds == 30

    def test_reminder_extraction_word_number(self):
        seconds, message = _engine.extract_reminder(
            "remind me in five minutes to take a break"
        )
        assert seconds == 300


# ── Edge case tests ─────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_input(self):
        intent, confidence = _engine.classify("")
        assert intent == "unknown"

    def test_gibberish(self):
        intent, confidence = _engine.classify("asdfghjkl qwerty")
        assert intent == "unknown"

    def test_confidence_returned(self):
        intent, confidence = _engine.classify("hello")
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

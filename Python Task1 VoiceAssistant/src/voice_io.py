"""
Voice I/O module — handles microphone input (speech-to-text) and
speaker output (text-to-speech).

Speech recognition uses the Google Web Speech API via the
SpeechRecognition library. Text-to-speech uses pyttsx3 (offline).
"""

import speech_recognition as sr
import pyttsx3
import threading


# ── TTS engine (singleton, lazily initialized) ──────────────────────
# pyttsx3 engines are not thread-safe, so we guard with a lock.

_tts_engine: pyttsx3.Engine | None = None
_tts_lock = threading.Lock()


def _get_tts_engine() -> pyttsx3.Engine:
    """
    Return the shared pyttsx3 engine, creating it on first call.
    Adjusting speech rate slightly slower than default for clarity.
    """
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init()
        # Default rate is ~200 wpm; 170 is more natural for an assistant
        _tts_engine.setProperty("rate", 170)
        # Use the first available voice (system default)
        voices = _tts_engine.getProperty("voices")
        if voices:
            _tts_engine.setProperty("voice", voices[0].id)
    return _tts_engine


def speak(text: str) -> None:
    """
    Speak the given text aloud using pyttsx3.

    Thread-safe: acquires a lock before using the engine so that
    background threads (e.g., reminders) can also call speak().
    """
    if not text:
        return
    print(f"[ASSISTANT] {text}")
    with _tts_lock:
        engine = _get_tts_engine()
        engine.say(text)
        engine.runAndWait()


def listen(timeout: int = 5, phrase_time_limit: int = 10) -> str | None:
    """
    Listen for speech through the microphone and return the recognised text.

    Args:
        timeout: Maximum seconds to wait for speech to begin.
        phrase_time_limit: Maximum seconds of speech to capture.

    Returns:
        Recognised text as a lowercase string, or None if recognition
        failed or no speech was detected.

    Error behaviour:
        - Microphone unavailable → prints a message, returns None.
        - No speech detected → returns None (caller should re-prompt).
        - Network/API error → prints a message, returns None.
    """
    recognizer = sr.Recognizer()

    # Adjust for ambient noise sensitivity
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            # Brief calibration for background noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("[LISTENING] Speak now...")
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
            )
    except OSError:
        print("[MIC ERROR] Microphone is not available or not connected.")
        return None
    except sr.WaitTimeoutError:
        # User didn't say anything within the timeout
        return None
    except Exception as exc:
        print(f"[MIC ERROR] Unexpected microphone error: {exc}")
        return None

    # Attempt recognition via Google Web Speech API (free tier)
    try:
        text = recognizer.recognize_google(audio)
        recognised = text.strip().lower()
        print(f"[YOU] {recognised}")
        return recognised
    except sr.UnknownValueError:
        # Speech was detected but could not be transcribed
        return None
    except sr.RequestError as exc:
        print(f"[NETWORK ERROR] Speech recognition service unavailable: {exc}")
        return None

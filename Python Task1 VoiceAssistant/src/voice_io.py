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


# ── Microphone selection helper ──────────────────────────────────────

# ── Microphone selection helper ──────────────────────────────────────

_cached_mic_index: int | None = None
_cached_sample_rate: int = 48000


def list_available_microphones() -> list[tuple[int, str]]:
    """
    Return a list of functional input microphones formatted as (device_index, display_name).
    Filters out output devices, virtual mappers, and inactive channels.
    """
    import pyaudio
    p = pyaudio.PyAudio()
    devices = []
    seen_names = set()

    for idx in range(p.get_device_count()):
        try:
            dev = p.get_device_info_by_index(idx)
            name = dev.get("name", "").strip()
            channels = dev.get("maxInputChannels", 0)
            rate = int(dev.get("defaultSampleRate", 44100))
            name_lower = name.lower()

            if channels <= 0 or "output" in name_lower or "mapper" in name_lower or "stereo mix" in name_lower:
                continue

            # Try a quick test open
            s = p.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, input_device_index=idx, frames_per_buffer=512)
            s.close()

            # Format user-friendly name
            clean_name = f"{name} ({rate}Hz)"
            if clean_name not in seen_names:
                seen_names.add(clean_name)
                devices.append((idx, clean_name))
        except Exception:
            continue

    p.terminate()
    return devices


def set_active_microphone(index: int) -> None:
    """Manually set the active microphone device index."""
    global _cached_mic_index, _cached_sample_rate
    import pyaudio
    p = pyaudio.PyAudio()
    try:
        dev = p.get_device_info_by_index(index)
        _cached_sample_rate = int(dev.get("defaultSampleRate", 48000))
        _cached_mic_index = index
        print(f"[MIC] Switched to Device {index} ({dev.get('name')}) at {_cached_sample_rate}Hz")
    except Exception as exc:
        print(f"[MIC ERROR] Could not switch to device {index}: {exc}")
    finally:
        p.terminate()


def get_working_microphone() -> sr.Microphone:
    """
    Find and return a functional Microphone instance.
    - If user set a specific microphone via set_active_microphone or .env, use it.
    - If a USB microphone or headset is connected, prioritizes it over internal laptop mics.
    - Otherwise picks the best active internal microphone with live signal.
    """
    global _cached_mic_index, _cached_sample_rate

    # 1. Check if user configured a specific index in .env
    from src.utils.config import get_env
    env_index = get_env("MICROPHONE_INDEX")
    if env_index and env_index.isdigit():
        set_active_microphone(int(env_index))
        return sr.Microphone(device_index=_cached_mic_index, sample_rate=_cached_sample_rate)

    # 2. Return cached working index if already selected
    if _cached_mic_index is not None:
        try:
            return sr.Microphone(device_index=_cached_mic_index, sample_rate=_cached_sample_rate)
        except Exception:
            _cached_mic_index = None

    # 3. Find available devices and prioritize USB / Headset mics
    try:
        available = list_available_microphones()
        chosen_idx = None
        chosen_rate = 48000

        # Prioritize USB / Headset devices (like Device 14)
        for idx, desc in available:
            desc_l = desc.lower()
            if ("usb" in desc_l or "headset" in desc_l) and "48000" in desc_l:
                chosen_idx = idx
                chosen_rate = 48000
                break

        if chosen_idx is None:
            for idx, desc in available:
                desc_l = desc.lower()
                if "usb" in desc_l or "headset" in desc_l:
                    chosen_idx = idx
                    break

        # Fallback to any active internal microphone (e.g. 48000Hz)
        if chosen_idx is None:
            for idx, desc in available:
                if "48000" in desc:
                    chosen_idx = idx
                    chosen_rate = 48000
                    break

        # Last resort: first available valid mic
        if chosen_idx is None and available:
            chosen_idx = available[0][0]

        if chosen_idx is not None:
            set_active_microphone(chosen_idx)
            return sr.Microphone(device_index=_cached_mic_index, sample_rate=_cached_sample_rate)

    except Exception as exc:
        print(f"[MIC WARNING] Auto-detection failed: {exc}")

    # Fallback to default
    return sr.Microphone()


def listen(timeout: int = 10, phrase_time_limit: int = 14) -> str | None:
    """
    Listen for speech through the microphone and return the recognised text.
    Uses safe energy calibration so that speech isn't absorbed as background noise.
    """
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.0
    recognizer.non_speaking_duration = 0.5

    try:
        mic = get_working_microphone()
        with mic as source:
            # Very fast background noise sample (0.2s)
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            
            # Clamp threshold so human speech is always picked up
            if recognizer.energy_threshold > 800:
                recognizer.energy_threshold = 450
            elif recognizer.energy_threshold < 150:
                recognizer.energy_threshold = 300

            print(f"[LISTENING] Listening actively... (threshold: {recognizer.energy_threshold:.0f})")
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
            )
    except OSError as exc:
        print(f"[MIC ERROR] Microphone is unavailable or not connected: {exc}")
        return None
    except sr.WaitTimeoutError:
        print("[MIC TIMEOUT] No speech detected within the timeout period.")
        return None
    except Exception as exc:
        print(f"[MIC ERROR] Unexpected microphone error: {exc}")
        return None

    # Attempt recognition via Google Web Speech API
    # Try en-IN first (optimal for Indian English), fallback to en-US
    for lang in ["en-IN", "en-US"]:
        try:
            print(f"[STT] Contacting speech service ({lang})...")
            text = recognizer.recognize_google(audio, language=lang)
            recognised = text.strip().lower()
            print(f"[YOU] {recognised}")
            return recognised
        except sr.UnknownValueError:
            continue
        except sr.RequestError as exc:
            print(f"[NETWORK ERROR] Speech recognition service error: {exc}")
            break

    print("[STT] Speech was detected but could not be understood.")
    return None

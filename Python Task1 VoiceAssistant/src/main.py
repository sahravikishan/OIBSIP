"""
Main entry point for the Voice Assistant.

Lifecycle:
1. Load configuration and environment variables.
2. Initialise the intent engine and custom commands.
3. Greet the user.
4. Enter the main loop: listen → classify → dispatch → speak.
5. Shut down gracefully on 'exit' intent or KeyboardInterrupt.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so imports work when running
# this file directly (python src/main.py)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.voice_io import speak, listen
from src.intent_engine import IntentEngine
from src.dispatcher import dispatch
from src.handlers.custom_commands import load_custom_commands
from src.handlers.reminders import cancel_all_reminders
from src.gui import launch_gui


def run_cli() -> None:
    """Run the voice assistant in interactive terminal CLI mode."""

    # ── Startup ──────────────────────────────────────────────────────
    print("=" * 55)
    print("  VOICE ASSISTANT — OIBSIP Task 1 (Advanced)")
    print("=" * 55)
    print()

    # Load custom commands from config file
    load_custom_commands()

    # Initialise the NLP intent engine
    print("[INIT] Building intent engine...")
    engine = IntentEngine()
    print("[INIT] Intent engine ready.")
    print()

    # Greet the user
    speak("Hello! I'm your voice assistant. How can I help you?")
    print()
    print("Tip: Say 'exit', 'quit', or 'goodbye' to stop.")
    print("-" * 55)

    # ── Main loop ────────────────────────────────────────────────────
    while True:
        try:
            # Listen for user speech
            user_text = listen(timeout=6, phrase_time_limit=12)

            if user_text is None:
                # No speech detected or recognition failed
                speak("I didn't catch that. Could you please repeat?")
                continue

            # Classify the intent
            intent, confidence = engine.classify(user_text)
            print(f"[INTENT] {intent} (confidence: {confidence:.2f})")

            # Check for exit intent before dispatching
            if intent == "exit":
                speak("Goodbye! Have a great day.")
                break

            # Dispatch to the appropriate handler
            response = dispatch(
                intent=intent,
                confidence=confidence,
                raw_text=user_text,
                intent_engine=engine,
                listen_fn=listen,
                speak_fn=speak,
            )

            # Speak the response (some handlers speak directly, returning None)
            if response:
                speak(response)

        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Interrupted by user.")
            speak("Shutting down. Goodbye!")
            break
        except Exception as exc:
            # Catch-all: do not crash the assistant
            print(f"[ERROR] Unexpected error: {exc}")
            speak("Something went wrong on my end. Let's try again.")
            continue

    # ── Cleanup ──────────────────────────────────────────────────────
    cancel_all_reminders()
    print("\n[SHUTDOWN] Voice assistant stopped.")


def main() -> None:
    """Entry point: runs GUI mode by default, or CLI mode if --cli flag is given."""
    if "--cli" in sys.argv:
        run_cli()
    else:
        launch_gui()


if __name__ == "__main__":
    main()

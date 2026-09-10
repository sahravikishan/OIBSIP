# OIBSIP Task 1 — Advanced Voice Assistant

A Python-based voice assistant built as part of the Oasis Infobyte Python Programming Internship (OIBSIP). The assistant listens to spoken commands through a microphone, understands natural-language requests using NLTK-based NLP intent classification, responds using text-to-speech, and performs useful actions including weather lookups, email sending, timed reminders, and more.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Objectives](#objectives)
3. [Features](#features)
4. [Technologies Used](#technologies-used)
5. [Architecture](#architecture)
6. [Project Structure](#project-structure)
7. [Installation](#installation)
8. [Configuration](#configuration)
9. [How to Run](#how-to-run)
10. [Example Voice Commands](#example-voice-commands)
11. [Error Handling](#error-handling)
12. [Privacy Considerations](#privacy-considerations)
13. [Security Considerations](#security-considerations)
14. [Screenshots](#screenshots)
15. [Limitations](#limitations)
16. [Future Improvements](#future-improvements)

---

## Project Overview

This voice assistant captures speech input from a microphone, converts it to text using the Google Web Speech API (via the `SpeechRecognition` library), classifies the user's intent using an NLTK-based NLP engine, executes the appropriate action, and responds audibly using pyttsx3 text-to-speech.

Unlike simple keyword-matching assistants, this project uses **bag-of-stems cosine similarity** for intent classification — tokenizing and stemming input text, vectorizing it against a trained vocabulary, and selecting the intent with the highest similarity score above a confidence threshold.

---

## Objectives

- Listen to spoken commands through a microphone
- Understand natural-language requests using NLP (not just keyword matching)
- Respond using text-to-speech
- Perform useful actions (time, date, search, email, weather, reminders, knowledge QA)
- Use APIs where required (OpenWeatherMap, Google Web Speech, Wikipedia)
- Handle errors gracefully with spoken feedback
- Support reminders and custom commands
- Document privacy and data processing clearly

---

## Features

### Beginner Features

| Feature | Description |
|---------|-------------|
| **Microphone Voice Input** | Captures speech via `speech_recognition` with ambient noise calibration |
| **Hello Greeting** | Recognises "hello", "hi", "hey", "good morning" etc. with time-appropriate responses |
| **Current Time** | Reports the current time in a natural spoken format |
| **Current Date** | Reports today's date in a natural spoken format |
| **Web Search** | Opens Google search in the default browser for spoken queries |
| **Graceful Error Handling** | Handles mic errors, network errors, API failures, and unrecognised speech without crashing |
| **Text-to-Speech** | All responses spoken aloud via pyttsx3 with a clean reusable `speak()` function |

### Advanced Features

| Feature | Description |
|---------|-------------|
| **NLP Intent Recognition** | NLTK-based bag-of-stems cosine similarity classifier — not keyword matching |
| **Voice-Controlled Email** | Interactive voice flow to compose and send emails via SMTP with TLS |
| **Timed Reminders** | Background threaded reminders with audible TTS alerts |
| **Live Weather** | Real-time weather from OpenWeatherMap API (temperature, conditions, humidity, wind) |
| **General Knowledge QA** | Local JSON knowledge base with stem-overlap matching + Wikipedia API fallback |
| **Custom Commands** | User-configurable URL shortcuts loaded from `config/custom_commands.json` |
| **Privacy Documentation** | Clear documentation of data processing and external services |

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3.13 | Core language |
| `speech_recognition` | Microphone input and speech-to-text (Google Web Speech API) |
| `pyttsx3` | Offline text-to-speech |
| `nltk` | Tokenization and stemming for NLP intent classification |
| `datetime` | Time and date information |
| `webbrowser` | Opening web searches and custom command URLs |
| `smtplib` | Sending emails via SMTP with TLS |
| `requests` | HTTP requests to OpenWeatherMap and Wikipedia APIs |
| `python-dotenv` | Loading environment variables from `.env` file |
| `threading` | Background timer threads for reminders |
| `PyAudio` | Microphone audio capture backend |

---

## Architecture

The project follows a modular architecture with separated responsibilities:

```
┌─────────────────────────────────────────────────┐
│                    main.py                       │
│         (Application lifecycle & loop)           │
│                                                  │
│    listen() → classify() → dispatch() → speak()  │
└──────┬────────────┬──────────────┬───────────────┘
       │            │              │
  ┌────▼────┐  ┌────▼─────┐  ┌────▼──────┐
  │voice_io │  │  intent   │  │dispatcher │
  │         │  │  engine   │  │           │
  │ speak() │  │           │  │ Routes to │
  │listen() │  │ classify()│  │ handlers  │
  └─────────┘  │ extract() │  └─────┬─────┘
               └───────────┘        │
                              ┌─────▼─────────────┐
                              │     handlers/      │
                              │                    │
                              │ greetings.py       │
                              │ datetime_info.py   │
                              │ web_search.py      │
                              │ email_sender.py    │
                              │ weather.py         │
                              │ reminders.py       │
                              │ knowledge.py       │
                              │ custom_commands.py  │
                              └────────────────────┘
```

**Key design decisions:**
- **`voice_io.py`**: Single module for all speech I/O with thread-safe TTS locking
- **`intent_engine.py`**: NLTK-based classifier using bag-of-stems cosine similarity
- **`dispatcher.py`**: Decouples intent classification from action execution
- **`handlers/`**: Each feature is self-contained in its own file
- **`utils/config.py`**: Centralised environment variable management

---

## Project Structure

```
Python Task1 VoiceAssistant/
│
├── src/
│   ├── __init__.py              # Package marker
│   ├── main.py                  # Entry point — routes to GUI or CLI
│   ├── gui.py                   # Tkinter desktop interface (Nova Voice Assistant)
│   ├── voice_io.py              # Microphone capture + TTS output
│   ├── intent_engine.py         # NLTK-based NLU: tokenize → classify → extract
│   ├── dispatcher.py            # Maps intents → handler functions
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── greetings.py         # Greeting responses
│   │   ├── datetime_info.py     # Time & date
│   │   ├── web_search.py        # Browser search
│   │   ├── email_sender.py      # SMTP email workflow
│   │   ├── weather.py           # OpenWeatherMap integration
│   │   ├── reminders.py         # Threaded timed reminders
│   │   ├── knowledge.py         # Local knowledge base + Wikipedia QA
│   │   └── custom_commands.py   # User-configurable commands
│   └── utils/
│       ├── __init__.py
│       └── config.py            # Environment variable loader
│
├── config/
│   └── custom_commands.json     # User-editable custom commands
│
├── data/
│   └── knowledge_base.json      # Local knowledge base (30 Q&A pairs)
│
├── tests/
│   ├── __init__.py
│   └── test_intent_engine.py    # Unit tests for intent classification
│
├── screenshots/                  # Screenshots for documentation
├── .env.example                  # Placeholder environment variables
├── .gitignore                    # Excludes .env, __pycache__, venv
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## Installation

### Prerequisites

- Python 3.10 or higher
- A working microphone
- Internet connection (for speech recognition, weather API, Wikipedia fallback)

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/OIBSIP.git
cd "OIBSIP/Python Task1 VoiceAssistant"
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download NLTK Data

```bash
python -c "import nltk; nltk.download('punkt_tab')"
```

### Step 5: Microphone Setup

- Ensure a microphone is connected and set as the default input device
- On Windows: Settings → Sound → Input → Select your microphone
- The assistant uses `PyAudio` as the audio backend

> **Note**: If `PyAudio` fails to install, you may need to install it from a pre-built wheel:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

---

## Configuration

### Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Email Configuration (use a test/dummy account only)
EMAIL_ADDRESS=your_test_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# OpenWeatherMap API Key
OPENWEATHER_API_KEY=your_api_key_here
```

### OpenWeatherMap API Setup

1. Go to [openweathermap.org](https://openweathermap.org/)
2. Create a free account
3. Navigate to API Keys in your profile
4. Copy your API key
5. Paste it into `.env` as `OPENWEATHER_API_KEY`

### Email Configuration

1. Use a **test/dummy Gmail account** (not your primary email)
2. Enable 2-Factor Authentication on the Google account
3. Generate an App Password: Google Account → Security → App Passwords
4. Use the generated App Password as `EMAIL_PASSWORD` in `.env`

> **Security Warning**: Never use your primary email account. Never commit `.env` to version control.

### Custom Commands

Edit `config/custom_commands.json` to add your own URL shortcuts:

```json
{
    "open github": "https://github.com/",
    "open gmail": "https://mail.google.com/",
    "open youtube": "https://www.youtube.com/"
}
```

- Keys are the trigger phrases (spoken commands)
- Values must be `http://` or `https://` URLs
- No shell commands are allowed (security restriction)
- The assistant loads these at startup — no code changes needed

---

## How to Run

### GUI Desktop Mode (Default)

```bash
cd "Python Task1 VoiceAssistant"
python src/main.py
```
*(or run directly: `python src/gui.py`)*

This launches the **Nova Voice Assistant** desktop window featuring:
- **[ 🎙 Start Listening ]** interactive microphone button
- Live status indicator: `Ready`, `Listening...`, `Processing...`, `Speaking...`, `Error`
- Scrollable conversation history (`YOU` and `NOVA`)
- Quick action buttons: `Time`, `Weather`, `Search`, `Help`, `Clear`, and `Exit`

### Terminal / CLI Mode

If you prefer running in the terminal without a GUI:

```bash
python src/main.py --cli
```

---

## Example Voice Commands

| What you say | Intent | What happens |
|--------------|--------|--------------|
| "Hello" / "Hi there" / "Hey assistant" | greeting | Time-appropriate spoken greeting |
| "What time is it?" / "Tell me the current time" | time | Speaks the current time |
| "What's today's date?" / "What day is it?" | date | Speaks today's date |
| "Search Python decorators" / "Look up machine learning" | web_search | Opens Google search in browser |
| "Send an email" / "Compose an email" | send_email | Starts interactive email flow |
| "What's the weather in Pune?" / "How hot is it in Delhi?" | weather | Speaks live weather data |
| "Remind me in 10 minutes to drink water" | reminder | Sets a background timer with TTS alert |
| "What is Python?" / "What is the capital of France?" | general_knowledge | Answers from local KB or Wikipedia |
| "Open GitHub" / "Open Gmail" | custom_command | Opens the configured URL in browser |
| "Exit" / "Goodbye" / "Quit" | exit | Shuts down the assistant gracefully |

---

## Error Handling

The assistant handles errors gracefully without crashing:

| Error Scenario | Response |
|----------------|----------|
| No speech detected | "I didn't catch that. Could you please repeat?" |
| Microphone unavailable | Printed error message, returns to listening |
| Network unavailable | "Speech recognition service unavailable" / appropriate message |
| Invalid weather city | "I couldn't find weather data for 'XYZ'" |
| Weather API key missing | "Please set OPENWEATHER_API_KEY in your environment variables" |
| Email not configured | "Please set EMAIL_ADDRESS and EMAIL_PASSWORD" |
| Email auth failure | "Email authentication failed. Check your credentials." |
| Invalid email recipient | "The recipient address does not look valid" |
| Unknown command | "I'm not sure I understood that. Could you please rephrase?" |
| Malformed custom_commands.json | Warning printed, custom commands disabled |
| Knowledge question not found | "I don't have enough information to answer that" |
| Any unexpected error | "Something went wrong on my end. Let's try again." |

---

## Privacy Considerations

This section explains how the voice assistant processes data:

### Microphone Input
- The microphone is activated only when the assistant is listening for commands
- Audio is captured in memory and sent to the **Google Web Speech API** for transcription
- **No voice recordings are stored** on disk or sent to any other service
- Audio data is discarded immediately after transcription

### External API Usage

| Service | Data Sent | Purpose |
|---------|-----------|---------|
| Google Web Speech API | Audio data | Converting speech to text |
| OpenWeatherMap API | City name | Retrieving weather information |
| Wikipedia REST API | Search query text | Answering general knowledge questions |

### Email
- Email credentials (address, password) are stored **locally** in a `.env` file
- Credentials are loaded into memory at runtime via environment variables
- **No credentials are stored in source code** or committed to version control
- Email content (recipient, subject, body) is transmitted to the configured SMTP server

### Command History
- **No command history is stored**. Each spoken command is processed in memory and discarded after the response is generated
- No logs of user commands are written to disk

### Third-Party Services
- **Google Web Speech API**: Free tier, used for speech-to-text. Subject to Google's privacy policy
- **OpenWeatherMap API**: Free tier, used for weather data. Only the city name is sent
- **Wikipedia API**: Free, used for general knowledge fallback. Only the search query is sent
- **SMTP Server**: Used to send emails. Only email content is transmitted to the configured server

### What This Assistant Does NOT Do
- Does not store voice recordings
- Does not track or log user activity
- Does not share data with third parties beyond the APIs listed above
- Does not store passwords in source code
- Does not execute arbitrary shell commands

---

## Security Considerations

- **No hard-coded credentials**: All secrets are loaded from environment variables
- **`.env` file**: Listed in `.gitignore` to prevent accidental commits
- **`.env.example`**: Contains only placeholder values with no real credentials
- **Custom commands**: Only `http://` and `https://` URLs are allowed — no shell command execution
- **Email**: Uses SMTP with TLS encryption for secure transmission
- **API keys**: Loaded from environment variables, never embedded in source code

---

## Screenshots

> Add screenshots of the assistant in action here before final submission.
> 
> Suggested screenshots:
> 1. Assistant startup
> 2. Greeting response
> 3. Time/Date response
> 4. Web search opening browser
> 5. Weather response
> 6. Reminder confirmation and alert
> 7. General knowledge answer
> 8. Custom command execution
> 9. Error handling (unrecognised speech)

---

## Limitations

- **Speech recognition** requires an internet connection (uses Google Web Speech API)
- **Text-to-speech** quality depends on the system's installed speech engine
- **Intent classification** uses a vocabulary derived from training phrases — very unusual phrasings may not be classified correctly
- **Weather** requires a valid OpenWeatherMap API key
- **Email** requires a properly configured SMTP account with an App Password
- **Wikipedia fallback** requires an internet connection and may not have answers for very niche questions
- **Reminders** are lost if the assistant is shut down before they fire
- The assistant processes **one command at a time** (sequential, not concurrent)

---

## Future Improvements

- Add offline speech recognition (e.g., Vosk or PocketSphinx)
- Implement a wake word ("Hey Assistant") for hands-free activation
- Add support for multiple languages
- Implement persistent reminder storage (survive restarts)
- Add a GUI or web interface
- Expand the local knowledge base
- Add calendar integration
- Implement conversation context (multi-turn dialogue)
- Add support for music playback
- Implement voice authentication

"""
Intent Engine — classifies free-form user speech into action intents
using NLTK-based NLP (tokenization, stemming, bag-of-stems cosine similarity).

This is NOT simple keyword matching. The approach:
1. Each intent has multiple example training phrases.
2. All phrases are tokenized and stemmed to build a shared vocabulary.
3. Each training phrase becomes a bag-of-stems frequency vector.
4. User input is vectorized the same way and compared against all
   training vectors using cosine similarity.
5. The intent with the highest similarity above a confidence threshold
   is returned. Below threshold → 'unknown'.
"""

import math
import re
from collections import Counter

import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize


# ── Training data: intent → list of example phrases ────────────────
# Each intent has varied phrasings so the vectorizer can generalise.

TRAINING_DATA: dict[str, list[str]] = {
    "greeting": [
        "hello",
        "hello assistant",
        "hi",
        "hi there",
        "hey",
        "hey assistant",
        "good morning",
        "good afternoon",
        "good evening",
        "howdy",
        "what's up",
        "greetings",
    ],
    "time": [
        "what time is it",
        "tell me the current time",
        "what is the time now",
        "what time do we have",
        "current time please",
        "can you tell me the time",
        "time right now",
        "do you know the time",
    ],
    "date": [
        "what is today's date",
        "what's the date today",
        "tell me the date",
        "today's date please",
        "what day is it",
        "current date",
        "could you tell me today's date",
        "which date is today",
    ],
    "web_search": [
        "search for something",
        "search the internet for",
        "look up something online",
        "google something",
        "google this topic",
        "google it for me",
        "google artificial intelligence",
        "google python programming",
        "search python decorators",
        "look up machine learning",
        "search for weather in pune",
        "i want you to search the internet",
        "can you search for",
        "find information about",
        "search online for",
        "web search for",
        "Open Youtube",
        "Open Facebook",
        "Open Twitter",
        "Open Instagram",
        "Open LinkedIn",
        "Open Reddit",
        "Open Google",
        "Open Stack Overflow",
        "Open GitHub",
        "Open Gmail",
        "Open Outlook",
        "Open Microsoft Teams",
        "Open Microsoft Word",
        "Open Microsoft Excel",
        "Open Microsoft Powerpoint",
        "Open Microsoft OneNote",
        "Open Microsoft OneDrive",
        "Open Microsoft Teams",
        "Open Microsoft Outlook",

    ],
    "send_email": [
        "send an email",
        "send email",
        "compose an email",
        "i want to send an email",
        "write an email",
        "email someone",
        "can you send an email for me",
        "help me send an email",
        "compose a message",
        "send a mail",

    ],
    "reminder": [
        "remind me in ten minutes to drink water",
        "set a reminder for thirty seconds",
        "remind me to check the oven",
        "set a reminder",
        "remind me in five minutes",
        "create a reminder",
        "alert me in one hour",
        "remind me later",
        "set a timer for two minutes",
        "remind me to take medicine",
        "can you set a reminder for me",
        "help me set a reminder",
        "set a reminder for tomorrow",
        "set a reminder for next week",
        "set a reminder for next month",
        "set a reminder for next year",
        "set a reminder for next day",
        "set a reminder for next hour",
        "set a reminder for next minute",
        "set a reminder for next second",
        "set a reminder for next week",
        "set a reminder for next month",
        "set a reminder for next year",
        "set a reminder for next day",
        "set a reminder for next hour",
        "set a reminder for next minute",
        "set a reminder for next second",
    ],
    "weather": [
        "what's the weather in pune",
        "tell me the weather in mumbai",
        "how hot is it in delhi",
        "weather forecast for london",
        "what is the weather like",
        "current weather in new york",
        "is it raining in bangalore",
        "temperature in chennai",
        "how is the weather today",
        "weather report for hyderabad",
        "weather in sao paulo",
        "weather in sydney",
        "weather in tokyo",
        "weather in seoul",
    ],
    "general_knowledge": [
        "what is python",
        "what is machine learning",
        "what is the capital of france",
        "who invented the telephone",
        "what is artificial intelligence",
        "tell me about the solar system",
        "what is the speed of light",
        "who is the president of the united states",
        "what is quantum computing",
        "define photosynthesis",
        "explain gravity",
        "what is deep learning",
    ],
    "custom_command": [
        "open github",
        "open gmail",
        "open youtube",
        "open google",
        "open stackoverflow",
        "launch github",
        "go to gmail",
    ],
    "exit": [
        "exit",
        "quit",
        "bye",
        "goodbye",
        "stop",
        "shut down",
        "close the assistant",
        "that's all",
        "see you later",
        "i'm done",
        "terminate",
    ],
}


class IntentEngine:
    """
    Classifies user text into one of the predefined intents using
    bag-of-stems cosine similarity against training phrases.
    """

    CONFIDENCE_THRESHOLD = 0.25  # minimum similarity to accept an intent

    def __init__(self) -> None:
        self._stemmer = PorterStemmer()
        # Build vocabulary and training vectors
        self._vocabulary: list[str] = []
        self._training_vectors: list[tuple[str, list[float]]] = []
        self._build_model()

    # ── Model construction ──────────────────────────────────────────

    def _tokenize_and_stem(self, text: str) -> list[str]:
        """Tokenize text into words, lowercase, remove non-alpha, and stem."""
        tokens = word_tokenize(text.lower())
        return [self._stemmer.stem(t) for t in tokens if t.isalpha()]

    def _build_model(self) -> None:
        """
        Build the vocabulary and vectorize all training phrases.
        Called once during __init__.
        """
        # Collect all stems across all training phrases to form vocabulary
        all_stems: set[str] = set()
        phrase_stems: list[tuple[str, list[str]]] = []

        for intent, phrases in TRAINING_DATA.items():
            for phrase in phrases:
                stems = self._tokenize_and_stem(phrase)
                phrase_stems.append((intent, stems))
                all_stems.update(stems)

        self._vocabulary = sorted(all_stems)
        vocab_index = {stem: i for i, stem in enumerate(self._vocabulary)}

        # Vectorize each training phrase as a bag-of-stems frequency vector
        for intent, stems in phrase_stems:
            vector = [0.0] * len(self._vocabulary)
            counts = Counter(stems)
            for stem, count in counts.items():
                if stem in vocab_index:
                    vector[vocab_index[stem]] = float(count)
            self._training_vectors.append((intent, vector))

    # ── Cosine similarity ───────────────────────────────────────────

    @staticmethod
    def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = math.sqrt(sum(a * a for a in vec_a))
        mag_b = math.sqrt(sum(b * b for b in vec_b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    # ── Classification ──────────────────────────────────────────────

    def classify(self, text: str) -> tuple[str, float]:
        """
        Classify user text into an intent.

        Returns:
            (intent_name, confidence) where confidence is the cosine
            similarity score. If below threshold, intent is 'unknown'.
        """
        stems = self._tokenize_and_stem(text)
        if not stems:
            return ("unknown", 0.0)

        # Vectorize input
        vocab_index = {stem: i for i, stem in enumerate(self._vocabulary)}
        input_vector = [0.0] * len(self._vocabulary)
        counts = Counter(stems)
        for stem, count in counts.items():
            if stem in vocab_index:
                input_vector[vocab_index[stem]] = float(count)

        # Compare against all training vectors
        best_intent = "unknown"
        best_score = 0.0

        for intent, train_vec in self._training_vectors:
            score = self._cosine_similarity(input_vector, train_vec)
            if score > best_score:
                best_score = score
                best_intent = intent

        if best_score < self.CONFIDENCE_THRESHOLD:
            return ("unknown", best_score)

        return (best_intent, best_score)

    # ── Entity extraction ───────────────────────────────────────────

    def extract_search_query(self, text: str) -> str:
        """
        Extract the search query from a web_search intent.
        Strips common search-related preambles to isolate the actual query.
        """
        # Remove common lead-in phrases
        patterns = [
            r"(?:can you |please |i want you to )?(?:search|look up|google|find)"
            r"(?: the internet| online| the web)?"
            r"(?: for| about)?",
            r"(?:find |get )(?:information |info )(?:about |on )?",
        ]
        query = text.lower().strip()
        for pattern in patterns:
            query = re.sub(pattern, "", query, count=1).strip()

        # Clean up leftover leading articles/prepositions
        query = re.sub(r"^(?:the |a |an |on |about )", "", query).strip()
        return query if query else text

    def extract_city(self, text: str) -> str:
        """
        Extract the city name from a weather intent.
        Looks for 'in <city>' pattern or returns the last meaningful words.
        """
        # Try "in <city>" pattern first
        match = re.search(r"\bin\s+([a-zA-Z\s]+?)(?:\s+(?:right now|today|now|please))?$",
                          text.lower())
        if match:
            return match.group(1).strip().title()

        # Try "weather [forecast/report] [in/for] <city>"
        match = re.search(
            r"weather\s+(?:forecast\s+|report\s+|conditions\s+)?"
            r"(?:in\s+|for\s+|of\s+)?([a-zA-Z\s]+)",
            text.lower(),
        )
        if match:
            city = match.group(1).strip()
            # Remove trailing filler words
            city = re.sub(r"\s+(?:right now|today|now|please)$", "", city)
            return city.title()

        # Fallback: return empty (handler will ask the user)
        return ""

    def extract_reminder(self, text: str) -> tuple[int | None, str]:
        """
        Extract duration (in seconds) and the reminder message from
        a reminder intent.

        Returns:
            (seconds, message) — seconds is None if parsing fails.
        """
        text_lower = text.lower()

        # Number words → digits mapping
        word_to_num = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
            "thirty": 30, "forty": 40, "forty five": 45, "sixty": 60,
            "half": 30,  # "half an hour" handled separately
        }

        # Time unit multipliers
        unit_seconds = {
            "second": 1, "seconds": 1,
            "minute": 60, "minutes": 60,
            "hour": 3600, "hours": 3600,
        }

        # Try "in <number/word> <unit>" pattern
        # Matches: "in 10 minutes", "in ten minutes", "for 30 seconds"
        pattern = (
            r"(?:in|for|after)\s+"
            r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
            r"eleven|twelve|fifteen|twenty|thirty|forty|forty five|sixty|half)"
            r"\s*(seconds?|minutes?|hours?|an?\s+hour)"
        )
        match = re.search(pattern, text_lower)

        seconds = None
        if match:
            num_str = match.group(1)
            unit_str = match.group(2).strip()

            # Convert number
            if num_str.isdigit():
                num = int(num_str)
            else:
                num = word_to_num.get(num_str)
                if num is None:
                    num = 1  # fallback

            # Convert unit
            if "hour" in unit_str:
                multiplier = 3600
            else:
                multiplier = unit_seconds.get(unit_str, 60)

            # Special case: "half an hour"
            if num_str == "half" and "hour" in unit_str:
                seconds = 1800
            else:
                seconds = num * multiplier

        # Extract the reminder message — text after "to" or "that"
        msg_match = re.search(r"\bto\s+(.+?)(?:\s+in\s+\d|\s*$)", text_lower)
        if not msg_match:
            msg_match = re.search(r"\bthat\s+(.+)", text_lower)
        if not msg_match:
            # Try extracting everything after the time specification
            msg_match = re.search(
                r"(?:seconds?|minutes?|hours?)\s+(?:to\s+)?(.+)", text_lower
            )

        message = msg_match.group(1).strip() if msg_match else "your reminder"

        return (seconds, message)

    def extract_custom_command(self, text: str) -> str:
        """Return the cleaned text to match against custom command keys."""
        return text.lower().strip()

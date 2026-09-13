"""
Knowledge handler — answers general-knowledge questions using a local
knowledge base (JSON file) with NLTK-based fuzzy matching, and falls
back to the Wikipedia API for broader coverage.

Approach:
- Primary: Local KB with ~30 curated Q&A pairs. User questions are
  compared against KB keys using stem overlap scoring.
- Fallback: Wikipedia REST API summary endpoint (free, no key needed).
- If neither source has an answer: honest "I don't know" response.
"""

import json
from pathlib import Path

import requests
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize


_stemmer = PorterStemmer()

# ── Load the local knowledge base ───────────────────────────────────

_KB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge_base.json"
_knowledge_base: dict[str, str] = {}

try:
    with open(_KB_PATH, "r", encoding="utf-8") as f:
        _raw = json.load(f)
    if isinstance(_raw, dict):
        _knowledge_base = {k.lower().strip(): v for k, v in _raw.items()}
except FileNotFoundError:
    print("[KNOWLEDGE] knowledge_base.json not found. Local QA unavailable.")
except json.JSONDecodeError:
    print("[KNOWLEDGE] knowledge_base.json is malformed. Local QA unavailable.")


# Common question stop words that should not trigger false positive matches
_STOP_WORDS = {
    "what", "is", "are", "the", "a", "an", "who", "which",
    "how", "tell", "me", "about", "your", "can", "you", "do",
    "of", "in", "to", "for", "please", "my"
}


def _stem_set(text: str, remove_stop_words: bool = False) -> set[str]:
    """Return the set of stems from the given text."""
    tokens = word_tokenize(text.lower())
    if remove_stop_words:
        tokens = [t for t in tokens if t not in _STOP_WORDS]
    return {_stemmer.stem(t) for t in tokens if t.isalpha()}


def _search_local_kb(question: str) -> str | None:
    """
    Search the local knowledge base.
    1. Tests exact string match first.
    2. Compares content-word stem overlap (ignoring stop words like 'what', 'is').
    3. Requires substantive keyword overlap to prevent false positive answers.
    """
    if not _knowledge_base:
        return None

    q_clean = question.lower().strip().rstrip("?.!")
    if q_clean in _knowledge_base:
        return _knowledge_base[q_clean]

    # Partial substring match for common questions
    for key, answer in _knowledge_base.items():
        if key in q_clean or q_clean in key:
            return answer

    # Content-word stem matching (excluding stop words)
    q_content_stems = _stem_set(question, remove_stop_words=True)
    if not q_content_stems:
        return None

    best_match = None
    best_score = 0.0

    for key, answer in _knowledge_base.items():
        k_content_stems = _stem_set(key, remove_stop_words=True)
        if not k_content_stems:
            continue

        overlap = len(q_content_stems & k_content_stems)
        if overlap == 0:
            continue

        union = len(q_content_stems | k_content_stems)
        score = overlap / union if union else 0.0

        if score > best_score:
            best_score = score
            best_match = answer

    # Require at least 50% substantive keyword overlap
    if best_score >= 0.5 and best_match:
        return best_match

    return None


def _search_wikipedia(query: str) -> str | None:
    """
    Query the Wikipedia REST API for a short summary.
    Returns the extract text or None if not found.

    Privacy note: This sends the search query to the Wikipedia API.
    """
    # Use Wikipedia's REST API summary endpoint
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(query)}"

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "VoiceAssistant/1.0 (student project)"},
            timeout=8,
        )
        if response.status_code != 200:
            return None

        data = response.json()
        extract = data.get("extract", "")
        if extract and len(extract) > 20:
            # Truncate to first two sentences for spoken brevity
            sentences = extract.split(". ")
            short = ". ".join(sentences[:2])
            if not short.endswith("."):
                short += "."
            return short
    except (requests.RequestException, ValueError, KeyError):
        return None

    return None


def handle_knowledge(question: str) -> str:
    """
    Answer a general-knowledge question.

    1. Searches the local knowledge base first.
    2. Falls back to Wikipedia summary if not found locally.
    3. Returns an honest "I don't know" if neither source has an answer.

    Args:
        question: The user's question as text.

    Returns:
        The answer as a spoken sentence.
    """
    if not question or not question.strip():
        return "Could you repeat your question? I didn't catch it."

    # Try local KB first
    local_answer = _search_local_kb(question)
    if local_answer:
        return local_answer

    # Fall back to Wikipedia
    # Extract a cleaner search term by removing question words
    search_term = question.lower()
    for prefix in ["what is ", "what are ", "who is ", "who was ",
                    "define ", "explain ", "tell me about ",
                    "what's ", "who invented ", "what does ", "describe "]:
        if search_term.startswith(prefix):
            search_term = search_term[len(prefix):]
            break

    wiki_answer = _search_wikipedia(search_term.strip())
    if wiki_answer:
        return wiki_answer

    return "I don't have enough information to answer that. You could try a web search."

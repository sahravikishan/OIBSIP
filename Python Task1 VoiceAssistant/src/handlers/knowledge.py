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


def _stem_set(text: str) -> set[str]:
    """Return the set of stems from the given text."""
    tokens = word_tokenize(text.lower())
    return {_stemmer.stem(t) for t in tokens if t.isalpha()}


def _search_local_kb(question: str) -> str | None:
    """
    Search the local knowledge base by comparing stem overlap between
    the user's question and each KB key. Returns the answer for the
    best match above a threshold, or None.
    """
    if not _knowledge_base:
        return None

    question_stems = _stem_set(question)
    if not question_stems:
        return None

    best_match = None
    best_score = 0.0

    for key, answer in _knowledge_base.items():
        key_stems = _stem_set(key)
        if not key_stems:
            continue
        # Jaccard-like overlap: intersection / union
        overlap = len(question_stems & key_stems)
        union = len(question_stems | key_stems)
        score = overlap / union if union else 0.0

        if score > best_score:
            best_score = score
            best_match = answer

    # Require at least 40% overlap to consider it a match
    if best_score >= 0.4 and best_match:
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

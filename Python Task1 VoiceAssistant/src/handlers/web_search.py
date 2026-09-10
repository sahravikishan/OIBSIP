"""
Web search handler — opens the user's default browser with a Google search.
"""

import webbrowser
import urllib.parse


def handle_search(query: str) -> str:
    """
    Open a Google search for the given query in the default browser.

    Args:
        query: The search terms extracted from user speech.

    Returns:
        Confirmation message to speak.
    """
    if not query or not query.strip():
        return "I didn't catch what you want to search for. Could you repeat that?"

    # URL-encode the query for safe inclusion in the URL
    encoded = urllib.parse.quote_plus(query.strip())
    url = f"https://www.google.com/search?q={encoded}"

    try:
        webbrowser.open(url)
        return f"Searching the web for {query}."
    except webbrowser.Error:
        return "I wasn't able to open your browser. Please check your system settings."

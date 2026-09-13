import re
from typing import Dict, List

# Standard emoji shortcode mappings
EMOJI_MAP: Dict[str, str] = {
    # Smileys & Emotions
    ":smile:": "😄",
    ":grinning:": "😀",
    ":laughing:": "😆",
    ":joy:": "😂",
    ":rofl:": "🤣",
    ":blush:": "😊",
    ":wink:": "😉",
    ":heart_eyes:": "😍",
    ":sunglasses:": "😎",
    ":thinking:": "🤔",
    ":neutral:": "😐",
    ":smirk:": "😏",
    ":cry:": "😢",
    ":sob:": "😭",
    ":angry:": "😠",
    ":exploding_head:": "🤯",
    ":partying:": "🥳",
    ":sleeping:": "😴",
    ":pleading:": "🥺",
    ":sweat_smile:": "😅",
    ":relieved:": "😌",
    ":nerd:": "🤓",

    # Gestures & People
    ":thumbsup:": "👍",
    ":thumbsdown:": "👎",
    ":clap:": "👏",
    ":wave:": "👋",
    ":handshake:": "🤝",
    ":pray:": "🙏",
    ":muscle:": "💪",
    ":ok_hand:": "👌",
    ":point_up:": "☝️",
    ":eyes:": "👀",
    ":salute:": "🫡",

    # Hearts & Symbols
    ":heart:": "❤️",
    ":blue_heart:": "💙",
    ":green_heart:": "💚",
    ":sparkles:": "✨",
    ":star:": "⭐",
    ":fire:": "🔥",
    ":100:": "💯",
    ":check:": "✅",
    ":cross:": "❌",
    ":warning:": "⚠️",
    ":question:": "❓",
    ":exclamation:": "❗",
    ":lock:": "🔒",
    ":key:": "🔑",

    # Objects & Activities
    ":rocket:": "🚀",
    ":tada:": "🎉",
    ":party:": "🥳",
    ":coffee:": "☕",
    ":pizza:": "🍕",
    ":beer:": "🍺",
    ":computer:": "💻",
    ":bulb:": "💡",
    ":book:": "📖",
    ":bug:": "🐛",
    ":wrench:": "🔧",
    ":bell:": "🔔",
    ":chat:": "💬"
}

# Regex to match any candidate shortcode like :smile: or :thumbs_up:
SHORTCODE_REGEX = re.compile(r":([a-zA-Z0-9_+-]+):")

def parse_emoji(text: str) -> str:
    """
    Replace recognized emoji shortcodes with their Unicode characters.
    Unrecognized shortcodes (e.g. :foobar:) are left intact without error.
    """
    if not text or not isinstance(text, str):
        return text

    def replace_match(match: re.Match) -> str:
        code = match.group(0)
        return EMOJI_MAP.get(code, code)

    return SHORTCODE_REGEX.sub(replace_match, text)

def get_emoji_catalog() -> List[Dict[str, str]]:
    """Return list of shortcodes and emojis for frontend selector."""
    return [{"code": code, "char": char} for code, char in EMOJI_MAP.items()]

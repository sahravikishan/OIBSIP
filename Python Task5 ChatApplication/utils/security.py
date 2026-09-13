import re
from typing import Tuple
from werkzeug.security import generate_password_hash, check_password_hash

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,25}$")
ROOM_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\- ]{2,32}$")

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-SHA256 with salt."""
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against its PBKDF2 hash."""
    if not password or not password_hash:
        return False
    return check_password_hash(password_hash, password)

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format and length."""
    if not username or not isinstance(username, str):
        return False, "Username is required."
    username = username.strip()
    if len(username) < 3 or len(username) > 25:
        return False, "Username must be between 3 and 25 characters."
    if not USERNAME_PATTERN.match(username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens."
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength minimums."""
    if not password or not isinstance(password, str):
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if len(password) > 128:
        return False, "Password is too long (maximum 128 characters)."
    return True, ""

def validate_room_name(name: str) -> Tuple[bool, str]:
    """Validate room name format and length."""
    if not name or not isinstance(name, str):
        return False, "Room name is required."
    name = name.strip()
    if len(name) < 2 or len(name) > 32:
        return False, "Room name must be between 2 and 32 characters."
    if not ROOM_NAME_PATTERN.match(name):
        return False, "Room name can only contain letters, numbers, spaces, hyphens, and underscores."
    return True, ""

def validate_room_passcode(passcode: str) -> Tuple[bool, str]:
    """Validate room passcode format (e.g. 4-12 alphanumeric characters/digits)."""
    if not passcode:
        return True, ""  # Passcode is optional
    passcode = passcode.strip()
    if len(passcode) < 3 or len(passcode) > 16:
        return False, "Room passcode must be between 3 and 16 characters."
    return True, ""

def validate_message_content(content: str) -> Tuple[bool, str]:
    """Validate message length and non-emptiness."""
    if not content or not isinstance(content, str):
        return False, "Message cannot be empty."
    content = content.strip()
    if len(content) == 0:
        return False, "Message cannot be blank."
    if len(content) > 2000:
        return False, "Message exceeds the maximum limit of 2000 characters."
    return True, ""



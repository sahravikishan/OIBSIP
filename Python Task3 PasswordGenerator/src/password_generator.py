"""
Cryptographically secure password generation module for OIBSIP Task 3.

Security Notice:
- Uses Python's `secrets` module for all randomness.
- Under NO circumstances is the standard `random` module imported or used.
"""

from dataclasses import dataclass
import secrets
import string
from typing import List, Set


# Standard character sets
UPPERCASE_CHARS: str = string.ascii_uppercase
LOWERCASE_CHARS: str = string.ascii_lowercase
DIGIT_CHARS: str = string.digits
SYMBOL_CHARS: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"

# Set of characters that are often visually ambiguous across fonts/displays
AMBIGUOUS_CHARS: Set[str] = set("0Oo1lI|`'\"")

# Validation limits
MIN_PASSWORD_LENGTH: int = 8
MAX_PASSWORD_LENGTH: int = 128
MIN_CHARACTER_TYPES: int = 2


class PasswordGeneratorError(Exception):
    """Base exception for password generator errors."""
    pass


class ValidationError(PasswordGeneratorError):
    """Raised when user criteria fails validation."""
    pass


@dataclass(frozen=True)
class PasswordCriteria:
    """Encapsulates user-selected criteria for password generation."""
    length: int = 16
    include_uppercase: bool = True
    include_lowercase: bool = True
    include_digits: bool = True
    include_symbols: bool = True
    exclude_ambiguous: bool = False


def _cryptographic_fisher_yates_shuffle(items: List[str]) -> List[str]:
    """
    Shuffles a list of characters in-place using the Fisher-Yates algorithm,
    driven strictly by cryptographically secure `secrets.randbelow`.
    
    Guarantees unbiased permutation without using `random.shuffle`.
    """
    arr = list(items)
    for i in range(len(arr) - 1, 0, -1):
        # secrets.randbelow(i + 1) generates a cryptographically secure
        # integer j uniformly in [0, i]
        j = secrets.randbelow(i + 1)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def validate_criteria(criteria: PasswordCriteria) -> None:
    """
    Validates password generation criteria.
    Raises ValidationError with a clear, user-friendly message upon failure.
    """
    if not isinstance(criteria.length, int):
        raise ValidationError("Password length must be a valid whole number.")

    if criteria.length < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Password length must be at least {MIN_PASSWORD_LENGTH} characters."
        )

    if criteria.length > MAX_PASSWORD_LENGTH:
        raise ValidationError(
            f"Password length cannot exceed {MAX_PASSWORD_LENGTH} characters."
        )

    selected_types_count = sum([
        criteria.include_uppercase,
        criteria.include_lowercase,
        criteria.include_digits,
        criteria.include_symbols,
    ])

    if selected_types_count < MIN_CHARACTER_TYPES:
        raise ValidationError(
            f"Please select at least {MIN_CHARACTER_TYPES} character types."
        )


def get_active_pools(criteria: PasswordCriteria) -> List[str]:
    """
    Builds the active character pools based on criteria.
    Filters ambiguous characters if requested, ensuring none of the selected
    pools become empty.
    """
    pools: List[str] = []

    def filter_pool(chars: str) -> str:
        if criteria.exclude_ambiguous:
            return "".join(c for c in chars if c not in AMBIGUOUS_CHARS)
        return chars

    if criteria.include_uppercase:
        pool = filter_pool(UPPERCASE_CHARS)
        if not pool:
            raise ValidationError("Uppercase character set became empty after ambiguous exclusion.")
        pools.append(pool)

    if criteria.include_lowercase:
        pool = filter_pool(LOWERCASE_CHARS)
        if not pool:
            raise ValidationError("Lowercase character set became empty after ambiguous exclusion.")
        pools.append(pool)

    if criteria.include_digits:
        pool = filter_pool(DIGIT_CHARS)
        if not pool:
            raise ValidationError("Digits character set became empty after ambiguous exclusion.")
        pools.append(pool)

    if criteria.include_symbols:
        pool = filter_pool(SYMBOL_CHARS)
        if not pool:
            raise ValidationError("Symbols character set became empty after ambiguous exclusion.")
        pools.append(pool)

    return pools


def generate_secure_password(criteria: PasswordCriteria) -> str:
    """
    Generates a cryptographically secure random password satisfying:
    1. Input validation (length, type count).
    2. Guaranteed representation: At least one character from EVERY selected pool.
    3. Securely fills remaining slots using `secrets.choice`.
    4. Cryptographically shuffles all positions using Fisher-Yates with `secrets.randbelow`.
    
    Returns the generated password string.
    """
    validate_criteria(criteria)

    active_pools = get_active_pools(criteria)

    # 1. Guarantee at least 1 character from each selected pool
    password_chars: List[str] = []
    for pool in active_pools:
        password_chars.append(secrets.choice(pool))

    # 2. Combine all active pools to fill remaining character slots
    combined_pool = "".join(active_pools)
    remaining_length = criteria.length - len(password_chars)

    for _ in range(remaining_length):
        password_chars.append(secrets.choice(combined_pool))

    # 3. Cryptographically shuffle the characters to remove any positional predictability
    shuffled_chars = _cryptographic_fisher_yates_shuffle(password_chars)

    return "".join(shuffled_chars)

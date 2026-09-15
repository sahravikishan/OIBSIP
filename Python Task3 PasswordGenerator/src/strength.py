"""
Password strength evaluation module for OIBSIP Task 3.

Evaluates password strength based on:
1. Length
2. Character set diversity (Uppercase, Lowercase, Digits, Symbols)
3. Shannon pool entropy approximation

Classification levels:
- Weak (Score < 50)
- Medium (Score 50 - 74)
- Strong (Score >= 75)
"""

import math
import string
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class StrengthAssessment:
    """Holds assessment metrics for a password."""
    score: int               # 0 to 100
    level: str               # "Weak", "Medium", "Strong"
    color_hex: str           # Hex color code for UI display
    entropy_bits: float      # Approximate information entropy in bits
    feedback: str            # Friendly guidance string


def calculate_entropy(password: str) -> float:
    """
    Approximates the entropy of the password in bits based on character pool size:
    Entropy = Length * log2(Pool Size)
    """
    if not password:
        return 0.0

    pool_size = 0
    has_lower = any(c in string.ascii_lowercase for c in password)
    has_upper = any(c in string.ascii_uppercase for c in password)
    has_digits = any(c in string.digits for c in password)
    has_symbols = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" or (not c.isalnum() and not c.isspace()) for c in password)

    if has_lower:
        pool_size += 26
    if has_upper:
        pool_size += 26
    if has_digits:
        pool_size += 10
    if has_symbols:
        pool_size += 32

    if pool_size == 0:
        return 0.0

    return len(password) * math.log2(pool_size)


def assess_password_strength(password: str) -> StrengthAssessment:
    """
    Computes an approximate strength score (0-100) and classification.
    
    Scoring criteria:
    - Length contributes up to 50 points.
    - Diversity contributes up to 40 points.
    - Diversity combinations and entropy boost contribute up to 10 points.
    """
    if not password:
        return StrengthAssessment(
            score=0,
            level="Empty",
            color_hex="#94a3b8",
            entropy_bits=0.0,
            feedback="No password entered or generated yet."
        )

    length = len(password)

    # 1. Length scoring (0 - 50 points)
    if length < 8:
        length_score = length * 3.5  # < 28 points
    elif length <= 12:
        length_score = 28 + (length - 8) * 4  # 28 to 44
    elif length <= 16:
        length_score = 44 + (length - 12) * 1.25  # 44 to 49
    else:
        length_score = 50

    # 2. Diversity scoring (0 - 40 points)
    has_lower = any(c in string.ascii_lowercase for c in password)
    has_upper = any(c in string.ascii_uppercase for c in password)
    has_digits = any(c in string.digits for c in password)
    has_symbols = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" or (not c.isalnum() and not c.isspace()) for c in password)

    types_present = sum([has_lower, has_upper, has_digits, has_symbols])
    diversity_score = 0
    if has_lower:
        diversity_score += 8
    if has_upper:
        diversity_score += 10
    if has_digits:
        diversity_score += 10
    if has_symbols:
        diversity_score += 12

    # Bonus for 3 or 4 types
    bonus = 0
    if types_present == 4:
        bonus += 10
    elif types_present == 3:
        bonus += 5

    # Penalties
    penalty = 0
    # Penalty if only 1 type
    if types_present <= 1:
        penalty += 20
    # Penalty if very short even if varied
    if length < 8:
        penalty += 25

    total_score = max(0, min(100, int(round(length_score + diversity_score + bonus - penalty))))
    entropy_bits = round(calculate_entropy(password), 1)

    # Classification
    if total_score < 50:
        level = "Weak"
        color = "#ef4444"  # Red
        feedback = "Weak: Consider increasing length and adding more character types."
    elif total_score < 75:
        level = "Medium"
        color = "#f59e0b"  # Amber / Warm Gold
        feedback = "Medium: Good, but adding more length or symbols makes it stronger."
    else:
        level = "Strong"
        color = "#10b981"  # Emerald Green
        feedback = "Strong: Excellent length and character diversity."

    return StrengthAssessment(
        score=total_score,
        level=level,
        color_hex=color,
        entropy_bits=entropy_bits,
        feedback=feedback
    )

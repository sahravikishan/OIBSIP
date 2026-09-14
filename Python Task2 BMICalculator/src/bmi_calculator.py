"""
BMI Calculator Business Logic Module.

Provides robust validation, exact BMI arithmetic, and standard category
classification according to the Oasis Infobyte Task 2 specification.
"""

from typing import Tuple


class ValidationError(ValueError):
    """Raised when user input fails numerical or logical validation."""
    pass


# Exact category definitions and display color hex codes
CATEGORY_UNDERWEIGHT = "Underweight"
CATEGORY_NORMAL = "Normal"
CATEGORY_OVERWEIGHT = "Overweight"
CATEGORY_OBESE = "Obese"

# Accessible, high-contrast palette for visual feedback
CATEGORY_COLORS = {
    CATEGORY_UNDERWEIGHT: "#1976D2",  # Informative Blue / Accent
    CATEGORY_NORMAL: "#2E7D32",       # Balanced Green
    CATEGORY_OVERWEIGHT: "#F57C00",   # Cautionary Amber / Orange
    CATEGORY_OBESE: "#D32F2F",        # Alert Red
}


def validate_name(name: str) -> str:
    """
    Validate a user name string.

    Rejects:
      - None or empty string
      - Whitespace-only string
    """
    if not name or not name.strip():
        raise ValidationError("Please enter a user name.")
    return name.strip()


def validate_measurement(value_str: str, field_name: str) -> float:
    """
    Validate and parse a measurement input string (weight in kg or height in m).

    Rejects:
      - Empty string or whitespace
      - Non-numeric or alphabetic strings
      - Negative values
      - Zero values
    """
    if not value_str or not value_str.strip():
        raise ValidationError(f"Please enter a valid numeric {field_name.lower()}.")

    cleaned = value_str.strip()
    try:
        val = float(cleaned)
    except ValueError:
        raise ValidationError(f"Please enter a valid numeric {field_name.lower()}.")

    if val == 0:
        raise ValidationError(f"{field_name} must be greater than zero.")
    if val < 0:
        raise ValidationError(f"{field_name} must be greater than zero.")

    # Prevent astronomically absurd inputs that cause float overflows
    if val > 1000:
        raise ValidationError(f"{field_name} exceeds realistic limits (must be <= 1000).")

    return val


def calculate_bmi(weight: float, height: float) -> float:
    """
    Calculate Body Mass Index (BMI) using the exact formula:
        BMI = weight / (height^2)
    where weight is in kilograms and height is in meters.

    Returns:
        BMI value rounded to exactly 2 decimal places.
    """
    if height <= 0:
        raise ValidationError("Height must be greater than zero.")
    if weight <= 0:
        raise ValidationError("Weight must be greater than zero.")

    raw_bmi = weight / (height ** 2)
    return round(raw_bmi, 2)


def classify_bmi(bmi: float) -> Tuple[str, str]:
    """
    Classify a calculated BMI into standard categories:
      - Underweight: BMI < 18.5
      - Normal: 18.5 <= BMI <= 24.9
      - Overweight: 25 <= BMI <= 29.9
      - Obese: BMI >= 30

    Returns:
        tuple of (category_name, hex_color)
    """
    if bmi < 18.5:
        category = CATEGORY_UNDERWEIGHT
    elif bmi <= 24.9:
        category = CATEGORY_NORMAL
    elif bmi <= 29.9:
        category = CATEGORY_OVERWEIGHT
    else:
        category = CATEGORY_OBESE

    color = CATEGORY_COLORS[category]
    return category, color

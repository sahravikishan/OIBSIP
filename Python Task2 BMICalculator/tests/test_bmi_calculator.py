"""
Unit tests for BMI calculation, input validation, and category classification.
"""

import unittest
from src.bmi_calculator import (
    ValidationError,
    validate_name,
    validate_measurement,
    calculate_bmi,
    classify_bmi,
    CATEGORY_UNDERWEIGHT,
    CATEGORY_NORMAL,
    CATEGORY_OVERWEIGHT,
    CATEGORY_OBESE,
)


class TestBMICalculator(unittest.TestCase):

    def test_validate_name_valid(self):
        self.assertEqual(validate_name("Ravi"), "Ravi")
        self.assertEqual(validate_name("  Amit Sharma  "), "Amit Sharma")

    def test_validate_name_invalid(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_name("")
        self.assertIn("user name", str(ctx.exception).lower())

        with self.assertRaises(ValidationError) as ctx:
            validate_name("    ")
        self.assertIn("user name", str(ctx.exception).lower())

    def test_validate_measurement_valid(self):
        self.assertEqual(validate_measurement("70", "Weight"), 70.0)
        self.assertEqual(validate_measurement("72.5", "Weight"), 72.5)
        self.assertEqual(validate_measurement("1.75", "Height"), 1.75)
        self.assertEqual(validate_measurement("  1.82  ", "Height"), 1.82)

    def test_validate_measurement_invalid_non_numeric(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_measurement("abc", "Weight")
        self.assertIn("valid numeric weight", str(ctx.exception).lower())

        with self.assertRaises(ValidationError) as ctx:
            validate_measurement("70kg", "Weight")
        self.assertIn("valid numeric weight", str(ctx.exception).lower())

        with self.assertRaises(ValidationError) as ctx:
            validate_measurement("", "Height")
        self.assertIn("valid numeric height", str(ctx.exception).lower())

    def test_validate_measurement_zero_and_negative(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_measurement("0", "Weight")
        self.assertIn("greater than zero", str(ctx.exception).lower())

        with self.assertRaises(ValidationError) as ctx:
            validate_measurement("-5", "Height")
        self.assertIn("greater than zero", str(ctx.exception).lower())

        with self.assertRaises(ValidationError) as ctx:
            validate_measurement("-70.5", "Weight")
        self.assertIn("greater than zero", str(ctx.exception).lower())

    def test_calculate_bmi_values_and_rounding(self):
        # Example 1: 70 kg, 1.75 m -> 70 / 3.0625 = 22.85714... -> 22.86
        bmi1 = calculate_bmi(70, 1.75)
        self.assertEqual(bmi1, 22.86)

        # Example 2: 85 kg, 1.80 m -> 85 / 3.24 = 26.23456... -> 26.23
        bmi2 = calculate_bmi(85, 1.80)
        self.assertEqual(bmi2, 26.23)

        # Example 3: 50 kg, 1.65 m -> 50 / 2.7225 = 18.3654... -> 18.37
        bmi3 = calculate_bmi(50, 1.65)
        self.assertEqual(bmi3, 18.37)

        # Check that result is rounded to exactly 2 decimal places
        self.assertEqual(str(bmi1).split(".")[1], "86")

    def test_calculate_bmi_invalid_args(self):
        with self.assertRaises(ValidationError):
            calculate_bmi(0, 1.75)
        with self.assertRaises(ValidationError):
            calculate_bmi(70, 0)
        with self.assertRaises(ValidationError):
            calculate_bmi(-70, 1.75)
        with self.assertRaises(ValidationError):
            calculate_bmi(70, -1.75)

    def test_classify_bmi_boundaries(self):
        # Underweight: < 18.5
        cat, _ = classify_bmi(16.0)
        self.assertEqual(cat, CATEGORY_UNDERWEIGHT)
        cat, _ = classify_bmi(18.49)
        self.assertEqual(cat, CATEGORY_UNDERWEIGHT)

        # Normal: 18.5 to 24.9
        cat, _ = classify_bmi(18.5)
        self.assertEqual(cat, CATEGORY_NORMAL)
        cat, _ = classify_bmi(22.86)
        self.assertEqual(cat, CATEGORY_NORMAL)
        cat, _ = classify_bmi(24.9)
        self.assertEqual(cat, CATEGORY_NORMAL)

        # Overweight: 25.0 to 29.9
        cat, _ = classify_bmi(25.0)
        self.assertEqual(cat, CATEGORY_OVERWEIGHT)
        cat, _ = classify_bmi(26.23)
        self.assertEqual(cat, CATEGORY_OVERWEIGHT)
        cat, _ = classify_bmi(29.9)
        self.assertEqual(cat, CATEGORY_OVERWEIGHT)

        # Obese: >= 30.0
        cat, _ = classify_bmi(30.0)
        self.assertEqual(cat, CATEGORY_OBESE)
        cat, _ = classify_bmi(34.8)
        self.assertEqual(cat, CATEGORY_OBESE)


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for password_generator module.
Verifies security, constraints, character guarantees, and ambiguous exclusion.
"""

import string
import unittest
from src.password_generator import (
    PasswordCriteria,
    ValidationError,
    generate_secure_password,
    validate_criteria,
    AMBIGUOUS_CHARS,
    UPPERCASE_CHARS,
    LOWERCASE_CHARS,
    DIGIT_CHARS,
    SYMBOL_CHARS
)


class TestPasswordGenerator(unittest.TestCase):

    def test_minimum_length_validation(self):
        """Length below 8 must be rejected."""
        criteria = PasswordCriteria(length=7, include_uppercase=True, include_lowercase=True)
        with self.assertRaises(ValidationError) as ctx:
            validate_criteria(criteria)
        self.assertIn("at least 8", str(ctx.exception))

    def test_maximum_length_validation(self):
        """Excessive length must be rejected to prevent memory abuse."""
        criteria = PasswordCriteria(length=200, include_uppercase=True, include_lowercase=True)
        with self.assertRaises(ValidationError) as ctx:
            validate_criteria(criteria)
        self.assertIn("cannot exceed", str(ctx.exception))

    def test_non_integer_length(self):
        """Non-integer length must be rejected."""
        # type: ignore for runtime safety testing
        criteria = PasswordCriteria(length="16", include_uppercase=True, include_lowercase=True) # type: ignore
        with self.assertRaises(ValidationError):
            validate_criteria(criteria)

    def test_insufficient_character_types(self):
        """Selecting fewer than 2 character types must be rejected."""
        # 0 types
        criteria_none = PasswordCriteria(
            length=12,
            include_uppercase=False,
            include_lowercase=False,
            include_digits=False,
            include_symbols=False
        )
        with self.assertRaises(ValidationError) as ctx:
            validate_criteria(criteria_none)
        self.assertIn("at least 2", str(ctx.exception))

        # 1 type
        criteria_one = PasswordCriteria(
            length=12,
            include_uppercase=True,
            include_lowercase=False,
            include_digits=False,
            include_symbols=False
        )
        with self.assertRaises(ValidationError) as ctx:
            validate_criteria(criteria_one)
        self.assertIn("at least 2", str(ctx.exception))

    def test_guaranteed_representation_all_types(self):
        """
        Critical requirement: If all 4 types are selected, EVERY generated password
        must contain at least 1 uppercase, 1 lowercase, 1 digit, and 1 symbol.
        Test across 100 successive generations.
        """
        criteria = PasswordCriteria(
            length=10,
            include_uppercase=True,
            include_lowercase=True,
            include_digits=True,
            include_symbols=True
        )

        for _ in range(100):
            pwd = generate_secure_password(criteria)
            self.assertEqual(len(pwd), 10)
            self.assertTrue(any(c in UPPERCASE_CHARS for c in pwd), "Missing uppercase!")
            self.assertTrue(any(c in LOWERCASE_CHARS for c in pwd), "Missing lowercase!")
            self.assertTrue(any(c in DIGIT_CHARS for c in pwd), "Missing digit!")
            self.assertTrue(any(c in SYMBOL_CHARS for c in pwd), "Missing symbol!")

    def test_guaranteed_representation_subset(self):
        """
        Verify guarantees when only 2 types are chosen (e.g. Lowercase and Symbols).
        """
        criteria = PasswordCriteria(
            length=8,
            include_uppercase=False,
            include_lowercase=True,
            include_digits=False,
            include_symbols=True
        )

        for _ in range(50):
            pwd = generate_secure_password(criteria)
            self.assertEqual(len(pwd), 8)
            self.assertTrue(any(c in LOWERCASE_CHARS for c in pwd))
            self.assertTrue(any(c in SYMBOL_CHARS for c in pwd))
            self.assertFalse(any(c in UPPERCASE_CHARS for c in pwd))
            self.assertFalse(any(c in DIGIT_CHARS for c in pwd))

    def test_ambiguous_character_exclusion(self):
        """
        When exclude_ambiguous is True, no ambiguous character should ever appear.
        """
        criteria = PasswordCriteria(
            length=32,
            include_uppercase=True,
            include_lowercase=True,
            include_digits=True,
            include_symbols=True,
            exclude_ambiguous=True
        )

        for _ in range(50):
            pwd = generate_secure_password(criteria)
            for ch in pwd:
                self.assertNotIn(ch, AMBIGUOUS_CHARS, f"Ambiguous character '{ch}' found in password!")

    def test_no_random_module_used(self):
        """
        Strict security check: inspect password_generator module to ensure `random`
        is not imported.
        """
        import src.password_generator as pg_mod
        self.assertNotIn("random", dir(pg_mod), "Security violation: 'random' module imported in password_generator!")
        with open(pg_mod.__file__, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertNotIn("import random", code)
        self.assertNotIn("from random", code)


if __name__ == "__main__":
    unittest.main()

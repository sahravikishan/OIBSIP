"""
Unit tests for strength assessment module.
"""

import unittest
from src.strength import assess_password_strength, calculate_entropy


class TestStrengthAssessment(unittest.TestCase):

    def test_empty_password(self):
        result = assess_password_strength("")
        self.assertEqual(result.score, 0)
        self.assertEqual(result.level, "Empty")

    def test_weak_password_short(self):
        # Short with few characters
        result = assess_password_strength("ab12")
        self.assertEqual(result.level, "Weak")
        self.assertLess(result.score, 50)

    def test_weak_password_single_type(self):
        # Single type long password is still vulnerable
        result = assess_password_strength("aaaaaaaa")
        self.assertEqual(result.level, "Weak")

    def test_medium_password(self):
        # Length 10 with 2 or 3 types
        result = assess_password_strength("Abcdef12")
        self.assertEqual(result.level, "Medium")
        self.assertTrue(50 <= result.score < 75)

    def test_strong_password(self):
        # Length 16 with all 4 character types
        result = assess_password_strength("K9#mQ2!vL7$zW1*x")
        self.assertEqual(result.level, "Strong")
        self.assertGreaterEqual(result.score, 75)
        self.assertGreater(result.entropy_bits, 60.0)

    def test_entropy_monotonic(self):
        # Longer password of same complexity should have higher entropy
        ent1 = calculate_entropy("aA1!")
        ent2 = calculate_entropy("aA1!bB2@")
        self.assertGreater(ent2, ent1)


if __name__ == "__main__":
    unittest.main()

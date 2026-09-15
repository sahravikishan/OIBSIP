"""
Unit tests for GUI components and actions.
Exercises Tkinter widgets, event callbacks, history limits, and validation handlers.
"""

import unittest
import tkinter as tk
from unittest.mock import patch
from src.gui import PasswordGeneratorGUI


class TestPasswordGeneratorGUI(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Keep window hidden during automated tests
        self.app = PasswordGeneratorGUI(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_gui_initialization_defaults(self):
        """Verify default variable values on startup."""
        self.assertEqual(self.app.var_length.get(), 16)
        self.assertTrue(self.app.var_uppercase.get())
        self.assertTrue(self.app.var_lowercase.get())
        self.assertTrue(self.app.var_digits.get())
        self.assertTrue(self.app.var_symbols.get())
        self.assertFalse(self.app.var_exclude_ambiguous.get())
        self.assertEqual(len(self.app.session_history), 0)

    def test_generate_password_action_success(self):
        """Verify password generation updates UI and session history."""
        self.app.generate_password_action()
        self.assertNotEqual(self.app.current_password, "")
        self.assertEqual(len(self.app.current_password), 16)
        self.assertEqual(len(self.app.session_history), 1)
        self.assertEqual(self.app.session_history[-1], self.app.current_password)

    def test_history_sliding_window_max_five(self):
        """
        Verify that generating 7 passwords keeps ONLY the latest 5,
        evicting the oldest entries.
        """
        generated = []
        for _ in range(7):
            self.app.generate_password_action()
            generated.append(self.app.current_password)

        self.assertEqual(len(self.app.session_history), 5)
        # Should match the last 5 items generated
        self.assertEqual(list(self.app.session_history), generated[-5:])

    def test_clear_history(self):
        """Verify clearing history clears the in-memory deque and UI."""
        self.app.generate_password_action()
        self.assertEqual(len(self.app.session_history), 1)
        self.app.clear_history()
        self.assertEqual(len(self.app.session_history), 0)

    @patch("tkinter.messagebox.showwarning")
    def test_validation_insufficient_types_warning(self, mock_warn):
        """Deselecting all types except one should trigger warning and not crash."""
        self.app.var_uppercase.set(True)
        self.app.var_lowercase.set(False)
        self.app.var_digits.set(False)
        self.app.var_symbols.set(False)

        self.app.generate_password_action()
        mock_warn.assert_called_once()
        self.assertIn("at least 2", mock_warn.call_args[0][1])

    @patch("tkinter.messagebox.showwarning")
    def test_validation_length_too_short_warning(self, mock_warn):
        """Setting length below 8 should trigger warning."""
        self.app.spinbox.delete(0, tk.END)
        self.app.spinbox.insert(0, "6")
        self.app.generate_password_action()
        mock_warn.assert_called_once()
        self.assertIn("at least 8", mock_warn.call_args[0][1])

    @patch("tkinter.messagebox.showerror")
    def test_validation_invalid_length_format_error(self, mock_err):
        """Entering non-numeric string into spinbox triggers error."""
        self.app.spinbox.delete(0, tk.END)
        self.app.spinbox.insert(0, "invalid")
        self.app.generate_password_action()
        mock_err.assert_called_once()

    def test_toggle_history_mask(self):
        """Verify toggling history mask."""
        initial_mask = self.app.history_mask_state
        self.app.toggle_history_mask()
        self.assertNotEqual(self.app.history_mask_state, initial_mask)
        self.app.toggle_history_mask()
        self.assertEqual(self.app.history_mask_state, initial_mask)

    def test_reset_defaults(self):
        """Verify reset defaults restores configurations."""
        self.app.var_length.set(30)
        self.app.var_symbols.set(False)
        self.app.var_exclude_ambiguous.set(True)

        self.app.reset_defaults()
        self.assertEqual(self.app.var_length.get(), 16)
        self.assertTrue(self.app.var_symbols.get())
        self.assertFalse(self.app.var_exclude_ambiguous.get())

    def test_theme_toggle(self):
        """Verify toggling between Light and Dark themes."""
        # Starts in light theme
        self.assertFalse(self.app.is_dark_theme)
        self.assertEqual(self.app.theme["name"], "light")

        # Toggle to dark
        self.app.toggle_theme()
        self.assertTrue(self.app.is_dark_theme)
        self.assertEqual(self.app.theme["name"], "dark")

        # Toggle back to light
        self.app.toggle_theme()
        self.assertFalse(self.app.is_dark_theme)
        self.assertEqual(self.app.theme["name"], "light")


if __name__ == "__main__":
    unittest.main()

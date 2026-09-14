"""
Automated unit and integration tests for the BMICalculatorApp GUI.
"""

import os
import tempfile
import unittest
import tkinter as tk
from unittest.mock import patch

from src.database import DatabaseManager
from src.gui import BMICalculatorApp


class TestBMICalculatorGUI(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_gui_bmi.db")
        self.db = DatabaseManager(db_path=self.db_path)

        # Initialize Tk in withdrawn mode (invisible)
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = BMICalculatorApp(self.root, db_manager=self.db)

    def tearDown(self):
        self.root.destroy()
        self.temp_dir.cleanup()

    def test_gui_initial_state(self):
        self.assertEqual(self.app.lbl_bmi_value.cget("text"), "--.--")
        self.assertEqual(self.app.lbl_category.cget("text"), "Category: Pending Input")
        self.assertEqual(len(self.app.history_tree.get_children()), 0)

    def test_calculate_and_save_workflow(self):
        # Set inputs for Ravi
        self.app.user_var.set("Ravi")
        self.app.weight_var.set("70")
        self.app.height_var.set("1.75")

        self.app._handle_calculate_and_save()

        # Check result card
        self.assertEqual(self.app.lbl_bmi_value.cget("text"), "22.86")
        self.assertEqual(self.app.lbl_category.cget("text"), "Category: Normal")

        # Check Treeview history updated
        records = self.app.history_tree.get_children()
        self.assertEqual(len(records), 1)

        values = self.app.history_tree.item(records[0], "values")
        # values: id, date, weight, height, bmi, category
        self.assertEqual(values[2], "70.0 kg")
        self.assertEqual(values[3], "1.75 m")
        self.assertEqual(values[4], "22.86")
        self.assertEqual(values[5], "Normal")

    def test_multi_user_gui_switching(self):
        # 1. Add record for User 1: Ravi
        self.app.user_var.set("Ravi")
        self.app.weight_var.set("70")
        self.app.height_var.set("1.75")
        self.app._handle_calculate_and_save()

        # 2. Add record for User 2: Amit
        self.app.user_var.set("Amit")
        self.app.weight_var.set("85")
        self.app.height_var.set("1.80")
        self.app._handle_calculate_and_save()

        # Amit should have 1 record currently visible
        amit_records = self.app.history_tree.get_children()
        self.assertEqual(len(amit_records), 1)
        values_amit = self.app.history_tree.item(amit_records[0], "values")
        self.assertEqual(values_amit[4], "26.23")
        self.assertEqual(values_amit[5], "Overweight")

        # 3. Switch back to Ravi in combobox
        self.app.user_var.set("Ravi")
        self.app._on_user_selected(None)

        ravi_records = self.app.history_tree.get_children()
        self.assertEqual(len(ravi_records), 1)
        values_ravi = self.app.history_tree.item(ravi_records[0], "values")
        self.assertEqual(values_ravi[4], "22.86")
        self.assertEqual(values_ravi[5], "Normal")

    def test_reset_fields(self):
        self.app.weight_var.set("80")
        self.app.height_var.set("1.80")
        self.app.lbl_bmi_value.config(text="24.69")

        self.app._handle_reset_fields()

        self.assertEqual(self.app.weight_var.get(), "")
        self.assertEqual(self.app.height_var.get(), "")
        self.assertEqual(self.app.lbl_bmi_value.cget("text"), "--.--")

    @patch("tkinter.messagebox.showwarning")
    def test_validation_rejection_empty_name(self, mock_warn):
        self.app.user_var.set("")
        self.app.weight_var.set("70")
        self.app.height_var.set("1.75")

        self.app._handle_calculate_and_save()
        mock_warn.assert_called_once()
        self.assertIn("user name", mock_warn.call_args[0][1].lower())

    @patch("tkinter.messagebox.showwarning")
    def test_validation_rejection_negative_weight(self, mock_warn):
        self.app.user_var.set("Ravi")
        self.app.weight_var.set("-70")
        self.app.height_var.set("1.75")

        self.app._handle_calculate_and_save()
        mock_warn.assert_called_once()
        self.assertIn("greater than zero", mock_warn.call_args[0][1].lower())

    @patch("tkinter.messagebox.showwarning")
    def test_validation_rejection_zero_height(self, mock_warn):
        self.app.user_var.set("Ravi")
        self.app.weight_var.set("70")
        self.app.height_var.set("0")

        self.app._handle_calculate_and_save()
        mock_warn.assert_called_once()
        self.assertIn("greater than zero", mock_warn.call_args[0][1].lower())

    @patch("tkinter.messagebox.showinfo")
    def test_trend_graph_insufficient_records_notification(self, mock_info):
        self.app.user_var.set("Ravi")
        self.app.weight_var.set("70")
        self.app.height_var.set("1.75")
        self.app._handle_calculate_and_save()  # Only 1 record

        self.app._handle_view_trend_graph()
        mock_info.assert_called_once()
        self.assertIn("at least two bmi records are required", mock_info.call_args[0][1].lower())


if __name__ == "__main__":
    unittest.main()

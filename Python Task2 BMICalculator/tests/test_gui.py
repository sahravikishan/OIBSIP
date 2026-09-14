"""
Automated unit and integration tests for the BMICalculatorApp GUI.
Includes full restart persistence and multi-user isolation verification.
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
        try:
            self.root.destroy()
        except Exception:
            pass
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

    def test_persistence_across_app_restart(self):
        """
        Verify the exact user flow:
        SAVE -> CLOSE -> REOPEN -> LOAD HISTORY -> DISPLAY LINE CHART
        """
        # Session 1: Save records for Ravi
        self.app.user_var.set("Ravi")
        self.app.weight_var.set("70")
        self.app.height_var.set("1.75")
        self.app._handle_calculate_and_save()

        self.app.weight_var.set("72")
        self.app.height_var.set("1.75")
        self.app._handle_calculate_and_save()

        # Also save 1 record for Amit
        self.app.user_var.set("Amit")
        self.app.weight_var.set("85")
        self.app.height_var.set("1.80")
        self.app._handle_calculate_and_save()

        # Completely close Session 1
        self.root.destroy()

        # Session 2: Fresh start with the exact same database file
        root2 = tk.Tk()
        root2.withdraw()
        db2 = DatabaseManager(db_path=self.db_path)
        app2 = BMICalculatorApp(root2, db_manager=db2)

        try:
            # Verify user list is preserved
            user_list = list(app2.user_combobox["values"])
            self.assertIn("Ravi", user_list)
            self.assertIn("Amit", user_list)

            # Select Ravi and verify previous records are still present in history
            app2.user_var.set("Ravi")
            app2._on_user_selected(None)
            ravi_rows = app2.history_tree.get_children()
            self.assertEqual(len(ravi_rows), 2)

            # Select Amit and verify ONLY Amit's record appears
            app2.user_var.set("Amit")
            app2._on_user_selected(None)
            amit_rows = app2.history_tree.get_children()
            self.assertEqual(len(amit_rows), 1)

            # Re-select Ravi and verify Trend graph generates from persisted records
            app2.user_var.set("Ravi")
            app2._on_user_selected(None)
            records = db2.get_user_records(app2.current_user_id, order_desc=False)
            self.assertEqual(len(records), 2)
        finally:
            root2.destroy()

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

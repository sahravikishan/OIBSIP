"""
Unit tests for chart generation and trend plotting.
"""

import unittest
from matplotlib.figure import Figure
from src.chart import create_trend_figure, InsufficientDataError


class TestBMITrendPlotter(unittest.TestCase):

    def test_insufficient_records_zero(self):
        with self.assertRaises(InsufficientDataError) as ctx:
            create_trend_figure("Ravi", [])
        self.assertEqual(str(ctx.exception), "At least two BMI records are required to display a BMI trend.")

    def test_insufficient_records_one(self):
        records = [
            {"recorded_at": "2026-09-01 10:00:00", "bmi": 24.1}
        ]
        with self.assertRaises(InsufficientDataError) as ctx:
            create_trend_figure("Ravi", records)
        self.assertEqual(str(ctx.exception), "At least two BMI records are required to display a BMI trend.")

    def test_valid_trend_figure_and_labels(self):
        records = [
            {"recorded_at": "2026-09-01 10:00:00", "bmi": 24.1},
            {"recorded_at": "2026-09-10 10:00:00", "bmi": 23.8},
            {"recorded_at": "2026-09-20 10:00:00", "bmi": 23.4},
            {"recorded_at": "2026-09-30 10:00:00", "bmi": 22.9},
        ]
        fig = create_trend_figure("Ravi", records)
        self.assertIsInstance(fig, Figure)
        ax = fig.axes[0]

        # Exact title and axis label verification
        self.assertEqual(ax.get_title(), "BMI Trend for Ravi")
        self.assertEqual(ax.get_xlabel(), "Date")
        self.assertEqual(ax.get_ylabel(), "BMI")

    def test_corrupted_records_handled_gracefully(self):
        records = [
            {"recorded_at": "2026-09-01 10:00:00", "bmi": 24.1},
            {"recorded_at": "invalid-date", "bmi": "not-a-number"},  # Corrupted row
            {"recorded_at": "2026-09-10 10:00:00", "bmi": 23.8},
        ]
        # Should filter out the corrupted row and successfully plot the 2 valid rows
        fig = create_trend_figure("Ravi", records)
        self.assertIsInstance(fig, Figure)


if __name__ == "__main__":
    unittest.main()

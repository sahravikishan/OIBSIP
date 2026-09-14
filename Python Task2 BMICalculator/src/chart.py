"""
BMI Trend Visualization Module using Matplotlib.

Generates a line chart showing the selected user's BMI trajectory over time
against standard WHO BMI category thresholds.
"""

from typing import List, Dict, Any
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.dates as mdates

# Set non-interactive backend default to prevent GUI thread conflicts
matplotlib.use("Agg")


class InsufficientDataError(ValueError):
    """Raised when there are fewer than 2 records to plot a trend."""
    pass


def create_trend_figure(user_name: str, records: List[Dict[str, Any]]) -> Figure:
    """
    Generate a Matplotlib Figure plotting a selected user's BMI line chart over time.

    Args:
        user_name: Display name of the selected user.
        records: List of BMI record dictionaries containing 'recorded_at' and 'bmi'.

    Returns:
        matplotlib.figure.Figure: Configured figure ready for display or embedding in Tkinter.

    Raises:
        InsufficientDataError: If fewer than 2 valid records are present.
    """
    if not records or len(records) < 2:
        raise InsufficientDataError("At least two BMI records are required to display a BMI trend.")

    # Filter and validate records gracefully to ignore corrupted or invalid entries
    valid_records = []
    for r in records:
        if not isinstance(r, dict):
            continue
        dt_val = r.get("recorded_at")
        bmi_val = r.get("bmi")
        if dt_val is None or bmi_val is None:
            continue

        try:
            bmi_float = float(bmi_val)
        except (ValueError, TypeError):
            continue

        dt_obj = None
        if isinstance(dt_val, datetime):
            dt_obj = dt_val
        else:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    dt_obj = datetime.strptime(str(dt_val), fmt)
                    break
                except ValueError:
                    pass
            if dt_obj is None:
                try:
                    dt_obj = datetime.fromisoformat(str(dt_val))
                except (ValueError, TypeError):
                    continue

        valid_records.append((dt_obj, bmi_float))

    if len(valid_records) < 2:
        raise InsufficientDataError("At least two BMI records are required to display a BMI trend.")

    # Sort chronologically (oldest to newest)
    valid_records.sort(key=lambda item: item[0])
    dates = [item[0] for item in valid_records]
    bmis = [item[1] for item in valid_records]

    # Create figure with high DPI and clean aesthetics
    fig = Figure(figsize=(7.5, 4.8), dpi=100)
    ax = fig.add_subplot(111)

    # Plot trend line with clear data-point markers
    ax.plot(
        dates,
        bmis,
        marker="o",
        markersize=6.5,
        linewidth=2.2,
        color="#1E88E5",
        label=f"{user_name}'s BMI",
        zorder=5,
    )

    # Add numeric labels at each data point
    for dt, val in zip(dates, bmis):
        ax.annotate(
            f"{val:.2f}",
            (dt, val),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color="#263238",
            zorder=6,
        )

    # Plot WHO category boundary reference bands
    min_y = max(10.0, min(bmis) - 3.0)
    max_y = max(35.0, max(bmis) + 3.0)
    ax.set_ylim(min_y, max_y)

    # Background color bands for standard WHO reference categories
    ax.axhspan(0, 18.5, color="#BBDEFB", alpha=0.35, label="Underweight (< 18.5)")
    ax.axhspan(18.5, 24.9, color="#C8E6C9", alpha=0.35, label="Normal (18.5 – 24.9)")
    ax.axhspan(25.0, 29.9, color="#FFE0B2", alpha=0.35, label="Overweight (25 – 29.9)")
    ax.axhspan(30.0, 100, color="#FFCDD2", alpha=0.35, label="Obese (≥ 30)")

    # Date formatting on X-axis
    span_days = (dates[-1] - dates[0]).total_seconds() / 86400.0
    if span_days < 2.0:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b %H:%M"))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    fig.autofmt_xdate(rotation=25)

    # Exact required labels and title
    ax.set_title(f"BMI Trend for {user_name}", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=10, fontweight="bold", labelpad=8)
    ax.set_ylabel("BMI", fontsize=10, fontweight="bold", labelpad=8)
    ax.grid(True, linestyle="--", alpha=0.5, color="#9E9E9E", zorder=1)

    # Legend
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0.0, fontsize=8.5)

    fig.tight_layout()
    return fig

"""
BMI Trend Visualization Module using Matplotlib.

Generates a clean, professional line chart showing the selected user's BMI
trajectory over time against standard WHO BMI category thresholds.
"""

from typing import List, Dict, Any
from datetime import datetime
import matplotlib
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

    # Sort records chronologically (oldest to newest)
    valid_records.sort(key=lambda item: item[0])
    dates = [item[0] for item in valid_records]
    bmis = [item[1] for item in valid_records]

    # Create figure with high DPI and clean aesthetics
    fig = Figure(figsize=(7.5, 4.8), dpi=100)
    ax = fig.add_subplot(111)

    # Automatically determine a sensible Y-axis range from actual BMI values.
    # DO NOT force the Y-axis to start at 10 unless the actual data requires it.
    min_val = min(bmis)
    max_val = max(bmis)
    if min_val == max_val:
        pad = max(1.5, min_val * 0.15)
    else:
        pad = max(1.2, (max_val - min_val) * 0.20)

    y_min = max(0.0, min_val - pad)
    y_max = max_val + pad
    ax.set_ylim(y_min, y_max)

    # Plot WHO category boundary reference background regions
    ax.axhspan(0.0, 18.5, color="#BBDEFB", alpha=0.30, label="Underweight (< 18.5)", zorder=0)
    ax.axhspan(18.5, 24.9, color="#C8E6C9", alpha=0.30, label="Normal (18.5 – 24.9)", zorder=0)
    ax.axhspan(25.0, 29.9, color="#FFE0B2", alpha=0.30, label="Overweight (25 – 29.9)", zorder=0)
    ax.axhspan(30.0, 150.0, color="#FFCDD2", alpha=0.30, label="Obese (≥ 30)", zorder=0)

    # Draw subtle reference lines for category boundaries if within range
    for boundary, col in [(18.5, "#1565C0"), (24.9, "#2E7D32"), (29.9, "#E65100")]:
        if y_min < boundary < y_max:
            ax.axhline(boundary, color=col, linestyle=":", alpha=0.55, linewidth=1.1, zorder=1)

    # Plot line chart with distinct data-point markers (zorder above backgrounds)
    ax.plot(
        dates,
        bmis,
        marker="o",
        markersize=7.0,
        linewidth=2.4,
        color="#1565C0",
        markerfacecolor="#0D47A1",
        markeredgecolor="#FFFFFF",
        markeredgewidth=1.5,
        label=f"{user_name}'s BMI",
        zorder=5,
    )

    # Add legible point annotations for exact BMI values
    last_dt = None
    last_val = None
    for idx, (dt, val) in enumerate(zip(dates, bmis)):
        is_close_to_prev = (
            last_dt is not None
            and (dt - last_dt).total_seconds() < 180
            and abs(val - last_val) < 2.5
        )
        if is_close_to_prev:
            y_offset = -16 if (idx % 2 != 0) else 10
            x_offset = -10 if (idx % 2 != 0) else 10
        else:
            y_offset = -15 if (y_max - val) < (val - y_min) * 0.25 else 8
            x_offset = 0

        ax.annotate(
            f"{val:.2f}",
            (dt, val),
            textcoords="offset points",
            xytext=(x_offset, y_offset),
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color="#212121",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="#CFD8DC", alpha=0.9),
            zorder=6,
        )
        last_dt = dt
        last_val = val

    # Format X-axis timestamps so they are readable and do not overlap
    span_seconds = (dates[-1] - dates[0]).total_seconds()
    if span_seconds <= 3600:
        # Closely spaced records within 1 hour: include seconds to distinguish timestamps
        date_fmt = "%d-%b %H:%M:%S"
    elif span_seconds <= 86400 * 2:
        # Records within 2 days: include date and hour:minute
        date_fmt = "%d-%b %H:%M"
    else:
        # Records over multiple days: show full date
        date_fmt = "%d %b %Y"

    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_fmt))
    locator = mdates.AutoDateLocator(minticks=2, maxticks=6)
    ax.xaxis.set_major_locator(locator)

    ax.margins(x=0.08)
    fig.autofmt_xdate(rotation=22, ha="right")

    # Titles and labels exactly matching requirements
    ax.set_title(f"BMI Trend for {user_name}", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=10, fontweight="bold", labelpad=8)
    ax.set_ylabel("BMI", fontsize=10, fontweight="bold", labelpad=8)
    ax.grid(True, linestyle="--", alpha=0.5, color="#9E9E9E", zorder=1)

    # Legend
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0.0, fontsize=8.5)

    fig.tight_layout()
    return fig

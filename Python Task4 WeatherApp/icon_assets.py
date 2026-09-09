"""
Icon Assets Module for Weather Application.
Generates anti-aliased, high-resolution vector-like graphical icons using Pillow.
Eliminates the need for system emojis and ensures pixel-perfect, theme-adaptive icons.
"""

import math
from typing import Tuple
from PIL import Image, ImageDraw


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """Convert hex color string like '#38BDF8' to RGBA tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b, alpha)
    return (255, 255, 255, alpha)


def create_icon(name: str, hex_color: str, size: Tuple[int, int] = (24, 24)) -> Image.Image:
    """
    Renders an anti-aliased graphical icon at 4x resolution and downsamples with Lanczos.
    """
    scale = 4
    w, h = size[0] * scale, size[1] * scale
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    color = _hex_to_rgba(hex_color)

    if name == "search":
        # Magnifying glass
        r = int(w * 0.28)
        cx, cy = int(w * 0.42), int(h * 0.42)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=int(scale * 2.2))
        # Handle
        draw.line([int(w * 0.62), int(h * 0.62), int(w * 0.88), int(h * 0.88)], fill=color, width=int(scale * 2.8))

    elif name == "location":
        # Map location pin
        cx, cy = int(w * 0.5), int(h * 0.38)
        r = int(w * 0.26)
        # Circular head
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=int(scale * 2.2))
        # Center dot
        dot_r = int(scale * 2.5)
        draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=color)
        # Pointy triangle base
        draw.polygon([
            (cx - int(w * 0.20), cy + int(h * 0.15)),
            (cx + int(w * 0.20), cy + int(h * 0.15)),
            (cx, int(h * 0.88))
        ], fill=color)

    elif name == "gear":
        # Precision settings gear
        cx, cy = int(w * 0.5), int(h * 0.5)
        outer_r = int(w * 0.34)
        inner_r = int(w * 0.16)
        # Center hole
        draw.ellipse([cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r], outline=color, width=int(scale * 3))
        draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=color)
        # Teeth lines
        num_teeth = 8
        tooth_len = int(scale * 4.5)
        for i in range(num_teeth):
            angle = i * (2 * math.pi / num_teeth)
            x1 = cx + (outer_r - tooth_len) * math.cos(angle)
            y1 = cy + (outer_r - tooth_len) * math.sin(angle)
            x2 = cx + (outer_r + tooth_len) * math.cos(angle)
            y2 = cy + (outer_r + tooth_len) * math.sin(angle)
            draw.line([x1, y1, x2, y2], fill=color, width=int(scale * 2.5))

    elif name == "sun":
        # Sun with rays for theme
        cx, cy = int(w * 0.5), int(h * 0.5)
        r = int(w * 0.22)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        for i in range(8):
            angle = i * (math.pi / 4)
            x1 = cx + (r + int(scale * 2.5)) * math.cos(angle)
            y1 = cy + (r + int(scale * 2.5)) * math.sin(angle)
            x2 = cx + (r + int(scale * 6.5)) * math.cos(angle)
            y2 = cy + (r + int(scale * 6.5)) * math.sin(angle)
            draw.line([x1, y1, x2, y2], fill=color, width=int(scale * 2))

    elif name == "moon":
        # Crescent moon
        cx, cy = int(w * 0.5), int(h * 0.5)
        r = int(w * 0.34)
        # Draw base moon circle
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        # Mask out inner circle with transparent pixels
        mask_canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        mask_draw = ImageDraw.Draw(mask_canvas)
        offset_x = int(scale * 4)
        offset_y = -int(scale * 3)
        mask_draw.ellipse(
            [cx - r + offset_x, cy - r + offset_y, cx + r + offset_x, cy + r + offset_y],
            fill=(0, 0, 0, 255)
        )
        # Erase overlap from canvas
        c_pixels = canvas.load()
        m_pixels = mask_canvas.load()
        for y in range(h):
            for x in range(w):
                if m_pixels[x, y][3] > 0:
                    c_pixels[x, y] = (0, 0, 0, 0)

    elif name == "thermometer":
        # Thermometer for Feels Like
        cx = int(w * 0.5)
        stem_w = int(scale * 3.5)
        bulb_r = int(scale * 6.5)
        bulb_y = int(h * 0.72)
        stem_top = int(h * 0.2)
        # Outer stem
        draw.rectangle([cx - stem_w, stem_top, cx + stem_w, bulb_y], fill=color)
        # Top rounded cap
        draw.ellipse([cx - stem_w, stem_top - stem_w, cx + stem_w, stem_top + stem_w], fill=color)
        # Bulb
        draw.ellipse([cx - bulb_r, bulb_y - bulb_r, cx + bulb_r, bulb_y + bulb_r], fill=color)

    elif name == "droplet":
        # Water droplet for Humidity
        cx = int(w * 0.5)
        top_y = int(h * 0.16)
        bulb_cy = int(h * 0.64)
        bulb_r = int(w * 0.28)
        # Bottom circle
        draw.ellipse([cx - bulb_r, bulb_cy - bulb_r, cx + bulb_r, bulb_cy + bulb_r], fill=color)
        # Top triangle pointing upwards
        draw.polygon([
            (cx, top_y),
            (cx - bulb_r + int(scale * 2), bulb_cy),
            (cx + bulb_r - int(scale * 2), bulb_cy)
        ], fill=color)

    elif name == "wind":
        # Wind stream lines
        lw = int(scale * 2.2)
        # Top stream with loop
        draw.line([int(w * 0.15), int(h * 0.32), int(w * 0.65), int(h * 0.32)], fill=color, width=lw)
        draw.arc([int(w * 0.55), int(h * 0.18), int(w * 0.78), int(h * 0.40)], start=270, end=90, fill=color, width=lw)
        # Middle stream
        draw.line([int(w * 0.10), int(h * 0.52), int(w * 0.85), int(h * 0.52)], fill=color, width=lw)
        draw.arc([int(w * 0.75), int(h * 0.52), int(w * 0.95), int(h * 0.74)], start=90, end=270, fill=color, width=lw)
        # Bottom stream
        draw.line([int(w * 0.20), int(h * 0.72), int(w * 0.60), int(h * 0.72)], fill=color, width=lw)

    elif name == "barometer":
        # Pressure gauge / barometer
        cx, cy = int(w * 0.5), int(h * 0.55)
        r = int(w * 0.36)
        # Arc dial
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=160, end=380, fill=color, width=int(scale * 2.5))
        # Center pivot
        p_r = int(scale * 3)
        draw.ellipse([cx - p_r, cy - p_r, cx + p_r, cy + p_r], fill=color)
        # Needle pointing up-right
        draw.line([cx, cy, cx + int(r * 0.65), cy - int(r * 0.65)], fill=color, width=int(scale * 2))

    elif name == "clock":
        # Clock for Hourly Timeline
        cx, cy = int(w * 0.5), int(h * 0.5)
        r = int(w * 0.36)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=int(scale * 2))
        # Center pivot
        draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=color)
        # Hour hand
        draw.line([cx, cy, cx, cy - int(r * 0.6)], fill=color, width=int(scale * 1.8))
        # Minute hand
        draw.line([cx, cy, cx + int(r * 0.5), cy], fill=color, width=int(scale * 1.8))

    elif name == "calendar":
        # Calendar for 5-Day Outlook
        top_y = int(h * 0.22)
        bottom_y = int(h * 0.82)
        left_x = int(w * 0.18)
        right_x = int(w * 0.82)
        lw = int(scale * 2)
        # Main box
        draw.rectangle([left_x, top_y, right_x, bottom_y], outline=color, width=lw)
        # Header banner line
        draw.line([left_x, top_y + int(scale * 6), right_x, top_y + int(scale * 6)], fill=color, width=lw)
        # Hanging binder rings
        ring_w = int(scale * 1.8)
        draw.line([left_x + int(scale * 5), top_y - int(scale * 4), left_x + int(scale * 5), top_y + int(scale * 3)], fill=color, width=ring_w)
        draw.line([right_x - int(scale * 5), top_y - int(scale * 4), right_x - int(scale * 5), top_y + int(scale * 3)], fill=color, width=ring_w)

    elif name == "logo":
        # App logo: Vibrant sun rising behind a clean rounded cloud
        sun_color = (251, 191, 36, 255)  # Amber gold
        draw.ellipse([int(w * 0.44), int(h * 0.16), int(w * 0.80), int(h * 0.52)], fill=sun_color)

        # Cloud in front: 3 overlapping circles + rounded base
        cloud_color = color
        draw.ellipse([int(w * 0.16), int(h * 0.40), int(w * 0.52), int(h * 0.76)], fill=cloud_color)
        draw.ellipse([int(w * 0.36), int(h * 0.30), int(w * 0.74), int(h * 0.68)], fill=cloud_color)
        draw.ellipse([int(w * 0.54), int(h * 0.42), int(w * 0.86), int(h * 0.74)], fill=cloud_color)
        # Rounded bottom base
        draw.rounded_rectangle([int(w * 0.20), int(h * 0.52), int(w * 0.82), int(h * 0.76)], radius=int(scale * 3), fill=cloud_color)

    elif name == "dot":
        # Status dot
        cx, cy = int(w * 0.5), int(h * 0.5)
        r = int(w * 0.36)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    # Downscale with high-quality anti-aliasing filter
    return canvas.resize(size, Image.Resampling.LANCZOS)

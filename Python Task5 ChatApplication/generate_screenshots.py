import os
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    font_paths = [
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    if bold:
        font_paths = [
            "C:\\Windows\\Fonts\\segoeuib.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf"
        ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_chat_icon(draw, x, y, size=18, color="#10b981"):
    # Clean vector chat bubble icon
    draw.rounded_rectangle([x, y, x + size, y + int(size * 0.75)], radius=3, outline=color, width=2)
    draw.polygon([(x + 3, y + int(size * 0.75)), (x + 3, y + size), (x + 8, y + int(size * 0.75))], fill=color)

def draw_moon_icon(draw, x, y, size=14, color="#ecfdf5"):
    # Clean crescent moon shape
    draw.arc([x, y, x + size, y + size], 45, 270, fill=color, width=2)

def draw_sun_icon(draw, x, y, size=14, color="#064e3b"):
    # Clean sun shape with rays
    cx, cy = x + size // 2, y + size // 2
    r = size // 3
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
    # 4 cardinal rays
    draw.line([cx, y, cx, y + 2], fill=color, width=2)
    draw.line([cx, y + size - 2, cx, y + size], fill=color, width=2)
    draw.line([x, cy, x + 2, cy], fill=color, width=2)
    draw.line([x + size - 2, cy, x + size, cy], fill=color, width=2)

def draw_smiley_icon(draw, x, y, size=18, color="#8da69e"):
    # Vector smiley icon for composer
    draw.ellipse([x, y, x + size, y + size], outline=color, width=2)
    draw.ellipse([x + 4, y + 5, x + 6, y + 7], fill=color)
    draw.ellipse([x + size - 6, y + 5, x + size - 4, y + 7], fill=color)
    draw.arc([x + 4, y + 6, x + size - 4, y + size - 4], 10, 170, fill=color, width=2)

def create_login_screenshot(output_path):
    w, h = 1000, 700
    img = Image.new("RGB", (w, h), "#0b1412")
    draw = ImageDraw.Draw(img)

    # Background ambient radial glow
    for r in range(300, 50, -30):
        draw.ellipse([w//2 - r, h//2 - r, w//2 + r, h//2 + r], outline="#11221e", width=4)

    # Card
    card_w, card_h = 420, 450
    card_x = (w - card_w) // 2
    card_y = (h - card_h) // 2

    # Draw card
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=20, fill="#182b27", outline="#223d37", width=1)
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + 4], radius=2, fill="#10b981")

    # Theme toggle icon button
    draw.rounded_rectangle([card_x + card_w - 45, card_y + 15, card_x + card_w - 15, card_y + 45], radius=15, fill="#0b1412", outline="#223d37")
    draw_moon_icon(draw, card_x + card_w - 36, card_y + 23, size=14, color="#ecfdf5")

    # Brand icon + Title
    draw.rounded_rectangle([card_x + 185, card_y + 35, card_x + 235, card_y + 85], radius=12, fill="#152723", outline="#10b981", width=1)
    draw_chat_icon(draw, card_x + 198, card_y + 49, size=24, color="#10b981")

    f_title = get_font(24, bold=True)
    f_sub = get_font(12)
    draw.text((card_x + 160, card_y + 98), "Sanwad", font=f_title, fill="#ecfdf5")
    draw.text((card_x + 85, card_y + 130), "Nordic Pine & Fresh Mint Workspace", font=f_sub, fill="#8da69e")

    # Tabs (Pill style)
    tab_y = card_y + 160
    draw.rounded_rectangle([card_x + 35, tab_y, card_x + card_w - 35, tab_y + 42], radius=21, fill="#0b1412", outline="#223d37", width=1)
    draw.rounded_rectangle([card_x + 37, tab_y + 2, card_x + (card_w // 2) - 2, tab_y + 40], radius=19, fill="#10b981")
    draw.text((card_x + 85, tab_y + 11), "Sign In", font=get_font(13, bold=True), fill="#ffffff")
    draw.text((card_x + 250, tab_y + 11), "Register", font=get_font(13, bold=False), fill="#8da69e")

    # Inputs
    inp_y = tab_y + 55
    f_lbl = get_font(12, bold=True)
    draw.text((card_x + 40, inp_y), "Username", font=f_lbl, fill="#a7f3d0")
    draw.rounded_rectangle([card_x + 35, inp_y + 22, card_x + card_w - 35, inp_y + 64], radius=21, fill="#0b1412", outline="#223d37", width=1)
    draw.text((card_x + 55, inp_y + 36), "alex_smith", font=get_font(14), fill="#ecfdf5")

    inp2_y = inp_y + 75
    draw.text((card_x + 40, inp2_y), "Password", font=f_lbl, fill="#a7f3d0")
    draw.rounded_rectangle([card_x + 35, inp2_y + 22, card_x + card_w - 35, inp2_y + 64], radius=21, fill="#0b1412", outline="#223d37", width=1)
    draw.text((card_x + 55, inp2_y + 38), "••••••••••••", font=get_font(14), fill="#8da69e")

    # Button (Elevated Pill)
    btn_y = inp2_y + 80
    draw.rounded_rectangle([card_x + 35, btn_y, card_x + card_w - 35, btn_y + 45], radius=22, fill="#10b981")
    draw.text((card_x + 125, btn_y + 13), "Sign In to Sanwad →", font=get_font(14, bold=True), fill="#ffffff")

    img.save(output_path)
    print(f"Saved {output_path}")

def create_chat_screenshot(output_path):
    w, h = 1200, 750
    img = Image.new("RGB", (w, h), "#0b1412")
    draw = ImageDraw.Draw(img)

    # Sidebar (290px)
    draw.rectangle([0, 0, 290, h], fill="#182b27", outline="#223d37", width=1)

    # Sidebar Header with vector icon
    draw_chat_icon(draw, 25, 24, size=20, color="#10b981")
    draw.text((54, 22), "Sanwad", font=get_font(18, bold=True), fill="#10b981")
    draw.rounded_rectangle([180, 18, 270, 44], radius=13, fill="#1f332f", outline="#223d37")
    draw.ellipse([190, 28, 198, 36], fill="#10b981")
    draw.text((205, 24), "Online", font=get_font(11), fill="#a7f3d0")

    # User profile card
    draw.rounded_rectangle([16, 65, 274, 120], radius=12, fill="#1f332f", outline="#223d37")
    draw.ellipse([26, 74, 62, 110], fill="#10b981")
    draw.text((39, 81), "A", font=get_font(16, bold=True), fill="#ffffff")
    draw.text((72, 77), "alex_smith", font=get_font(13, bold=True), fill="#ecfdf5")
    draw.text((72, 96), "• Active Now", font=get_font(10), fill="#34d399")

    # 2 Options Switcher: Chat Rooms & Personal Chat
    draw.rounded_rectangle([16, 132, 140, 164], radius=16, fill="#059669")
    draw.text((36, 142), "Chat Rooms", font=get_font(11, bold=True), fill="#ffffff")
    draw.rounded_rectangle([148, 132, 274, 164], radius=16, fill="#1f332f", outline="#223d37")
    draw.text((165, 142), "Personal Chat", font=get_font(11, bold=False), fill="#a7f3d0")

    # Room list section
    draw.text((20, 180), "CHAT ROOMS", font=get_font(11, bold=True), fill="#8da69e")
    draw.rounded_rectangle([245, 174, 272, 201], radius=6, fill="#1f332f", outline="#223d37")
    draw.text((254, 178), "+", font=get_font(14, bold=True), fill="#a7f3d0")

    # Rooms
    rooms = [
        ("# General", True, "24"),
        ("# Python Lounge", False, "12"),
        ("# Projects", False, "5"),
        ("# Random", False, "8")
    ]
    ry = 210
    for rname, is_act, count in rooms:
        bg = "#1f332f" if is_act else "#182b27"
        border = "#223d37" if is_act else "#182b27"
        txt_col = "#ecfdf5" if is_act else "#8da69e"
        draw.rounded_rectangle([16, ry, 274, ry + 42], radius=12, fill=bg, outline=border, width=1)
        draw.text((32, ry + 12), rname, font=get_font(13, bold=is_act), fill=txt_col)
        draw.rounded_rectangle([240, ry + 11, 265, ry + 31], radius=10, fill="#10b981" if is_act else "#0b1412")
        draw.text((246, ry + 13), count, font=get_font(10, bold=True), fill="#ffffff")
        ry += 48

    # Security transparency button
    draw.text((22, h - 35), "[Shield] Security & Privacy Info", font=get_font(11), fill="#8da69e")

    # Main Chat Viewport (290 to 1200)
    # Header
    draw.rectangle([290, 0, w, 64], fill="#111f1c", outline="#223d37", width=1)
    draw.text((315, 16), "# General", font=get_font(18, bold=True), fill="#ecfdf5")
    draw.text((315, 40), "Open discussion for all participants", font=get_font(11), fill="#8da69e")
    
    # Presence badge
    draw.rounded_rectangle([w - 220, 16, w - 100, 48], radius=16, fill="#1f332f", outline="#223d37")
    draw.ellipse([w - 208, 27, w - 200, 35], fill="#10b981")
    draw.text((w - 192, 23), "2 online", font=get_font(11), fill="#a7f3d0")

    # Theme toggle with moon icon
    draw.rounded_rectangle([w - 85, 16, w - 45, 48], radius=16, fill="#1f332f", outline="#223d37")
    draw_moon_icon(draw, w - 71, 24, size=14, color="#ecfdf5")

    # Messages Viewport
    draw.rectangle([290, 64, w, h - 90], fill="#111f1c")

    # System join pill
    draw.rounded_rectangle([600, 85, 885, 115], radius=15, fill="#182b27", outline="#223d37")
    draw.text((615, 92), "Bob has joined the room.  [02:34 PM]", font=get_font(11), fill="#8da69e")

    # Message 1 (Other user: Bob)
    draw.ellipse([320, 135, 356, 171], fill="#182b27", outline="#223d37")
    draw.text((333, 143), "B", font=get_font(14, bold=True), fill="#ecfdf5")
    draw.text((368, 132), "Bob", font=get_font(12, bold=True), fill="#a7f3d0")
    draw.text((403, 134), "[02:35 PM]", font=get_font(10), fill="#8da69e")
    draw.rounded_rectangle([368, 150, 710, 192], radius=14, fill="#1a302b", outline="#294740")
    draw.text((382, 161), "Hello Alice! Notice the sleek vector icons across the UI?", font=get_font(12), fill="#ecfdf5")

    # Message 2 (Own user: Alice)
    draw.ellipse([w - 65, 215, w - 29, 251], fill="#10b981")
    draw.text((w - 52, 223), "A", font=get_font(14, bold=True), fill="#ffffff")
    draw.text((w - 430, 210), "[02:36 PM]   You", font=get_font(11, bold=True), fill="#8da69e")
    draw.rounded_rectangle([w - 530, 228, w - 75, 270], radius=14, fill="#059669")
    draw.text((w - 515, 239), "Hi Bob! Yes, clean SVGs, 12-hour timestamps & personal chat!", font=get_font(12), fill="#ffffff")

    # Live Typing indicator
    draw.text((325, h - 110), "Bob is typing...", font=get_font(11), fill="#8da69e")

    # Elevated SaaS Floating Composer
    comp_y = h - 75
    draw.rounded_rectangle([315, comp_y, w - 30, comp_y + 54], radius=27, fill="#1f332f", outline="#10b981", width=1)
    draw_smiley_icon(draw, 335, comp_y + 18, size=18, color="#8da69e")
    draw.text((375, comp_y + 18), "Message #General (press Enter to send)...", font=get_font(13), fill="#8da69e")
    draw.rounded_rectangle([w - 125, comp_y + 8, w - 42, comp_y + 46], radius=19, fill="#10b981")
    draw.text((w - 105, comp_y + 17), "Send →", font=get_font(11, bold=True), fill="#ffffff")

    img.save(output_path)
    print(f"Saved {output_path}")

def create_chat_light_screenshot(output_path):
    w, h = 1200, 750
    # Fresh Mint / Light Porcelain canvas
    img = Image.new("RGB", (w, h), "#f0fdf4")
    draw = ImageDraw.Draw(img)

    # Sidebar (290px)
    draw.rectangle([0, 0, 290, h], fill="#ecfdf5", outline="#d1fae5", width=1)

    # Sidebar Header with vector icon
    draw_chat_icon(draw, 25, 24, size=20, color="#10b981")
    draw.text((54, 22), "Sanwad", font=get_font(18, bold=True), fill="#065f46")
    draw.rounded_rectangle([180, 18, 270, 44], radius=13, fill="#ffffff", outline="#d1fae5")
    draw.ellipse([190, 28, 198, 36], fill="#10b981")
    draw.text((205, 24), "Online", font=get_font(11), fill="#059669")

    # User profile card
    draw.rounded_rectangle([16, 65, 274, 120], radius=12, fill="#ffffff", outline="#d1fae5")
    draw.ellipse([26, 74, 62, 110], fill="#10b981")
    draw.text((39, 81), "A", font=get_font(16, bold=True), fill="#ffffff")
    draw.text((72, 77), "alex_smith", font=get_font(13, bold=True), fill="#064e3b")
    draw.text((72, 96), "• Active Now", font=get_font(10), fill="#059669")

    # 2 Options Switcher: Chat Rooms & Personal Chat
    draw.rounded_rectangle([16, 132, 140, 164], radius=16, fill="#10b981")
    draw.text((36, 142), "Chat Rooms", font=get_font(11, bold=True), fill="#ffffff")
    draw.rounded_rectangle([148, 132, 274, 164], radius=16, fill="#d1fae5", outline="#a7f3d0")
    draw.text((165, 142), "Personal Chat", font=get_font(11, bold=False), fill="#047857")

    # Room list section
    draw.text((20, 180), "CHAT ROOMS", font=get_font(11, bold=True), fill="#047857")
    draw.rounded_rectangle([245, 174, 272, 201], radius=6, fill="#ffffff", outline="#d1fae5")
    draw.text((254, 178), "+", font=get_font(14, bold=True), fill="#059669")

    # Rooms
    rooms = [
        ("# General", True, "24"),
        ("# Python Lounge", False, "12"),
        ("# Projects", False, "5"),
        ("# Random", False, "8")
    ]
    ry = 210
    for rname, is_act, count in rooms:
        bg = "#ffffff" if is_act else "#ecfdf5"
        border = "#10b981" if is_act else "#ecfdf5"
        txt_col = "#064e3b" if is_act else "#4b5563"
        draw.rounded_rectangle([16, ry, 274, ry + 42], radius=12, fill=bg, outline=border, width=1)
        draw.text((32, ry + 12), rname, font=get_font(13, bold=is_act), fill=txt_col)
        draw.rounded_rectangle([240, ry + 11, 265, ry + 31], radius=10, fill="#10b981" if is_act else "#d1fae5")
        draw.text((246, ry + 13), count, font=get_font(10, bold=True), fill="#ffffff" if is_act else "#047857")
        ry += 48

    # Security transparency button
    draw.text((22, h - 35), "[Shield] Security & Privacy Info", font=get_font(11), fill="#047857")

    # Main Chat Viewport (290 to 1200)
    # Header
    draw.rectangle([290, 0, w, 64], fill="#ffffff", outline="#d1fae5", width=1)
    draw.text((315, 16), "# General", font=get_font(18, bold=True), fill="#064e3b")
    draw.text((315, 40), "Open discussion for all participants", font=get_font(11), fill="#047857")
    
    # Presence badge
    draw.rounded_rectangle([w - 220, 16, w - 100, 48], radius=16, fill="#f0fdf4", outline="#d1fae5")
    draw.ellipse([w - 208, 27, w - 200, 35], fill="#10b981")
    draw.text((w - 192, 23), "2 online", font=get_font(11), fill="#047857")

    # Theme toggle with sun icon
    draw.rounded_rectangle([w - 85, 16, w - 45, 48], radius=16, fill="#f0fdf4", outline="#d1fae5")
    draw_sun_icon(draw, w - 71, 24, size=14, color="#064e3b")

    # Messages Viewport
    draw.rectangle([290, 64, w, h - 90], fill="#f7fee7")

    # System join pill
    draw.rounded_rectangle([600, 85, 885, 115], radius=15, fill="#ffffff", outline="#d1fae5")
    draw.text((615, 92), "Bob has joined the room.  [02:34 PM]", font=get_font(11), fill="#047857")

    # Message 1 (Other user: Bob)
    draw.ellipse([320, 135, 356, 171], fill="#ffffff", outline="#d1fae5")
    draw.text((333, 143), "B", font=get_font(14, bold=True), fill="#064e3b")
    draw.text((368, 132), "Bob", font=get_font(12, bold=True), fill="#059669")
    draw.text((403, 134), "[02:35 PM]", font=get_font(10), fill="#6b7280")
    draw.rounded_rectangle([368, 150, 710, 192], radius=14, fill="#ffffff", outline="#d1fae5")
    draw.text((382, 161), "Hello Alice! Notice the sleek vector icons across the UI?", font=get_font(12), fill="#064e3b")

    # Message 2 (Own user: Alice)
    draw.ellipse([w - 65, 215, w - 29, 251], fill="#10b981")
    draw.text((w - 52, 223), "A", font=get_font(14, bold=True), fill="#ffffff")
    draw.text((w - 430, 210), "[02:36 PM]   You", font=get_font(11, bold=True), fill="#6b7280")
    draw.rounded_rectangle([w - 530, 228, w - 75, 270], radius=14, fill="#059669")
    draw.text((w - 515, 239), "Hi Bob! Yes, clean SVGs, 12-hour timestamps & personal chat!", font=get_font(12), fill="#ffffff")

    # Live Typing indicator
    draw.text((325, h - 110), "Bob is typing...", font=get_font(11), fill="#047857")

    # Elevated SaaS Floating Composer
    comp_y = h - 75
    draw.rounded_rectangle([315, comp_y, w - 30, comp_y + 54], radius=27, fill="#ffffff", outline="#10b981", width=1)
    draw_smiley_icon(draw, 335, comp_y + 18, size=18, color="#047857")
    draw.text((375, comp_y + 18), "Message #General (press Enter to send)...", font=get_font(13), fill="#6b7280")
    draw.rounded_rectangle([w - 125, comp_y + 8, w - 42, comp_y + 46], radius=19, fill="#10b981")
    draw.text((w - 105, comp_y + 17), "Send →", font=get_font(11, bold=True), fill="#ffffff")

    img.save(output_path)
    print(f"Saved {output_path}")

if __name__ == "__main__":
    os.makedirs("screenshots", exist_ok=True)
    create_login_screenshot("screenshots/login_screen.png")
    create_chat_screenshot("screenshots/chat_screen_dark.png")
    create_chat_screenshot("screenshots/chat_screen.png")
    create_chat_light_screenshot("screenshots/chat_screen_light.png")

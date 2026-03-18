"""
Dark theme color constants and font helpers for the dart scorer app.
"""

BG = "#1a1a2e"          # deep navy background
BG2 = "#16213e"         # slightly lighter panel
ACCENT = "#e94560"      # red accent
ACCENT2 = "#0f3460"     # blue accent panel
TEXT = "#eaeaea"        # primary text
TEXT_DIM = "#888888"    # secondary text
GREEN = "#4ecca3"       # score highlight
YELLOW = "#f5c518"      # current player highlight
WHITE = "#ffffff"

DART_COLORS = ["#00d4ff", "#ff6b6b", "#69ff47"]  # cyan, pink, green per dart

FONT_TITLE = ("Helvetica", 28, "bold")
FONT_HEADING = ("Helvetica", 16, "bold")
FONT_SUBHEADING = ("Helvetica", 13, "bold")
FONT_BODY = ("Helvetica", 11)
FONT_SCORE_LARGE = ("Helvetica", 42, "bold")
FONT_SCORE_MED = ("Helvetica", 22, "bold")
FONT_MONO = ("Courier", 11)

BTN_STYLE = {
    "bg": ACCENT,
    "fg": WHITE,
    "font": ("Helvetica", 12, "bold"),
    "relief": "flat",
    "cursor": "hand2",
    "padx": 18,
    "pady": 8,
    "borderwidth": 0,
    "activebackground": "#c73652",
    "activeforeground": WHITE,
}

BTN_SECONDARY = {
    "bg": ACCENT2,
    "fg": TEXT,
    "font": ("Helvetica", 11),
    "relief": "flat",
    "cursor": "hand2",
    "padx": 14,
    "pady": 6,
    "borderwidth": 0,
    "activebackground": "#1a4a80",
    "activeforeground": WHITE,
}

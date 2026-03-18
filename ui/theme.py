"""
Design system for Dart Scorer.
Dark premium palette inspired by sports scoreboards + gaming UIs.
"""

# ── Palette ────────────────────────────────────────────────────────────────
BG            = "#0e0e18"   # main app background
SURFACE       = "#15152a"   # card / panel surface
SURFACE2      = "#1c1c34"   # elevated card (hover, active)
BORDER        = "#2a2a48"   # subtle card borders
BORDER_BRIGHT = "#3d3d68"   # highlighted border

ACCENT        = "#e8365d"   # primary red – CTAs, active states
ACCENT_HOVER  = "#ff4d72"
ACCENT_DIM    = "#2a0d18"   # accent bg tint

TEAL          = "#10d48a"   # success / positive scores
TEAL_DIM      = "#06301f"

GOLD          = "#f59e0b"   # current-player highlight
GOLD_DIM      = "#2c1c00"

BLUE          = "#38bdf8"   # info / dart 1
ORANGE        = "#fb923c"   # dart 2
PURPLE        = "#a78bfa"   # dart 3

TEXT          = "#e8e8ff"   # primary text
TEXT_MID      = "#7878a0"   # secondary text
TEXT_DIM      = "#3a3a58"   # very muted
WHITE         = "#ffffff"

DART_COLORS   = [BLUE, ORANGE, PURPLE]

# ── Fonts ──────────────────────────────────────────────────────────────────
FONT_TITLE        = ("Helvetica", 38, "bold")
FONT_HEADING      = ("Helvetica", 18, "bold")
FONT_SUBHEADING   = ("Helvetica", 13, "bold")
FONT_BODY         = ("Helvetica", 11)
FONT_CAPTION      = ("Helvetica", 9)
FONT_SCORE_HUGE   = ("Helvetica", 54, "bold")
FONT_SCORE_BIG    = ("Helvetica", 34, "bold")
FONT_SCORE_MED    = ("Helvetica", 22, "bold")
FONT_SCORE_SM     = ("Helvetica", 15, "bold")

# ── Button styles ──────────────────────────────────────────────────────────
BTN_PRIMARY = dict(
    bg=ACCENT, fg=WHITE,
    font=("Helvetica", 12, "bold"),
    relief="flat", cursor="hand2",
    padx=24, pady=10,
    borderwidth=0,
    activebackground=ACCENT_HOVER,
    activeforeground=WHITE,
)

BTN_SECONDARY = dict(
    bg=SURFACE2, fg=TEXT,
    font=("Helvetica", 11),
    relief="flat", cursor="hand2",
    padx=18, pady=8,
    borderwidth=0,
    activebackground=BORDER_BRIGHT,
    activeforeground=WHITE,
)

BTN_GHOST = dict(
    bg=BG, fg=TEXT_MID,
    font=("Helvetica", 10),
    relief="flat", cursor="hand2",
    padx=12, pady=6,
    borderwidth=0,
    activebackground=SURFACE,
    activeforeground=TEXT,
)

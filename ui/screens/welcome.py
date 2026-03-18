"""
Welcome screen — dartboard illustration + hero title + CTAs.
"""
import tkinter as tk
from ui.theme import *
from ui.widgets import draw_dartboard


class WelcomeScreen(tk.Frame):
    def __init__(self, parent, on_start, on_tutorial):
        super().__init__(parent, bg=BG)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_left(on_start, on_tutorial)
        self._build_right()

    # ── Left column ────────────────────────────────────────────

    def _build_left(self, on_start, on_tutorial):
        left = tk.Frame(self, bg=BG)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        for r in range(10):
            left.rowconfigure(r, weight=1)

        # Brand / wordmark
        tk.Label(left, text="DARTS", font=("Helvetica", 64, "bold"),
                 bg=BG, fg=TEXT).grid(row=2, column=0)

        tk.Label(left, text="S C O R E R", font=("Helvetica", 18),
                 bg=BG, fg=ACCENT).grid(row=3, column=0, pady=(0, 6))

        # Divider line
        div = tk.Frame(left, bg=BORDER, height=1, width=220)
        div.grid(row=4, column=0, pady=16)

        tk.Label(left, text="Automatic webcam dart detection.\nNo subscription. No hardware.",
                 font=FONT_BODY, bg=BG, fg=TEXT_MID, justify="center").grid(row=5, column=0, pady=(0, 32))

        # CTA buttons
        btn_frame = tk.Frame(left, bg=BG)
        btn_frame.grid(row=6, column=0)

        new_game_btn = tk.Button(btn_frame, text="NEW GAME",
                                 command=on_start, **BTN_PRIMARY)
        new_game_btn.grid(row=0, column=0, sticky="ew", pady=6, ipady=4)

        how_btn = tk.Button(btn_frame, text="HOW TO PLAY",
                            command=on_tutorial, **BTN_SECONDARY)
        how_btn.grid(row=1, column=0, sticky="ew", pady=6)

        # Hover effects
        for btn, hover, normal in [
            (new_game_btn, ACCENT_HOVER, ACCENT),
            (how_btn, BORDER_BRIGHT, SURFACE2),
        ]:
            btn.bind("<Enter>", lambda e, b=btn, c=hover: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=normal: b.config(bg=c))

        # Footer
        tk.Label(left, text="Free & open source  ·  No cloud required",
                 font=FONT_CAPTION, bg=BG, fg=TEXT_DIM).grid(row=8, column=0)

    # ── Right column — dartboard canvas ────────────────────────

    def _build_right(self):
        right = tk.Frame(self, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        # Canvas sized to show a large dartboard
        size = 480
        c = tk.Canvas(right, width=size, height=size, bg=BG,
                      highlightthickness=0)
        c.grid(row=0, column=0, padx=20, pady=20)

        cx, cy = size // 2, size // 2
        radius = size // 2 - 30

        draw_dartboard(c, cx, cy, radius, bg=BG)

        # Subtle tagline over the center
        c.create_text(cx, cy, text="●", font=("Helvetica", 6),
                      fill=TEAL)

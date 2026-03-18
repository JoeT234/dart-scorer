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

        # Keyboard shortcut: Enter = new game
        self.bind_all("<Return>", lambda e: on_start())

    # ── Left column ────────────────────────────────────────────

    def _build_left(self, on_start, on_tutorial):
        left = tk.Frame(self, bg=BG)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        for r in range(12):
            left.rowconfigure(r, weight=1)

        # Version chip
        chip = tk.Frame(left, bg=SURFACE2, padx=12, pady=4)
        chip.grid(row=1, column=0)
        tk.Label(chip, text="🎯  DART SCORER  v1.0",
                 font=FONT_CAPTION, bg=SURFACE2, fg=TEXT_MID).pack()

        # Brand / wordmark
        tk.Label(left, text="DARTS", font=("Helvetica", 64, "bold"),
                 bg=BG, fg=TEXT).grid(row=2, column=0)

        tk.Label(left, text="S C O R E R", font=("Helvetica", 18),
                 bg=BG, fg=ACCENT).grid(row=3, column=0, pady=(0, 4))

        # Divider line
        div = tk.Frame(left, bg=BORDER, height=1, width=220)
        div.grid(row=4, column=0, pady=14)

        tk.Label(left,
                 text="Automatic webcam dart detection.\nNo subscription. No hardware.",
                 font=FONT_BODY, bg=BG, fg=TEXT_MID,
                 justify="center").grid(row=5, column=0, pady=(0, 28))

        # CTA buttons
        btn_frame = tk.Frame(left, bg=BG)
        btn_frame.grid(row=6, column=0)
        btn_frame.columnconfigure(0, weight=1)

        new_game_btn = tk.Button(btn_frame, text="▶   NEW GAME",
                                 command=on_start, **BTN_PRIMARY)
        new_game_btn.grid(row=0, column=0, sticky="ew", pady=5, ipady=6)

        how_btn = tk.Button(btn_frame, text="HOW TO PLAY",
                            command=on_tutorial, **BTN_SECONDARY)
        how_btn.grid(row=1, column=0, sticky="ew", pady=5, ipady=4)

        # Hover effects
        for btn, hover, normal in [
            (new_game_btn, ACCENT_HOVER, ACCENT),
            (how_btn,      BORDER_BRIGHT, SURFACE2),
        ]:
            btn.bind("<Enter>", lambda e, b=btn, c=hover: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=normal: b.config(bg=c))

        # Keyboard hint
        tk.Label(left, text="Press  Enter  to start",
                 font=FONT_CAPTION, bg=BG, fg=TEXT_DIM).grid(row=7, column=0, pady=(4, 0))

        # Feature pills
        pills = tk.Frame(left, bg=BG)
        pills.grid(row=8, column=0, pady=(18, 0))
        for label in ["⚡ Auto-detect", "📐 Multi-angle", "👥 Multiplayer"]:
            p = tk.Frame(pills, bg=SURFACE2, padx=10, pady=4)
            p.pack(side="left", padx=4)
            tk.Label(p, text=label, font=FONT_CAPTION, bg=SURFACE2, fg=TEXT_MID).pack()

        # Footer
        tk.Label(left, text="Free & open source  ·  No cloud required",
                 font=FONT_CAPTION, bg=BG, fg=TEXT_DIM).grid(row=10, column=0)

    # ── Right column — dartboard canvas ────────────────────────

    def _build_right(self):
        right = tk.Frame(self, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        size = 480
        c = tk.Canvas(right, width=size, height=size, bg=BG,
                      highlightthickness=0)
        c.grid(row=0, column=0, padx=20, pady=20)

        cx, cy = size // 2, size // 2
        radius = size // 2 - 30

        draw_dartboard(c, cx, cy, radius, bg=BG)

        # Teal bullseye pulse ring
        r = 18
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      outline=TEAL, width=2, fill="")

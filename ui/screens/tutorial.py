"""
Tutorial screen: left sidebar nav + rich content panel.
"""
import tkinter as tk
from ui.theme import *
from ui.widgets import separator


SECTIONS = [
    {
        "icon": "📷",
        "title": "Camera Setup",
        "steps": [
            ("Position", "Mount the webcam above or to the side of the board at a "
             "slight downward angle. The entire board should be visible."),
            ("Lighting", "Ensure the board is well-lit and avoid strong backlighting "
             "or shadows. A desk lamp aimed at the board works well."),
            ("Distance", "The dartboard should fill at least 50 % of the camera "
             "frame. Closer = better accuracy."),
            ("Stability", "Any camera movement resets detection. Mount the webcam "
             "firmly — a tripod or monitor clip works great."),
            ("Resolution", "720p or higher is recommended. Set Camera Index to 0 "
             "for the built-in webcam, or 1/2 for an external camera."),
        ],
    },
    {
        "icon": "🎯",
        "title": "Calibration",
        "steps": [
            ("Why", "Calibration tells the app exactly where the scoring rings are, "
             "so it can map a dart's pixel position to a score."),
            ("Start", "On the game screen click 'Calibrate Board'. The camera feed "
             "will go live."),
            ("Click 4 points", "Click on these four corners of the double ring "
             "(the outermost thin ring):\n"
             "   1. Top of the 20 segment\n"
             "   2. Right of the 6 segment\n"
             "   3. Left of the 11 segment\n"
             "   4. Bottom of the 3 segment"),
            ("Done", "The board overlay appears. Calibrate once per session. "
             "If the camera moves, re-calibrate."),
        ],
    },
    {
        "icon": "🏹",
        "title": "Detection",
        "steps": [
            ("How it works", "The app captures a reference frame of the empty "
             "board, then detects darts by comparing each new frame to that reference."),
            ("Start round", "Press R (or 'Reset Reference') before each player's "
             "turn to capture the board without darts."),
            ("Auto-detect", "Throw your darts — each dart appears as a colored "
             "dot on the feed within a few seconds."),
            ("Manual add", "If a dart isn't detected, press A to add it manually "
             "at a default position, then drag it on the feed."),
            ("Undo", "Press Undo to remove the last detected dart."),
        ],
    },
    {
        "icon": "🎮",
        "title": "Gameplay",
        "steps": [
            ("501 / 301", "Score counts DOWN. You must reach exactly 0 by finishing "
             "on a Double or the Bullseye (50 pts)."),
            ("Bust", "Going below 0, or landing on 1, is a BUST — your score "
             "reverts to what it was before that visit."),
            ("Commit", "After all 3 darts press Enter (or Commit Visit) to lock in "
             "the score and advance to the next player."),
            ("Legs", "First player to win the set number of legs wins the match. "
             "Scores reset at the start of each leg."),
            ("Shortcuts", "Enter = Commit   ·   R = Reset reference\n"
             "A = Add dart   ·   Esc = Back to menu"),
        ],
    },
]


class TutorialScreen(tk.Frame):
    def __init__(self, parent, on_back):
        super().__init__(parent, bg=BG)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar(on_back)
        self._build_content()
        self._show(0)

    # ── Sidebar ─────────────────────────────────────────────────

    def _build_sidebar(self, on_back):
        sidebar = tk.Frame(self, bg=SURFACE, width=220)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.columnconfigure(0, weight=1)
        sidebar.grid_propagate(False)

        # Logo / title
        tk.Label(sidebar, text="How to Play",
                 font=FONT_SUBHEADING, bg=SURFACE, fg=TEXT,
                 anchor="w").pack(fill="x", padx=20, pady=(28, 6))
        separator(sidebar, color=BORDER).pack(fill="x", padx=20, pady=(0, 16))

        # Section buttons
        self._nav_btns = []
        for i, sec in enumerate(SECTIONS):
            btn = tk.Button(
                sidebar,
                text=f"  {sec['icon']}  {sec['title']}",
                font=FONT_BODY, relief="flat", cursor="hand2",
                anchor="w", padx=20, pady=10, borderwidth=0,
                command=lambda i=i: self._show(i),
            )
            btn.pack(fill="x", pady=1)
            self._nav_btns.append(btn)

        # Spacer
        tk.Frame(sidebar, bg=SURFACE).pack(fill="both", expand=True)

        # Back button
        separator(sidebar, color=BORDER).pack(fill="x", padx=20, pady=8)
        tk.Button(sidebar, text="← Back to Menu", command=on_back,
                  **BTN_GHOST).pack(fill="x", padx=16, pady=(0, 20))

    # ── Content area ────────────────────────────────────────────

    def _build_content(self):
        self._content = tk.Frame(self, bg=BG)
        self._content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self._content.columnconfigure(0, weight=1)
        self._content.rowconfigure(1, weight=1)

    def _show(self, index):
        sec = SECTIONS[index]

        # Refresh sidebar button styles
        for i, btn in enumerate(self._nav_btns):
            if i == index:
                btn.config(bg=ACCENT_DIM, fg=ACCENT,
                           activebackground=ACCENT_DIM, activeforeground=ACCENT)
            else:
                btn.config(bg=SURFACE, fg=TEXT_MID,
                           activebackground=SURFACE2, activeforeground=TEXT)

        # Clear content
        for w in self._content.winfo_children():
            w.destroy()

        # Header
        header = tk.Frame(self._content, bg=BG)
        header.grid(row=0, column=0, sticky="ew", padx=50, pady=(40, 0))
        tk.Label(header, text=sec["icon"], font=("Helvetica", 32),
                 bg=BG).pack(side="left", padx=(0, 12))
        tk.Label(header, text=sec["title"], font=FONT_TITLE,
                 bg=BG, fg=TEXT).pack(side="left")

        separator(self._content, color=BORDER).grid(
            row=1, column=0, sticky="ew", padx=50, pady=16)

        # Steps
        steps_frame = tk.Frame(self._content, bg=BG)
        steps_frame.grid(row=2, column=0, sticky="nsew", padx=50)

        for i, (label, body) in enumerate(sec["steps"]):
            row_f = tk.Frame(steps_frame, bg=BG)
            row_f.pack(fill="x", pady=10)

            # Step number badge
            badge = tk.Canvas(row_f, width=28, height=28, bg=BG,
                              highlightthickness=0)
            badge.pack(side="left", anchor="nw", padx=(0, 14), pady=2)
            badge.create_oval(2, 2, 26, 26, fill=ACCENT_DIM, outline=ACCENT, width=1)
            badge.create_text(14, 14, text=str(i+1),
                              font=("Helvetica", 9, "bold"), fill=ACCENT)

            text_frame = tk.Frame(row_f, bg=BG)
            text_frame.pack(side="left", fill="x", expand=True)

            tk.Label(text_frame, text=label, font=FONT_SUBHEADING,
                     bg=BG, fg=TEXT, anchor="w").pack(fill="x")
            tk.Label(text_frame, text=body, font=FONT_BODY,
                     bg=BG, fg=TEXT_MID, anchor="w", justify="left",
                     wraplength=580).pack(fill="x", pady=(2, 0))

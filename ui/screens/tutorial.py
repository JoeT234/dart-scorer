"""
Tutorial screen: tabbed sections explaining setup, calibration, gameplay.
"""
import tkinter as tk
from ui.theme import *


SECTIONS = [
    {
        "title": "📷 Camera Setup",
        "content": (
            "Position your webcam so the entire dartboard is visible in the frame.\n\n"
            "Tips for best results:\n"
            "  • Mount the webcam above or to the side of the board at a slight angle\n"
            "  • Ensure the board is well-lit — avoid strong backlighting\n"
            "  • The board should fill at least 50% of the camera frame\n"
            "  • Keep the camera steady — any movement resets detection\n"
            "  • A resolution of 720p or higher gives the best accuracy\n\n"
            "Camera Index 0 is usually the built-in webcam. If that doesn't work, try 1 or 2."
        ),
    },
    {
        "title": "🎯 Calibration",
        "content": (
            "Before playing, you need to calibrate the board so the app knows exactly\n"
            "where the scoring segments are.\n\n"
            "How it works:\n"
            "  1. Click CALIBRATE on the game screen — the camera shows a live feed\n"
            "  2. Click on 4 specific points on the board (marked with orange crosshairs):\n"
            "       • Top-left corner of the 20 segment double ring\n"
            "       • Top-right corner of the 6 segment double ring\n"
            "       • Bottom-left corner of the 11 segment double ring\n"
            "       • Bottom-right corner of the 3 segment double ring\n"
            "  3. Press CONFIRM — the board overlay will appear\n\n"
            "You only need to calibrate once per session. If the camera moves, re-calibrate."
        ),
    },
    {
        "title": "🏹 Detection",
        "content": (
            "How dart detection works:\n\n"
            "  1. When you press START ROUND, the app captures a reference frame\n"
            "     (the board without any darts)\n"
            "  2. As you throw darts, the app compares each frame to the reference\n"
            "  3. New objects (darts) are detected by the difference between frames\n"
            "  4. The dart tip is identified and its position is transformed to\n"
            "     board coordinates using the calibration\n"
            "  5. The score is automatically calculated and displayed\n\n"
            "Manual controls:\n"
            "  • ADD DART — manually place a dart if detection misses\n"
            "  • UNDO — remove the last detected dart\n"
            "  • COMMIT SCORE — manually advance to the next player's turn"
        ),
    },
    {
        "title": "🎮 Gameplay",
        "content": (
            "Playing a game:\n\n"
            "  1. Select your game mode (301, 501, or 701) and players on the setup screen\n"
            "  2. Players take turns throwing 3 darts each\n"
            "  3. The score counts DOWN from the starting value to exactly 0\n"
            "  4. You must finish on a DOUBLE or the Bullseye (50)\n"
            "  5. If you go below 0 or land on 1, it's a BUST — your score reverts\n\n"
            "Keyboard shortcuts during the game:\n"
            "  Enter    — Commit current visit\n"
            "  R        — Reset reference frame (re-capture board state)\n"
            "  Escape   — Return to menu\n\n"
            "The game automatically tracks averages (points per visit) for each player."
        ),
    },
]


class TutorialScreen(tk.Frame):
    def __init__(self, parent, on_back):
        super().__init__(parent, bg=BG)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        tk.Label(self, text="How to Play", font=FONT_TITLE, bg=BG, fg=TEXT).grid(
            row=0, column=0, pady=(30, 10))

        # Tab buttons
        self.tab_frame = tk.Frame(self, bg=BG)
        self.tab_frame.grid(row=1, column=0, pady=(0, 10))
        self.active_section = tk.IntVar(value=0)
        self._tab_buttons = []
        for i, sec in enumerate(SECTIONS):
            btn = tk.Button(self.tab_frame, text=sec["title"],
                            command=lambda i=i: self._show(i),
                            font=FONT_BODY, relief="flat", cursor="hand2", padx=10, pady=6)
            btn.pack(side="left", padx=4)
            self._tab_buttons.append(btn)

        # Content area
        self.content_frame = tk.Frame(self, bg=BG2, padx=30, pady=20)
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=40, pady=(0, 10))
        self.content_frame.columnconfigure(0, weight=1)

        self.content_label = tk.Label(self.content_frame, text="", font=FONT_BODY,
                                      bg=BG2, fg=TEXT, justify="left", wraplength=680,
                                      anchor="nw")
        self.content_label.grid(row=0, column=0, sticky="nw")

        # Back button
        tk.Button(self, text="← Back to Menu", command=on_back, **BTN_SECONDARY).grid(
            row=3, column=0, pady=20)

        self._show(0)

    def _show(self, index):
        self.active_section.set(index)
        sec = SECTIONS[index]
        self.content_label.config(text=sec["content"])
        for i, btn in enumerate(self._tab_buttons):
            if i == index:
                btn.config(bg=ACCENT, fg=WHITE)
            else:
                btn.config(bg=ACCENT2, fg=TEXT)

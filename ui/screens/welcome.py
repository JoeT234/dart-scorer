"""
Welcome / home screen.
"""
import tkinter as tk
from ui.theme import *


class WelcomeScreen(tk.Frame):
    def __init__(self, parent, on_start, on_tutorial):
        super().__init__(parent, bg=BG)

        # center content vertically
        self.columnconfigure(0, weight=1)
        for i in range(8):
            self.rowconfigure(i, weight=1)

        # logo / title
        tk.Label(self, text="🎯", font=("Helvetica", 64), bg=BG, fg=ACCENT).grid(row=1, column=0)
        tk.Label(self, text="DART SCORER", font=FONT_TITLE, bg=BG, fg=TEXT).grid(row=2, column=0, pady=(0, 4))
        tk.Label(self, text="Automatic webcam dart detection", font=FONT_BODY, bg=BG, fg=TEXT_DIM).grid(row=3, column=0, pady=(0, 30))

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.grid(row=4, column=0)

        tk.Button(btn_frame, text="NEW GAME", command=on_start, **BTN_STYLE).pack(side="left", padx=10)
        tk.Button(btn_frame, text="HOW TO PLAY", command=on_tutorial, **BTN_SECONDARY).pack(side="left", padx=10)

        tk.Label(self, text="Free & open source • No cloud required", font=("Helvetica", 9),
                 bg=BG, fg=TEXT_DIM).grid(row=6, column=0, pady=(30, 0))

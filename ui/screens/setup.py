"""
Game setup screen: mode, starting score, player names.
"""
import tkinter as tk
from tkinter import ttk
from ui.theme import *


class SetupScreen(tk.Frame):
    def __init__(self, parent, on_start_game, on_back):
        super().__init__(parent, bg=BG)
        self.on_start_game = on_start_game

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # ── Header ─────────────────────────────────────────────
        tk.Label(self, text="Game Setup", font=FONT_TITLE, bg=BG, fg=TEXT).grid(
            row=0, column=0, columnspan=2, pady=(30, 20))

        # ── Game mode ──────────────────────────────────────────
        tk.Label(self, text="Game Mode", font=FONT_SUBHEADING, bg=BG, fg=TEXT_DIM).grid(
            row=1, column=0, sticky="e", padx=(0, 10), pady=6)

        self.game_mode = tk.StringVar(value="501")
        mode_frame = tk.Frame(self, bg=BG)
        mode_frame.grid(row=1, column=1, sticky="w")
        for mode in ["301", "501", "701"]:
            tk.Radiobutton(mode_frame, text=mode, variable=self.game_mode, value=mode,
                           bg=BG, fg=TEXT, selectcolor=ACCENT2, activebackground=BG,
                           font=FONT_BODY).pack(side="left", padx=6)

        # ── Legs ───────────────────────────────────────────────
        tk.Label(self, text="First to (legs)", font=FONT_SUBHEADING, bg=BG, fg=TEXT_DIM).grid(
            row=2, column=0, sticky="e", padx=(0, 10), pady=6)

        self.num_legs = tk.IntVar(value=1)
        legs_frame = tk.Frame(self, bg=BG)
        legs_frame.grid(row=2, column=1, sticky="w")
        for n in [1, 3, 5]:
            tk.Radiobutton(legs_frame, text=str(n), variable=self.num_legs, value=n,
                           bg=BG, fg=TEXT, selectcolor=ACCENT2, activebackground=BG,
                           font=FONT_BODY).pack(side="left", padx=6)

        # ── Number of players ──────────────────────────────────
        tk.Label(self, text="Players", font=FONT_SUBHEADING, bg=BG, fg=TEXT_DIM).grid(
            row=3, column=0, sticky="e", padx=(0, 10), pady=6)

        self.num_players = tk.IntVar(value=2)
        self.num_players.trace_add("write", self._update_player_fields)
        spin = tk.Spinbox(self, from_=1, to=6, textvariable=self.num_players, width=4,
                          font=FONT_BODY, bg=BG2, fg=TEXT, buttonbackground=ACCENT2,
                          relief="flat", insertbackground=TEXT)
        spin.grid(row=3, column=1, sticky="w")

        # ── Player name fields (dynamic) ────────────────────────
        self.names_frame = tk.Frame(self, bg=BG)
        self.names_frame.grid(row=4, column=0, columnspan=2, pady=10)
        self.name_vars = []
        self._update_player_fields()

        # ── Camera index ───────────────────────────────────────
        tk.Label(self, text="Camera Index", font=FONT_SUBHEADING, bg=BG, fg=TEXT_DIM).grid(
            row=5, column=0, sticky="e", padx=(0, 10), pady=6)
        self.cam_index = tk.IntVar(value=0)
        tk.Spinbox(self, from_=0, to=5, textvariable=self.cam_index, width=4,
                   font=FONT_BODY, bg=BG2, fg=TEXT, buttonbackground=ACCENT2,
                   relief="flat", insertbackground=TEXT).grid(row=5, column=1, sticky="w")

        # ── Buttons ────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=30)
        tk.Button(btn_frame, text="← Back", command=on_back, **BTN_SECONDARY).pack(side="left", padx=10)
        tk.Button(btn_frame, text="START GAME →", command=self._start, **BTN_STYLE).pack(side="left", padx=10)

    def _update_player_fields(self, *_):
        for w in self.names_frame.winfo_children():
            w.destroy()
        self.name_vars = []
        n = self.num_players.get()
        tk.Label(self.names_frame, text="Player Names", font=FONT_SUBHEADING,
                 bg=BG, fg=TEXT_DIM).grid(row=0, column=0, columnspan=2, pady=(0, 6))
        for i in range(n):
            var = tk.StringVar(value=f"Player {i + 1}")
            self.name_vars.append(var)
            tk.Label(self.names_frame, text=f"Player {i + 1}:", font=FONT_BODY,
                     bg=BG, fg=TEXT).grid(row=i + 1, column=0, sticky="e", padx=(0, 8), pady=3)
            tk.Entry(self.names_frame, textvariable=var, font=FONT_BODY,
                     bg=BG2, fg=TEXT, insertbackground=TEXT, relief="flat",
                     width=18).grid(row=i + 1, column=1, sticky="w", pady=3)

    def _start(self):
        names = [v.get().strip() or f"Player {i+1}" for i, v in enumerate(self.name_vars)]
        self.on_start_game(
            mode=self.game_mode.get(),
            starting_score=int(self.game_mode.get()),
            num_legs=self.num_legs.get(),
            player_names=names,
            cam_index=self.cam_index.get(),
        )

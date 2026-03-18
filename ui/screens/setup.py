"""
Setup screen: clean card-based form for game config + player names.
"""
import tkinter as tk
from ui.theme import *
from ui.widgets import PillGroup, card, separator


class SetupScreen(tk.Frame):
    def __init__(self, parent, on_start_game, on_back):
        super().__init__(parent, bg=BG)
        self.on_start_game = on_start_game
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Center the form card
        outer = tk.Frame(self, bg=BG)
        outer.grid(row=0, column=0)
        outer.columnconfigure(0, weight=1)

        # Page title
        tk.Label(outer, text="New Game", font=FONT_TITLE,
                 bg=BG, fg=TEXT).grid(row=0, column=0, pady=(40, 4))
        tk.Label(outer, text="Configure your match below",
                 font=FONT_BODY, bg=BG, fg=TEXT_MID).grid(row=1, column=0, pady=(0, 30))

        # ── Card wrapper ────────────────────────────────────────
        card_border, card_inner = card(outer, bg=SURFACE, border_color=BORDER, border_width=1,
                                       padx=36, pady=30)
        card_border.grid(row=2, column=0)
        card_inner.columnconfigure(1, weight=1)

        row = 0

        # Game Mode
        self._section_label(card_inner, "Game Mode", row)
        row += 1
        self.game_mode = tk.StringVar(value="501")
        PillGroup(card_inner,
                  options=[("301", "301"), ("501", "501"), ("701", "701")],
                  variable=self.game_mode, bg=SURFACE).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 20))
        row += 1

        # Legs
        self._section_label(card_inner, "First to X Legs", row)
        row += 1
        self.num_legs = tk.StringVar(value="1")
        PillGroup(card_inner,
                  options=[("1", "1"), ("3", "3"), ("5", "5")],
                  variable=self.num_legs, bg=SURFACE).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 20))
        row += 1

        # Separator
        separator(card_inner, color=BORDER).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        row += 1

        # Number of players
        self._section_label(card_inner, "Number of Players", row)
        row += 1
        self.num_players = tk.IntVar(value=2)
        counter_frame = tk.Frame(card_inner, bg=SURFACE)
        counter_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 20))
        self._build_counter(counter_frame)
        row += 1

        # Separator
        separator(card_inner, color=BORDER).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        row += 1

        # Player names (dynamic)
        self._section_label(card_inner, "Player Names", row)
        row += 1
        self.names_frame = tk.Frame(card_inner, bg=SURFACE)
        self.names_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        self.name_vars = []
        self.num_players.trace_add("write", self._update_player_fields)
        self._update_player_fields()
        row += 1

        # Separator
        separator(card_inner, color=BORDER).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        row += 1

        # Camera
        self._section_label(card_inner, "Camera Index", row)
        row += 1
        cam_frame = tk.Frame(card_inner, bg=SURFACE)
        cam_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.cam_index = tk.IntVar(value=0)
        self._build_counter(cam_frame, variable=self.cam_index, min_val=0, max_val=5)
        tk.Label(cam_frame, text="  (0 = built-in webcam)",
                 font=FONT_CAPTION, bg=SURFACE, fg=TEXT_DIM).pack(side="left")
        row += 1

        # ── Bottom buttons (outside card) ───────────────────────
        btn_outer = tk.Frame(outer, bg=BG)
        btn_outer.grid(row=3, column=0, pady=24)

        tk.Button(btn_outer, text="← Back", command=on_back, **BTN_GHOST).pack(side="left", padx=8)
        start_btn = tk.Button(btn_outer, text="START GAME  →",
                              command=self._start, **BTN_PRIMARY)
        start_btn.pack(side="left", padx=8, ipady=4)
        start_btn.bind("<Enter>", lambda e: start_btn.config(bg=ACCENT_HOVER))
        start_btn.bind("<Leave>", lambda e: start_btn.config(bg=ACCENT))

    # ── Helpers ─────────────────────────────────────────────────

    def _section_label(self, parent, text, row):
        tk.Label(parent, text=text.upper(), font=FONT_CAPTION,
                 bg=SURFACE, fg=TEXT_MID, anchor="w").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 6))

    def _build_counter(self, parent, variable=None, min_val=1, max_val=6):
        """Plus/minus counter widget."""
        if variable is None:
            variable = self.num_players
        f = parent
        tk.Button(f, text="−", font=("Helvetica", 14, "bold"),
                  bg=SURFACE2, fg=TEXT, relief="flat", cursor="hand2",
                  padx=12, pady=4, borderwidth=0,
                  activebackground=BORDER_BRIGHT, activeforeground=WHITE,
                  command=lambda: variable.set(max(min_val, variable.get() - 1))
                  ).pack(side="left")

        lbl = tk.Label(f, textvariable=variable, font=FONT_SCORE_SM,
                       bg=SURFACE, fg=TEXT, width=3, anchor="center")
        lbl.pack(side="left", padx=8)

        tk.Button(f, text="+", font=("Helvetica", 14, "bold"),
                  bg=SURFACE2, fg=TEXT, relief="flat", cursor="hand2",
                  padx=12, pady=4, borderwidth=0,
                  activebackground=BORDER_BRIGHT, activeforeground=WHITE,
                  command=lambda: variable.set(min(max_val, variable.get() + 1))
                  ).pack(side="left")

    def _update_player_fields(self, *_):
        for w in self.names_frame.winfo_children():
            w.destroy()
        self.name_vars = []
        n = self.num_players.get()
        for i in range(n):
            row_frame = tk.Frame(self.names_frame, bg=SURFACE)
            row_frame.pack(fill="x", pady=3)

            tk.Label(row_frame, text=f"P{i+1}", font=FONT_SUBHEADING,
                     bg=SURFACE, fg=TEXT_MID, width=3, anchor="w").pack(side="left")

            var = tk.StringVar(value=f"Player {i+1}")
            self.name_vars.append(var)

            entry_frame = tk.Frame(row_frame, bg=BORDER)
            entry_frame.pack(side="left", fill="x", expand=True)

            entry = tk.Entry(entry_frame, textvariable=var,
                             font=FONT_BODY, bg=SURFACE2, fg=TEXT,
                             insertbackground=TEXT, relief="flat",
                             bd=0, highlightthickness=0)
            entry.pack(padx=1, pady=1, fill="x", expand=True, ipady=6)

            # Focus highlight
            entry.bind("<FocusIn>",
                       lambda e, f=entry_frame: f.config(bg=ACCENT))
            entry.bind("<FocusOut>",
                       lambda e, f=entry_frame: f.config(bg=BORDER))

    def _start(self):
        names = [v.get().strip() or f"Player {i+1}" for i, v in enumerate(self.name_vars)]
        self.on_start_game(
            mode=self.game_mode.get(),
            starting_score=int(self.game_mode.get()),
            num_legs=int(self.num_legs.get()),
            player_names=names,
            cam_index=self.cam_index.get(),
        )

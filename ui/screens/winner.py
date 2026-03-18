"""
Match summary / winner celebration screen.
Shown after the last leg of a game is won.
"""
import tkinter as tk
from ui.theme import *
from ui.widgets import separator, card, draw_dartboard


class WinnerScreen(tk.Frame):
    def __init__(self, parent, game, on_rematch, on_home):
        super().__init__(parent, bg=BG)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=1)

        self._build_left(game, on_rematch, on_home)
        self._build_right()
        self._animate_in()

    # ── Left — winner info ───────────────────────────────────────

    def _build_left(self, game, on_rematch, on_home):
        left = tk.Frame(self, bg=BG)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        center = tk.Frame(left, bg=BG)
        center.grid(row=0, column=0)
        center.columnconfigure(0, weight=1)

        # Teal "MATCH OVER" chip
        chip = tk.Frame(center, bg=TEAL_DIM, padx=14, pady=4)
        chip.grid(row=0, column=0, pady=(50, 0))
        tk.Label(chip, text="MATCH OVER", font=FONT_CAPTION,
                 bg=TEAL_DIM, fg=TEAL).pack()

        # Trophy + winner name
        tk.Label(center, text="🏆", font=("Helvetica", 56), bg=BG).grid(
            row=1, column=0, pady=(16, 4))

        tk.Label(center, text=game.winner, font=FONT_TITLE,
                 bg=BG, fg=GOLD).grid(row=2, column=0, pady=(0, 4))

        tk.Label(center, text="WINS THE MATCH", font=FONT_HEADING,
                 bg=BG, fg=TEXT_MID).grid(row=3, column=0, pady=(0, 28))

        separator(center, color=BORDER).grid(
            row=4, column=0, sticky="ew", padx=40, pady=(0, 28))

        # Final standings card
        card_wrap, card_inner = card(center, bg=SURFACE, border_color=BORDER,
                                     border_width=1, padx=28, pady=20)
        card_wrap.grid(row=5, column=0, padx=40, pady=(0, 32))
        card_inner.columnconfigure(1, weight=1)

        tk.Label(card_inner, text="FINAL STANDINGS", font=FONT_CAPTION,
                 bg=SURFACE, fg=TEXT_DIM, anchor="w").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        separator(card_inner, color=BORDER).grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(0, 12))

        MEDALS = ["🥇", "🥈", "🥉", "4th", "5th", "6th"]
        avgs = game.averages

        # Rank: winner first, then legs desc, then avg desc
        ranked = sorted(
            range(game.num_players),
            key=lambda i: (-game.leg_scores[i], -avgs[i])
        )

        for rank, i in enumerate(ranked):
            is_winner = (game.leg_scores[i] == max(game.leg_scores))
            fg_name  = GOLD if is_winner else TEXT_MID
            fg_info  = GOLD_HOVER if is_winner else TEXT_DIM
            medal    = MEDALS[rank] if rank < len(MEDALS) else ""

            tk.Label(card_inner, text=medal, font=FONT_BODY,
                     bg=SURFACE, fg=fg_name, anchor="w", width=4).grid(
                row=rank + 2, column=0, padx=(0, 8), pady=5)

            tk.Label(card_inner, text=game.player_names[i],
                     font=FONT_SUBHEADING, bg=SURFACE, fg=fg_name,
                     anchor="w", width=16).grid(
                row=rank + 2, column=1, padx=(0, 20))

            leg_s = game.leg_scores[i]
            info  = f"{leg_s} leg{'s' if leg_s != 1 else ''}  ·  avg {avgs[i]:.0f}"
            tk.Label(card_inner, text=info, font=FONT_CAPTION,
                     bg=SURFACE, fg=fg_info, anchor="e").grid(
                row=rank + 2, column=2, pady=5)

        separator(center, color=BORDER).grid(
            row=6, column=0, sticky="ew", padx=40, pady=(0, 28))

        # CTA buttons
        btn_frame = tk.Frame(center, bg=BG)
        btn_frame.grid(row=7, column=0, pady=(0, 50))

        home_btn = tk.Button(btn_frame, text="← Main Menu",
                             command=on_home, **BTN_SECONDARY)
        home_btn.pack(side="left", padx=8, ipady=6)

        rematch_btn = tk.Button(btn_frame, text="↺  Rematch",
                                command=on_rematch, **BTN_PRIMARY)
        rematch_btn.pack(side="left", padx=8, ipady=6)

        for btn, hover, normal in [
            (home_btn,    BORDER_BRIGHT, SURFACE2),
            (rematch_btn, ACCENT_HOVER,  ACCENT),
        ]:
            btn.bind("<Enter>", lambda e, b=btn, c=hover: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=normal: b.config(bg=c))

        # Keyboard shortcuts
        self.bind_all("<Return>", lambda e: on_rematch())
        self.bind_all("<Escape>", lambda e: on_home())

    # ── Right — decorative dartboard ────────────────────────────

    def _build_right(self):
        right = tk.Frame(self, bg=BG, width=340)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_propagate(False)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        size = 320
        c = tk.Canvas(right, width=size, height=size, bg=BG, highlightthickness=0)
        c.grid(row=0, column=0, padx=20, pady=20)

        draw_dartboard(c, size // 2, size // 2, size // 2 - 20, bg=BG)

        # Gold centre dot
        c.create_oval(size//2 - 5, size//2 - 5, size//2 + 5, size//2 + 5,
                      fill=GOLD, outline="")

    # ── Entrance animation (subtle fade-in via background fill) ─

    def _animate_in(self):
        """Animate the trophy label dropping in."""
        # Simple: use after() to set geometry, Tkinter can't do real animations
        # Just ensure the screen is visible
        self.update_idletasks()

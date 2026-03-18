"""
Reusable custom widgets: dartboard canvas drawing, player cards, dart slots.
"""
import tkinter as tk
import math
from ui.theme import *


# ── Dartboard drawing ──────────────────────────────────────────────────────

def draw_dartboard(canvas, cx, cy, radius, bg=BG, alpha=1.0):
    """
    Draw a complete dartboard on a Tkinter Canvas.
    cx, cy: center coords. radius: outer board radius in pixels.
    bg: color to use for the "cutout" between rings — must match canvas bg.
    """
    # Board dimensions (proportional to radius, from dart-sense get_scores.py)
    D_OUT = radius
    D_IN  = 160.0 / 170.0 * radius
    T_OUT = 107.4 / 170.0 * radius
    T_IN  = 97.4  / 170.0 * radius
    SB    = 15.9  / 170.0 * radius
    DB    = 6.35  / 170.0 * radius

    WIRE  = "#5a5a35"

    # Board backing (slight overshoot to show a wire border)
    canvas.create_oval(cx-D_OUT-3, cy-D_OUT-3, cx+D_OUT+3, cy+D_OUT+3,
                       fill="#181408", outline="#777755", width=3)

    # Draw layers from outside in. Each layer = 20 pie slices, then
    # a bg-colored circle covers the center so only the ring is visible.
    layers = [
        (D_IN, D_OUT, "#bf2e2e", "#2a9e52"),   # double ring (red / green)
        (T_OUT, D_IN, "#ddd8b8", "#1a1a1a"),   # outer single (cream / black)
        (T_IN,  T_OUT,"#bf2e2e", "#2a9e52"),   # triple ring
        (SB,    T_IN, "#ddd8b8", "#1a1a1a"),   # inner single
    ]

    for r_inner, r_outer, c_even, c_odd in layers:
        for i in range(20):
            color = c_even if i % 2 == 0 else c_odd
            # Tkinter arc: 0° = 3 o'clock, positive = CCW.
            # Segment 0 (20) is at top (90°). Each segment = 18°.
            start = 90 - i * 18 + 9   # left edge of segment i
            canvas.create_arc(
                cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer,
                start=start, extent=-18,
                fill=color, outline="", style="pie"
            )
        # Cover center to leave only the ring visible
        canvas.create_oval(cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner,
                           fill=bg, outline="")

    # Single bull (red)
    canvas.create_oval(cx-SB, cy-SB, cx+SB, cy+SB, fill="#bf2e2e", outline=WIRE, width=1)
    # Double bull (green)
    canvas.create_oval(cx-DB, cy-DB, cx+DB, cy+DB, fill="#2a9e52", outline=WIRE, width=1)

    # Segment divider lines (from SB outward to board edge)
    for i in range(20):
        angle = math.radians(90 - i * 18)
        x1 = cx + SB * math.cos(angle)
        y1 = cy - SB * math.sin(angle)
        x2 = cx + D_OUT * math.cos(angle)
        y2 = cy - D_OUT * math.sin(angle)
        canvas.create_line(x1, y1, x2, y2, fill=WIRE, width=1)

    # Wire ring circles
    for r in [D_OUT, D_IN, T_OUT, T_IN, SB, DB]:
        canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="", outline=WIRE, width=1)

    # Segment number labels (drawn last, on top)
    SEGMENTS = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
    label_r = D_OUT * 1.08
    font_size = max(7, int(radius * 0.09))
    for i, num in enumerate(SEGMENTS):
        angle = math.radians(90 - i * 18)
        lx = cx + label_r * math.cos(angle)
        ly = cy - label_r * math.sin(angle)
        canvas.create_text(lx, ly, text=str(num),
                           font=("Helvetica", font_size, "bold"),
                           fill="#cccc99")


# ── Card helpers ───────────────────────────────────────────────────────────

def card(parent, bg=SURFACE, border_color=BORDER, border_width=1, **kwargs):
    """A Frame styled as a card with a colored border."""
    wrapper = tk.Frame(parent, bg=border_color,
                       padx=border_width, pady=border_width)
    inner = tk.Frame(wrapper, bg=bg, **kwargs)
    inner.pack(fill="both", expand=True)
    return wrapper, inner


def separator(parent, color=BORDER, horizontal=True, thickness=1, **kwargs):
    """A thin separator line."""
    if horizontal:
        return tk.Frame(parent, bg=color, height=thickness, **kwargs)
    return tk.Frame(parent, bg=color, width=thickness, **kwargs)


# ── Pill toggle buttons ────────────────────────────────────────────────────

class PillGroup(tk.Frame):
    """
    A row of mutually-exclusive toggle buttons styled as pills.
    Selected pill has ACCENT bg; others have SURFACE2.
    """
    def __init__(self, parent, options, variable, **kwargs):
        super().__init__(parent, bg=kwargs.pop("bg", BG), **kwargs)
        self._var = variable
        self._btns = []
        for i, (label, value) in enumerate(options):
            btn = tk.Button(
                self, text=label, relief="flat", cursor="hand2",
                font=FONT_SUBHEADING, padx=20, pady=8,
                borderwidth=0,
                command=lambda v=value: self._select(v),
            )
            btn.pack(side="left", padx=(0 if i == 0 else 4, 0))
            self._btns.append((btn, value))
        variable.trace_add("write", lambda *_: self._refresh())
        self._refresh()

    def _select(self, value):
        self._var.set(value)

    def _refresh(self):
        current = self._var.get()
        for btn, val in self._btns:
            if val == current:
                btn.config(bg=ACCENT, fg=WHITE,
                           activebackground=ACCENT_HOVER, activeforeground=WHITE)
            else:
                btn.config(bg=SURFACE2, fg=TEXT_MID,
                           activebackground=BORDER_BRIGHT, activeforeground=TEXT)


# ── Dart slot widget ───────────────────────────────────────────────────────

class DartSlot(tk.Canvas):
    """
    A small card-like slot for one dart.
    Shows either empty (dashed outline) or a score label in dart color.
    """
    W, H = 76, 62

    def __init__(self, parent, dart_index=0, **kwargs):
        super().__init__(parent, width=self.W, height=self.H,
                         bg=SURFACE, highlightthickness=0, **kwargs)
        self._index = dart_index
        self._color = DART_COLORS[dart_index % len(DART_COLORS)]
        self.set_empty()

    def set_empty(self):
        self.delete("all")
        # Dart index badge top-left
        self.create_text(10, 10, text=f"#{self._index + 1}",
                         font=("Helvetica", 7), fill=TEXT_DIM)
        # Dashed border
        self.create_rectangle(3, 3, self.W - 3, self.H - 3,
                              outline=BORDER_BRIGHT, width=1, dash=(4, 4))
        # Dash placeholder
        self.create_text(self.W // 2, self.H // 2 + 2, text="—",
                         font=FONT_SCORE_SM, fill=TEXT_DIM)

    def set_score(self, notation, points):
        self.delete("all")
        # Subtle tint background
        self.create_rectangle(3, 3, self.W - 3, self.H - 3,
                              fill=self._dim_color(), outline="")
        # Colored border
        self.create_rectangle(3, 3, self.W - 3, self.H - 3,
                              outline=self._color, width=2, fill="")
        # Dart index badge top-left in dart color
        self.create_text(10, 9, text=f"#{self._index + 1}",
                         font=("Helvetica", 7, "bold"), fill=self._color)
        # Notation — centred, large
        self.create_text(self.W // 2, self.H // 2 - 6,
                         text=notation, font=FONT_SCORE_SM, fill=self._color)
        # Points — centred, smaller
        self.create_text(self.W // 2, self.H // 2 + 14,
                         text=f"{points} pts", font=FONT_CAPTION, fill=TEXT_MID)

    def _dim_color(self):
        # Return a very dark version of the dart color
        dims = {BLUE: "#0a1f2e", ORANGE: "#2e1a0a", PURPLE: "#1a1228"}
        return dims.get(self._color, SURFACE2)


# ── Player score card ──────────────────────────────────────────────────────

class PlayerCard(tk.Frame):
    """
    Horizontal player score card for the top bar of the game screen.
    Active player has a bottom accent bar and gold score.
    """
    def __init__(self, parent, name, starting_score, **kwargs):
        super().__init__(parent, bg=SURFACE, **kwargs)
        self.columnconfigure(0, weight=1)

        self._name_var = tk.StringVar(value=name)
        self._score_var = tk.StringVar(value=str(starting_score))
        self._info_var = tk.StringVar(value="Avg  0  ·  Legs  0")
        self._active = False

        # Active indicator bar (bottom)
        self._bar = tk.Frame(self, height=3, bg=SURFACE)
        self._bar.grid(row=0, column=0, sticky="ew")

        # Name
        self._name_lbl = tk.Label(self, textvariable=self._name_var,
                                   font=FONT_SUBHEADING, bg=SURFACE,
                                   fg=TEXT_MID, anchor="center")
        self._name_lbl.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 0))

        # Score
        self._score_lbl = tk.Label(self, textvariable=self._score_var,
                                    font=FONT_SCORE_HUGE, bg=SURFACE,
                                    fg=TEXT_DIM, anchor="center")
        self._score_lbl.grid(row=2, column=0, sticky="ew", padx=16)

        # Info
        self._info_lbl = tk.Label(self, textvariable=self._info_var,
                                   font=FONT_CAPTION, bg=SURFACE,
                                   fg=TEXT_DIM, anchor="center")
        self._info_lbl.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 8))

    def update(self, score, avg, legs, active, total_legs=None):
        self._score_var.set(str(score))
        legs_txt = f"{legs}/{total_legs}" if total_legs else str(legs)
        self._info_var.set(f"avg  {avg:.0f}  ·  legs  {legs_txt}")
        self._active = active
        if active:
            self._bar.config(bg=ACCENT)
            self._name_lbl.config(fg=GOLD)
            self._score_lbl.config(fg=GOLD)
            self.config(bg=SURFACE2)
            for w in (self._name_lbl, self._score_lbl, self._info_lbl, self._bar):
                w.config(bg=SURFACE2)
        else:
            self._bar.config(bg=BORDER)     # subtle top rule when inactive
            self._name_lbl.config(fg=TEXT_MID)
            self._score_lbl.config(fg=TEXT_DIM)
            self.config(bg=SURFACE)
            for w in (self._name_lbl, self._score_lbl, self._info_lbl):
                w.config(bg=SURFACE)
            self._bar.config(bg=BORDER)

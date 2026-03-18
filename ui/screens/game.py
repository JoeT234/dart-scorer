"""
Game screen: top scorebar + camera feed + right action panel.
"""
import tkinter as tk
from tkinter import messagebox
import threading
import numpy as np
import cv2
from PIL import Image, ImageTk

from dart_engine.detector import DartDetector
from dart_engine.get_scores import GetScores
from dart_engine.game_logic import GameLogic
from ui.theme import *
from ui.widgets import PlayerCard, DartSlot, separator

STATE_CALIBRATING = "calibrating"
STATE_WAITING     = "waiting"
STATE_DETECTING   = "detecting"


class GameScreen(tk.Frame):
    def __init__(self, parent, game_config, on_back):
        super().__init__(parent, bg=BG)
        self.on_back = on_back

        # Engine
        self.detector = DartDetector(camera_index=game_config["cam_index"])
        self.scorer   = GetScores()
        self.game     = GameLogic(
            ruleset="x01",
            player_names=game_config["player_names"],
            starting_score=game_config["starting_score"],
            num_legs=game_config["num_legs"],
        )

        # Calibration
        self.calib_coords  = -np.ones((4, 2))
        self.calib_labels  = ["20 (top)", "6 (right)", "11 (left)", "3 (bottom)"]
        self.calib_index   = 0
        self.H_matrix      = None

        # Visit state
        self.state         = STATE_CALIBRATING
        self.current_darts = []
        self.current_dart_img_coords = []
        self.visit_history = []
        self._last_stable  = []
        self._stop_event   = threading.Event()

        # Display
        self.DISPLAY_W = 660
        self.DISPLAY_H = 495
        self._photo    = None

        self._build_ui()
        self._open_camera()
        self._video_loop()

    # ════════════════════════════════════════════════════════════
    # UI BUILD
    # ════════════════════════════════════════════════════════════

    def _build_ui(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_top_bar()
        self._build_main_area()
        self._bind_keys()
        self._update_scoreboard()
        self._set_status("calibrate", "Click 'Calibrate Board' — then click the 4 corners on the camera feed.")

    # ── Top scorebar ────────────────────────────────────────────

    def _build_top_bar(self):
        bar = tk.Frame(self, bg=SURFACE)
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(tuple(range(self.game.num_players + 2)), weight=1)

        # Left: back button
        tk.Button(bar, text="←", command=self._back_to_menu,
                  bg=SURFACE, fg=TEXT_DIM, font=("Helvetica", 16),
                  relief="flat", cursor="hand2", padx=14, pady=0,
                  borderwidth=0, activebackground=SURFACE2,
                  activeforeground=TEXT).grid(row=0, column=0, sticky="ns", padx=(4, 0))

        # Player cards
        self._player_cards = []
        for i, name in enumerate(self.game.player_names):
            pc = PlayerCard(bar, name, self.game.starting_score)
            pc.grid(row=0, column=i+1, sticky="nsew", padx=1, pady=1)
            self._player_cards.append(pc)

        # Right: game info badge
        info = tk.Frame(bar, bg=SURFACE, padx=16)
        info.grid(row=0, column=self.game.num_players+1, sticky="ns")
        tk.Label(info, text=f"{self.game.starting_score}", font=FONT_SCORE_SM,
                 bg=SURFACE, fg=ACCENT).pack(anchor="center", pady=(8, 0))
        tk.Label(info, text=f"Best of {self.game.num_legs}", font=FONT_CAPTION,
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor="center", pady=(0, 8))

        # Bottom border
        separator(self, color=BORDER).grid(row=0, column=0, sticky="sew")

    # ── Main area ───────────────────────────────────────────────

    def _build_main_area(self):
        main = tk.Frame(self, bg=BG)
        main.grid(row=1, column=0, sticky="nsew")
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)  # camera side
        main.columnconfigure(1, weight=0)  # fixed sidebar

        self._build_camera_panel(main)
        self._build_sidebar(main)

    # ── Camera panel ────────────────────────────────────────────

    def _build_camera_panel(self, parent):
        cam_frame = tk.Frame(parent, bg=BG)
        cam_frame.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        cam_frame.rowconfigure(0, weight=1)
        cam_frame.columnconfigure(0, weight=1)

        # Canvas
        cam_border = tk.Frame(cam_frame, bg=BORDER)
        cam_border.grid(row=0, column=0, sticky="nsew")
        cam_border.rowconfigure(0, weight=1)
        cam_border.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(cam_border, bg="#05050f",
                                width=self.DISPLAY_W, height=self.DISPLAY_H,
                                highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Status bar below camera
        self._status_bar = tk.Frame(cam_frame, bg=SURFACE, height=36)
        self._status_bar.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self._status_bar.columnconfigure(1, weight=1)

        # Status dot indicator
        self._status_dot = tk.Canvas(self._status_bar, width=10, height=10,
                                     bg=SURFACE, highlightthickness=0)
        self._status_dot.grid(row=0, column=0, padx=(12, 6), pady=13)

        self._status_msg = tk.Label(self._status_bar, text="",
                                    font=FONT_BODY, bg=SURFACE, fg=TEXT_MID,
                                    anchor="w")
        self._status_msg.grid(row=0, column=1, sticky="w")

    # ── Right sidebar ────────────────────────────────────────────

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=SURFACE, width=300)
        sb.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=0)
        sb.columnconfigure(0, weight=1)
        sb.grid_propagate(False)

        inner = tk.Frame(sb, bg=SURFACE, padx=20)
        inner.pack(fill="both", expand=True, pady=16)
        inner.columnconfigure(0, weight=1)

        # Current player label
        self._turn_lbl = tk.Label(inner, text="", font=FONT_CAPTION,
                                   bg=SURFACE, fg=TEXT_MID, anchor="w")
        self._turn_lbl.pack(fill="x", pady=(0, 2))

        self._player_lbl = tk.Label(inner, text="", font=FONT_HEADING,
                                     bg=SURFACE, fg=GOLD, anchor="w")
        self._player_lbl.pack(fill="x", pady=(0, 12))

        separator(inner, color=BORDER).pack(fill="x", pady=(0, 16))

        # Dart slots
        tk.Label(inner, text="THIS VISIT", font=FONT_CAPTION,
                 bg=SURFACE, fg=TEXT_MID, anchor="w").pack(fill="x", pady=(0, 8))

        slots_frame = tk.Frame(inner, bg=SURFACE)
        slots_frame.pack(fill="x")
        self._dart_slots = []
        for i in range(3):
            slot = DartSlot(slots_frame, dart_index=i)
            slot.pack(side="left", padx=(0, 6))
            self._dart_slots.append(slot)

        # Visit total
        self._visit_total = tk.Label(inner, text="", font=FONT_BODY,
                                      bg=SURFACE, fg=TEXT_MID, anchor="w")
        self._visit_total.pack(fill="x", pady=(10, 0))

        self._leaves_lbl = tk.Label(inner, text="", font=FONT_SCORE_MED,
                                     bg=SURFACE, fg=TEXT, anchor="w")
        self._leaves_lbl.pack(fill="x", pady=(2, 0))

        separator(inner, color=BORDER).pack(fill="x", pady=16)

        # Action buttons
        self._auto_calib_btn = tk.Button(inner, text="✨  Auto Calibrate",
                                          command=self._auto_calibrate, **BTN_PRIMARY)
        self._auto_calib_btn.pack(fill="x", pady=3, ipady=2)

        self._calib_btn = tk.Button(inner, text="🎯  Manual Calibrate",
                                     command=self._start_calibration, **BTN_SECONDARY)
        self._calib_btn.pack(fill="x", pady=3)

        self._ref_btn = tk.Button(inner, text="📷  Reset Reference  [R]",
                                   command=self._capture_reference, **BTN_SECONDARY)
        self._ref_btn.pack(fill="x", pady=3)

        separator(inner, color=BORDER).pack(fill="x", pady=(8, 8))

        self._add_btn = tk.Button(inner, text="＋  Add Dart  [A]",
                                   command=self._add_dart_manual, **BTN_GHOST)
        self._add_btn.pack(fill="x", pady=2)

        self._undo_btn = tk.Button(inner, text="↩  Undo Last Dart",
                                    command=self._undo_dart, **BTN_GHOST)
        self._undo_btn.pack(fill="x", pady=2)

        # Commit — main CTA
        tk.Frame(inner, bg=SURFACE).pack(fill="both", expand=True)

        self._commit_btn = tk.Button(inner, text="✓  Commit Visit  [Enter]",
                                      command=self._commit_visit, **BTN_PRIMARY)
        self._commit_btn.pack(fill="x", pady=(8, 0), ipady=4)

        # Hover effects
        for btn, hover, normal in [
            (self._auto_calib_btn, ACCENT_HOVER, ACCENT),
            (self._commit_btn,     ACCENT_HOVER, ACCENT),
            (self._calib_btn,      BORDER_BRIGHT, SURFACE2),
            (self._ref_btn,        BORDER_BRIGHT, SURFACE2),
        ]:
            btn.bind("<Enter>", lambda e, b=btn, c=hover: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=normal: b.config(bg=c))

    # ════════════════════════════════════════════════════════════
    # KEY BINDINGS
    # ════════════════════════════════════════════════════════════

    def _bind_keys(self):
        self.bind_all("<Return>",  lambda e: self._commit_visit())
        self.bind_all("r",         lambda e: self._capture_reference())
        self.bind_all("R",         lambda e: self._capture_reference())
        self.bind_all("a",         lambda e: self._add_dart_manual())
        self.bind_all("A",         lambda e: self._add_dart_manual())
        self.bind_all("<Escape>",  lambda e: self._back_to_menu())

    # ════════════════════════════════════════════════════════════
    # VIDEO LOOP
    # ════════════════════════════════════════════════════════════

    def _open_camera(self):
        try:
            self.detector.open()
        except RuntimeError as e:
            messagebox.showerror("Camera Error", str(e))

    def _video_loop(self):
        if not self.winfo_exists():
            return

        frame, _ = self.detector.read_frame()
        if frame is not None:
            if self.state == STATE_DETECTING:
                stable = self.detector.get_stable_dart_positions(frame)
                if len(stable) > len(self._last_stable):
                    self._last_stable = stable
                    self._update_dart_detections(stable)

            display = self._prepare_display(frame)
            img = Image.fromarray(cv2.cvtColor(display, cv2.COLOR_BGR2RGB))
            img = img.resize((self.DISPLAY_W, self.DISPLAY_H), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._photo = photo
            self.canvas.create_image(0, 0, image=photo, anchor="nw")

        self.after(33, self._video_loop)

    def _prepare_display(self, frame):
        display = frame.copy()
        h, w = display.shape[:2]

        # Calibration crosses
        for i, (cx, cy) in enumerate(self.calib_coords):
            if cx >= 0:
                px, py = int(cx * w), int(cy * h)
                cv2.drawMarker(display, (px, py), (0, 150, 255),
                               cv2.MARKER_CROSS, 22, 2)
                cv2.putText(display, self.calib_labels[i], (px+8, py-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 150, 255), 1)

        # Calibration hint overlay
        if self.state == STATE_CALIBRATING and self.calib_index < 4:
            msg = f"Click  {self.calib_labels[self.calib_index]}  ({self.calib_index+1} / 4)"
            tw = len(msg) * 8
            cv2.rectangle(display, (8, 8), (tw + 16, 34), (14, 14, 30), -1)
            cv2.putText(display, msg, (14, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 180, 255), 1)

        # Board overlay rings
        if self.H_matrix is not None:
            self._draw_board_overlay(display)

        # Dart markers
        for i, (dx, dy) in enumerate(self._last_stable):
            px, py = int(dx * w), int(dy * h)
            hex_c = DART_COLORS[i % 3].lstrip("#")
            r, g, b = [int(hex_c[j:j+2], 16) for j in (0, 2, 4)]
            cv2.circle(display, (px, py), 10, (b, g, r), 2)
            cv2.circle(display, (px, py), 3, (b, g, r), -1)
            label = self.current_darts[i] if i < len(self.current_darts) else "?"
            cv2.putText(display, label, (px+14, py-6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (b, g, r), 2)

        return display

    def _draw_board_overlay(self, frame):
        if self.H_matrix is None:
            return
        try:
            inv_H = np.linalg.inv(self.H_matrix)
        except np.linalg.LinAlgError:
            return

        h, w = frame.shape[:2]
        size = float(min(w, h))
        center_bp = np.array([[[0.5 * size, 0.5 * size]]], dtype=np.float32)
        c_img = cv2.perspectiveTransform(center_bp, inv_H)
        cx, cy = int(c_img[0][0][0]), int(c_img[0][0][1])
        scale = size * 0.85
        for r_norm in self.scorer.scoring_radii[1:]:
            r_px = int(r_norm * scale)
            cv2.circle(frame, (cx, cy), r_px, (60, 80, 200), 1)

    # ════════════════════════════════════════════════════════════
    # CALIBRATION
    # ════════════════════════════════════════════════════════════

    def _auto_calibrate(self):
        """
        Detect the dartboard circle using Hough transforms and automatically
        place the 4 calibration points based on standard board geometry.
        Segment 20 must be at the top of the board for this to work.
        """
        self._set_status("calibrate", "Auto-calibrating — analysing frame...")
        self._auto_calib_btn.config(state="disabled", text="⏳  Detecting...")
        self.update_idletasks()

        # Grab several frames and average the detected circle for stability
        detections = []
        for _ in range(8):
            frame, _ = self.detector.read_frame()
            if frame is None:
                continue
            result = self.detector.auto_detect_board(frame)
            if result is not None:
                detections.append(result)

        self._auto_calib_btn.config(state="normal", text="✨  Auto Calibrate")

        if len(detections) < 3:
            self._set_status("error",
                             "Board not detected. Ensure the board is visible and well-lit, "
                             "or use Manual Calibrate.")
            return

        cx_norm = float(np.mean([d[0] for d in detections]))
        cy_norm = float(np.mean([d[1] for d in detections]))
        r_norm  = float(np.mean([d[2] for d in detections]))

        # Get actual frame size to work in pixels
        frame, _ = self.detector.read_frame()
        if frame is None:
            self._set_status("error", "Camera read failed.")
            return
        h_px, w_px = frame.shape[:2]

        cx_px = cx_norm * w_px
        cy_px = cy_norm * h_px
        r_px  = r_norm * min(w_px, h_px)  # detected circle radius in pixels

        # The detected circle ≈ outer double ring.
        # scorer.scoring_radii[-1] = double-ring outer radius as fraction of
        # the full board diameter (451 mm).  Invert to get full board size.
        h_score = float(self.scorer.scoring_radii[-1])   # ≈ 0.377
        board_diam_px = r_px / h_score                   # full board diameter

        # boardplane_calibration_coords are in [0,1] space where 0.5 = board centre.
        # bp_order maps self.calib_coords[0..3] → boardplane indices [0,3,2,1]
        bp_order = [0, 3, 2, 1]
        for i, bp_i in enumerate(bp_order):
            bx, by = self.scorer.boardplane_calibration_coords[bp_i]
            dx = bx - 0.5
            dy = by - 0.5
            px = cx_px + dx * board_diam_px
            py = cy_px + dy * board_diam_px
            self.calib_coords[i] = [px / w_px, py / h_px]

        self.calib_index = 4
        self._finish_calibration()

    def _start_calibration(self):
        self.state       = STATE_CALIBRATING
        self.calib_coords = -np.ones((4, 2))
        self.calib_index  = 0
        self.H_matrix     = None
        self._set_status("calibrate",
                         f"Click the outer corner of the double ring — '{self.calib_labels[0]}' (1/4)")

    def _on_canvas_click(self, event):
        if self.state != STATE_CALIBRATING or self.calib_index >= 4:
            return
        cw = self.canvas.winfo_width() or self.DISPLAY_W
        ch = self.canvas.winfo_height() or self.DISPLAY_H
        self.calib_coords[self.calib_index] = [event.x / cw, event.y / ch]
        self.calib_index += 1
        if self.calib_index < 4:
            self._set_status("calibrate",
                             f"Good! Now click '{self.calib_labels[self.calib_index]}' ({self.calib_index+1}/4)")
        else:
            self._finish_calibration()

    def _finish_calibration(self):
        bp_order = [0, 3, 2, 1]
        calib_full = -np.ones((6, 2))
        for i, bp_i in enumerate(bp_order):
            calib_full[bp_i] = self.calib_coords[i]

        H, _ = self.scorer.find_homography(calib_full, 1.0)
        if H is None:
            self._set_status("error", "Calibration failed — try again.")
            self._start_calibration()
            return

        self.H_matrix = H
        self.state    = STATE_WAITING
        self._set_status("ok", "Calibrated  ✓  —  Press R to capture the board, then throw your darts.")

    # ════════════════════════════════════════════════════════════
    # DETECTION
    # ════════════════════════════════════════════════════════════

    def _capture_reference(self):
        ok = self.detector.capture_reference()
        self.detector.reset_darts()
        self._last_stable = []
        self.current_darts = []
        self.current_dart_img_coords = []
        if ok:
            self.state = STATE_DETECTING
            self._set_status("active",
                             f"{self.game.player_names[self.game.current_player]}'s turn  —  throw your darts!")
        else:
            self._set_status("error", "Could not capture reference frame. Check camera.")
        self._refresh_slots()
        self._refresh_visit_total()

    def _update_dart_detections(self, stable_norm):
        if not stable_norm or self.H_matrix is None:
            return
        arr = np.array(stable_norm)
        transformed = self.scorer.transform_to_boardplane(self.H_matrix, arr, 1.0)
        if len(transformed) == 0:
            return
        darts, _ = self.scorer.score(transformed)
        self.current_darts = darts
        self.current_dart_img_coords = list(stable_norm)
        self._refresh_slots()
        self._refresh_visit_total()
        if len(darts) >= 3:
            self._set_status("active", "3 darts detected  —  press Enter to commit or adjust.")

    # ════════════════════════════════════════════════════════════
    # UI UPDATES
    # ════════════════════════════════════════════════════════════

    def _refresh_slots(self):
        # Slots show each dart
        for i, slot in enumerate(self._dart_slots):
            if i < len(self.current_darts) and self.current_darts[i]:
                pts = self.game.get_score_for_dart(self.current_darts[i])
                slot.set_score(self.current_darts[i], pts)
            else:
                slot.set_empty()

    def _refresh_visit_total(self):
        darts = self.current_darts
        if not darts:
            self._visit_total.config(text="")
            self._leaves_lbl.config(text="")
            return

        total = sum(self.game.get_score_for_dart(d) for d in darts if d)
        remaining = self.game.scores[self.game.current_player] - total

        self._visit_total.config(text=f"Visit total:  {total}")

        if remaining < 0 or remaining == 1:
            self._leaves_lbl.config(text="BUST", fg=ACCENT)
        elif remaining == 0:
            self._leaves_lbl.config(text="CHECKOUT  🎯", fg=TEAL)
        else:
            self._leaves_lbl.config(text=f"Leaves  {remaining}", fg=TEXT)

    def _update_scoreboard(self):
        avgs = self.game.averages
        for i, pc in enumerate(self._player_cards):
            pc.update(
                score=self.game.scores[i],
                avg=avgs[i],
                legs=self.game.leg_scores[i],
                active=(i == self.game.current_player),
            )
        # Update sidebar player indicator
        name = self.game.player_names[self.game.current_player]
        self._turn_lbl.config(text="NOW PLAYING")
        self._player_lbl.config(text=name)

    def _set_status(self, kind, msg):
        """
        kind: "calibrate" | "active" | "ok" | "error" | "info"
        """
        colors = {
            "calibrate": GOLD,
            "active":    TEAL,
            "ok":        TEAL,
            "error":     ACCENT,
            "info":      TEXT_MID,
        }
        dot_color = colors.get(kind, TEXT_MID)
        self._status_dot.delete("all")
        self._status_dot.create_oval(1, 1, 9, 9, fill=dot_color, outline="")
        self._status_msg.config(text=msg, fg=TEXT_MID)

    # ════════════════════════════════════════════════════════════
    # GAME ACTIONS
    # ════════════════════════════════════════════════════════════

    def _add_dart_manual(self):
        if len(self.current_darts) >= 3:
            return
        self.current_darts.append("S1")
        self.current_dart_img_coords.append((0.5, 0.5))
        self._refresh_slots()
        self._refresh_visit_total()

    def _undo_dart(self):
        if self.current_darts:
            self.current_darts.pop()
            if self.current_dart_img_coords:
                self.current_dart_img_coords.pop()
            if self._last_stable:
                self._last_stable.pop()
            self._refresh_slots()
            self._refresh_visit_total()

    def _commit_visit(self):
        if self.state == STATE_CALIBRATING:
            return
        if not self.current_darts:
            self._set_status("info", "No darts detected yet — throw your darts first.")
            return

        prev_score  = self.game.scores[self.game.current_player]
        prev_player = self.game.current_player

        v_score, _, bust, leg_won, game_over = self.game.commit_visit(self.current_darts)
        self.visit_history.append((prev_player, prev_score))

        self.current_darts = []
        self.current_dart_img_coords = []
        self._last_stable  = []
        self.detector.reset_darts()

        self._update_scoreboard()
        self._refresh_slots()
        self._refresh_visit_total()

        if game_over:
            self._handle_game_over()
        elif leg_won:
            self._handle_leg_won(prev_player)
        elif bust:
            self.state = STATE_WAITING
            self._set_status("error",
                             f"BUST  —  {self.game.player_names[prev_player]} stays at {prev_score}")
        else:
            self.state = STATE_WAITING
            nxt = self.game.player_names[self.game.current_player]
            self._set_status("info", f"Next up: {nxt}  —  press R to capture reference")

    def _handle_leg_won(self, player_idx):
        name = self.game.player_names[player_idx]
        legs = self.game.leg_scores[player_idx]
        self._set_status("ok",
                         f"🏆  {name} wins the leg!  ({legs} / {self.game.num_legs})")
        self.state = STATE_WAITING
        self._update_scoreboard()
        self.after(2500, lambda: self._set_status(
            "info",
            f"Next: {self.game.player_names[self.game.current_player]}  —  press R to start"
        ))

    def _handle_game_over(self):
        self.state = STATE_WAITING
        self._set_status("ok", f"🎉  {self.game.winner} wins the match!")
        self.after(400, lambda: messagebox.showinfo(
            "Game Over",
            f"🎉  {self.game.winner} wins!\n\n" +
            "\n".join(f"  {n}:  {s} leg{'s' if s != 1 else ''}"
                      for n, s in zip(self.game.player_names, self.game.leg_scores))
        ))

    # ════════════════════════════════════════════════════════════
    # CLEANUP
    # ════════════════════════════════════════════════════════════

    def _back_to_menu(self):
        self._stop_event.set()
        self.detector.close()
        self.on_back()

    def destroy(self):
        self._stop_event.set()
        try:
            self.detector.close()
        except Exception:
            pass
        super().destroy()

"""
Game screen: live webcam feed + dart detection + scoreboard.
"""
import tkinter as tk
from tkinter import messagebox
import threading
import time
import numpy as np
import cv2
from PIL import Image, ImageTk

from dart_engine.detector import DartDetector
from dart_engine.get_scores import GetScores
from dart_engine.game_logic import GameLogic
from ui.theme import *

# States
STATE_CALIBRATING = "calibrating"
STATE_WAITING = "waiting"       # between visits — reference captured
STATE_DETECTING = "detecting"   # darts being thrown
STATE_BUST = "bust"
STATE_LEG_WON = "leg_won"


class GameScreen(tk.Frame):
    def __init__(self, parent, game_config, on_back):
        super().__init__(parent, bg=BG)
        self.on_back = on_back

        # ── Engine setup ───────────────────────────────────────
        self.detector = DartDetector(camera_index=game_config["cam_index"])
        self.scorer = GetScores()
        self.game = GameLogic(
            ruleset="x01",
            player_names=game_config["player_names"],
            starting_score=game_config["starting_score"],
            num_legs=game_config["num_legs"],
        )

        # calibration: 4 points (20, 6, 11, 3) clicked by user
        self.calib_coords = -np.ones((4, 2))   # normalized image-plane coords
        self.calib_labels = ["20 (top)", "6 (right)", "11 (left)", "3 (bottom)"]
        self.calib_index = 0
        self.H_matrix = None

        # visit state
        self.state = STATE_CALIBRATING
        self.current_darts = []       # list of notation strings
        self.current_dart_img_coords = []  # list of (x_norm, y_norm) image-plane
        self.visit_history = []       # for undo: list of (player_idx, prev_score)
        self._last_stable = []
        self._detecting_thread = None
        self._stop_event = threading.Event()

        # display
        self.DISPLAY_W = 640
        self.DISPLAY_H = 480
        self._current_photo = None

        self._build_ui()
        self._open_camera()
        self._video_loop()

    # ── UI ──────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        # Left: video canvas
        left = tk.Frame(self, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        self.status_label = tk.Label(left, text="", font=FONT_SUBHEADING,
                                     bg=BG, fg=YELLOW, wraplength=620)
        self.status_label.grid(row=0, column=0, pady=(0, 4))

        self.canvas = tk.Canvas(left, bg="black", width=self.DISPLAY_W, height=self.DISPLAY_H,
                                highlightthickness=2, highlightbackground=ACCENT2)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Right: scoreboard + controls
        right = tk.Frame(self, bg=BG2, padx=16, pady=16)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.columnconfigure(0, weight=1)

        # Scoreboard header
        tk.Label(right, text="SCOREBOARD", font=FONT_HEADING, bg=BG2, fg=ACCENT).grid(
            row=0, column=0, pady=(0, 10))

        self.player_frames = []
        for i, name in enumerate(self.game.player_names):
            pf = tk.Frame(right, bg=BG2)
            pf.grid(row=i + 1, column=0, sticky="ew", pady=4)
            pf.columnconfigure(1, weight=1)

            name_lbl = tk.Label(pf, text=name, font=FONT_SUBHEADING, bg=BG2, fg=TEXT, anchor="w")
            name_lbl.grid(row=0, column=0, columnspan=2, sticky="w")

            score_lbl = tk.Label(pf, text=str(self.game.starting_score),
                                 font=FONT_SCORE_LARGE, bg=BG2, fg=GREEN, anchor="w")
            score_lbl.grid(row=1, column=0, sticky="w")

            info_lbl = tk.Label(pf, text="Avg: 0 | Legs: 0", font=FONT_BODY, bg=BG2, fg=TEXT_DIM)
            info_lbl.grid(row=2, column=0, sticky="w")

            self.player_frames.append({
                "frame": pf, "name": name_lbl, "score": score_lbl, "info": info_lbl
            })

        sep = tk.Frame(right, bg=ACCENT2, height=1)
        sep.grid(row=len(self.game.player_names) + 1, column=0, sticky="ew", pady=10)

        # Current visit panel
        visit_row = len(self.game.player_names) + 2
        tk.Label(right, text="Current Visit", font=FONT_SUBHEADING, bg=BG2, fg=TEXT_DIM).grid(
            row=visit_row, column=0, sticky="w")
        self.visit_label = tk.Label(right, text="—  —  —", font=FONT_SCORE_MED, bg=BG2, fg=YELLOW)
        self.visit_label.grid(row=visit_row + 1, column=0, sticky="w")
        self.visit_total_label = tk.Label(right, text="", font=FONT_BODY, bg=BG2, fg=TEXT_DIM)
        self.visit_total_label.grid(row=visit_row + 2, column=0, sticky="w")

        sep2 = tk.Frame(right, bg=ACCENT2, height=1)
        sep2.grid(row=visit_row + 3, column=0, sticky="ew", pady=10)

        # Control buttons
        ctrl_row = visit_row + 4
        self.calib_btn = tk.Button(right, text="🎯 Calibrate Board",
                                   command=self._start_calibration, **BTN_STYLE)
        self.calib_btn.grid(row=ctrl_row, column=0, sticky="ew", pady=3)

        self.ref_btn = tk.Button(right, text="📷 Reset Reference (R)",
                                 command=self._capture_reference, **BTN_SECONDARY)
        self.ref_btn.grid(row=ctrl_row + 1, column=0, sticky="ew", pady=3)

        self.add_btn = tk.Button(right, text="➕ Add Dart (A)",
                                 command=self._add_dart_manual, **BTN_SECONDARY)
        self.add_btn.grid(row=ctrl_row + 2, column=0, sticky="ew", pady=3)

        self.undo_btn = tk.Button(right, text="↩ Undo Last Dart",
                                  command=self._undo_dart, **BTN_SECONDARY)
        self.undo_btn.grid(row=ctrl_row + 3, column=0, sticky="ew", pady=3)

        self.commit_btn = tk.Button(right, text="✓ Commit Visit (Enter)",
                                    command=self._commit_visit, **BTN_STYLE)
        self.commit_btn.grid(row=ctrl_row + 4, column=0, sticky="ew", pady=3)

        tk.Button(right, text="← Menu (Esc)", command=self._back_to_menu,
                  font=("Helvetica", 9), bg=BG, fg=TEXT_DIM, relief="flat",
                  cursor="hand2").grid(row=ctrl_row + 5, column=0, sticky="ew", pady=(15, 0))

        # Key bindings
        self.bind_all("<Return>", lambda e: self._commit_visit())
        self.bind_all("r", lambda e: self._capture_reference())
        self.bind_all("R", lambda e: self._capture_reference())
        self.bind_all("a", lambda e: self._add_dart_manual())
        self.bind_all("A", lambda e: self._add_dart_manual())
        self.bind_all("<Escape>", lambda e: self._back_to_menu())

        self._update_scoreboard()
        self._set_status("Click 'Calibrate Board' to begin, then click the 4 calibration points.")

    # ── Camera / Video loop ─────────────────────────────────────

    def _open_camera(self):
        try:
            self.detector.open()
        except RuntimeError as e:
            messagebox.showerror("Camera Error", str(e))

    def _video_loop(self):
        if not self.winfo_exists():
            return

        frame, stable_darts = self._get_frame_and_darts()

        if frame is not None:
            display = self._prepare_display(frame, stable_darts)
            img = Image.fromarray(cv2.cvtColor(display, cv2.COLOR_BGR2RGB))
            img = img.resize((self.DISPLAY_W, self.DISPLAY_H), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._current_photo = photo
            self.canvas.create_image(0, 0, image=photo, anchor="nw")

        self.after(33, self._video_loop)  # ~30 fps

    def _get_frame_and_darts(self):
        frame, _ = self.detector.read_frame()
        if frame is None:
            return None, []

        if self.state == STATE_DETECTING:
            stable = self.detector.get_stable_dart_positions(frame)
            if len(stable) > len(self._last_stable):
                self._last_stable = stable
                self._update_dart_detections(stable)
        return frame, self._last_stable

    def _prepare_display(self, frame, dart_coords_norm):
        display = frame.copy()
        h, w = display.shape[:2]

        # draw calibration points
        for i, (cx, cy) in enumerate(self.calib_coords):
            if cx >= 0:
                px, py = int(cx * w), int(cy * h)
                cv2.drawMarker(display, (px, py), (0, 165, 255),
                               cv2.MARKER_CROSS, 20, 2)
                cv2.putText(display, self.calib_labels[i], (px + 6, py - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)

        # draw board overlay if calibrated
        if self.H_matrix is not None:
            self._draw_board_overlay(display)

        # draw detected darts
        for i, (dx, dy) in enumerate(dart_coords_norm):
            px, py = int(dx * w), int(dy * h)
            color_hex = DART_COLORS[i % len(DART_COLORS)].lstrip("#")
            r, g, b = tuple(int(color_hex[j:j+2], 16) for j in (0, 2, 4))
            cv2.circle(display, (px, py), 8, (b, g, r), 2)
            label = self.current_darts[i] if i < len(self.current_darts) else "?"
            cv2.putText(display, label, (px + 10, py - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (b, g, r), 2)

        # calibration target crosshair
        if self.state == STATE_CALIBRATING and self.calib_index < 4:
            msg = f"Click: {self.calib_labels[self.calib_index]} ({self.calib_index+1}/4)"
            cv2.putText(display, msg, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        return display

    def _draw_board_overlay(self, frame):
        h, w = frame.shape[:2]
        size = min(w, h)
        radii_px = (self.scorer.scoring_radii * size * 0.4).astype(int)
        cx, cy = w // 2, h // 2  # approximate — use center of transformed region

        if self.H_matrix is None:
            return

        # invert H to go from boardplane → imageplane for overlay
        try:
            inv_H = np.linalg.inv(self.H_matrix)
        except np.linalg.LinAlgError:
            return

        center_bp = np.array([[[0.5 * size, 0.5 * size]]], dtype=np.float32)
        center_img = cv2.perspectiveTransform(center_bp, inv_H)
        cx, cy = int(center_img[0][0][0]), int(center_img[0][0][1])

        scale = size * 0.9
        for r_norm in self.scorer.scoring_radii[1:]:
            r_px = int(r_norm * scale)
            cv2.circle(frame, (cx, cy), r_px, (80, 80, 255), 1)

    # ── Calibration ─────────────────────────────────────────────

    def _start_calibration(self):
        self.state = STATE_CALIBRATING
        self.calib_coords = -np.ones((4, 2))
        self.calib_index = 0
        self.H_matrix = None
        self._set_status(
            f"Calibration: click the outer corner of the DOUBLE ring for the '{self.calib_labels[0]}' segment (1/4)")

    def _on_canvas_click(self, event):
        if self.state != STATE_CALIBRATING:
            return
        if self.calib_index >= 4:
            return

        # convert canvas coords to normalized image coords
        cw = self.canvas.winfo_width() or self.DISPLAY_W
        ch = self.canvas.winfo_height() or self.DISPLAY_H
        x_norm = event.x / cw
        y_norm = event.y / ch

        self.calib_coords[self.calib_index] = [x_norm, y_norm]
        self.calib_index += 1

        if self.calib_index < 4:
            self._set_status(
                f"Good! Now click: '{self.calib_labels[self.calib_index]}' segment ({self.calib_index+1}/4)")
        else:
            self._finish_calibration()

    def _finish_calibration(self):
        # Map our 4 calibration points (20, 6, 11, 3) to boardplane
        # These correspond to indices 0,3,2,1 in scorer.boardplane_calibration_coords
        # Order we ask user: 20(0), 6(3), 11(2), 3(1)
        bp_order = [0, 3, 2, 1]
        calib_full = -np.ones((6, 2))
        for i, bp_i in enumerate(bp_order):
            calib_full[bp_i] = self.calib_coords[i]

        H, _ = self.scorer.find_homography(calib_full, 1.0)
        if H is None:
            self._set_status("Calibration failed — not enough points. Try again.")
            self._start_calibration()
            return

        self.H_matrix = H
        self.state = STATE_WAITING
        self._set_status("✓ Calibrated! Click 'Reset Reference' then throw your darts.")

    # ── Detection callbacks ──────────────────────────────────────

    def _capture_reference(self):
        ok = self.detector.capture_reference()
        self.detector.reset_darts()
        self._last_stable = []
        self.current_darts = []
        self.current_dart_img_coords = []
        if ok:
            self.state = STATE_DETECTING
            self._set_status(f"{self.game.player_names[self.game.current_player]}'s turn — throw your darts!")
        else:
            self._set_status("Could not capture reference frame. Check camera.")
        self._update_visit_display()

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
        self._update_visit_display()

        if len(darts) >= 3:
            self._set_status("3 darts detected! Press Enter to commit or adjust.")

    def _update_visit_display(self):
        darts = self.current_darts
        if not darts:
            self.visit_label.config(text="—  —  —", fg=YELLOW)
            self.visit_total_label.config(text="")
            return

        parts = []
        total = 0
        for d in darts:
            if d:
                parts.append(d)
                total += self.game.get_score_for_dart(d)

        while len(parts) < 3:
            parts.append("—")

        self.visit_label.config(text="  ".join(parts), fg=YELLOW)

        remaining = self.game.scores[self.game.current_player] - total
        if remaining < 0 or remaining == 1:
            self.visit_total_label.config(text=f"Total: {total}  →  BUST!", fg=ACCENT)
        elif remaining == 0:
            self.visit_total_label.config(text=f"Total: {total}  →  CHECKOUT! 🎯", fg=GREEN)
        else:
            self.visit_total_label.config(text=f"Total: {total}  →  Leaves: {remaining}", fg=TEXT_DIM)

    # ── Game actions ─────────────────────────────────────────────

    def _add_dart_manual(self):
        if len(self.current_darts) >= 3:
            return
        # add a placeholder "S1" dart (user can see in visit)
        self.current_darts.append("S1")
        self.current_dart_img_coords.append((0.5, 0.5))
        self._update_visit_display()

    def _undo_dart(self):
        if self.current_darts:
            self.current_darts.pop()
            if self.current_dart_img_coords:
                self.current_dart_img_coords.pop()
            if self._last_stable:
                self._last_stable.pop()
            self._update_visit_display()

    def _commit_visit(self):
        if self.state == STATE_CALIBRATING:
            return
        if not self.current_darts:
            self._set_status("No darts detected yet. Throw your darts first!")
            return

        prev_score = self.game.scores[self.game.current_player]
        prev_player = self.game.current_player

        visit_score, remaining, bust, leg_won, game_over = self.game.commit_visit(self.current_darts)
        self.visit_history.append((prev_player, prev_score))

        # reset for next visit
        self.current_darts = []
        self.current_dart_img_coords = []
        self._last_stable = []
        self.detector.reset_darts()

        self._update_scoreboard()
        self._update_visit_display()

        if game_over:
            self._handle_game_over()
        elif leg_won:
            self._handle_leg_won(prev_player)
        elif bust:
            self._set_status(f"💥 BUST! {self.game.player_names[prev_player]}'s score stays at {prev_score}")
            self.state = STATE_WAITING
        else:
            self.state = STATE_WAITING
            self._set_status(
                f"{self.game.player_names[self.game.current_player]}'s turn — press R to capture reference")

    def _handle_leg_won(self, player_idx):
        name = self.game.player_names[player_idx]
        legs = self.game.leg_scores[player_idx]
        self._set_status(f"🏆 {name} wins the leg! ({legs}/{self.game.num_legs} legs)")
        self.state = STATE_WAITING
        self._update_scoreboard()
        self.after(2000, lambda: self._set_status(
            f"{self.game.player_names[self.game.current_player]}'s turn — press R to start"))

    def _handle_game_over(self):
        self.state = STATE_WAITING
        self._set_status(f"🎉 GAME OVER! {self.game.winner} wins the match!")
        self.after(500, lambda: messagebox.showinfo(
            "Game Over", f"🎉 {self.game.winner} wins!\n\nFinal leg scores:\n" +
            "\n".join(f"{n}: {s} legs" for n, s in zip(self.game.player_names, self.game.leg_scores))
        ))

    # ── Scoreboard update ────────────────────────────────────────

    def _update_scoreboard(self):
        avgs = self.game.averages
        for i, pf in enumerate(self.player_frames):
            score = self.game.scores[i]
            pf["score"].config(text=str(score))

            if i == self.game.current_player:
                pf["name"].config(fg=YELLOW)
                pf["score"].config(fg=GREEN)
                pf["frame"].config(bg=ACCENT2)
                pf["name"].config(bg=ACCENT2)
                pf["score"].config(bg=ACCENT2)
                pf["info"].config(bg=ACCENT2)
            else:
                pf["name"].config(fg=TEXT)
                pf["score"].config(fg=TEXT_DIM)
                pf["frame"].config(bg=BG2)
                pf["name"].config(bg=BG2)
                pf["score"].config(bg=BG2)
                pf["info"].config(bg=BG2)

            pf["info"].config(
                text=f"Avg: {avgs[i]:.0f} | Legs: {self.game.leg_scores[i]}")

    def _set_status(self, msg):
        self.status_label.config(text=msg)

    # ── Cleanup ──────────────────────────────────────────────────

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

"""
Dart detection via background subtraction.
Board detection via HSV color segmentation + ellipse fitting (primary)
and Hough Circle Transform (fallback). Works at any camera angle.
"""
import cv2
import numpy as np
import threading
import math


class DetectedBoard:
    """Holds the result of a board detection pass."""
    __slots__ = ("cx_n", "cy_n", "a_n", "b_n", "angle_deg", "confidence", "method")

    def __init__(self, cx_n, cy_n, a_n, b_n, angle_deg, confidence, method="color"):
        self.cx_n       = cx_n        # board centre x  (0-1)
        self.cy_n       = cy_n        # board centre y  (0-1)
        self.a_n        = a_n         # semi-major / min(w,h)
        self.b_n        = b_n         # semi-minor / min(w,h)
        self.angle_deg  = angle_deg   # major-axis angle, CCW from x in screen coords
        self.confidence = confidence  # 0-1
        self.method     = method


class DartDetector:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.reference_frame = None
        self._lock = threading.Lock()

        # dart tracking
        self._dart_positions = []
        self._stable_count   = []
        self.STABLE_THRESHOLD = 8
        self.MIN_CONTOUR_AREA = 80
        self.MAX_CONTOUR_AREA = 4000

    # ── Camera ─────────────────────────────────────────────────

    def open(self):
        for idx in list(dict.fromkeys([self.camera_index, 0, 1, 2, 3])):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                self.camera_index = idx
                self.cap = cap
                break
            cap.release()
        else:
            raise RuntimeError(
                "No webcam found. Make sure your camera is connected "
                "and not in use by another app, then restart."
            )
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    def read_frame(self):
        if not self.cap or not self.cap.isOpened():
            return None, []
        ret, frame = self.cap.read()
        if not ret:
            return None, []
        return frame, []

    # ── Board detection ────────────────────────────────────────

    def detect_board(self, frame):
        """
        Detect the dartboard in a frame.
        Primary: HSV color segmentation on red/green rings → ellipse fit.
        Fallback: Hough Circle Transform.
        Returns a DetectedBoard or None.
        Works from any camera angle (handles ellipse, not just circles).
        """
        h, w = frame.shape[:2]
        min_dim = min(h, w)

        result = self._detect_by_color(frame, w, h, min_dim)
        if result is not None:
            return result

        return self._detect_by_hough(frame, w, h, min_dim)

    def _detect_by_color(self, frame, w, h, min_dim):
        """HSV color segmentation on the red + green ring segments."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Red (hue wraps around 0/180)
        mask_r = cv2.bitwise_or(
            cv2.inRange(hsv, np.array([0,   55, 45]), np.array([14,  255, 255])),
            cv2.inRange(hsv, np.array([164, 55, 45]), np.array([180, 255, 255])),
        )
        # Green
        mask_g = cv2.inRange(hsv, np.array([36, 45, 40]), np.array([95, 255, 255]))

        combined = cv2.bitwise_or(mask_r, mask_g)

        # Morphological cleanup: close small gaps, remove noise
        k_big = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
        k_sml = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k_big, iterations=3)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN,  k_sml, iterations=2)

        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        # Keep contours larger than a minimum board fraction
        min_area = (min_dim * 0.07) ** 2
        valid = [c for c in contours if cv2.contourArea(c) > min_area]
        if len(valid) < 2:   # need at least 2 coloured segments to be confident
            return None

        # Merge all valid contours and fit one ellipse
        all_pts = np.vstack(valid)
        if len(all_pts) < 5:
            return None
        try:
            (ex, ey), (ea, eb), angle = cv2.fitEllipse(all_pts)
        except cv2.error:
            return None

        # Reject wild aspect ratios (not a board)
        semi_a = max(ea, eb) / 2.0
        semi_b = min(ea, eb) / 2.0
        if semi_b / semi_a < 0.35:
            return None
        # Reject if too small or too large
        if semi_a / min_dim < 0.08 or semi_a / min_dim > 0.60:
            return None

        # Confidence: what fraction of the expected ring area was detected
        ring_area_est = np.pi * semi_a * semi_b * 0.30  # rings ≈ 30% of board area
        actual_area   = sum(cv2.contourArea(c) for c in valid)
        confidence    = float(min(actual_area / max(ring_area_est, 1), 1.0))

        # Ensure semi_a is really the major axis
        if ea < eb:
            angle = (angle + 90) % 180

        return DetectedBoard(
            cx_n=ex / w, cy_n=ey / h,
            a_n=semi_a / min_dim, b_n=semi_b / min_dim,
            angle_deg=angle, confidence=confidence, method="color"
        )

    def _detect_by_hough(self, frame, w, h, min_dim):
        """Hough Circle Transform fallback."""
        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        min_r = int(min_dim * 0.08)
        max_r = int(min_dim * 0.56)

        circles = None
        for dp, p1, p2 in [(1.0, 100, 35), (1.2, 70, 26), (1.5, 50, 18)]:
            circles = cv2.HoughCircles(
                blurred, cv2.HOUGH_GRADIENT,
                dp=dp, minDist=min_dim * 0.25,
                param1=p1, param2=p2,
                minRadius=min_r, maxRadius=max_r,
            )
            if circles is not None:
                break

        if circles is None:
            return None

        cx_c, cy_c = w / 2.0, h / 2.0
        best = min(circles[0], key=lambda c: (c[0]-cx_c)**2 + (c[1]-cy_c)**2)
        cx, cy, r = float(best[0]), float(best[1]), float(best[2])
        return DetectedBoard(
            cx_n=cx/w, cy_n=cy/h,
            a_n=r/min_dim, b_n=r/min_dim,
            angle_deg=0.0, confidence=0.45, method="hough"
        )

    # ── Dart detection ─────────────────────────────────────────

    def capture_reference(self):
        if not self.cap or not self.cap.isOpened():
            return False
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.reference_frame = cv2.GaussianBlur(gray, (21, 21), 0)
            with self._lock:
                self._dart_positions = []
                self._stable_count   = []
            return True
        return False

    def reset_darts(self):
        with self._lock:
            self._dart_positions = []
            self._stable_count   = []
        if self.reference_frame is None:
            self.capture_reference()

    def get_stable_dart_positions(self, frame):
        detected = self._detect_darts(frame)
        with self._lock:
            new_pos, new_cnt = [], []
            for dx, dy in detected:
                matched = False
                for i, (px, py) in enumerate(self._dart_positions):
                    if ((dx-px)**2 + (dy-py)**2)**0.5 < 0.03:
                        new_pos.append(((px+dx)/2, (py+dy)/2))
                        new_cnt.append(self._stable_count[i] + 1)
                        matched = True
                        break
                if not matched:
                    new_pos.append((dx, dy))
                    new_cnt.append(1)
            self._dart_positions = new_pos
            self._stable_count   = new_cnt
            return [p for p, c in zip(new_pos, new_cnt)
                    if c >= self.STABLE_THRESHOLD][:3]

    def _detect_darts(self, frame):
        if self.reference_frame is None:
            return []
        h, w = frame.shape[:2]
        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        diff    = cv2.absdiff(self.reference_frame, blurred)
        _, thr  = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        thr     = cv2.dilate(thr, None, iterations=2)
        cnts, _ = cv2.findContours(thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out = []
        for c in cnts:
            area = cv2.contourArea(c)
            if self.MIN_CONTOUR_AREA <= area <= self.MAX_CONTOUR_AREA:
                lowest = tuple(c[c[:, :, 1].argmax()][0])
                out.append((lowest[0]/w, lowest[1]/h))
        return out

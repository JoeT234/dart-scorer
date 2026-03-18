"""
Background subtraction dart detector.
Captures a reference frame (board without darts), then on each frame
finds new objects (darts) by diffing against the reference.
"""
import cv2
import numpy as np
import threading


class DartDetector:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.reference_frame = None
        self.running = False
        self._thread = None
        self._lock = threading.Lock()

        # callbacks
        self.on_frame = None          # called every frame with (frame, dart_coords_norm)
        self.on_dart_detected = None  # called when new dart confirmed

        # detection state
        self._dart_positions = []     # list of (x_norm, y_norm) in image plane
        self._stable_count = []       # how many consecutive frames each position was seen
        self.STABLE_THRESHOLD = 8     # frames before we call it confirmed
        self.MIN_CONTOUR_AREA = 80
        self.MAX_CONTOUR_AREA = 4000

    def open(self):
        # Try the requested index first, then fall back through 0-3
        indices_to_try = list(dict.fromkeys([self.camera_index, 0, 1, 2, 3]))
        for idx in indices_to_try:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                self.camera_index = idx
                self.cap = cap
                break
            cap.release()
        else:
            raise RuntimeError(
                "No webcam found. Make sure your camera is connected and not "
                "in use by another app, then restart."
            )
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def close(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self.cap:
            self.cap.release()
            self.cap = None

    def capture_reference(self):
        """Capture current frame as the reference (board with no darts)."""
        if not self.cap or not self.cap.isOpened():
            return False
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.reference_frame = cv2.GaussianBlur(gray, (21, 21), 0)
            with self._lock:
                self._dart_positions = []
                self._stable_count = []
            return True
        return False

    def reset_darts(self):
        """Reset dart state (after visitor commits their score)."""
        with self._lock:
            self._dart_positions = []
            self._stable_count = []
        if self.reference_frame is None:
            self.capture_reference()

    def read_frame(self):
        """Read a single frame and return (frame, detected_normalized_coords)."""
        if not self.cap or not self.cap.isOpened():
            return None, []
        ret, frame = self.cap.read()
        if not ret:
            return None, []
        coords = self._detect(frame)
        return frame, coords

    def _detect(self, frame):
        """Returns list of (x_norm, y_norm) for detected darts in this frame."""
        if self.reference_frame is None:
            return []

        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)

        diff = cv2.absdiff(self.reference_frame, blurred)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < self.MIN_CONTOUR_AREA or area > self.MAX_CONTOUR_AREA:
                continue
            # use the lowest point of the contour as dart tip (assumes dart enters from top)
            lowest = tuple(c[c[:, :, 1].argmax()][0])
            x_norm = lowest[0] / w
            y_norm = lowest[1] / h
            detected.append((x_norm, y_norm))

        return detected

    def get_stable_dart_positions(self, frame):
        """
        Update internal tracking and return only positions that have been
        stable for STABLE_THRESHOLD frames. Returns list of (x_norm, y_norm).
        """
        detected = self._detect(frame)
        h, w = frame.shape[:2]

        with self._lock:
            new_positions = []
            new_counts = []

            for dx, dy in detected:
                matched = False
                for i, (px, py) in enumerate(self._dart_positions):
                    dist = ((dx - px) ** 2 + (dy - py) ** 2) ** 0.5
                    if dist < 0.03:  # within 3% of frame size
                        # update with running average
                        new_positions.append(((px + dx) / 2, (py + dy) / 2))
                        new_counts.append(self._stable_count[i] + 1)
                        matched = True
                        break
                if not matched:
                    new_positions.append((dx, dy))
                    new_counts.append(1)

            self._dart_positions = new_positions
            self._stable_count = new_counts

            stable = [
                pos for pos, count in zip(self._dart_positions, self._stable_count)
                if count >= self.STABLE_THRESHOLD
            ]

        return stable[:3]  # max 3 darts per visit

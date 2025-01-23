# cv_close_eye_detect.py

import cv2
import time
import math

class EyeDetector:
    def __init__(self):
        """
        Initialize cascades, counters, and defaults.
        """
        self.face_cascade_path = "./haarcascade_frontalface_alt.xml"
        self.eye_cascade_path = "./haarcascade_eye_tree_eyeglasses.xml"
        self.face_cascade = cv2.CascadeClassifier(self.face_cascade_path)
        self.eye_cascade = cv2.CascadeClassifier(self.eye_cascade_path)

        # Internal state
        self.mode = None            # "setup_open", "setup_closed", "run", or None
        self.sensitivity = 0.5      # threshold ratio
        self.start_time = None
        self.frame_count = 0
        self.hit_count = 0
        self.active = False         # indicates we are in some detection mode

    def start_detection(self, mode, sensitivity=0.5):
        """
        Begin a new detection session (setup or run).
        Resets counters/timers and sets detection mode/sensitivity.
        """
        self.mode = mode
        self.sensitivity = float(sensitivity)
        self.start_time = time.time()
        self.frame_count = 0
        self.hit_count = 0
        self.active = True

    def stop_detection(self):
        """
        Cancel or stop any active detection session.
        """
        self.active = False
        self.mode = None

    def process_frame(self, frame):
        """
        If active, run detection logic on the given frame.
        Returns:
          - None if still running (not finished),
          - 1 if success condition (eyes open or closed ratio above threshold) was reached,
          - 0 if time window ended but ratio wasn't high enough (fail).
        
        For 'run' mode, we do the same 15-second rolling logic as before.
        For 'setup_open' or 'setup_closed', we do one 15-second measurement.
        """
        if not self.active:
            return None  # not in detection mode

        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        eyes_open = False

        if len(faces) > 0:
            for (x, y, w, h) in faces:
                face_roi = gray[y : y + h, x : x + w]
                eyes = self.eye_cascade.detectMultiScale(
                    face_roi,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                if len(eyes) > 0:
                    eyes_open = True
                    break  # if any face has eyes, we consider them open

        # Update counters
        self.frame_count += 1
        if eyes_open:
            # "open" frames for "setup_open" or "run"
            if self.mode in ("setup_open", "run"):
                self.hit_count += 1
        else:
            # "closed" frames for "setup_closed"
            if self.mode == "setup_closed":
                self.hit_count += 1

        # Check time elapsed
        elapsed = time.time() - self.start_time

        # *** We'll handle each mode's logic here. ***
        if self.mode == "run":
            # We do a repeating 15-second window check
            if elapsed > 15:
                ratio = self.hit_count / float(self.frame_count) if self.frame_count else 0
                if ratio > self.sensitivity:
                    # success -> eyes open
                    self.stop_detection()  # stop
                    return 1
                else:
                    # reset counters and time
                    self.hit_count = 0
                    self.frame_count = 0
                    self.start_time = time.time()
            return None  # still running

        elif self.mode in ("setup_open", "setup_closed"):
            # A single 15-second measurement
            if elapsed > 15:
                ratio = self.hit_count / float(self.frame_count) if self.frame_count else 0
                self.stop_detection()
                if ratio > 0.8:
                    return 1  # success
                else:
                    return 0  # fail
            return None  # still measuring

        return None

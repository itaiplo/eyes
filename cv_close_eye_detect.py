# cv_close_eye_detect.py

import cv2
import time

class EyeDetector:
    def __init__(self):
        # Paths to Haar cascades
        self.face_cascade_path = "./haarcascade_frontalface_alt.xml"
        self.eye_cascade_path = "./haarcascade_eye_tree_eyeglasses.xml"

        self.face_cascade = cv2.CascadeClassifier(self.face_cascade_path)
        self.eye_cascade = cv2.CascadeClassifier(self.eye_cascade_path)

        # Internal state
        self.mode = None           # "setup_open", "setup_closed", "run"
        self.sensitivity = 0.5
        self.start_time = None
        self.frame_count = 0
        self.hit_count = 0
        self.active = False

    def start_detection(self, mode, sensitivity=0.5):
        """
        Begin a new detection session (setup or run).
        """
        self.mode = mode
        self.sensitivity = float(sensitivity)
        self.start_time = time.time()
        self.frame_count = 0
        self.hit_count = 0
        self.active = True
        print(f"[EyeDetector] Starting {mode} mode with sensitivity={self.sensitivity}")

    def stop_detection(self):
        """Stop any active detection session."""
        self.active = False
        self.mode = None

    def process_frame(self, frame):
        """
        Process a single frame.

        Returns a tuple (status, old_mode, out_frame):
          - status: None if still running, 1 if success, 0 if fail
          - old_mode: the mode in which we ended (so GUI can display correct message)
          - out_frame: same frame with green rectangle if face is detected

        For run mode:
          - 15-second rolling window. If ratio > sensitivity => success => return (1, "run", frame)
          - else reset counters.

        For setup_open or setup_closed:
          - Single 15-second window. If ratio > 0.8 => (1, mode, frame), else (0, mode, frame).
        """
        # We always return the same frame with or without a rectangle drawn.
        out_frame = frame

        if not self.active:
            # Not in detection mode; just return the frame unmodified
            return (None, None, out_frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        eyes_open = False
        if len(faces) == 0:
            print("[EyeDetector] No face detected")
        else:
            for (x, y, w, h) in faces:
                # Draw a green rectangle around the face
                cv2.rectangle(out_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Focus on the face region
                face_roi = gray[y : y + h, x : x + w]
                eyes = self.eye_cascade.detectMultiScale(
                    face_roi,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                if len(eyes) > 0:
                    print("[EyeDetector] Eyes are OPEN")
                    eyes_open = True
                    break
                else:
                    print("[EyeDetector] Eyes are CLOSED")

        self.frame_count += 1

        # If eyes_open => increment hit_count in setup_open/run
        # If eyes_closed => increment hit_count in setup_closed
        if eyes_open and self.mode in ("setup_open", "run"):
            self.hit_count += 1
        elif (not eyes_open) and (len(faces) > 0) and (self.mode == "setup_closed"):
            # Only increment closed if at least one face is found
            self.hit_count += 1

        elapsed = time.time() - self.start_time

        # -- Decide if we finished --
        if self.mode == "run":
            # Rolling 15-second window
            if elapsed > 15:
                ratio = self.hit_count / float(self.frame_count) if self.frame_count else 0
                if ratio > self.sensitivity:
                    old_mode = self.mode
                    self.stop_detection()
                    print(f"[EyeDetector] run success => ratio={ratio:.2f}")
                    return (1, old_mode, out_frame)
                else:
                    # reset counters/time
                    print(f"[EyeDetector] run reset => ratio={ratio:.2f} < {self.sensitivity}")
                    self.hit_count = 0
                    self.frame_count = 0
                    self.start_time = time.time()

            # still running
            return (None, None, out_frame)

        elif self.mode in ("setup_open", "setup_closed"):
            # Single 15-second measurement
            if elapsed > 15:
                ratio = self.hit_count / float(self.frame_count) if self.frame_count else 0
                old_mode = self.mode
                self.stop_detection()
                if ratio > 0.8:
                    print(f"[EyeDetector] {old_mode} SUCCESS => ratio={ratio:.2f}")
                    return (1, old_mode, out_frame)
                else:
                    print(f"[EyeDetector] {old_mode} FAIL => ratio={ratio:.2f}")
                    return (0, old_mode, out_frame)
            # still measuring
            return (None, None, out_frame)

        # If none of the above, keep going
        return (None, None, out_frame)

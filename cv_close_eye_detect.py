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
          - old_mode: the mode in which we ended
          - out_frame: same frame with green rectangle if a face is detected

        In run mode:
          - We treat "no face" or "eyes open" as a "hit".
          - Rolling 15-second window. If ratio > sensitivity => success => return (1, "run", frame).
            Otherwise, reset counters each 15s.

        In setup_open or setup_closed:
          - Single 15-second measurement.
          - If ratio > 0.8 => success => return (1, mode, frame).
          - Else => fail => return (0, mode, frame).
        """
        out_frame = frame.copy()  # So we can draw bounding boxes if needed

        if not self.active:
            # Not in detection mode; just return the frame unmodified
            return (None, None, out_frame)

        gray = cv2.cvtColor(out_frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        # We'll figure out if "eyes_open" or "no_face" later
        eyes_open = False
        no_face = False

        if len(faces) == 0:
            print("[EyeDetector] No face detected")
            no_face = True
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

        # --- Update counters based on mode ---
        if self.mode == "run":
            # For run mode, "hit" if eyes_open OR no_face
            if eyes_open or no_face:
                self.hit_count += 1

        elif self.mode == "setup_open":
            # If eyes_open => increment
            if eyes_open:
                self.hit_count += 1

        elif self.mode == "setup_closed":
            # If face is found but no eyes => increment
            # (We do not consider "no face" as closed)
            if len(faces) > 0 and not eyes_open:
                self.hit_count += 1

        elapsed = time.time() - self.start_time

        # ------------- RUN MODE LOGIC -------------
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

        # ------------- SETUP MODE LOGIC -------------
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

        return (None, None, out_frame)

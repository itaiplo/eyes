import cv2
import time

class EyeDetector:
    def __init__(self):
        # Paths to Haar cascades
        self.face_cascade_path = "./haarcascade_frontalface_alt.xml"
        self.eye_cascade_path = "./haarcascade_eye_tree_eyeglasses.xml"

        self.face_cascade = cv2.CascadeClassifier(self.face_cascade_path)
        self.eye_cascade = cv2.CascadeClassifier(self.eye_cascade_path)

        self.mode = None
        self.active = False

        # For setup_open / setup_closed
        self.start_time = 0
        self.frame_count = 0
        self.hit_count = 0

        # For run mode (15-second blocks, FIFO array)
        self.block_start_time = 0
        self.block_frame_count = 0
        self.block_hit_count = 0
        self.run_results = [0]*20
        self.block_index = 0
        self.awake_time = 30  # user-chosen

    def start_detection(self, mode, awake_time=30):
        """
        mode can be "setup_open", "setup_closed", or "run".
        For run mode, we do the 15s block logic and track success/fail in a FIFO array of length 20.
        'awake_time' in seconds (30..300).
        """
        self.mode = mode
        self.active = True

        # Reset counters
        self.start_time = time.time()
        self.frame_count = 0
        self.hit_count = 0

        if mode == "run":
            self.awake_time = awake_time
            self.run_results = [0]*20
            self.block_index = 0
            self.block_start_time = time.time()
            self.block_frame_count = 0
            self.block_hit_count = 0

        print(f"[EyeDetector] Starting '{mode}' with awake_time={awake_time}")

    def stop_detection(self):
        """
        Stop any active detection session and reset everything.
        """
        self.active = False
        self.mode = None

        # Reset run-related
        self.run_results = [0]*20
        self.block_index = 0
        self.block_start_time = 0
        self.block_frame_count = 0
        self.block_hit_count = 0

        # Reset setup counters
        self.start_time = 0
        self.frame_count = 0
        self.hit_count = 0

    def process_frame(self, frame):
        """
        Called each frame from the GUI to do detection.

        Returns: (status, old_mode, out_frame)
          - status = None => still running
          - status = 0 => fail (setup modes)
          - status = 1 => success (setup modes)
          - status = 2 => "awake threshold" event => play the song (run mode)

          old_mode => "setup_open", "setup_closed", or "run"
          out_frame => frame with green bounding box if face detected
        """
        out_frame = frame.copy()
        if not self.active:
            # Not in detection mode
            return (None, None, out_frame)

        # Convert to grayscale
        gray = cv2.cvtColor(out_frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        eyes_open = False
        no_face = False

        if len(faces) == 0:
            print("[EyeDetector] No face detected")
            no_face = True
        else:
            for (x, y, w, h) in faces:
                cv2.rectangle(out_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                face_roi = gray[y:y+h, x:x+w]
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

        # -------- Setup Modes -----------
        if self.mode in ("setup_open", "setup_closed"):
            self.frame_count += 1
            if self.mode == "setup_open":
                # Count eyes_open
                if eyes_open:
                    self.hit_count += 1
            elif self.mode == "setup_closed":
                # Count closed only if a face is found but no eyes
                if len(faces) > 0 and not eyes_open:
                    self.hit_count += 1

            elapsed = time.time() - self.start_time
            if elapsed > 15:
                # Check ratio > 0.8 for success
                ratio = self.hit_count / float(self.frame_count) if self.frame_count else 0
                old_mode = self.mode
                self.stop_detection()
                if ratio > 0.8:
                    print(f"[EyeDetector] {old_mode} SUCCESS => ratio={ratio:.2f}")
                    return (1, old_mode, out_frame)
                else:
                    print(f"[EyeDetector] {old_mode} FAIL => ratio={ratio:.2f}")
                    return (0, old_mode, out_frame)

            return (None, None, out_frame)

        # -------- Run Mode (15-second blocks) -----------
        if self.mode == "run":
            self.block_frame_count += 1
            # "hit" if eyes_open OR no_face
            if eyes_open or no_face:
                self.block_hit_count += 1

            block_elapsed = time.time() - self.block_start_time
            if block_elapsed > 15:
                # Evaluate success if ratio > 0.65
                ratio = 0.0
                if self.block_frame_count > 0:
                    ratio = self.block_hit_count / float(self.block_frame_count)

                success_val = 1 if (ratio > 0.65) else 0

                idx = self.block_index % 20
                self.run_results[idx] = success_val
                self.block_index += 1

                # Reset for next block
                self.block_hit_count = 0
                self.block_frame_count = 0
                self.block_start_time = time.time()

                total_success = sum(self.run_results)
                threshold_blocks = self.awake_time / 15.0
                print(f"[EyeDetector] run block => block_ratio={ratio:.2f}, success={success_val}, sum={total_success}")

                # If total_success >= threshold_blocks => return code=2 => play the song
                if total_success >= threshold_blocks:
                    return (2, "run", out_frame)

            return (None, None, out_frame)

        # default
        return (None, None, out_frame)

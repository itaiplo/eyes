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
        self.mode = None  # "setup_open", "setup_closed", or "run"
        self.active = False

        # --- For setup_open/setup_closed ---
        self.start_time = 0
        self.frame_count = 0
        self.hit_count = 0

        # --- For run mode (discrete blocks) ---
        self.block_start_time = 0     # start time for current 15s block
        self.block_frame_count = 0
        self.block_hit_count = 0

        self.run_results = [0]*20     # FIFO array of length 20
        self.block_index = 0          # which slot we’re writing
        self.awake_time = 30          # user-chosen param (30..300)
        # The threshold = awake_time/15. If sum(run_results) > threshold => play song

    def start_detection(self, mode, awake_time=30):
        """
        Begin a detection session.
        For 'setup_open' or 'setup_closed', we do the old 15-second window logic.
        For 'run', we do indefinite 15-second blocks, storing success/fail in run_results.
        """
        self.mode = mode
        self.active = True

        # Reset counters
        self.start_time = time.time()
        self.frame_count = 0
        self.hit_count = 0

        # If run mode, also reset block logic
        if mode == "run":
            self.awake_time = awake_time
            self.run_results = [0]*20
            self.block_index = 0
            self.block_start_time = time.time()
            self.block_frame_count = 0
            self.block_hit_count = 0

        print(f"[EyeDetector] Starting '{mode}' with awake_time={awake_time}")

    def stop_detection(self):
        """Stop any active detection session (resets everything)."""
        self.active = False
        self.mode = None

        # Also reset run-related counters if needed
        self.run_results = [0]*20
        self.block_index = 0
        self.block_start_time = 0
        self.block_frame_count = 0
        self.block_hit_count = 0

        self.start_time = 0
        self.frame_count = 0
        self.hit_count = 0

    def process_frame(self, frame):
        """
        Called each frame from the GUI.
        
        Returns: (status, old_mode, out_frame)
          - status = None => still ongoing
          - status = 0 => fail (only relevant for setup modes)
          - status = 1 => success (only relevant for setup modes)
          - status = 2 => "Awake threshold" event (run mode) => play the song
          
          old_mode => "setup_open", "setup_closed", or "run"
          out_frame => frame with face bounding box if face detected
          
        For 'setup_open' or 'setup_closed', same old logic: single 15s window => success/fail => exit.
        For 'run', indefinite 15s blocks => store 1 if success, else 0 in run_results => 
                if sum(run_results) > (awake_time/15), return code=2 => triggers the song.
        """
        out_frame = frame.copy()  # so we can draw bounding boxes

        if not self.active:
            # Not detecting
            return (None, None, out_frame)

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
                # draw green rectangle
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

        # ---------- SETUP MODES ----------
        if self.mode in ("setup_open", "setup_closed"):
            self.frame_count += 1

            if self.mode == "setup_open":
                # If eyes_open => increment
                if eyes_open:
                    self.hit_count += 1
            elif self.mode == "setup_closed":
                # If face found but eyes not open => increment
                if len(faces) > 0 and not eyes_open:
                    self.hit_count += 1

            elapsed = time.time() - self.start_time
            if elapsed > 15:
                ratio = (self.hit_count / float(self.frame_count)) if self.frame_count else 0
                old_mode = self.mode
                self.stop_detection()
                if ratio > 0.8:
                    print(f"[EyeDetector] {old_mode} SUCCESS => ratio={ratio:.2f}")
                    return (1, old_mode, out_frame)
                else:
                    print(f"[EyeDetector] {old_mode} FAIL => ratio={ratio:.2f}")
                    return (0, old_mode, out_frame)

            return (None, None, out_frame)

        # ---------- RUN MODE ----------
        if self.mode == "run":
            # 1) Update block counters
            self.block_frame_count += 1

            # "hit" if eyes_open or no_face
            if eyes_open or no_face:
                self.block_hit_count += 1

            # Check if 15s block ended
            block_elapsed = time.time() - self.block_start_time
            if block_elapsed > 15:
                # Evaluate block success (if block_hit_count>0 => success=1)
                # (Alternatively, you could do ratio>0 to decide success. 
                #  But for simplicity, let's say "any hits => success=1".)
                if self.block_hit_count > 0:
                    success_val = 1
                else:
                    success_val = 0

                # Write to FIFO array
                idx = self.block_index % 20
                self.run_results[idx] = success_val
                self.block_index += 1

                # Reset for next block
                self.block_hit_count = 0
                self.block_frame_count = 0
                self.block_start_time = time.time()

                # Check sum of run_results
                total_success = sum(self.run_results)
                threshold_blocks = self.awake_time / 15.0
                print(f"[EyeDetector] run block ended => success={success_val}, sum={total_success}")

                # If sum > threshold_blocks => return code=2 => GUI plays song
                if total_success > threshold_blocks:
                    # We'll return a special code=2 => meaning "Play Song"
                    return (2, "run", out_frame)

            # If still within the block, or block ended but sum <= threshold => keep going
            return (None, None, out_frame)

        return (None, None, out_frame)

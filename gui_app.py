# gui_app.py

import customtkinter as ctk
import threading
import cv2
import pygame
import os

import top_cv  # Your refactored top_cv.py from before

class EyeDetectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Eye Detection GUI")
        self.geometry("500x500")

        # 1) Initialize Pygame mixer
        pygame.mixer.init()

        # 2) Create UI elements
        self.label_info = ctk.CTkLabel(self, text="Eye Detection Setup", font=("Arial", 16))
        self.label_info.pack(pady=10)

        # Button to open camera preview
        self.button_camera = ctk.CTkButton(self, text="Open Camera Preview", command=self.open_camera_preview)
        self.button_camera.pack(pady=5)

        # Buttons for setup
        self.button_setup_open = ctk.CTkButton(self, text="Setup Open Eyes", command=self.setup_open_handler)
        self.button_setup_open.pack(pady=5)

        self.button_setup_closed = ctk.CTkButton(self, text="Setup Closed Eyes", command=self.setup_closed_handler)
        self.button_setup_closed.pack(pady=5)

        # Entries for sensitivity & sleep time
        self.entry_sensitivity = ctk.CTkEntry(self, placeholder_text="Sensitivity (e.g. 0.5)")
        self.entry_sensitivity.pack(pady=5)

        self.entry_sleep_time = ctk.CTkEntry(self, placeholder_text="Sleep time (seconds)")
        self.entry_sleep_time.pack(pady=5)

        # Button to run process
        self.button_run = ctk.CTkButton(self, text="Run Process", command=self.run_process_handler)
        self.button_run.pack(pady=5)

        # Stop/Reset button
        self.button_stop = ctk.CTkButton(self, text="Stop/Reset", command=self.stop_handler)
        self.button_stop.pack(pady=5)

        # Status label
        self.label_status = ctk.CTkLabel(self, text="Status: Waiting...", font=("Arial", 14))
        self.label_status.pack(pady=10)

        # Thread references
        self.process_thread = None
        self.running = False  # Flag to control thread

    def open_camera_preview(self):
        """
        Opens the camera in a blocking loop using OpenCV.
        The user must press 'q' in the OpenCV window to close it.
        """
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.label_status.configure(text="Error: Cannot open camera.")
            return

        self.label_status.configure(text="Camera preview opened. Press 'q' to close.")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow("Camera Preview (press 'q' to close)", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        self.label_status.configure(text="Camera preview closed.")

    def setup_open_handler(self):
        """Call setup_open_eyes from top_cv and update status label."""
        success = top_cv.setup_open_eyes()
        if success:
            self.label_status.configure(text="Setup Open Eyes: SUCCESS!")
        else:
            self.label_status.configure(text="Setup Open Eyes: FAILED. Try again.")

    def setup_closed_handler(self):
        """Call setup_closed_eyes from top_cv and update status label."""
        success = top_cv.setup_closed_eyes()
        if success:
            self.label_status.configure(text="Setup Closed Eyes: SUCCESS!")
        else:
            self.label_status.configure(text="Setup Closed Eyes: FAILED. Try again.")

    def run_process_handler(self):
        """Start the detection process in a separate thread."""
        sensitivity = self.entry_sensitivity.get()
        sleep_time = self.entry_sleep_time.get()

        # Basic validation
        if not sensitivity or not sleep_time:
            self.label_status.configure(text="Enter sensitivity & sleep time!")
            return

        # Create a background thread so GUI remains responsive
        self.running = True
        self.process_thread = threading.Thread(
            target=self.run_process_in_thread,
            args=(sensitivity, sleep_time),
            daemon=True
        )
        self.process_thread.start()
        self.label_status.configure(text="Process started in background...")

    def run_process_in_thread(self, sensitivity, sleep_time):
        """
        Runs the eye detection process in a background thread.
        If eyes are detected as open, we play the MP3 file using pygame.
        """
        def on_eyes_open_callback():
            self.label_status.configure(text="Eyes detected as open!")
            self.play_song()

        ret = top_cv.run_process(sensitivity, sleep_time, on_eyes_open=on_eyes_open_callback)

        # Once the process finishes, update status
        if self.running:
            self.label_status.configure(text=f"Process finished with return={ret}")

    def play_song(self):
        """
        Plays the song.mp3 file in a non-blocking way using pygame.
        """
        # If you want to ensure the file is found, build an absolute path
        # or confirm the file is in the same folder.
        # For example:
        # script_dir = os.path.dirname(os.path.abspath(__file__))
        # mp3_path = os.path.join(script_dir, "song.mp3")

        mp3_path = "song.mp3"  # Or absolute path
        try:
            # Stop any currently playing music first (optional)
            pygame.mixer.music.stop()

            pygame.mixer.music.load(mp3_path)
            pygame.mixer.music.play()
        except pygame.error as e:
            print(f"Error playing {mp3_path}: {e}")

    def stop_handler(self):
        """
        Attempts to stop the detection process.
        If you have a special mechanism in cv_close_eye_detect to break the loop, call it here.
        """
        self.label_status.configure(text="Stop requested...")
        self.running = False

        # If you want to stop the music as well:
        pygame.mixer.music.stop()
        # If you have custom logic in cv_close_eye_detect.py to forcibly break loops, call it:
        # cv_close_eye_detect.stop_detection()  # Hypothetical method

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = EyeDetectionApp()
    app.mainloop()

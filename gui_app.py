import customtkinter as ctk
import threading
import cv2
import time
import pygame
import os
from PIL import Image, ImageTk

from cv_close_eye_detect import EyeDetector

class EyeDetectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Unified Camera & Detection with Song Playback")
        self.geometry("900x600")

        # --------------- Initialize Pygame for MP3 Playback --------------- #
        pygame.mixer.init()

        # --------------- State Variables --------------- #
        self.running_preview = True
        self.detection_active = False
        self.sensitivity_value = 0.5
        self.sleep_value = 0

        # We'll create a single EyeDetector instance
        self.eye_detector = EyeDetector()

        # --------------- Layout --------------- #
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Camera Preview label (left side)
        self.camera_label = ctk.CTkLabel(self, text="")
        self.camera_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Controls frame (right side)
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Sensitivity slider
        self.sensitivity_label = ctk.CTkLabel(self.controls_frame, text="Sensitivity (0.5 - 1.0)")
        self.sensitivity_label.pack(pady=(10, 0))

        self.sensitivity_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0.5,
            to=1.0,
            number_of_steps=5,  # steps of 0.1
            command=self.on_sensitivity_change
        )
        self.sensitivity_slider.set(0.5)
        self.sensitivity_slider.pack(pady=(0,5))

        self.sensitivity_value_label = ctk.CTkLabel(self.controls_frame, text="0.5")
        self.sensitivity_value_label.pack(pady=(0,10))

        # Sleep Time slider (0..900 in steps of 60)
        self.sleep_label = ctk.CTkLabel(self.controls_frame, text="Sleep Time (0 - 900s, step 60)")
        self.sleep_label.pack(pady=(10,0))

        self.sleep_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0,
            to=900,
            number_of_steps=15,  # 0..900/60 => 15 steps
            command=self.on_sleep_change
        )
        self.sleep_slider.set(0)
        self.sleep_slider.pack(pady=(0,5))

        self.sleep_value_label = ctk.CTkLabel(self.controls_frame, text="0 sec")
        self.sleep_value_label.pack(pady=(0,10))

        # Buttons
        self.button_setup_open = ctk.CTkButton(
            self.controls_frame, text="Setup Open Eyes", command=self.setup_open_handler
        )
        self.button_setup_open.pack(pady=5)

        self.button_setup_closed = ctk.CTkButton(
            self.controls_frame, text="Setup Closed Eyes", command=self.setup_closed_handler
        )
        self.button_setup_closed.pack(pady=5)

        self.button_run = ctk.CTkButton(
            self.controls_frame, text="Run Process", command=self.run_process_handler
        )
        self.button_run.pack(pady=5)

        self.button_stop = ctk.CTkButton(
            self.controls_frame, text="Stop/Reset", command=self.stop_handler
        )
        self.button_stop.pack(pady=5)

        self.label_status = ctk.CTkLabel(self.controls_frame, text="Status: Waiting...")
        self.label_status.pack(pady=10)

        # --------------- Open ONE Camera --------------- #
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.label_status.configure(text="Error: Cannot open camera.")
        else:
            self.label_status.configure(text="Camera opened. Ready.")

        # --------------- Start Preview Loop --------------- #
        self.update_preview()

    # ------------------- Slider Callbacks ------------------- #
    def on_sensitivity_change(self, val):
        new_val = round(val, 1)
        self.sensitivity_value = new_val
        self.sensitivity_value_label.configure(text=str(new_val))

    def on_sleep_change(self, val):
        step = 60
        new_val = int(round(val / step) * step)
        self.sleep_slider.set(new_val)
        self.sleep_value = new_val
        self.sleep_value_label.configure(text=f"{new_val} sec")

    # ------------------- Detection Actions ------------------- #
    def setup_open_handler(self):
        self.label_status.configure(text="Setup Open Eyes scheduled...")
        self.detection_active = True

        if self.sleep_value > 0:
            # Sleep in a background thread, then start detection
            threading.Thread(target=self.delayed_start, args=("setup_open",), daemon=True).start()
        else:
            self.do_setup_open()

    def do_setup_open(self):
        self.label_status.configure(text="Setting up Open Eyes (15s)...")
        self.eye_detector.start_detection("setup_open", self.sensitivity_value)

    def setup_closed_handler(self):
        self.label_status.configure(text="Setup Closed Eyes scheduled...")
        self.detection_active = True

        if self.sleep_value > 0:
            threading.Thread(target=self.delayed_start, args=("setup_closed",), daemon=True).start()
        else:
            self.do_setup_closed()

    def do_setup_closed(self):
        self.label_status.configure(text="Setting up Closed Eyes (15s)...")
        self.eye_detector.start_detection("setup_closed", self.sensitivity_value)

    def run_process_handler(self):
        self.label_status.configure(text="Run Process scheduled...")
        self.detection_active = True

        if self.sleep_value > 0:
            threading.Thread(target=self.delayed_start, args=("run",), daemon=True).start()
        else:
            self.do_run()

    def do_run(self):
        self.label_status.configure(text="Running detection (15s rolling window)...")
        self.eye_detector.start_detection("run", self.sensitivity_value)

    def delayed_start(self, mode_str):
        """ Wait for self.sleep_value seconds, then call the appropriate start function. """
        time.sleep(self.sleep_value)
        if mode_str == "setup_open":
            self.do_setup_open()
        elif mode_str == "setup_closed":
            self.do_setup_closed()
        elif mode_str == "run":
            self.do_run()

    def stop_handler(self):
        """Stop/Reset detection and stop the song."""
        self.label_status.configure(text="Stop/Reset requested...")
        self.detection_active = False
        self.eye_detector.stop_detection()
        # Also stop any music
        pygame.mixer.music.stop()

    # ------------------- Preview + Detection Loop ------------------- #
    def update_preview(self):
        """
        - Grabs a frame from self.cap
        - Mirror it horizontally
        - If detection is active, pass frame to eye_detector
        - Show the returned frame in the GUI
        - If detection finishes => handle success/fail
        - Repeats every ~30ms
        """
        if self.running_preview and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # 1) Mirror the frame horizontally
                frame = cv2.flip(frame, 1)

                status = None
                old_mode = None
                processed_frame = frame

                if self.detection_active:
                    # process_frame returns (status, old_mode, out_frame)
                    result = self.eye_detector.process_frame(frame)
                    if result is not None:
                        status, old_mode, processed_frame = result
                    else:
                        status, old_mode, processed_frame = (None, None, frame)
                else:
                    # Not detecting => just show normal mirrored frame
                    processed_frame = frame

                # Show the processed_frame in the GUI
                frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                pil_img = pil_img.resize((500, 400), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_img, size=(500, 400))
                self.camera_label.configure(image=ctk_img)
                self.camera_label.image = ctk_img

                # If detection finished
                if status is not None:
                    # status=1 => success, 0 => fail
                    self.detection_active = False
                    if status == 1:
                        # success
                        if old_mode == "run":
                            # Eyes open success => play the song
                            self.label_status.configure(text="Eyes detected as open! (RUN SUCCESS)")
                            self.play_song()
                        else:
                            # setup success
                            if old_mode is not None:
                                self.label_status.configure(text=f"{old_mode} SUCCESS!")
                    else:
                        # fail
                        if old_mode in ("setup_open", "setup_closed"):
                            self.label_status.configure(text=f"{old_mode} FAILED.")
                        elif old_mode == "run":
                            self.label_status.configure(text="Run: ratio too low => no success yet.")

        # schedule next
        self.after(30, self.update_preview)

    # ------------------- Song Playback ------------------- #
    def play_song(self):
        """
        Play 'song.mp3' once using pygame.
        """
        try:
            pygame.mixer.music.stop()  # stop if something else is playing
            mp3_path = "song.mp3"  # or absolute path
            pygame.mixer.music.load(mp3_path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing {mp3_path}: {e}")

    # ------------------- Window Close ------------------- #
    def on_closing(self):
        self.running_preview = False
        if self.cap.isOpened():
            self.cap.release()
        pygame.mixer.quit()  # optional: cleanly shut down audio
        self.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = EyeDetectionApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

import customtkinter as ctk
import threading
import cv2
import time
import pygame
import os
import random  # for placeholder audio level
import asyncio
from bleak import BleakScanner
import comtypes
from ctypes import cast, POINTER
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# For CLSCTX_ALL:
from comtypes import CLSCTX_ALL

from PIL import Image, ImageTk

from cv_close_eye_detect import EyeDetector

class EyeDetectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Unified Detection (Block Logic + Mirror + Bluetooth + AudioLevel)")
        self.geometry("1000x600")

        pygame.mixer.init()

        self.running_preview = True
        self.detection_active = False
        self.awake_time_value = 30
        self.sleep_value = 0

        self.eye_detector = EyeDetector()

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Camera Preview
        self.camera_label = ctk.CTkLabel(self, text="")
        self.camera_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Controls
        self.controls_frame = ctk.CTkFrame(self, width=300)
        self.controls_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Awake Time slider
        self.awake_label = ctk.CTkLabel(self.controls_frame, text="Awake Time (30..300, step=30)")
        self.awake_label.pack(pady=(10,0))

        self.awake_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=30,
            to=300,
            number_of_steps=9,
            command=self.on_awake_change
        )
        self.awake_slider.set(30)
        self.awake_slider.pack(pady=(0,5))

        self.awake_value_label = ctk.CTkLabel(self.controls_frame, text="30 sec")
        self.awake_value_label.pack(pady=(0,10))

        # Sleep Time slider
        self.sleep_label = ctk.CTkLabel(self.controls_frame, text="Sleep Time (0..900, step=60)")
        self.sleep_label.pack(pady=(10,0))

        self.sleep_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0,
            to=900,
            number_of_steps=15,
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

        # Bluetooth device indicator
        self.bluetooth_label = ctk.CTkLabel(self.controls_frame, text="Bluetooth: Checking...")
        self.bluetooth_label.pack(pady=10)

        # Audio level indicator
        self.audio_level_label = ctk.CTkLabel(self.controls_frame, text="Audio Level: 0")
        self.audio_level_label.pack(pady=10)

        # Open camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.label_status.configure(text="Error: Cannot open camera.")
        else:
            self.label_status.configure(text="Camera opened. Ready.")

        self.update_preview()

        # Periodically check bluetooth and audio levels
        self.update_bluetooth_and_audio()

    # -----------------------------------------
    # Slider callbacks
    # -----------------------------------------
    def on_awake_change(self, val):
        step = 30
        new_val = int(round(val / step) * step)
        self.awake_slider.set(new_val)
        self.awake_time_value = new_val
        self.awake_value_label.configure(text=f"{new_val} sec")

    def on_sleep_change(self, val):
        step = 60
        new_val = int(round(val / step) * step)
        self.sleep_slider.set(new_val)
        self.sleep_value_label.configure(text=f"{new_val} sec")
        self.sleep_value = new_val

    # -----------------------------------------
    # Setup handlers
    # -----------------------------------------
    def setup_open_handler(self):
        self.label_status.configure(text="Setup Open Eyes scheduled...")
        self.detection_active = True
        if self.sleep_value > 0:
            threading.Thread(target=self.delayed_start, args=("setup_open",), daemon=True).start()
        else:
            self.do_setup_open()

    def do_setup_open(self):
        self.label_status.configure(text="Setting up Open Eyes (15s)...")
        self.eye_detector.start_detection("setup_open", awake_time=0)

    def setup_closed_handler(self):
        self.label_status.configure(text="Setup Closed Eyes scheduled...")
        self.detection_active = True
        if self.sleep_value > 0:
            threading.Thread(target=self.delayed_start, args=("setup_closed",), daemon=True).start()
        else:
            self.do_setup_closed()

    def do_setup_closed(self):
        self.label_status.configure(text="Setting up Closed Eyes (15s)...")
        self.eye_detector.start_detection("setup_closed", awake_time=0)

    # -----------------------------------------
    # Run mode (block-based logic)
    # -----------------------------------------
    def run_process_handler(self):
        self.label_status.configure(text="Run Process scheduled...")
        self.detection_active = True
        if self.sleep_value > 0:
            threading.Thread(target=self.delayed_start, args=("run",), daemon=True).start()
        else:
            self.do_run()

    def do_run(self):
        self.label_status.configure(text="Running detection (15s blocks) ...")
        self.eye_detector.start_detection("run", awake_time=self.awake_time_value)

    def delayed_start(self, mode_str):
        time.sleep(self.sleep_value)
        if mode_str == "setup_open":
            self.do_setup_open()
        elif mode_str == "setup_closed":
            self.do_setup_closed()
        elif mode_str == "run":
            self.do_run()

    # -----------------------------------------
    # Stop/reset
    # -----------------------------------------
    def stop_handler(self):
        self.label_status.configure(text="Stop/Reset requested...")
        self.detection_active = False
        self.eye_detector.stop_detection()
        pygame.mixer.music.stop()

    # -----------------------------------------
    # Main preview loop
    # -----------------------------------------
    def update_preview(self):
        if self.running_preview and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Mirror the camera
                frame = cv2.flip(frame, 1)

                if self.detection_active:
                    status, old_mode, processed_frame = self.eye_detector.process_frame(frame)
                else:
                    status, old_mode, processed_frame = (None, None, frame)

                # Display
                frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb).resize((500, 400), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_img, size=(500, 400))
                self.camera_label.configure(image=ctk_img)
                self.camera_label.image = ctk_img

                # Check result
                if status is not None:
                    if old_mode in ("setup_open", "setup_closed"):
                        self.detection_active = False
                        if status == 1:
                            self.label_status.configure(text=f"{old_mode} SUCCESS!")
                        else:
                            self.label_status.configure(text=f"{old_mode} FAILED.")
                    elif old_mode == "run":
                        if status == 2:
                            self.label_status.configure(text="Run => sum >= threshold => playing song!")
                            self.play_song()

        self.after(30, self.update_preview)

    # -----------------------------------------
    # Song playback
    # -----------------------------------------
    def play_song(self):
        try:
            pygame.mixer.music.stop()
            mp3_path = "song.mp3"
            pygame.mixer.music.load(mp3_path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing {mp3_path}: {e}")

    # -----------------------------------------
    # Bluetooth & Audio-level updates
    # -----------------------------------------
    def update_bluetooth_and_audio(self):
        """
        Called periodically to update:
          - Which bluetooth device is connected (placeholder)
          - The audio level (placeholder)
        """
        # 1) Check Bluetooth
        device_name = self.check_bluetooth_device()
        if device_name:
            self.bluetooth_label.configure(text=f"Bluetooth Device: {device_name}")
        else:
            self.bluetooth_label.configure(text="Bluetooth Device: None")

        # 2) Update audio level (placeholder)
        level = self.get_audio_level()
        self.audio_level_label.configure(text=f"Audio Level: {level}")

        # Schedule this method to run again in 2000 ms
        self.after(2000, self.update_bluetooth_and_audio)

    def check_bluetooth_device(self):
        """
        Scans for BLE (Bluetooth Low Energy) devices for 5 seconds on Windows 64-bit (and other platforms).
        Returns the name of the first discovered device, or None if none found.

        NOTE:
        - Only detects BLE devices, not 'classic' Bluetooth.
        - If your device is classic Bluetooth, this won't find it.
        """
        try:
            devices = asyncio.run(BleakScanner.discover(timeout=5.0))
            if devices:
                # Return the name of the first device discovered
                return devices[0].name or "Unnamed BLE Device"
            else:
                return None
        except Exception as e:
            print(f"Bleak scanning error: {e}")
            return None

    def get_audio_level(self):
        """
        Returns the master volume level scalar (0..100) for the default audio endpoint
        using PyCaw. If something goes wrong, returns None.
        """
        try:
            # Get default audio playback device
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            )
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            # volume.GetMasterVolumeLevelScalar() => float in [0.0, 1.0]
            level_scalar = volume.GetMasterVolumeLevelScalar()
            
            # Convert to percentage
            return int(level_scalar * 100)
        except Exception as e:
            print(f"get_audio_level() error: {e}")
            return None

    # -----------------------------------------
    # Window close
    # -----------------------------------------
    def on_closing(self):
        self.running_preview = False
        if self.cap.isOpened():
            self.cap.release()
        pygame.mixer.quit()
        self.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = EyeDetectionApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

import customtkinter as ctk
import threading
import cv2
import time
import pygame
import os
from PIL import Image, ImageTk

import asyncio
from bleak import BleakScanner

import comtypes
from ctypes import cast, POINTER
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL

from cv_close_eye_detect import EyeDetector

class EyeDetectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Eye Detection with BLE + Audio (Final Fixes)")
        self.geometry("1000x600")

        # Initialize Pygame for MP3 playback
        pygame.mixer.init()

        # State variables
        self.running_preview = True
        self.detection_active = False
        self.awake_time_value = 30  # 30..300
        self.sleep_value = 0        # 0..900

        # Single EyeDetector instance
        self.eye_detector = EyeDetector()

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Camera Preview (left)
        self.camera_label = ctk.CTkLabel(self, text="")
        self.camera_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Controls frame (right)
        self.controls_frame = ctk.CTkFrame(self, width=300)
        self.controls_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # 1) Awake Time slider (30..300 in steps of 30)
        self.awake_label = ctk.CTkLabel(self.controls_frame, text="Awake Time (30..300, step=30)")
        self.awake_label.pack(pady=(10,0))

        self.awake_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=30,
            to=300,
            number_of_steps=9,  # 10 distinct positions
            command=self.on_awake_change
        )
        self.awake_slider.set(30)
        self.awake_slider.pack(pady=(0,5))

        self.awake_value_label = ctk.CTkLabel(self.controls_frame, text="30 sec")
        self.awake_value_label.pack(pady=(0,10))

        # 2) Sleep Time slider (0..900 in steps of 60)
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

        # Buttons for setup/run
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

        # Bluetooth / audio indicators
        self.bluetooth_label = ctk.CTkLabel(self.controls_frame, text="Bluetooth: ...")
        self.bluetooth_label.pack(pady=5)

        self.audio_label = ctk.CTkLabel(self.controls_frame, text="Audio Level: ...")
        self.audio_label.pack(pady=5)

        self.scan_button = ctk.CTkButton(
            self.controls_frame, text="Scan BLE Now", command=self.scan_ble_devices
        )
        self.scan_button.pack(pady=10)

        self.audio_button = ctk.CTkButton(
            self.controls_frame, text="Get Audio Level", command=self.show_audio_level
        )
        self.audio_button.pack(pady=10)

        # Open camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.label_status.configure(text="Error: Cannot open camera.")
        else:
            self.label_status.configure(text="Camera opened. Ready.")

        # Start camera preview loop
        self.update_preview()

        # Optionally: Periodic updates for BLE + audio in background
        # (You can uncomment if you want continuous updates every X sec)
        # self.update_bluetooth_and_audio()

    # ----------------- Slider Callbacks -----------------
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
        self.sleep_value = new_val
        self.sleep_value_label.configure(text=f"{new_val} sec")

    # ----------------- Setup Handlers -----------------
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

    # ----------------- Run Process -----------------
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

    # ----------------- Stop/Reset -----------------
    def stop_handler(self):
        self.label_status.configure(text="Stop/Reset requested...")
        self.detection_active = False
        self.eye_detector.stop_detection()
        pygame.mixer.music.stop()

    # ----------------- Camera Preview Loop -----------------
    def update_preview(self):
        if self.running_preview and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Mirror the camera feed
                frame = cv2.flip(frame, 1)

                # Pass to EyeDetector if detection is active
                if self.detection_active:
                    status, old_mode, processed_frame = self.eye_detector.process_frame(frame)
                else:
                    status, old_mode, processed_frame = (None, None, frame)

                # Display processed_frame
                frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb).resize((500, 400), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_img, size=(500, 400))
                self.camera_label.configure(image=ctk_img)
                self.camera_label.image = ctk_img

                # Check if detection returned a code
                if status is not None:
                    if old_mode in ("setup_open", "setup_closed"):
                        # 0 => fail, 1 => success
                        self.detection_active = False
                        if status == 1:
                            self.label_status.configure(text=f"{old_mode} SUCCESS!")
                        else:
                            self.label_status.configure(text=f"{old_mode} FAILED.")
                    elif old_mode == "run":
                        if status == 2:
                            self.label_status.configure(text="Run => threshold exceeded => playing song!")
                            self.play_song()

        self.after(30, self.update_preview)

    # ----------------- Song Playback -----------------
    def play_song(self):
        try:
            pygame.mixer.music.stop()
            mp3_path = "song.mp3"
            pygame.mixer.music.load(mp3_path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing {mp3_path}: {e}")

    # ----------------- BLE + Audio Routines -----------------
    def scan_ble_devices(self):
        """
        Button handler to scan for BLE devices in a separate thread & event loop
        to avoid "Thread is configured for Windows GUI" error.
        """
        def bg_scan():
            name = self.check_bluetooth_device()
            if name:
                self.bluetooth_label.configure(text=f"Bluetooth: {name}")
            else:
                self.bluetooth_label.configure(text="Bluetooth: None")

        threading.Thread(target=bg_scan, daemon=True).start()

    def check_bluetooth_device(self):
        """
        Creates a new asyncio event loop for Bleak scanning to avoid conflicts.
        Returns name of first BLE device found, or None.
        """
        async def _async_scan():
            try:
                devices = await BleakScanner.discover(timeout=5.0)
                if devices:
                    return devices[0].name or "Unnamed BLE Device"
                return None
            except Exception as e:
                print(f"Bleak scanning error: {e}")
                return None

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        device_name = None
        try:
            device_name = loop.run_until_complete(_async_scan())
        except Exception as e:
            print(f"Bleak scanning error (sync): {e}")
        finally:
            loop.close()

        return device_name

    def show_audio_level(self):
        """
        Button handler to get the current master volume and update label.
        """
        level = self.get_audio_level()
        if level is not None:
            self.audio_label.configure(text=f"Audio Level: {level}%")
        else:
            self.audio_label.configure(text="Audio Level: Error")

    def get_audio_level(self):
        """
        Uses PyCaw to get the Windows master volume (0..100).
        """
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            level_scalar = volume.GetMasterVolumeLevelScalar()
            return int(level_scalar * 100)
        except Exception as e:
            print(f"Audio level error: {e}")
            return None

    # Optional continuous updates:
    def update_bluetooth_and_audio(self):
        """
        If you want to poll BLE & audio automatically every X seconds,
        uncomment self.update_bluetooth_and_audio() in __init__().
        """
        def bg_check():
            dev = self.check_bluetooth_device()
            if dev:
                self.bluetooth_label.configure(text=f"Bluetooth: {dev}")
            else:
                self.bluetooth_label.configure(text="Bluetooth: None")

            level = self.get_audio_level()
            if level is not None:
                self.audio_label.configure(text=f"Audio Level: {level}%")
            else:
                self.audio_label.configure(text="Audio Level: Error")

        threading.Thread(target=bg_check, daemon=True).start()

        self.after(5000, self.update_bluetooth_and_audio)  # re-check every 5 sec

    # ----------------- Window Close -----------------
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

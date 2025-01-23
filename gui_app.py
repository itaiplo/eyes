import customtkinter as ctk
import threading
import cv2
import time

import top_cv  # from your existing code
from PIL import Image, ImageTk

class EyeDetectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Eye Detection GUI")
        self.geometry("900x600")

        # Configure the main window's grid: 2 columns, 1 row
        self.grid_columnconfigure(0, weight=1)  # camera feed column
        self.grid_columnconfigure(1, weight=0)  # controls column
        self.grid_rowconfigure(0, weight=1)

        # ------------------ CAMERA PREVIEW (left side) ------------------ #
        self.camera_label = ctk.CTkLabel(self, text="")
        self.camera_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Start camera capture for continuous preview
        # (Assumes camera index = 0; change if needed)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Warning: Could not open camera 0.")
        self.preview_running = True
        self.update_preview()  # start the continuous preview loop

        # ------------------ CONTROLS (right side) ------------------ #
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # 1) Sensitivity slider
        self.sensitivity_label = ctk.CTkLabel(self.controls_frame, text="Sensitivity")
        self.sensitivity_label.pack(pady=(10,0))

        # We'll map 0.5..1.0 in steps of 0.1
        # ctk.CTkSlider doesn't have a "resolution" parameter like Tk's Scale,
        # but we can use 'number_of_steps' to approximate increments.
        # range 0.5..1.0 => total span 0.5 => in increments of 0.1 => 5 steps.
        self.sensitivity_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0.5,
            to=1.0,
            number_of_steps=5,  # 0.5->1.0 in steps of 0.1
            command=self.on_sensitivity_change
        )
        self.sensitivity_slider.set(0.5)
        self.sensitivity_slider.pack(pady=(0,5))

        # Display the sensitivity value
        self.sensitivity_value_label = ctk.CTkLabel(self.controls_frame, text="0.5")
        self.sensitivity_value_label.pack(pady=(0,10))

        # Internal variable to store current sensitivity
        self.sensitivity_value = 0.5

        # 2) Sleep Time slider (0..900 in steps of 60)
        self.sleep_label = ctk.CTkLabel(self.controls_frame, text="Sleep Time (seconds)")
        self.sleep_label.pack(pady=(10,0))

        # We have 15 intervals if we go from 0..900 in steps of 60
        # so number_of_steps=15 implies 16 discrete positions (including 0).
        self.sleep_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0,
            to=900,
            number_of_steps=15,  # 0..900 (16 positions)
            command=self.on_sleep_change
        )
        self.sleep_slider.set(0)
        self.sleep_slider.pack(pady=(0,5))

        # Display the sleep time value
        self.sleep_value_label = ctk.CTkLabel(self.controls_frame, text="0 sec")
        self.sleep_value_label.pack(pady=(0,10))

        # Internal variable to store current sleep time
        self.sleep_value = 0

        # 3) Buttons: Setup open/closed eyes, Run, Stop
        self.button_setup_open = ctk.CTkButton(
            self.controls_frame,
            text="Setup Open Eyes",
            command=self.setup_open_handler
        )
        self.button_setup_open.pack(pady=5)

        self.button_setup_closed = ctk.CTkButton(
            self.controls_frame,
            text="Setup Closed Eyes",
            command=self.setup_closed_handler
        )
        self.button_setup_closed.pack(pady=5)

        self.button_run = ctk.CTkButton(
            self.controls_frame,
            text="Run Process",
            command=self.run_process_handler
        )
        self.button_run.pack(pady=5)

        self.button_stop = ctk.CTkButton(
            self.controls_frame,
            text="Stop/Reset",
            command=self.stop_handler
        )
        self.button_stop.pack(pady=5)

        # Status label
        self.label_status = ctk.CTkLabel(self.controls_frame, text="Status: Waiting...")
        self.label_status.pack(pady=10)

        # Thread references
        self.process_thread = None
        self.running = False

    # ------------------ SLIDER CALLBACKS ------------------ #
    def on_sensitivity_change(self, val):
        """
        Slider callback for sensitivity: 0.5 -> 1.0 in steps of 0.1
        'val' is a float from 0.5..1.0
        """
        # Round to 1 decimal
        new_val = round(val, 1)
        self.sensitivity_value = new_val
        self.sensitivity_value_label.configure(text=str(new_val))

    def on_sleep_change(self, val):
        """
        Slider callback for sleep time: 0..900 in 15 steps => increments of 60.
        'val' is a float from 0..900. We'll round it properly to the nearest 60.
        """
        step = 60
        new_val = int(round(val / step) * step)  # e.g. 0, 60, 120, ...
        # Because we set number_of_steps=15, val is already quantized,
        # but we do this extra rounding to be safe.
        self.sleep_slider.set(new_val)
        self.sleep_value = new_val
        self.sleep_value_label.configure(text=f"{new_val} sec")

    # ------------------ CAMERA PREVIEW ------------------ #
    def update_preview(self):
        """
        Continuously capture frames from the camera and show them in 'camera_label'.
        Called repeatedly via .after().
        """
        if self.preview_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Convert BGR -> RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert to PIL
                pil_img = Image.fromarray(frame_rgb)
                # Resize if you want a certain dimension for display
                pil_img = pil_img.resize((500, 400), Image.Resampling.LANCZOS)

                # Convert to a CustomTkinter-compatible image
                ctk_img = ctk.CTkImage(light_image=pil_img, size=(500, 400))
                # Update label
                self.camera_label.configure(image=ctk_img)
                self.camera_label.image = ctk_img  # keep a reference to avoid GC

        # Schedule next update in 30 ms
        self.after(30, self.update_preview)

    # ------------------ BUTTON HANDLERS ------------------ #
    def setup_open_handler(self):
        """
        Start 'setup open eyes' calibration.
        In your code, top_cv calls cv_close_eye_detect, which opens its own camera capture, etc.
        """
        self.label_status.configure(text="Setting up Open Eyes...")
        success = top_cv.setup_open_eyes()
        if success:
            self.label_status.configure(text="Setup Open Eyes: SUCCESS!")
        else:
            self.label_status.configure(text="Setup Open Eyes: FAILED. Try again.")

    def setup_closed_handler(self):
        """
        Start 'setup closed eyes' calibration.
        """
        self.label_status.configure(text="Setting up Closed Eyes...")
        success = top_cv.setup_closed_eyes()
        if success:
            self.label_status.configure(text="Setup Closed Eyes: SUCCESS!")
        else:
            self.label_status.configure(text="Setup Closed Eyes: FAILED. Try again.")

    def run_process_handler(self):
        """
        Run the main detection process in a separate thread to avoid freezing the GUI.
        """
        self.label_status.configure(text="Process started in background...")
        self.running = True
        sensitivity = self.sensitivity_value
        sleep_time = self.sleep_value

        self.process_thread = threading.Thread(
            target=self.run_process_in_thread,
            args=(sensitivity, sleep_time),
            daemon=True
        )
        self.process_thread.start()

    def run_process_in_thread(self, sensitivity, sleep_time):
        """
        Background thread that calls top_cv.run_process(...).
        """
        def on_eyes_open_callback():
            self.label_status.configure(text="Eyes detected as open!")
            # If you want to play an MP3 with pygame or anything else, do it here.

        ret = top_cv.run_process(sensitivity, sleep_time, on_eyes_open=on_eyes_open_callback)

        if self.running:
            self.label_status.configure(text=f"Process finished with return={ret}")

    def stop_handler(self):
        """
        Stop detection or reset states.
        """
        self.label_status.configure(text="Stop/Reset requested...")
        self.running = False
        top_cv.stop_detection()

    # ------------------ WINDOW CLOSE OVERRIDE ------------------ #
    def on_closing(self):
        """
        Override to safely release camera and close.
        """
        self.preview_running = False
        if self.cap.isOpened():
            self.cap.release()
        self.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = EyeDetectionApp()
    # Override the default close behavior
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

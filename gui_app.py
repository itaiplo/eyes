# gui_app.py

import customtkinter as ctk
import threading
import top_cv

class EyeDetectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Eye Detection GUI")
        self.geometry("500x400")

        # Create UI elements
        self.label_info = ctk.CTkLabel(self, text="Eye Detection Setup", font=("Arial", 16))
        self.label_info.pack(pady=10)

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

        # Stop/Reset
        self.button_stop = ctk.CTkButton(self, text="Stop/Reset", command=self.stop_handler)
        self.button_stop.pack(pady=5)

        # Status label
        self.label_status = ctk.CTkLabel(self, text="Status: Waiting...", font=("Arial", 14))
        self.label_status.pack(pady=10)

        # Thread reference
        self.process_thread = None
        self.running = False  # Flag to control thread

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
        This is called inside a background thread so the GUI won't freeze.
        """
        def on_eyes_open_callback():
            self.label_status.configure(text="Eyes detected as open!")
        
        ret = top_cv.run_process(sensitivity, sleep_time, on_eyes_open=on_eyes_open_callback)
        if ret == 1:
            # Eyes open triggered
            pass
        else:
            # Process ended with ret=0 or something else
            pass

        # Once the process finishes, update status
        if self.running:
            self.label_status.configure(text=f"Process finished with return={ret}")

    def stop_handler(self):
        """
        Since we have a blocking while-loop in the detection,
        the simplest approach is to set a flag that your detection code
        checks periodically to break out of the loop, 
        or forcibly release the camera.
        """
        self.label_status.configure(text="Stop requested...")
        self.running = False
        # If you have custom logic in cv_close_eye_detect, call it:
        # For example:
        # cv_close_eye_detect.reset_logic("run")
        # Or forcibly release camera, etc.

        # If there's a thread running, we can attempt to close capture 
        # or forcibly kill the thread (not recommended). 
        # Usually, you'd design your detection loop to check 'self.running'
        # and break gracefully.
        

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = EyeDetectionApp()
    app.mainloop()

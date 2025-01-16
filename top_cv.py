# top_cv.py

import cv_close_eye_detect
import time

# For beep sounds on Windows
try:
    import winsound
except ImportError:
    winsound = None

# Global flags or states if needed
# (But we try to keep them to a minimum and pass parameters around)

def setup_open_eyes():
    """
    Setup (calibrate) open eyes using cv_close_eye_detect
    Returns True if succeeded, False if failed
    """
    ret_val = cv_close_eye_detect.main_fanc(mode="setup_open")
    return ret_val == 1

def setup_closed_eyes():
    """
    Setup (calibrate) closed eyes using cv_close_eye_detect
    Returns True if succeeded, False if failed
    """
    ret_val = cv_close_eye_detect.main_fanc(mode="setup_closed")
    return ret_val == 1

def run_process(sensitivity, sleep_time, on_eyes_open=None):
    """
    Run the main detection process. 
    This is a blocking function in its current form.
    The "on_eyes_open" parameter is a callback that can be invoked
    when eyes are detected as open (ret == 1 from main_fanc).
    """
    # Convert sensitivity to float, sleep_time to int if needed
    sensitivity = float(sensitivity)
    sleep_time = int(sleep_time)

    # Sleep before starting (as your original code does)
    time.sleep(sleep_time)

    print("Process started with sensitivity:", sensitivity, "and sleep time:", sleep_time)
    ret = cv_close_eye_detect.main_fanc(mode="run", sensitivity=sensitivity)
    
    if ret == 1:
        print("Eyes are open!")
        # Optional: beep to indicate
        if winsound:
            winsound.Beep(500, 200)
        # If a callback is provided, call it:
        if on_eyes_open is not None:
            on_eyes_open()
    if ret == -1:
        print("No face detected, Recomand to recalibrate")
        # Optional: beep to indicate
        if winsound:
            winsound.Beep(500, 200)
        # If a callback is provided, call it:
        if on_eyes_open is not None:
            on_eyes_open()

    return ret

def reset_counters(mode):
    """
    If you want to expose the 'reset' logic to the GUI, you can define it here.
    Your original code used input prompts; now you'd handle it in the GUI.
    """
    cv_close_eye_detect.reset_logic(mode)

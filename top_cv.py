# top_cv.py
from cv_close_eye_detect import EyeDetector

# We'll create one EyeDetector in the GUI, so top_cv can just define helper functions
# if you want them, or you can remove this file altogether.

def stop_detection(detector: EyeDetector):
    """
    If you want a single call to stop detection on an EyeDetector instance.
    """
    detector.stop_detection()

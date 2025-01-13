# cv_close_eye_detect.py

import cv2
import time
import keyboard

# Global counters if needed
counter = 0
counter_hit = 0
start_time = 0

def close_window(cap):
    cap.release()
    cv2.destroyAllWindows()

def reset_logic(mode):
    """
    Example placeholder for any reset counters or logic you had in your code.
    Instead of calling input(), we just reset the counters here.
    """
    global counter, counter_hit, start_time
    counter = 0
    counter_hit = 0
    start_time = time.time()
    print(f"Reset counters for mode {mode}")

def main_fanc(mode="", sensitivity=0.5):
    """
    Blocking function that opens the camera and runs detection.
    Returns 1 if eyes open (or closed, depending on your logic) were detected 
    in the specified threshold/time window, otherwise returns 0.
    """
    global counter, counter_hit, start_time
    # Paths to Haar cascades
    eye_cascPath = './haarcascade_eye_tree_eyeglasses.xml'
    face_cascPath = './haarcascade_frontalface_alt.xml'

    # Load the Haar cascades
    faceCascade = cv2.CascadeClassifier(face_cascPath)
    eyeCascade = cv2.CascadeClassifier(eye_cascPath)

    # Open the video capture
    cap = cv2.VideoCapture(0)

    # Initialize counters/timers
    counter = 0
    counter_hit = 0
    start_time = time.time()

    while True:
        # Instead of using 'r' to call a top_cv reset, 
        # let's just see if the user pressed 'q' to quit:
        if keyboard.is_pressed('q'):
            print("User pressed Q -> quitting detection loop.")
            close_window(cap)
            return 0  # or break / or do something else

        ret, img = cap.read()
        if not ret:
            print("Failed to read from camera.")
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        if len(faces) > 0:
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                face_roi = gray[y:y + h, x:x + w]

                eyes = eyeCascade.detectMultiScale(
                    face_roi,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )

                # Simple logic: if eyes detected => "open", else => "closed"
                if len(eyes) == 0:
                    if mode == 'setup_closed':
                        counter_hit += 1
                    print("Eyes are CLOSED.")
                else:
                    if mode in ('setup_open', 'run'):
                        counter_hit += 1
                    print("Eyes are OPEN.")
        else:
            print("No face detected.")

        # Show frame
        resized_frame = cv2.resize(img, (400, 400))
        cv2.imshow('Video Feed', resized_frame)

        # Keep track of counters/time
        counter += 1
        now = time.time()

        # Check logic for each mode
        if mode == 'run':
            # Example: every 15 seconds, check ratio
            if now - start_time > 15:
                ratio = counter_hit / counter if counter else 0
                if ratio > sensitivity:
                    close_window(cap)
                    return 1
                else:
                    # Reset counters and time
                    counter_hit = 0
                    counter = 0
                    start_time = now

        if mode in ('setup_open', 'setup_closed'):
            # Return 1 if we have a certain ratio
            if now - start_time > 15:
                ratio = counter_hit / counter if counter else 0
                close_window(cap)
                if ratio > 0.8:
                    return 1
                else:
                    return 0

        # If user presses 'Esc' or 'Q' in the OpenCV window
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):
            print("ESC or Q pressed, exiting detection loop.")
            break

    close_window(cap)
    return 0

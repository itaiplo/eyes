import cv2
import time
import top_cv
import keyboard



def close_window(cap):
    cap.release()
    cv2.destroyAllWindows()
    

def main_fanc(mode="",sensitivity=0.5):
    # Paths to Haar cascades
    eye_cascPath = './haarcascade_eye_tree_eyeglasses.xml'  # Eye detection model
    face_cascPath = './haarcascade_frontalface_alt.xml'     # Face detection model

    # Load the Haar cascades
    faceCascade = cv2.CascadeClassifier(face_cascPath)
    eyeCascade = cv2.CascadeClassifier(eye_cascPath)
    # Open the video capture
    cap = cv2.VideoCapture(0)
    counter=0
    counter_hit=0
    start = time.time()
    end=start

   
    while True:
        if keyboard.is_pressed('r'):
            ret=top_cv.handle_reset(mode)
            if ret==0: # reset to setup again
                close_window(cap)
                return 0
            elif ret==1: #reset counters and time
                counter=0
                counter_hit=0
                start = time.time()
                end=start
            elif ret==2: #exit
                close_window(cap)
                exit(0)
        
        # mode configs
        if mode == 'run':
            if end-start>15:
                if counter_hit/counter>float( sensitivity):
                    return 1
                else:
                    counter_hit=0
                    counter=0
                    start = time.time()
                    end=start
                
        if mode == 'setup_open' or mode == 'setup_closed':
            # if 'r' key detected, call handle_reset function from top_cv.py

            if end-start>15:
                if (counter_hit/counter>0.8):
                    return 1
                else:
                    return 0
                
        ret, img = cap.read()
        if ret:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Convert frame to grayscale

            # Detect faces in the image
            faces = faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    # Draw rectangle around the face
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Region of interest (ROI) for the face
                    face_roi = gray[y:y + h, x:x + w]

                    # Detect eyes in the ROI
                    eyes = eyeCascade.detectMultiScale(
                        face_roi,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=(30, 30)
                    )

                    if len(eyes) == 0:
                        if mode =='setup_closed':
                            counter_hit=counter_hit+1
                        print('The eyes are closed')
                    else:
                        if mode =='setup_open' or mode=='run':
                            counter_hit=counter_hit+1
                        print('The eyes are open')

            else:
                print("No face detected")

            # Resize the frame for display
            resized_frame = cv2.resize(img, (400, 400), interpolation=cv2.INTER_LINEAR)
            cv2.imshow('Video Feed', resized_frame)
        

        # Break the loop on 'q' or 'Q'
        key = cv2.waitKey(1)
        if key == ord('q') or key == ord('Q'):
            break
        counter=counter+1
        end = time.time()


    # Release the capture and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()


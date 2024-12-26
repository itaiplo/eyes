import cv2
import time
import top_cv
import keyboard

def main_fanc(freq_control=0.1,mode=""):
    # Paths to Haar cascades
    eye_cascPath = './haarcascade_eye_tree_eyeglasses.xml'  # Eye detection model
    face_cascPath = './haarcascade_frontalface_alt.xml'     # Face detection model

    # Load the Haar cascades
    faceCascade = cv2.CascadeClassifier(face_cascPath)
    eyeCascade = cv2.CascadeClassifier(eye_cascPath)
    # Open the video capture
    cap = cv2.VideoCapture(0)
    counter=0
    start = time.time()
    # for i in range(2):
    #     if i==0:
    #         ret=input("print y when ready to start setup open eyes: ")
    #     if (ret=="y"):
    while True:
        if(mode!="init_setup"):
            if keyboard.is_pressed('r'):
                inp=input("input was detectet, choose what you want to do(0 for beginigng reset, 1 for ignore reset, 2 for exit)")
                if(inp==2):
                    exit()
                if(mode==""):
                    if(inp==0):
                        break
                    if(inp==1):
                        counter_magic, time_magic=0 #TODO reset counters and timer of thresh hold to zero
            if(mode=="setup"):
                if((end-start)>30):
                    return end-start, counter
                

            
        counter=counter+1
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
                        print('The eyes are closed')
                    else:
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
        time.sleep(freq_control)
        end = time.time()
        print ("counter is"+ str(counter))
        print("time is" +str(end - start))

    # Release the capture and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()


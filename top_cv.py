import cv_close_eye_detect
import keyboard
import time

def open_eyes_setup():
    while (1):
        ret=input("print y when ready to start setup open eyes: ")
        if (ret=="y"):
            ret_func=cv_close_eye_detect.main_fanc(mode="setup_open")
            if (ret_func==1):
                print("setup open eyes secceded")
                break
            else:
                print("setup open eyes failed start again")
                
 

def closed_eyes_setup():
    while (1):
        ret=input("print y when ready to start setup closed eyes: ")
        if (ret=="y"):
            ret_func=cv_close_eye_detect.main_fanc(mode="setup_closed")
            if (ret_func==1):
                print("setup closed eyes secceded")
                break
            else:
                print("setup closed eyes failed start again")
                

def setup_open_and_close():
    open_eyes_setup()
    closed_eyes_setup()
    print ("setup closed and open done")

def run_proccess():
    sensitivity=input("enter sensitivity value: ")
    print ("proccess started")
    cv_close_eye_detect.main_fanc(mode="run",sensitivity=sensitivity)

def main():
    print("start setup")    
    setup_open_and_close()
    run_proccess()

if __name__ == "__main__":
    main()
import cv_close_eye_detect
import keyboard
import time
global_delay=0

def init_setup():
    time, laps=cv_close_eye_detect.main_fanc(mode="init_setup")
    base_freq = laps / time
    global global_delay
    global_delay = max(0, 0.1 - (1 / base_freq))
    global_delay=0 # remove if want to use the delay
    print("delay is: ", global_delay)
    

def open_eyes_setup():
    while (1):
        ret=input("print y when ready to start setup open eyes: ")
        if (ret=="y"):
            global global_delay
            ret_func=cv_close_eye_detect.main_fanc(mode="setup_open",delay=global_delay)
            if (ret_func==1):
                print("setup open eyes secceded")
                break
            else:
                print("setup open eyes failed start again")
                
 

def closed_eyes_setup():
    while (1):
        ret=input("print y when ready to start setup closed eyes: ")
        if (ret=="y"):
            ret_func=cv_close_eye_detect.main_fanc(mode="setup_closed",delay=global_delay)
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
    cv_close_eye_detect.main_fanc(mode="run",delay=global_delay,sensitivity=sensitivity)

def main():
    # init_setup()
    # print("start setup")    
    # setup_open_and_close()
    run_proccess()

if __name__ == "__main__":
    main()
import cv_close_eye_detect
import keyboard
import time

def init_setup():
    time, laps=cv_close_eye_detect.main_fanc(mode="init_setup")
    base_freq=laps/time
    delay = max(0, 0.1 - (1 / base_freq))
    if
def open_eyes_setup():
    while (1):
        ret=input("print y when ready to start setup open eyes: ")
        if (ret=="y"):
            ret_func=cv_close_eye_detect.main_fanc(mode="setup_open")
            if (ret_func==1):
                print("setup open eyes secceded")
                break


def closed_eyes_setup():
    while (1):
        ret=input("print y when ready to start setup closed eyes: ")
        if (ret=="y"):
            ret_func=cv_close_eye_detect.main_fanc(mode="setup_closed")
            if (ret_func==1):
                print("setup closed eyes secceded")
                break

def setup_open_and_close():
    open_eyes_setup()
    closed_eyes_setup()
    print ("setup closed and open done")

def handle_reset():
    inp=input("input was detectet, choose what you want to do(0 for beginigng reset, 1 for ignore reset, 2 for exit)")
    if(inp==0):
        print("starting setup again")
        break
        setup_open_and_close()
    if(inp==1):
        //we stoped here.. need to write better the hendle reset. look at line 23 of hendle reset during setup procces




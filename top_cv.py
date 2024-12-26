import cv_close_eye_detect
import keyboard
import time
import winsound

# Function to handle reset
def handle_reset(mode):
    print("Reset triggered.")
    if mode =='run':
        while (1):
            inp=input("0 for setup again, 1 for continue without setup, 2 for exit")
            inp= int(inp)
            if inp==0:
                return 0
            elif inp==1:
                return 1
            elif inp==2:
                return 2
    if mode == 'setup_open' or mode == 'setup_closed':
        while (1):
            inp=input("0 for setup again, 2 for exit")
            inp=int(inp)
            if inp==0:
                return 0
            elif inp==2:
                return 2
        

def setup_open_and_close():
    while (1):
        ret=input("print y when ready to start setup open eyes: ")
        if (ret=="y"):
            ret_func=cv_close_eye_detect.main_fanc(mode="setup_open")
            if (ret_func==1):
                print("setup open eyes secceded")
            else:
                print("setup open eyes failed start again")
                continue

        ret=input("print y when ready to start setup closed eyes: ")
        if (ret=="y"):
            ret_func=cv_close_eye_detect.main_fanc(mode="setup_closed")
            if (ret_func==1):
                print("setup closed eyes secceded")
                break
            else:
                print("setup closed eyes failed start again")
                continue

def run_proccess():
    sensitivity=input("enter sensitivity value: ")
    print ("proccess started")
    ret=cv_close_eye_detect.main_fanc(mode="run",sensitivity=sensitivity)
    return ret

def main():
    flag=0
    while (1):
        print("start setup")
        if(flag==0):
            setup_open_and_close()
        flag=0
        ret=run_proccess()
        if ret==1:
            while (1):    
                winsound.Beep(500,50)
                if keyboard.is_pressed('p'):
                    print("indicator was detected, what do you want to do?")
                    while (1):
                        break_flag=0
                        inp=input("0 for setup again, 1 for continue without setup, 2 for exit")
                        inp=int(inp)
                        if inp==0:
                            break_flag=1
                            break
                        elif inp==1:
                            flag=1
                            break_flag=1
                            break
                        elif inp==2:
                            exit(0)
                    if break_flag==1:
                        break


if __name__ == "__main__":
    main()
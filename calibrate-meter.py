print("Use this script to find calibration points for your meter (add to settings.py).")
print("Type Ctrl+C to exit.");

meterPin = 18 #pwm

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(meterPin, GPIO.OUT)
pwm = GPIO.PWM(meterPin, 50)
pwm.start(0)

dcLast = 0
meterLag = 0.18 #seconds between ballistics steps
def setMeter(dcNew): #Unlike carillon.py, this one is DC direct, not value converted
    #pwm must already have been started
    global dcLast #otherwise the fact that we set dcLast inside this function would make python complain
    if dcNew > 100: dcNew = 100 #apply range limits
    if dcNew < 0: dcNew = 0
    #set meter, using ballistics if dcChg is great enough
    dcChg = dcNew-dcLast    
    if(abs(dcChg) > 10): #apply ballistics
        #easing out equations by Robert Penner - gizma.com/easing
        steps = 4
        for t in range(1, steps+1):
            #quadratic t^2
            t /= float(steps)
            nowDC = float(-dcChg) * t * (t-2) + dcLast
            pwm.ChangeDutyCycle( nowDC )
            if(t<steps):
                time.sleep(meterLag)
    else: #just go to there
        pwm.ChangeDutyCycle(dcNew)
    dcLast = dcNew
#end def setMeter

try:
    while 1:
        userDC = input("Enter duty cycle 0-100: ")
        print("Setting meter to "+str(userDC))
        setMeter(float(userDC))
except KeyboardInterrupt:
    print("\r\nBye!")
# except:
#     print("Error")
finally:
    if dcLast > 20: #kill the meter softly
        setMeter(0)
    pwm.stop()
    GPIO.cleanup()
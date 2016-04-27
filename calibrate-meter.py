#!/usr/bin/env python
#Use this script to find calibration points for your meter (add to settings.py).

#External settings
import settings

#External modules
import time

if settings.piMode:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(settings.slavePin, GPIO.OUT)
    if(settings.meterPin != False):
        GPIO.setup(settings.meterPin, GPIO.OUT)
        pwm = GPIO.PWM(settings.meterPin, 50)
        pwm.start(0)
    else:
        print('Please set the meter pin in settings.py, if indeed you have a meter hooked up.')
        exit()
else:
    print('Please enable piMode in settings.py, if this is indeed running on a Pi.')
    exit()

dcLast = 0
meterLag = 0.18 #seconds between ballistics steps
def setMeter(dcNew): #Unlike carillon.py, this one is DC direct, not value converted; nor checks for piMode
    #pwm must already have been started
    global dcLast #otherwise the fact that we set dcLast inside this function would make python complain
    if dcNew > 100: dcNew = 100 #apply range limits
    if dcNew < 0: dcNew = 0
    #set meter, using ballistics if dcChg is great enough
    dcChg = dcNew-dcLast
    if(abs(dcChg) > settings.meterChg): #apply ballistics
        #easing out equations by Robert Penner - gizma.com/easing
        for t in range(1, settings.meterStp+1):
            #quadratic t^2
            t /= float(settings.meterStp)
            nowDC = float(-dcChg) * t * (t-2) + dcLast
            pwm.ChangeDutyCycle( nowDC )
            if(t<settings.meterStp):
                time.sleep(settings.meterLag)
    else: #just go to there
        pwm.ChangeDutyCycle(dcNew)
    dcLast = dcNew
#end def setMeter

try:
    print("Use this script to find calibration points for your meter (add to settings.py).")
    print("Type Ctrl+C to exit.");
    while 1:
        userDC = input("Enter duty cycle 0-100: ")
        print("Setting meter to "+str(userDC))
        setMeter(float(userDC))
        
except AttributeError: #Easier to ask forgiveness than permission (EAFP) - http://stackoverflow.com/a/610923
    print("\r\nAttributeError. Please ensure your settings.py includes all items from settings-sample.py.")
except KeyboardInterrupt:
    print("\r\nBye!")
# except:
#     print("Error")
finally:
    if settings.piMode:
        if dcLast > 20: #kill the meter softly
            setMeter(0)
        pwm.stop()
        GPIO.cleanup()
#end try/except/finally
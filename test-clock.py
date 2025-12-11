#!/usr/bin/env python

#External settings
import settings

#External modules
import time

if(settings.slaveBipolar):
    print("Use this to test clock impulses on alternating pins "+str(settings.slavePinEven)+" and "+str(settings.slavePinOdd)+" (per settings.py)")
else:
    print("Use this to test clock impulses on pin "+str(settings.slavePin)+" (per settings.py)")

if settings.piMode:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    if settings.slaveBipolar:
        GPIO.setup(settings.slavePinOdd, GPIO.OUT)
        GPIO.setup(settings.slavePinEven, GPIO.OUT)
    else:
        GPIO.setup(settings.slavePin, GPIO.OUT)
#end pi mode
else:
    print('Please enable piMode in settings.py, if this is indeed running on a Pi.')
    exit()

try:
    print("Type Ctrl+C to exit.");
    impDurLast = 0.2
    impCount = 0
    while 1:
        try:
            impDur = input("Duration of impulse in seconds (Enter for "+str(impDurLast)+"): ")
        except SyntaxError: #empty string
            impDur = impDurLast
        if impDur > 1:
            impDur = 1
        if impDur < 0.01:
            impDur = 0.01
        impDurLast = impDur
        impCount = impCount+1
        impPin = False
        if settings.slaveBipolar:
            impPin = settings.slavePinOdd if impCount % 2 else settings.slavePinEven
        else:
            impPin = settings.slavePin
        print("Impulse "+str(impCount)+": Waiting then impulsing pin "+str(impPin)+" for "+str(impDur)+" seconds")
        time.sleep(impDur) #so it will crash before setting the pin high, if it's going to crash
        GPIO.output(impPin, GPIO.HIGH)
        time.sleep(impDur)
        GPIO.output(impPin, GPIO.LOW)
        
except AttributeError: #Easier to ask forgiveness than permission (EAFP) - http://stackoverflow.com/a/610923
    print("\r\nAttributeError. Please ensure your settings.py includes all items from settings-sample.py.")
except KeyboardInterrupt:
    print("\r\nBye!")
# except:
#     print("Error")
finally:
    if settings.piMode:
        GPIO.cleanup()
#end try/except/finally
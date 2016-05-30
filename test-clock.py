#!/usr/bin/env python

#External settings
import settings

#External modules
import time

print("Use this to test clock impulses on pin "+str(settings.slavePin)+" (per settings.py)")

if settings.piMode:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(settings.slavePin, GPIO.OUT)
else:
    print('Please enable piMode in settings.py, if this is indeed running on a Pi.')
    exit()

try:
    print("Type Ctrl+C to exit.");
    impDurLast = 0.2
    while 1:
        try:
            impDur = input("Duration of impulse in seconds (Enter for "+str(impDurLast)+"): ")
        except SyntaxError: #empty string
            impDur = impDurLast
        if impDur > 1:
            impDur = 1
        if impDur < 0.05:
            impDur = 0.05
        impDurLast = impDur
        print("Waiting then impulsing for "+str(impDur)+" seconds")
        time.sleep(impDur) #so it will crash before setting the pin high, if it's going to crash
        GPIO.output(settings.slavePin, GPIO.HIGH)
        time.sleep(impDur)
        GPIO.output(settings.slavePin, GPIO.LOW)
        
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
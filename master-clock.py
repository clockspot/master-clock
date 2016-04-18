# print("Master clock starting.");

#External modules
import RPi.GPIO as GPIO
import os
#from os import path
#from os import listdir
import sys
import time
#from time import asctime, localtime
#from time import localtime
import subprocess
from subprocess import call #synchronous
from subprocess import Popen #asynchronous
from datetime import datetime

#External settings
import settings

# http://stackoverflow.com/a/4943474
def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

#Hardware stuff - Broadcom pin definitions
clockPin = 20 #trigger external circuit to advance slave clock #TODO correction mechanisms
meterPin = 18 #pwm to control moving-coil galvanometer (3VDC) as seconds display

def convertValueToDC(valNew):
    dcNew = 0
    #Which calibration range does valNew fall into?
    for i in range(0, len(settings.meterCal)):
        #If it falls in this one, or in/past the last one:
        if(valNew < settings.meterCal[i][0] or i == len(settings.meterCal)-1):
            valMax = settings.meterCal[i][0]
            valMin = 0
            dcMax = settings.meterCal[i][1]
            dcMin = 0
            #if valNew < first calibration point (indicated by i==0), lower bound is assumed calibration point of (0,0)
            if i > 0: #if valNew > first calibration point, set lower bound to previous calibration point
                valMin = settings.meterCal[i-1][0]
                dcMin = settings.meterCal[i-1][1]
            #Map new value. Not sure if I've reduced this as far as it can go mathwise.
            #print ("i="+str(i)+", valNew="+str(valNew)+", valMax="+str(valMax)+", valMin="+str(valMin)+", dcMax="+str(dcMax)+", dcMin="+str(dcMin))
            return float(dcMax-dcMin)*(float(valNew-valMin)/(valMax-valMin)) + dcMin
        #end found calibration range
    #end for each calibration range
#end def convertValueToDC

def updateMeter(valNew):
    #We will probably set it to valNew, but there may be some statuses to display instead. #TODO
    #if(no network connection): setMeter(10)
    #if(clockProcess != False and clockProcess.poll() is None): setMeter(30) #to indicate clock is moving
    #elif(no network connection): setMeter(10)
    #elif(bad ntp): setMeter(20)
        #ntpq -c rv | grep "reftime" with result e.g.
        #reftime=dabcecde.167297c4  Sat, Apr 16 2016 11:54:54.087,
        #reftime=00000000.00000000  Sat, Apr 16 2016 11:54:54.087,
    #else:
    setMeter(valNew)
#end def updateMeter

dcLast = 0
meterLag = 0.18 #seconds between ballistics steps
def setMeter(valNew):
    #pwm must already have been started
    global dcLast #otherwise the fact that we set dcLast inside this function would make python complain
    dcNew = convertValueToDC(valNew) #find new dc
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

def to12Hr(hr):
    if hr == 0: return 12
    elif hr > 12: return hr-12
    else: return hr
#end def to12Hr

def advanceClock():
    #This should be called a second early so you can activate a bit before the moment
    time.sleep(0.7)
    GPIO.output(clockPin, GPIO.HIGH)
    time.sleep(0.3)
    GPIO.output(clockPin, GPIO.LOW)

#Let's go!

#Pin setup
GPIO.setmode(GPIO.BCM)
#outputs
GPIO.setup(clockPin, GPIO.OUT)
GPIO.setup(meterPin, GPIO.OUT)
pwm = GPIO.PWM(meterPin, 50)
pwm.start(0)

#TODO read current time from .clocklast.txt
#TODO set into a "clock time" date variable

print("Master clock running. Press Ctrl+C to stop.");

lastSecond = -1
nowTime = datetime.now()
try:
    while 1:
        #important to snapshot current time, so test and assignment use same time value
        nowTime = datetime.now()
        if lastSecond != nowTime.second:
            lastSecond = nowTime.second
            updateMeter(nowTime.second)
            
            #TODO if the realtime and faketime are different, advance
            #there will need to be a 28-second grace period
            if(nowTime.second==29 or nowTime.second==59):
                advanceClock() #TODO can you call this asynchronously?            
            
        #end if new second
        time.sleep(0.05)
    #end while            
except KeyboardInterrupt:
    print("\r\nBye!")
# except:
#     print("Error")
finally:
    if dcLast > 20: #kill the meter softly
        setMeter(0)
    GPIO.output(clockPin, GPIO.LOW)
    pwm.stop()
    GPIO.cleanup()
#end try/except/finally
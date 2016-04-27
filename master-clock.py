#!/usr/bin/env python

#External settings
import settings

#External modules
if settings.piMode: import RPi.GPIO as GPIO
import os #includes path, listdir
import sys
import time #includes asctime, localtime
import subprocess
from subprocess import call #synchronous
from subprocess import Popen #asynchronous
from datetime import datetime
from datetime import timedelta

def getScriptPath():
    # http://stackoverflow.com/a/4943474
    return os.path.dirname(os.path.realpath(sys.argv[0]))

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
    #We will probably set it to valNew, but may want to set status instead. TODO
    #if(no network connection): setMeter(10)
    #elif(bad ntp): setMeter(20)
        #ntpq -c rv | grep "reftime" with result e.g.
        #reftime=dabcecde.167297c4  Sat, Apr 16 2016 11:54:54.087,
        #reftime=00000000.00000000  Sat, Apr 16 2016 11:54:54.087,
    #setMeter(30) during active slave setting is taken care of in syncSlave()
    #else:
    setMeter(valNew)
#end def updateMeter

dcLast = 0
def setMeter(valNew):
    #pwm must already have been started
    global dcLast
    dcNew = convertValueToDC(valNew) #find new dc
    if dcNew > 100: dcNew = 100 #apply range limits
    if dcNew < 0: dcNew = 0
    #set meter, using ballistics if dcChg is great enough
    dcChg = dcNew-dcLast
    if settings.piMode:
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
    else: #not piMode
        print('Set meter to val '+str(valNew)+': from dc '+str(dcLast)+' '+str(dcChg)+' to '+str(dcNew))
    dcLast = dcNew
#end def setMeter

#Slave clock control
slaveTime = datetime.now()
#This variable will keep (volatile) track of the slave-displayed time. To avoid wear on the SD card (is this unnecessary?), we'll only read the HD-stored slave time once, and write it (hopefully) once, in the program loop. All other calculations/adjustments will be made relative to this variable.
def getStoredSlaveTime():
    global slaveTime
    masterTime = datetime.now()
    #Normalize to the slave clock's interval
    masterTime = masterTime.replace(second=masterTime.second-(masterTime.second % settings.slaveInterval), microsecond=0)
    slaveTime = masterTime
    if os.path.exists(getScriptPath()+'/.slavetime.txt'):
        with open(getScriptPath()+'/.slavetime.txt', 'r') as f:
            #https://docs.python.org/2/tutorial/inputoutput.html
            savedTime = f.read().split(':') #expecting format h:m:s
            #shouldn't be necessary to close
        if(len(savedTime)==3): #validation close enough
            slaveTime = slaveTime.replace(hour=int(savedTime[0]),minute=int(savedTime[1]),second=int(savedTime[2])-(int(savedTime[2])%settings.slaveInterval))
            print('Read from file*: '+str(slaveTime.hour)+':'+str(slaveTime.minute)+':'+str(slaveTime.second))
        else: print('Bad file, so: '+str(slaveTime.hour)+':'+str(slaveTime.minute)+':'+str(slaveTime.second))
    else: print('No file, so: '+str(slaveTime.hour)+':'+str(slaveTime.minute)+':'+str(slaveTime.second))
    #slaveTime now gives (presumably) time displayed on slave, always in 24h format
    #If needed, apply offsets to put slaveTime within adjusting range of masterTime:
    #masterTime-(slaveHrs-slaveHold) < slaveTime <= masterTime+slaveHold
    #We consider slaveHrs because, if slave is 12h, we may assume 3:00 = 15:00 and vice versa
    
    #if slave is now AHEAD by more than slaveHold, set it back a day
    if (slaveTime-masterTime).total_seconds() > settings.slaveHold*3600:
        slaveTime = slaveTime - timedelta(days=1)
    
    #if slave is now BEHIND by more than slaveHrs-slaveHold, set it forward slaveHrs
    if (slaveTime-masterTime).total_seconds() <= settings.slaveHrs*-3600 + settings.slaveHold*3600:
        slaveTime = slaveTime + timedelta(hours=settings.slaveHrs)
#end getStoredSlaveTime

def setStoredSlaveTime():
    global slaveTime
    try:
        print('Writing to file: '+str(slaveTime.hour)+':'+str(slaveTime.minute)+':'+str(slaveTime.second))
        with open(getScriptPath()+'/.slavetime.txt', 'w') as f:
            #w truncates existing file http://stackoverflow.com/a/2967249
            f.seek(0)
            #Don't worry about leading zeroes, they'll be parsed to ints at read anyway
            f.write(str(slaveTime.hour)+':'+str(slaveTime.minute)+':'+str(slaveTime.second))
            f.truncate()
            #close
    except:
        print('No file written')
#end setStoredSlaveTIme

def impulseSlave():
    global slaveTime
    slaveTime = slaveTime + timedelta(seconds=settings.slaveInterval)
    if settings.piMode:
        GPIO.output(settings.slavePin, GPIO.HIGH)
        time.sleep(settings.slaveImpulse)
        GPIO.output(settings.slavePin, GPIO.LOW)
    else:
        print('Advance clock to '+str(slaveTime.hour)+':'+str(slaveTime.minute)+':'+str(slaveTime.second))

def syncSlave():
    #Synchronous proc to check if slave is in sync, and if not, to wait or advance.
    #Will interrupt main loop, but that's ok, seconds don't move during it anyway.
    global slaveTime
    diff = (slaveTime-datetime.now()).total_seconds()
    print('syncSlave - diff is: '+str(diff))
    if(diff > 0-settings.slaveInterval and diff <= 0): return
    
    #lucyyyyy you got some adjustin' to do
    setMeter(30)
    while (slaveTime-datetime.now()).total_seconds() > -1:
        #the -1 is to avoid advancing the clock as soon as it catches up
        time.sleep(1)
        print('Waiting... diff is '+str((slaveTime-datetime.now()).total_seconds()))
    while (slaveTime-datetime.now()).total_seconds() <= 0-settings.slaveInterval:
        impulseSlave()
        print('Advancing... diff is '+str((slaveTime-datetime.now()).total_seconds()))
        time.sleep(settings.slaveRecover)
#end syncSlave

#Let's go!
try:    
    print("Master clock running. Press Ctrl+C to stop.");
    
    if settings.piMode:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(settings.slavePin, GPIO.OUT)
        if(settings.meterPin != False):
            GPIO.setup(settings.meterPin, GPIO.OUT)
            pwm = GPIO.PWM(settings.meterPin, 50)
            pwm.start(0)
    
    getStoredSlaveTime() #just once per run
    syncSlave()
    
    lastSecond = -1
    while 1:
        #important to snapshot current time, so test and assignment use same time value
        nowTime = datetime.now()
        if lastSecond != nowTime.second:
            lastSecond = nowTime.second
            updateMeter(nowTime.second)
            if(nowTime.second % settings.slaveInterval == 0): impulseSlave()
            if(nowTime.minute == 0 and nowTime.second == 0): syncSlave() #in case of DST changes
        #end if new second
        time.sleep(0.05)
    #end while

except AttributeError: #Easier to ask forgiveness than permission (EAFP) - http://stackoverflow.com/a/610923
    print("\r\nAttributeError. Please ensure your settings.py includes all items from settings-sample.py.")
except KeyboardInterrupt:
    print("\r\nBye!")
# except:
#     print("Error")
finally:
    #TODO how best to deal with undefined variables in finally block
    setStoredSlaveTime() #just once per run
    if settings.piMode:
        if dcLast > 20: #kill the meter softly
            setMeter(0)
        GPIO.output(settings.clockPin, GPIO.LOW)
        pwm.stop()
        GPIO.cleanup()
#end try/except/finally
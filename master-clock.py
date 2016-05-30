#!/usr/bin/env python

#External settings
import settings

#External modules
if settings.piMode: import RPi.GPIO as GPIO
import os #includes path, listdir
import sys
import logging
import time #includes asctime, localtime
import subprocess
from subprocess import call #synchronous
from subprocess import Popen #asynchronous
from datetime import datetime
from datetime import timedelta

#External modules, separately installed
import daemon #via sudo apt-get install python-daemon
#help on this from:
#http://www.gavinj.net/2012/06/building-python-daemon-process.html
#https://www.python.org/dev/peps/pep-3143/

class MasterClock():
    def __init__(self):        
        self.dcLast = 0
        self.slaveTime = datetime.now()
        #This variable will keep (volatile) track of the slave-displayed time.
    
    def convertValueToDC(self,valNew):
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

    def updateMeter(self,valNew):
        #We will probably set it to valNew, but may want to set status instead. TODO
        #if(no network connection): self.setMeter(10)
        #elif(bad ntp): self.setMeter(20)
            #ntpq -c rv | grep "reftime" with result e.g.
            #reftime=dabcecde.167297c4  Sat, Apr 16 2016 11:54:54.087,
            #reftime=00000000.00000000  Sat, Apr 16 2016 11:54:54.087,
        #self.setMeter(30) during active slave setting is taken care of in syncSlave()
        #else:
        self.setMeter(valNew)
    #end def updateMeter

    def setMeter(self,valNew):
        #self.pwm must already have been started
        dcNew = self.convertValueToDC(valNew) #find new dc
        if dcNew > 100: dcNew = 100 #apply range limits
        if dcNew < 0: dcNew = 0
        #set meter, using ballistics if dcChg is great enough
        dcChg = dcNew-self.dcLast
        if settings.piMode:
            if(abs(dcChg) > settings.meterChg): #apply ballistics
                #easing out equations by Robert Penner - gizma.com/easing
                for t in range(1, settings.meterStp+1):
                    #quadratic t^2
                    t /= float(settings.meterStp)
                    nowDC = float(-dcChg) * t * (t-2) + self.dcLast
                    self.pwm.ChangeDutyCycle( nowDC )
                    if(t<settings.meterStp):
                        time.sleep(settings.meterLag)
            else: #just go to there
                self.pwm.ChangeDutyCycle(dcNew)
        #end pi mode
        #self.logger.debug('Set meter to val '+str(valNew)+': from dc '+str(self.dcLast)+' '+str(dcChg)+' to '+str(dcNew))
        self.dcLast = dcNew
    #end def setMeter

    #Slave clock control
    def getStoredSlaveTime(self):
        masterTime = datetime.now()
        #Normalize to the slave clock's interval
        masterTime = masterTime.replace(second=masterTime.second-(masterTime.second % settings.slaveInterval), microsecond=0)
        self.slaveTime = masterTime
        if os.path.exists(settings.slavePath):
            with open(settings.slavePath, 'r') as f:
                #https://docs.python.org/2/tutorial/inputoutput.html
                savedTime = f.read().split(':') #expecting format h:m:s
                #shouldn't be necessary to close
            if(len(savedTime)==3): #validation close enough
                self.slaveTime = self.slaveTime.replace(hour=int(savedTime[0]),minute=int(savedTime[1]),second=int(savedTime[2])-(int(savedTime[2])%settings.slaveInterval))
                self.logger.debug('Read from file: '+str(self.slaveTime.hour)+':'+str(self.slaveTime.minute)+':'+str(self.slaveTime.second))
            else: self.logger.warn('Bad slave time file. Assumed: '+str(self.slaveTime.hour)+':'+str(self.slaveTime.minute)+':'+str(self.slaveTime.second))
        else: self.logger.warn('No slave time file. Assumed: '+str(self.slaveTime.hour)+':'+str(self.slaveTime.minute)+':'+str(self.slaveTime.second))
        #self.slaveTime now gives (presumably) time displayed on slave, always in 24h format
        #If needed, apply offsets to put self.slaveTime within adjusting range of masterTime:
        #masterTime-(slaveHrs-slaveHold) < self.slaveTime <= masterTime+slaveHold
        #We consider slaveHrs because, if slave is 12h, we may assume 3:00 = 15:00 and vice versa

        #if slave is now AHEAD by more than slaveHold, set it back a day
        if (self.slaveTime-masterTime).total_seconds() > settings.slaveHold*3600:
            self.slaveTime = self.slaveTime - timedelta(days=1)

        #if slave is now BEHIND by more than slaveHrs-slaveHold, set it forward slaveHrs
        if (self.slaveTime-masterTime).total_seconds() <= settings.slaveHrs*-3600 + settings.slaveHold*3600:
            self.slaveTime = self.slaveTime + timedelta(hours=settings.slaveHrs)
    #end getStoredSlaveTime

    def setStoredSlaveTime(self):
        try:
            self.logger.debug('Writing to file: '+str(self.slaveTime.hour)+':'+str(self.slaveTime.minute)+':'+str(self.slaveTime.second))
            with open(settings.slavePath, 'w') as f:
                #w truncates existing file http://stackoverflow.com/a/2967249
                f.seek(0)
                #Don't worry about leading zeroes, they'll be parsed to ints at read anyway
                f.write(str(self.slaveTime.hour)+':'+str(self.slaveTime.minute)+':'+str(self.slaveTime.second))
                f.truncate()
                #close
        except:
            self.logger.warn('Could not write slave time to file.')
    #end setStoredSlaveTIme

    def impulseSlave(self,write=True):
        self.slaveTime = self.slaveTime + timedelta(seconds=settings.slaveInterval)
        if settings.piMode:
            GPIO.output(settings.slavePin, GPIO.HIGH)
            time.sleep(settings.slaveImpulse)
            GPIO.output(settings.slavePin, GPIO.LOW)
        #end pi mode
        self.logger.debug('Advance clock to '+str(self.slaveTime.hour)+':'+str(self.slaveTime.minute)+':'+str(self.slaveTime.second))
        if write and settings.slaveWriteRealTime:
            self.setStoredSlaveTime() #store in case of power failure.

    def syncSlave(self):
        #Synchronous proc to check if slave is in sync, and if not, to wait or advance.
        #Will interrupt main loop, but that's ok, seconds don't move during it anyway.
        diff = (self.slaveTime-datetime.now()).total_seconds()
        self.logger.info('syncSlave: diff is: '+str(diff))
        if(diff > 0-settings.slaveInterval and diff <= 0): return

        #lucyyyyy you got some adjustin' to do
        self.setMeter(30)
        while (self.slaveTime-datetime.now()).total_seconds() > -1:
            #the -1 is to avoid advancing the clock as soon as it catches up
            time.sleep(1)
            #self.logger.debug('Waiting... diff is '+str((self.slaveTime-datetime.now()).total_seconds()))
        while (self.slaveTime-datetime.now()).total_seconds() <= 0-settings.slaveInterval:
            self.impulseSlave(False) #don't write to file for each advance
            #self.logger.debug('Advancing... diff is '+str((self.slaveTime-datetime.now()).total_seconds()))
            time.sleep(settings.slaveRecover)
        self.logger.info('syncSlave: sync complete.');
        if settings.slaveWriteRealTime:
            self.setStoredSlaveTime()
    #end syncSlave
    
    def run(self):
        #Let's go!
        self.logger = logging.getLogger("DaemonLog")
        if(settings.logDebug):
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        handler = logging.FileHandler(settings.logPath)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        if settings.piMode:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(settings.slavePin, GPIO.OUT)
            if(settings.meterPin != False):
                GPIO.setup(settings.meterPin, GPIO.OUT)
                self.pwm = GPIO.PWM(settings.meterPin, 50)
                self.pwm.start(0)
        #end pi mode
        
        try:    
            self.logger.info("Master clock start. ********************");
    
            self.getStoredSlaveTime() #just once per run
            self.syncSlave()
    
            lastSecond = -1
            while 1:
                #important to snapshot current time, so test and assignment use same time value
                nowTime = datetime.now()
                if lastSecond != nowTime.second:
                    lastSecond = nowTime.second
                    #TODO: fight! fight! fight! clock or meter first?
                    if(nowTime.second % settings.slaveInterval == 0): self.impulseSlave()
                    if(nowTime.minute == 0 and nowTime.second == 0): self.syncSlave() #in case of DST changes
                    self.updateMeter(nowTime.second)
                #end if new second
                time.sleep(0.05)
            #end while

        finally:
            self.logger.info('Master clock stop. ....................');
            self.logger.exception('')
            self.setStoredSlaveTime()
            if settings.piMode:
                if self.dcLast > 20: #kill the meter softly
                    self.setMeter(0)
                GPIO.output(settings.slavePin, GPIO.LOW)
                self.pwm.stop()
                GPIO.cleanup()
            #end pi mode
        #end try/except/finally
    #end def run
#end class MasterClock

masterClock = MasterClock()
with daemon.DaemonContext():    
    masterClock.run()
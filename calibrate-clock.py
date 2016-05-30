#!/usr/bin/env python

print("Use this script to tell master-clock what time your slave clock displays.")
print("Type Ctrl+C to cancel.");

#External settings
import settings

#External modules
import os
import sys

#def getScriptPath():
#    # http://stackoverflow.com/a/4943474
#    return os.path.dirname(os.path.realpath(sys.argv[0]))
    
def getTimeInput(label,maxVal):
    while 1:
        try:
            newVal = int(input(label))
            if(newVal < 0 or newVal > maxVal):
                print "Please enter a number betwen 0 and "+str(maxVal)+"."
                continue
            break #it was fine
        except KeyboardInterrupt:
            print "\r\nOk bye."
            exit()
        except:
            print "Something's wrong with what you input. Please try again."
    return newVal

newHr  = getTimeInput('Enter hour (0-23): ',23)
newMin = getTimeInput('Enter minute (0-59): ',59)
newSec = getTimeInput('Enter second (0-59): ',59)
try:
    #print('Writing to file: '+str(slaveTime.hour)+':'+str(slaveTime.minute)+':'+str(slaveTime.second))
    with open(settings.slavePath, 'w') as f:
        #w truncates existing file http://stackoverflow.com/a/2967249
        f.seek(0)
        #Don't worry about leading zeroes, they'll be parsed to ints at read anyway
        f.write(str(newHr)+':'+str(newMin)+':'+str(newSec))
        f.truncate()
        #close
        print "Time saved."
except:
    print('Problem writing to file. If you want to do it manually, create/edit .slavetime.txt and enter time in format h:m:s')
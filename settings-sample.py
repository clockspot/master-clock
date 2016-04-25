# Running mode. If true, it outputs to GPIO; if false, it outputs to stdout (for dev/debugging).
piMode = False

# Slave clock control
slavePin = 20 #Broadcom pin ID
slaveInterval = 30 #seconds between impulses (normal operation, includes impulse duration)
slaveImpulse = 0.2 #seconds impulse duration
slaveRecover = 0.3 #seconds between impulses (fast forwarding, excludes impulse duration)
slaveHrs = 12 #Is it a 12-hour or 24-hour display?
#slaveIsBipolar = False #TODO support this with two GPIO pins
slaveHold = 2 #If the slave is no more than X hours ahead (disregarding date), wait for real time to catch up, instead of advancing all the way around. If your slave displays the day/date (e.g. Solari Emera/Dator), you may prefer to set this to 0, as the slave is unlikely to get ahead of real time (without being set forward manually).

# Seconds/status meter control
meterPin = 18 #Broadcom pin ID that supports PWM - set to False if you have no meter
# Meter calibration points, display value vs PWM duty cycle value. Use calibrate-meter.py to find points for your meter. This also defines the range of your meter scale. (If it starts at zero, you can omit (0,0); it will be assumed.)
meterCal = [(59,94)] #This default defines a 60-second scale, more or less, on a 3VDC meter (since Pi GPIO is 3.3V).
# Meter ballistics: when making a relatively large change to the meter display, quadratic easing is applied to prevent the needle from moving too violently (pegging, wobbling)
meterChg = 10 #min change in pwm duty cycle that will trigger ballistics
meterStp = 4 #apply ballistics in this many steps
meterLag = 0.18 #seconds between ballistics steps
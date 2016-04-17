# master-clock
Use your Raspberry Pi to drive impulse slave clocks and moving-coil galvanometers. Companion to [carillon](https://github.com/clockspot/carillon).

## What's it do?
**Time-of-day display.** Using a standard GPIO pin, master-clock will output a signal to control an amplifier circuit to drive an impulse slave clock(s). Once you've told it what time the clock is displaying, it will keep its own nonvolatile record of the displayed time, and will advance the clock in keeping with the system clock (itself synced via `ntpd` ideally). It will also advance the clock quickly to reset in case of power loss, DST changes, you stopped the daemon to watch a movie undisturbed, etc.

**Seconds and status display.** Using a GPIO pin that supports pulse-width modulation, it will control the PWM duty cycle to directly control a 3VDC moving-coil galvanometer. It includes ballistics control to move the needle quickly but gently, and (hopefully) never cause it to peg violently.

## Why?
I got a harebrained scheme to build an indoor carillon in two loosely-coupled parts:

* **the Clock,** a Raspberry Pi living inside and controlling a 1960s Gents slave clock, synced to NTP (via `ntpd`), and outputting MIDI (via `amidi` and `aplaymidi`) on schedule (see companion project (see [carillon](https://github.com/clockspot/carillon)); and
* **the Bells**, a small glockenspiel rigged with solenoids wired up to [a purpose-made MIDI decoder card from Orgautomatech](http://www.orgautomatech.com/), receiving MIDI from the Clock.

Because the only link between the Clock and Bells is MIDI, the Clock can control other MIDI instruments, and the Bells can be played with other MIDI controllers.

## How to use
* **Make your settings file** `settings.py` as a copy of `settings-sample.py`, and adjust accordingly.
* **Set up the moving-coil meter.** If you like, replace or modify the dial with a seconds scale (on a 3VDC meter scale, each 0.5V corresponds to 10 seconds). Run `meterCalibrate.py` to find good calibration points – that is, find the input values that make the needle point to N seconds on the scale. At minimum, you need a point at the max end of the scale (59 seconds), but as your meter probably won't have a perfectly linear response, you can pick more points along the scale as needed to fine-tune it.
* **Build the amplifier circuit** and attach to your clock. If you don't have one yet, you can connect an LED in its place for testing.
* Then *[TODO: insert method of starting daemon here]*.
* The meter will display as follows *[TODO]*:
  * Daemon not running: 0s
  * No network connection: 10s
  * No confirmed NTP sync: 20s
  * Slave clock is being adjusted: 30s
  * Normal: running seconds

## Best-laid plans
* Become a daemon
* Admin via web console?
* Details on hardware construction of amplifier circuit

## Files herein
* **masterclock.py** - *Coming soon.* Where the magic happens.
* **settings-sample.py** - Duplicate/rename this to **settings.py** and edit accordingly.
* **meterCalibrate.py** - Use this to calibrate your 3VDC meter.
* **clockCalibrate.py** - *Coming soon.* Use this to tell the Pi what time your slave clock reads (in case it runs, but is wrong).

## Credit where due!
* [Make an Atom Synchronised Clock from a 1950s Slave Clock on Instructables](http://www.instructables.com/id/Make-an-Atom-Synchronised-Clock-from-a-1950s-Slav/)
# master-clock
Drive impulse slave clocks and voltmeters with a Raspberry Pi. Companion to [carillon](https://github.com/clockspot/carillon).

## What's it do?
**Time-of-day display.** Using a standard GPIO pin, master-clock will output a signal to control an amplifier circuit to drive an impulse slave clock(s). It will keep its own nonvolatile record of the displayed time, and will keep the clock in sync with the system clock (itself synced via `ntpd` ideally). It will also fast-forward the clock in case of power loss, DST changes, you stopped the daemon to watch a movie undisturbed, etc.

**Seconds and status display.** Using a GPIO pin that supports pulse-width modulation, it will control the PWM duty cycle to directly control a 3VDC voltmeter. It includes ballistics control to move the needle quickly but gently, and (hopefully) never cause it to peg violently.

## Why?
I got a harebrained scheme to build an indoor carillon in two loosely-coupled parts:

* **the Clock,** a Raspberry Pi living inside and controlling a 1960s Gents slave clock, synced to NTP (via `ntpd`), and outputting MIDI (via `amidi` and `aplaymidi`) on schedule (see companion project [carillon](https://github.com/clockspot/carillon)); and
* **the Bells**, a small glockenspiel rigged with solenoids wired up to [a purpose-made MIDI decoder card from Orgautomatech](http://www.orgautomatech.com/), receiving MIDI from the Clock.

Because the only link between the Clock and Bells is MIDI, the Clock can control other MIDI instruments, and the Bells can be played with other MIDI controllers.

## How to use
* **Install packages** if not present: `python`, `python-daemon`
* **Make settings file** `settings.py` as a copy of `settings-sample.py`, and modify to suit. Other instructions within (e.g. file permissions).
* **Set up the voltmeter.** If you like, replace or modify the dial with a seconds scale (on a 3VDC meter scale, each 0.5V corresponds to 10 seconds). Run `calibrate-meter.py` to find good calibration points – that is, find the input values that make the needle point to N seconds on the scale. At minimum, you need a point at the max end of the scale (59 seconds), but as your meter probably won't have a perfectly linear response, you can pick more points along the scale as needed to fine-tune it.
* **Build the amplifier circuit** ([example](http://www.instructables.com/id/Make-an-Atom-Synchronised-Clock-from-a-1950s-Slav/)) and attach to your clock. Run `calibrate-clock.py` to tell master-clock what time the clock is displaying. If you don't have one yet, you can connect an LED+resistor in its place for testing. Run `test-clock.py` to test impulses of various lengths to the clock pin.
* Run the script, e.g. `./master-clock.py`, directly or at startup. It will detach from the shell and run as a daemon. No start/stop service controls just yet; for now, stop it via e.g. `pkill -f master-clock`.
* The meter will display as follows:
  * Daemon not running: 0s
  * *[TODO]* No network connection: 10s
  * *[TODO]* No confirmed NTP sync: 20s
  * Slave clock is being adjusted: 30s
  * Normal: running seconds

## Files herein
* `master-clock.py` - Where the magic happens.
* `settings-sample.py` - Duplicate/rename this to `settings.py` and edit accordingly.
* `calibrate-meter.py` - Use this to calibrate your 3VDC meter.
* `calibrate-clock.py` - Use this to tell master-clock what time your slave clock reads.
* `test-clock.py` - Use this to manually impulse the clock pin and find the right duration.

## Best-laid plans
* Admin via web console?
* Details on hardware construction of amplifier circuit

## Credit where due!
* [Make an Atom Synchronised Clock from a 1950s Slave Clock on Instructables](http://www.instructables.com/id/Make-an-Atom-Synchronised-Clock-from-a-1950s-Slav/)
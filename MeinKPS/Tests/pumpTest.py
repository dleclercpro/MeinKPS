#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    pumpTest

    Author:   David Leclerc

    Version:  0.1

    Date:     13.01.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that tests all of the pump commands stored in the
              pump.py script.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import sys
import time
import datetime
import json



# PATHS
sys.path.append("/home/pi/MeinKPS/MeinKPS")



# USER LIBRARIES
import pump



# CONSTANTS
sleep = 5



# MAIN

# Instanciate a pump for me
myPump = pump.Pump()

# Start dialogue with pump
myPump.start()

# Read pump time
myPump.time.read()
time.sleep(sleep)

# Read pump model
myPump.model.read()
time.sleep(sleep)

# Read pump firmware version
myPump.firmware.read()
time.sleep(sleep)

# Read pump battery level
myPump.battery.read()
time.sleep(sleep)

# Read remaining amount of insulin in pump
myPump.reservoir.read()
time.sleep(sleep)

# Read pump status
myPump.status.read()
time.sleep(sleep)
myPump.status.verify()
time.sleep(sleep)
myPump.status.suspend()
time.sleep(sleep)
myPump.status.resume()
time.sleep(sleep)

# Read pump settings
myPump.settings.read()
time.sleep(sleep)
myPump.settings.verify()
time.sleep(sleep)

# Read daily totals on pump
myPump.dailyTotals.read()
time.sleep(sleep)

# Read BG units set in pump's bolus wizard
myPump.units.BG.read()
time.sleep(sleep)

# Read carb units set in pump's bolus wizard
myPump.units.C.read()
time.sleep(sleep)

# Read current TBR units
myPump.units.TBR.read()
time.sleep(sleep)

# Read blood glucose targets stored in pump
myPump.BGTargets.read()
time.sleep(sleep)

# Read pump history
myPump.history.read()
time.sleep(sleep)

# Read insulin sensitivity factors stored in pump
myPump.ISF.read()
time.sleep(sleep)

# Read carb sensitivity factors stored in pump
myPump.CSF.read()
time.sleep(sleep)

# Read boluses from pump history
myPump.boluses.read()
time.sleep(sleep)

# Read carbs from pump history
myPump.carbs.read()
time.sleep(sleep)

# Send bolus to pump
myPump.boluses.deliver(0.1)
time.sleep(sleep)

# Read current TBR
myPump.TBR.read()
time.sleep(sleep)

# Send TBR to pump
myPump.TBR.set(5, "U/h", 30)
time.sleep(sleep)
myPump.TBR.set(50, "%", 90)
time.sleep(sleep)
myPump.TBR.cancel()
time.sleep(sleep)

# Push button on pump
myPump.buttons.push("EASY")
myPump.buttons.push("ESC")
myPump.buttons.push("ACT")
myPump.buttons.push("DOWN")
myPump.buttons.push("UP")

# Stop dialogue with pump
myPump.stop()

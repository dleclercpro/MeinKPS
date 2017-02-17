#! /usr/bin/python

"""
================================================================================

    Title:    pumpTest

    Author:   David Leclerc

    Version:  0.1

    Date:     13.01.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that tests all of the pump commands stored in the
              pump.py script.

    Notes:    ...

================================================================================
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

# Start dialogue pump
myPump.start()

# Read bolus history of pump
myPump.readTime()
time.sleep(sleep)

# Read pump model
myPump.readModel()
time.sleep(sleep)

# Read pump firmware version
myPump.readFirmwareVersion()
time.sleep(sleep)

# Read remaining amount of insulin in pump
myPump.readReservoirLevel()
time.sleep(sleep)

# Read pump status
myPump.readStatus()
time.sleep(sleep)

# Read pump settings
myPump.readSettings()
time.sleep(sleep)

# Read daily totals on pump
myPump.readDailyTotals()
time.sleep(sleep)

# Read current history page number
myPump.readNumberHistoryPages()
time.sleep(sleep)

# Read treatment history on pump (BG and carbs)
myPump.readTreatments()
time.sleep(sleep)

# Send bolus to pump
myPump.deliverBolus(0.1)
time.sleep(sleep)

# Read temporary basal
myPump.readCurrentTBR()
time.sleep(sleep)

# Send temporary basal to pump
myPump.setTBR(5, "U/h", 30)
time.sleep(sleep)
myPump.setTBR(200, "%", 60)
time.sleep(sleep)

# Read insulin sensitivity factors stored in pump
myPump.readInsulinSensitivityFactors()
time.sleep(sleep)

# Read carb sensitivity factors stored in pump
myPump.readCarbSensitivityFactors()
time.sleep(sleep)

# Read blood glucose targets stored in pump
myPump.readBGTargets()
time.sleep(sleep)

# Suspend pump activity
myPump.suspend()
time.sleep(sleep)

# Resume pump activity
myPump.resume()
time.sleep(sleep)

# Push button on pump
myPump.pushButton("DOWN")
time.sleep(sleep)

# Stop dialogue with pump
myPump.stop()

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



# USER LIBRARIES
import lib



# CONSTANTS
sleep = 5



# MAIN
# Instanciate a pump for me
pump = Pump()

# Start dialogue pump
pump.start()

# Read bolus history of pump
pump.readTime()
time.sleep(sleep)

# Read pump model
pump.readModel()
time.sleep(sleep)

# Read pump firmware version
pump.readFirmwareVersion()
time.sleep(sleep)

# Read remaining amount of insulin in pump
pump.readReservoirLevel()
time.sleep(sleep)

# Read pump status
pump.readStatus()
time.sleep(sleep)

# Read pump settings
pump.readSettings()
time.sleep(sleep)

# Read daily totals on pump
pump.readDailyTotals()
time.sleep(sleep)

# Read current history page number
pump.readNumberHistoryPages()
time.sleep(sleep)

# Read bolus history on pump
pump.readBoluses()
time.sleep(sleep)

# Send bolus to pump
pump.deliverBolus(0.1)
time.sleep(sleep)

# Read temporary basal
pump.readTemporaryBasal()
time.sleep(sleep)

# Send temporary basal to pump
pump.setTemporaryBasal(5, "U/h", 30)
time.sleep(sleep)
pump.setTemporaryBasal(200, "%", 60)
time.sleep(sleep)

# Read insulin sensitivity factors stored in pump
pump.readInsulinSensitivityFactors()
time.sleep(sleep)

# Read carb sensitivity factors stored in pump
pump.readCarbSensitivityFactors()
time.sleep(sleep)

# Read blood glucose targets stored in pump
pump.readBGTargets()
time.sleep(sleep)

# Suspend pump activity
pump.suspend()
time.sleep(sleep)

# Resume pump activity
pump.resume()
time.sleep(sleep)

# Push button on pump
pump.pushButton("DOWN")
time.sleep(sleep)

# Stop dialogue with pump
pump.stop()

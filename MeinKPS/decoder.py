#! /usr/bin/python

"""
================================================================================

    Title:    decoder

    Author:   David Leclerc

    Version:  0.1

    Date:     18.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that decoding functions for all devices used
              within MeinKPS.

    Notes:    ...

================================================================================
"""

# LIBRARIES
import datetime



# USER LIBRARIES
import lib



class Decoder:

    # DECODER CHARACTERISTICS



    def decode(self, device, command):

        """
        ========================================================================
        DECODE
        ========================================================================
        """

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READTIME                                                             #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        if command == "readTime":

            # Extract pump time from received data
            second = device.requester.data[2]
            minute = device.requester.data[1]
            hour   = device.requester.data[0]
            day    = device.requester.data[6]
            month  = device.requester.data[5]
            year   = lib.bangInt(device.requester.data[3:5])

            # Generate time object
            time = datetime.datetime(year, month, day, hour, minute, second)

            # Store formatted time
            device.time = lib.formatTime(time)



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READMODEL                                                            #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readModel":

            # Extract pump model from received data
            device.model = int("".join(
                [chr(x) for x in device.requester.data[1:4]]))



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READFIRMWARE                                                         #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readFirmware":

            # Extract pump firmware from received data
            device.firmware = ("".join(device.requester.responseChr[17:21]) +
                         " " + "".join(device.requester.responseChr[21:24]))



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READBATTERYLEVEL                                                     #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readBatteryLevel":

            # Decode battery level
            level = device.requester.data[0]

            if level == 0:
                device.batteryLevel = "Normal"
            elif level == 1:
                device.batteryLevel = "Low"

            # Decode battery voltage
            device.batteryVoltage = round(
                lib.bangInt([device.requester.data[1],
                device.requester.data[2]]) / 100.0, 1)



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READRESERVOIRLEVEL                                                   #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readReservoirLevel":

            # Decode remaining amount of insulin
            device.reservoir = (lib.bangInt(device.requester.data[0:2]) *
                                device.bolusStroke)

            # Round amount
            device.reservoir = round(device.reservoir, 1)



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READSTATUS                                                           #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readStatus":

            # Extract pump status from received data
            device.status = {"Normal" : device.requester.data[0] == 3,
                           "Bolusing" : device.requester.data[1] == 1,
                           "Suspended" : device.requester.data[2] == 1}



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READSETTINGS                                                         #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readSettings":

            # Extract pump settings from received data
            device.settings = {
                "IAC": device.requester.data[17],
                "Max Bolus": device.requester.data[5] * device.bolusStroke,
                "Max Basal": (lib.bangInt(device.requester.data[6:8]) *
                              device.basalStroke / 2.0)}



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READBGU                                                              #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readBGU":

            # Decode BG units set on pump
            units = device.requester.data[0]

            if units == 1:
                device.BGU = "mg/dL"

            elif units == 2:
                device.BGU = "mmol/L"



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READCU                                                               #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readCU":

            # Decode carb units set on pump
            units = device.requester.data[0]
            
            if units == 1:
                device.BGU = "g"

            elif units == 2:
                device.BGU = "exchanges"



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READDAILYTOTALS                                                      #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readDailyTotals":

            # Extract daily totals of today and yesterday
            device.dailyTotals["Today"] = round(
                lib.bangInt(device.requester.data[0:2]) * device.bolusStroke, 2)

            # Extract daily totals of yesterday
            device.dailyTotals["Yesterday"] = round(
                lib.bangInt(device.requester.data[2:4]) * device.bolusStroke, 2)



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READBGTARGETS                                                        #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readBGTargets":

            # Extract carb sensitivity units
            units = device.requester.data[0]

            # Decode units
            if units == 1:
                device.BGU = "mg/dL"

                # Define a multiplicator to decode ISF bytes
                m = 0

            elif units == 2:
                device.BGU = "mmol/L"

                # Define a multiplicator to decode ISF bytes
                m = 1.0

            # Initialize index as well as targets and times vectors
            i = 0
            targets = []
            times = []

            # Extract BG targets
            while True:

                # Define start (a) and end (b) indexes of current factor based
                # on number of bytes per entry
                n = 3
                a = 2 + n * i
                b = a + n

                # Get current target entry
                entry = device.requester.data[a:b]

                # Exit condition: no more targets stored
                if not sum(entry):
                    break

                else:
                    # Decode entry
                    target = [entry[0] / 10 ** m, entry[1] / 10 ** m]
                    time = entry[2] * 30 # Get time in minutes (each block
                                         # corresponds to 30 m)

                    # Format time
                    time = (str(time / 60).zfill(2) + ":" +
                            str(time % 60).zfill(2))

                    # Store decoded target and its corresponding ending time
                    targets.append(target)
                    times.append(time)

                # Increment index
                i += 1

            # Rearrange targets to have starting times instead of ending times
            for i in range(len(targets)):
                device.BGTargets.append(targets[i])
                device.BGTargetsTimes.append(times[i - 1])



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READISF                                                              #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readISF":

            # Extract insulin sensitivity units
            units = device.requester.data[0]

            # Decode units
            if units == 1:
                device.ISU = "mg/dL/U"
                device.BGU = "mg/dL"
                
                # Define a multiplicator to decode ISF bytes
                m = 0

            elif units == 2:
                device.ISU = "mmol/L/U"
                device.BGU = "mmol/L"

                # Define a multiplicator to decode ISF bytes
                m = 1.0

            # Initialize index as well as factors and times vectors
            i = 0
            factors = []
            times = []

            # Extract insulin sensitivity factors
            while True:

                # Define start (a) and end (b) indexes of current factor based
                # on number of bytes per entry
                n = 2
                a = 2 + n * i
                b = a + n

                # Get current factor entry
                entry = device.requester.data[a:b]

                # Exit condition: no more factors stored
                if not sum(entry):
                    break

                else:
                    # Decode entry
                    factor = entry[0] / 10 ** m
                    time = entry[1] * 30 # Get time in minutes (each block
                                         # corresponds to 30 m)

                    # Format time
                    time = (str(time / 60).zfill(2) + ":" +
                            str(time % 60).zfill(2))

                    # Store decoded factor and its corresponding ending time
                    factors.append(factor)
                    times.append(time)

                # Increment index
                i += 1

            # Rearrange factors to have starting times instead of ending times
            for i in range(len(factors)):
                device.ISF.append(factors[i])
                device.ISFTimes.append(times[i - 1])



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READCSF                                                              #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readCSF":

            # Extract carb sensitivity units
            units = device.requester.data[0]

            # Decode units
            if units == 1:
                device.CSU = "g/U"
                device.CU = "g"

                # Define a multiplicator to decode ISF bytes
                m = 0

            elif units == 2:
                device.CSU = "exchanges/U"
                device.CU = "exchanges"

                # Define a multiplicator to decode ISF bytes
                m = 1.0

            # Initialize index as well as factors and times vectors
            i = 0
            factors = []
            times = []

            # Extract carb sensitivity factors
            while True:

                # Define start (a) and end (b) indexes of current factor based on
                # number of bytes per entry
                n = 2
                a = 2 + n * i
                b = a + n

                # Get current factor entry
                entry = device.requester.data[a:b]

                # Exit condition: no more factors stored
                if not sum(entry):
                    break

                else:
                    # Decode entry
                    factor = entry[0] / 10 ** m
                    time = entry[1] * 30 # Get time in minutes (each block
                                         # corresponds to 30 m)

                    # Format time
                    time = (str(time / 60).zfill(2) + ":" +
                            str(time % 60).zfill(2))

                    # Store decoded factor and its corresponding ending time
                    factors.append(factor)
                    times.append(time)

                # Increment index
                i += 1

            # Rearrange factors to have starting times instead of ending times
            for i in range(len(factors)):
                device.CSF.append(factors[i])
                device.CSFTimes.append(times[i - 1])



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READNUMBERHISTORYPAGES                                               #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readNumberHistoryPages":

            # Store number of history pages
            device.nHistoryPages = device.requester.data[3] + 1



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # READTBR                                                              #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        elif command == "readTBR":

            units = device.requester.data[0]

            # Extract TBR [U/h]
            if units == 0:

                # Extract characteristics
                device.TBR["Units"] = "U/h"
                device.TBR["Value"] = round(
                    lib.bangInt(device.requester.data[2:4]) *
                    device.basalStroke / 2.0, 2)

            # Extract TBR [%]
            elif units == 1:

                # Extract characteristics
                device.TBR["Units"] = "%"
                device.TBR["Value"] = round(device.requester.data[1], 2)

            # Extract remaining time
            device.TBR["Duration"] = round(
                lib.bangInt(device.requester.data[4:6]), 0)



    def decodeBolusWizardRecord(self, device, code, headSize, dateSize,
                                      bodySize):

        """
        ========================================================================
        DECODEBOLUSWIZARDRECORD
        ========================================================================
        """

        # Read current time
        now = datetime.datetime.now()

        # Define an indicator dictionary to decode BG and carb bytes
        # <i>: [<BGU>, <CU>, <larger BG>, <larger C>]
        indicators = {80: ["mg/dL", "g", False, False],
                      82: ["mg/dL", "g", True, False],
                      84: ["mg/dL", "g", False, True],
                      86: ["mg/dL", "g", True, True],
                      96: ["mg/dL", "exchanges", False, False],
                      98: ["mg/dL", "exchanges", True, False],
                      144: ["mmol/L", "g", False, False],
                      145: ["mmol/L", "g", True, False],
                      148: ["mmol/L", "g", False, True],
                      149: ["mmol/L", "g", True, True],
                      160: ["mmol/L", "exchanges", False, False],
                      161: ["mmol/L", "exchanges", True, False]}

        # Search history for specified record
        for i in range(len(device.history)):

            # Try and find bolus wizard records
            try:

                # Look for code, with which every record should start
                if device.history[i] == code:

                    # Define a record running variable
                    x = i
            
                    # Assign record head
                    head = device.history[x:x + headSize]

                    # Update running variable
                    x += headSize

                    # Assign record date
                    date = device.history[x:x + dateSize]

                    # Update running variable
                    x += dateSize

                    # Assign record body
                    body = device.history[x:x + bodySize]

                    # Decode time using date bytes
                    time = lib.decodeTime(date)

                    # Build datetime object
                    time = datetime.datetime(time[0], time[1], time[2],
                                             time[3], time[4], time[5])

                    # Proof record year
                    if abs(time.year - now.year) > 1:

                        raise ValueError("Record and current year too far " +
                                         "apart!")

                    # Format time
                    time = lib.formatTime(time)

                    # Decode units and sizes of BG and carb entries using 2nd
                    # body byte as indicator linked with the previously
                    # defined dictionary
                    [BGU, CU, largerBG, largerC] = indicators[body[1]]

                    # Define rounding multiplicator for BGs and Cs
                    if BGU == "mmol/L":
                        mBGU = 1.0

                    elif BGU == "mg/dL":
                        mBGU = 0

                    if CU == "exchanges":
                        mCU = 1.0

                    elif CU == "g":
                        mCU = 0

                    # Define number of bytes to add for larger BGs and Cs
                    if largerBG:
                        
                        # Extra number of bytes depends on BG units
                        if BGU == "mmol/L":
                            mBG = 256

                        elif BGU == "mg/dL":
                            mBG = 512

                    else:
                        mBG = 0

                    if largerC:
                        mC = 256

                    else:
                        mC = 0

                    # Decode record
                    BG = (head[1] + mBG) / 10 ** mBGU
                    C = (body[0] + mC) / 10 ** mCU

                    # Not really necessary, but those are correct
                    BGTargets = [body[4] / 10 ** mBGU, body[12] / 10 ** mBGU]
                    CSF = body[2] / 10 ** mCU

                    # Add carbs and times at which they were consumed to their
                    # respective vectors only if they have a given value!
                    if C:
                        device.carbs.append([C, CU])
                        device.carbTimes.append(time)

                    # Give user output
                    #print "Time: " + time
                    #print "Response: " + str(head) + ", " + str(body)
                    #print "BG: " + str(BG) + " " + str(BGU)
                    #print "Carbs: " + str(C) + " " + str(CU)
                    #print "BG Targets: " + str(BGTargets) + " " + str(BGU)
                    #print "CSF: " + str(CSF) + " " + str(CU) + "/U"
                    #print

            except:
                pass



    def decodeBolusRecord(self, device, code, size):

        """
        ========================================================================
        DECODEBOLUSRECORD
        ========================================================================
        """

        # Read current time
        now = datetime.datetime.now()

        # Search history for specified record
        for i in range(len(device.history)):

            # Try and find bolus records
            try:

                # Define bolus criteria
                if ((device.history[i] == code) and
                    (device.history[i + 1] == device.history[i + 2]) and
                    (device.history[i + 3] == 0)):
            
                    # Extract bolus from pump history
                    bolus = round(device.history[i + 1] * device.bolusStroke, 1)

                    # Extract time at which bolus was delivered
                    time = lib.decodeTime(device.history[i + 4 : i + 9])

                    # Check for bolus year
                    if abs(time[0] - now.year) > 1:

                        raise ValueError("Bolus can't be more than one year " +
                                         "in the past!")

                    # Build datetime object
                    time = datetime.datetime(time[0], time[1], time[2],
                                             time[3], time[4], time[5])

                    # Format bolus time
                    time = lib.formatTime(time)

                    # Give user info
                    #print "Bolus read: " + str(bolus) + "U (" + time + ")"
                    
                    # Store bolus
                    device.boluses.append(bolus)
                    device.bolusTimes.append(time)

            except:
                pass



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    #print command.__class__.__name__



# Run this when script is called from terminal
if __name__ == "__main__":
    main()

#! /usr/bin/python

"""
================================================================================

    Title:    decoder

    Author:   David Leclerc

    Version:  0.1

    Date:     18.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that decodes the bytes constituting every
              response to every device request defined and sent by MeinKPS.

    Notes:    ...

================================================================================
"""

# LIBRARIES
import datetime



# USER LIBRARIES
import lib



class Decoder:

    def __init__(self, device, part):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give the decoder a device from which to read bytes
        self.device = device

        # Give the decoder a part of the device to which the previously decoded
        # information should be stored
        self.part = part



    def decode(self, command):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get device's response
        response = self.device.requester.response
        responseHex = self.device.requester.responseHex
        responseChr = self.device.requester.responseChr

        # Get device's data
        data = self.device.requester.data



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READINFOS
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if command == "readInfos":

            # Decode infos
            ACK = response[0]
            status = responseChr[1]
            description = "".join(responseChr[9:19])
            frequency = str(self.device.frequencies[response[8]]) + " MHz"
            version = 1.00 * response[19] + 0.01 * response[20]

            # Store infos
            self.device.infos["ACK"] = ACK
            self.device.infos["Status"] = status
            self.device.infos["Description"] = description
            self.device.infos["Version"] = version
            self.device.infos["Frequency"] = frequency



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READSIGNALSTRENGTH
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readSignalStrength":

            # Decode strength of signal
            self.device.signal = response[3]



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READUSBSTATE / READRADIOSTATE
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif (command == "readUSBState") or (command == "readRadioState"):

            # Define stick's interface for which state infos will be decoded
            if command == "readUSBState":
                i = "USB"

            elif command == "readRadioState":
                i = "Radio"

            # Decode state
            errorCRC = response[3]
            errorSEQ = response[4]
            errorNAK = response[5]
            errorTimeout = response[6]
            packetsReceived = lib.convertBytes(response[7:11])
            packetsSent = lib.convertBytes(response[11:15])

            # Store state
            self.device.state[i]["Errors"]["CRC"] = errorCRC
            self.device.state[i]["Errors"]["SEQ"] = errorSEQ
            self.device.state[i]["Errors"]["NAK"] = errorNAK
            self.device.state[i]["Errors"]["Timeout"] = errorTimeout
            self.device.state[i]["Packets"]["Received"] = packetsReceived
            self.device.state[i]["Packets"]["Sent"] = packetsSent



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READTIME
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readTime":

            # Decode pump time
            second = data[2]
            minute = data[1]
            hour   = data[0]
            day    = data[6]
            month  = data[5]
            year   = lib.bangInt(data[3:5])

            # Generate time object
            time = datetime.datetime(year, month, day, hour, minute, second)

            # Store formatted time
            self.part.value = lib.formatTime(time)



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READMODEL
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readModel":

            # Decode pump model
            self.part.value = int("".join([chr(x) for x in data[1:4]]))



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READFIRMWARE
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readFirmware":

            # Decode pump firmware
            self.part.value = ("".join(responseChr[17:21]) +
                               " " + "".join(responseChr[21:24]))



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READBATTERYLEVEL
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readBatteryLevel":

            # Decode battery level
            level = data[0]

            if level == 0:
                self.part.level = "Normal"
            elif level == 1:
                self.part.level = "Low"

            # Decode battery voltage
            self.part.voltage = round(lib.bangInt([data[1], data[2]]) / 100.0,
                                      1)



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READRESERVOIRLEVEL
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readReservoirLevel":

            # Decode remaining amount of insulin
            self.part.value = round(lib.bangInt(data[0:2]) *
                                    self.device.bolusStroke, 1)



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READSTATUS
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readStatus":

            # Extract pump status from received data
            self.part.value = {"Normal" : data[0] == 3,
                               "Bolusing" : data[1] == 1,
                               "Suspended" : data[2] == 1}



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READSETTINGS
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readSettings":

            # Decode pump settings
            self.part.values = {
                "IAC": data[17],
                "Max Bolus": data[5] * self.device.bolusStroke,
                "Max Basal": (lib.bangInt(data[6:8]) *
                              self.device.basalStroke / 2.0)}



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READBGU
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readBGU":

            # Decode BG units set on pump
            units = data[0]

            if units == 1:
                self.part.value = "mg/dL"

            elif units == 2:
                self.part.value = "mmol/L"



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READCU
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readCU":

            # Decode carb units set on pump
            units = data[0]
            
            if units == 1:
                self.part.value = "g"

            elif units == 2:
                self.part.value = "exchanges"



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READDAILYTOTALS
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readDailyTotals":

            # Decode daily totals
            self.part.value = {"Today": round(lib.bangInt(data[0:2]) *
                                              self.device.bolusStroke, 2),
                               "Yesterday": round(lib.bangInt(data[2:4]) *
                                                  self.device.bolusStroke, 2)}



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READBGTARGETS
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readBGTargets":

            # Extract carb sensitivity units
            units = data[0]

            # Decode units
            if units == 1:
                self.part.units = "mg/dL"

                # Define a multiplicator to decode ISF bytes
                m = 0

            elif units == 2:
                self.part.units = "mmol/L"

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
                entry = data[a:b]

                # Exit condition: no more targets stored
                if not sum(entry):
                    break

                else:
                    # Decode entry
                    target = [entry[0] / 10 ** m, entry[1] / 10 ** m]
                    time = entry[2] * self.device.timeBlock

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
                self.part.values.append(targets[i])
                self.part.times.append(times[i - 1])



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READNUMBERHISTORYPAGES
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readNumberHistoryPages":

            # Decode and store number of history pages
            self.part.size = data[3] + 1



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READISF
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readISF":

            # Extract insulin sensitivity units
            units = data[0]

            # Decode units
            if units == 1:
                self.part.units = "mg/dL"
                
                # Define a multiplicator to decode ISF bytes
                m = 0

            elif units == 2:
                self.part.units = "mmol/L"

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
                entry = data[a:b]

                # Exit condition: no more factors stored
                if not sum(entry):
                    break

                else:
                    # Decode entry
                    factor = entry[0] / 10 ** m
                    time = entry[1] * self.device.timeBlock

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
                self.part.values.append(factors[i])
                self.part.times.append(times[i - 1])



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READCSF
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readCSF":

            # Extract carb sensitivity units
            units = data[0]

            # Decode units
            if units == 1:
                self.part.units = "g"

                # Define a multiplicator to decode ISF bytes
                m = 0

            elif units == 2:
                self.part.units = "exchanges"

                # Define a multiplicator to decode ISF bytes
                m = 1.0

            # Initialize index as well as factors and times vectors
            i = 0
            factors = []
            times = []

            # Extract carb sensitivity factors
            while True:

                # Define start (a) and end (b) indexes of current factor based
                # on number of bytes per entry
                n = 2
                a = 2 + n * i
                b = a + n

                # Get current factor entry
                entry = data[a:b]

                # Exit condition: no more factors stored
                if not sum(entry):
                    break

                else:
                    # Decode entry
                    factor = entry[0] / 10 ** m
                    time = entry[1] * self.device.timeBlock

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
                self.part.values.append(factors[i])
                self.part.times.append(times[i - 1])



        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # READTBR
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif command == "readTBR":

            units = data[0]

            # Extract TBR [U/h]
            if units == 0:

                # Decode TBR characteristics
                self.part.value["Units"] = "U/h"
                self.part.value["Rate"] = round(lib.bangInt(data[2:4]) *
                                                self.device.basalStroke / 2.0,
                                                2)

            # Extract TBR [%]
            elif units == 1:

                # Decode TBR characteristics
                self.part.value["Units"] = "%"
                self.part.value["Rate"] = round(data[1], 2)

            # Decode TBR remaining time
            self.part.value["Duration"] = round(lib.bangInt(data[4:6]), 0)



    def decodeBolusRecord(self, code, size):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        DECODEBOLUSRECORD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read current time
        now = datetime.datetime.now()

        # Assign history
        history = self.device.history.pages

        # Search history for specified record
        for i in range(len(history)):

            # Try and find bolus records
            try:

                # Define bolus criteria
                if ((history[i] == code) and
                    (history[i + 1] == history[i + 2]) and
                    (history[i + 3] == 0)):
            
                    # Extract bolus from pump history
                    bolus = round(history[i + 1] * self.device.bolusStroke, 1)

                    # Extract time at which bolus was delivered
                    t = lib.decodeTime(history[i + 4 : i + 9])

                    # Check for bolus year
                    if abs(t[0] - now.year) > 1:

                        raise ValueError("Bolus can't be more than one year " +
                                         "in the past!")

                    # Build datetime object
                    t = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])

                    # Format bolus time
                    t = lib.formatTime(t)

                    # Give user info
                    #print "Bolus read: " + str(bolus) + "U (" + t + ")"
                    
                    # Store bolus
                    self.part.values.append(bolus)
                    self.part.times.append(t)

            except:
                pass



    def decodeBolusWizardRecord(self, code, headSize, dateSize, bodySize):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        DECODEBOLUSWIZARDRECORD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read current time
        now = datetime.datetime.now()

        # Assign history
        history = self.device.history.pages

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
        for i in range(len(history)):

            # Try and find bolus wizard records
            try:

                # Look for code, with which every record should start
                if history[i] == code:

                    # Define a record running variable
                    x = i
            
                    # Assign record head
                    head = history[x:x + headSize]

                    # Update running variable
                    x += headSize

                    # Assign record date
                    date = history[x:x + dateSize]

                    # Update running variable
                    x += dateSize

                    # Assign record body
                    body = history[x:x + bodySize]

                    # Decode time using date bytes
                    t = lib.decodeTime(date)

                    # Build datetime object
                    t = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])

                    # Proof record year
                    if abs(t.year - now.year) > 1:

                        raise ValueError("Record and current year too far " +
                                         "apart!")

                    # Format time
                    t = lib.formatTime(t)

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
                        self.part.values.append([C, CU])
                        self.part.times.append(t)

                    # Give user output
                    #print "Time: " + t
                    #print "Response: " + str(head) + ", " + str(body)
                    #print "BG: " + str(BG) + " " + str(BGU)
                    #print "Carbs: " + str(C) + " " + str(CU)
                    #print "BG Targets: " + str(BGTargets) + " " + str(BGU)
                    #print "CSF: " + str(CSF) + " " + str(CU) + "/U"
                    #print

            except:
                pass



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()

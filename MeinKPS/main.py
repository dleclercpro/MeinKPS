#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    main

    Author:   David Leclerc

    Version:  0.1

    Date:     28.03.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that contains various commands to control a
    		  Medtronic MiniMed insulin pump over radio frequencies using the
    		  Texas Instruments CC1111 USB radio stick.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import time



# USER LIBRARIES
from Pump import commands
from Pump import stick



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a stick
    _stick = stick.Stick()

    # Start it
    _stick.start()

    # Tune radio
    #_stick.tune(916.690)

    # Info
    print "// Power //"

    # Define power pump command
    powerCmd = commands.PowerPump(_stick)

    # Run it
    powerCmd.run()

    # Define pump commands
    cmds = {"Time": commands.ReadPumpTime(_stick),
            "Model": commands.ReadPumpModel(_stick),
            "Firmware": commands.ReadPumpFirmware(_stick),
            "Battery": commands.ReadPumpBattery(_stick),
            "Reservoir": commands.ReadPumpReservoir(_stick),
            "Status": commands.ReadPumpStatus(_stick),
            "Settings": commands.ReadPumpSettings(_stick),
            "BG Units": commands.ReadPumpBGUnits(_stick),
            "Carbs Units": commands.ReadPumpCarbsUnits(_stick),
            "BG Targets": commands.ReadPumpBGTargets(_stick),
            "ISF": commands.ReadPumpISF(_stick),
            "CSF": commands.ReadPumpCSF(_stick),
            "Basal Profile Standard": commands.ReadPumpBasalProfileStandard(_stick),
            "Basal Profile A": commands.ReadPumpBasalProfileA(_stick),
            "Basal Profile B": commands.ReadPumpBasalProfileB(_stick),
            "Daily Totals": commands.ReadPumpDailyTotals(_stick),
            "TB": commands.ReadPumpTB(_stick),
            "Button": commands.PushPumpButton(_stick),
            "History Size": commands.ReadPumpHistorySize(_stick),
            #"Suspend": commands.SuspendPump(_stick),
            #"Resume": commands.ResumePump(_stick)
            }

    # Define pump commands
    historyCmd = commands.ReadPumpHistoryPage(_stick)

    # Go through them
    for name, cmd in sorted(cmds.iteritems()):

        # Info
        print "// " + name + " //"

        # Send and listen to radio
        cmd.run()

    # Define history size (max 36)
    historySize = 0

    # Initialize history
    history = []

    # Read whole history
    for i in reversed(range(historySize)):

        # Info
        print "// History Page: " + str(i) + " //"

        # Get and extend history
        history.extend(historyCmd.run(i))

    # Show it
    print "History: " + str(history)

    # # Define bolus command
    # bolusCmd = commands.DeliverPumpBolus(_stick)

    # # Define bolus size
    # bolus = 0.4

    # # Info
    # print "// Bolus: " + str(bolus) + " U //"

    # # Send and listen to radio
    # bolusCmd.run(bolus)

    # Define TB commands
    tbCmds = [
              #["TB Absolute", commands.SetPumpAbsoluteTB(_stick), [0, 0]],
              #["TB Units",commands.SetPumpTBUnits(_stick), ["%"]],
              #["TB Percentage",commands.SetPumpPercentageTB(_stick), [98, 30]],
              #["TB Percentage",commands.SetPumpPercentageTB(_stick), [0, 0]],
              #["TB Units",commands.SetPumpTBUnits(_stick), ["U/h"]],
              #["TB Absolute", commands.SetPumpAbsoluteTB(_stick), [5.55, 30]],
              #["TB Absolute", commands.SetPumpAbsoluteTB(_stick), [0, 0]],
              ]

    # Run them
    for i in range(len(tbCmds)):

        # Sleep
        time.sleep(3)

        # Info
        print "// " + tbCmds[i][0] + " //"

        # Send and listen to radio
        tbCmds[i][1].run(*tbCmds[i][2])



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
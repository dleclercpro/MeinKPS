#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    calculator

    Author:   David Leclerc

    Version:  0.1

    Date:     27.05.2016

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib
import reporter
from Profiles import *



# Define a reporter
Reporter = reporter.Reporter()



class Calculator(object):

    def __init__(self, now):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define current time
        self.now = now

        # Initialize DIA
        self.DIA = None

        # Initialize IDC
        self.IDC = None

        # Give calculator a basal profile
        self.basal = basal.BasalProfile()

        # Give calculator a TB profile
        self.TB = TB.TBProfile()

        # Give calculator a bolus profile
        self.bolus = bolus.BolusProfile()

        # Give calculator a suspend profile
        self.suspend = suspend.SuspendProfile()

        # Give calculator a resume profile
        self.resume = resume.ResumeProfile()

        # Initialize net insulin profile
        self.net = net.NetProfile()

        # Give calculator an IOB profile
        self.IOB = IOB.FutureIOBProfile(IOB.PastIOBProfile())

        # Give calculator a COB profile
        self.COB = COB.COBProfile()

        # Give calculator an ISF profile
        self.ISF = ISF.ISFProfile()

        # Give calculator a CSF profile
        self.CSF = CSF.CSFProfile()

        # Give calculator a BG targets profile
        self.BGTargets = BGTargets.BGTargets()

        # Give calculator a BG profile
        self.BG = BG.FutureBGProfile(BG.PastBGProfile())

        # Initialize pump's max values
        self.max = {"Basal": None,
                    "Bolus": None}



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load components
        self.load()

        # Prepare components
        self.prepare()

        # Run autosens
        #self.autosens()

        # Recommend and return TB
        return self.recommend()



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read DIA
        self.DIA = Reporter.get("pump.json", ["Settings"], "DIA")

        # Give user info
        print "DIA: " + str(self.DIA) + " h"

        # Read max basal
        self.max["Basal"] = Reporter.get("pump.json", ["Settings"], "Max Basal")

        # Give user info
        print "Max basal: " + str(self.max["Basal"]) + " U/h"

        # Read max bolus
        self.max["Bolus"] = Reporter.get("pump.json", ["Settings"], "Max Bolus")

        # Give user info
        print "Max bolus: " + str(self.max["Bolus"]) + " U"



    def prepare(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Compute past start of insulin action
        past = self.now - datetime.timedelta(hours = self.DIA)

        # Compute future end of insulin action
        future = self.now + datetime.timedelta(hours = self.DIA)

        # Build net insulin profile
        self.net.build(past, self.now, self.basal, self.TB, self.suspend,
                                       self.resume, self.bolus)

        # Define IDC
        #self.IDC = IDC.FiaspIDC(self.DIA)
        self.IDC = IDC.WalshIDC(self.DIA)

        # Build past IOB profile
        self.IOB.past.build(past, self.now)

        # Build future IOB profile
        self.IOB.build(self.net, self.IDC)

        # Build COB profile
        #self.COB.build(past, self.now)

        # Build future ISF profile
        self.ISF.build(self.now, future)

        # Build future CSF profile
        self.CSF.build(self.now, future)

        # Build future BG targets profile
        self.BGTargets.build(self.now, future)

        # Build past BG profile
        self.BG.past.build(past, self.now)

        # Build future BG profile
        self.BG.build(self.IOB, self.ISF)



    def computeDose(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTEDOSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Compute the necessary insulin amount at the current time  based on
        latest BG input and future target, taking into account ISF step curve
        over the next DIA hours (assuming natural decay of insulin).
        """

        # Give user info
        print "Computing insulin dose..."

        # Check for insufficient data
        self.BG.past.verify(1)

        # Get current data
        BG = self.BG.past.y[-1]
        ISF = self.ISF.y[0]
        IOB = self.IOB.y[0]

        # Compute target by the end of insulin action
        targetRangeBG = self.BGTargets.y[-1]
        targetBG = np.mean(targetRangeBG)

        # Compute eventual BG after complete IOB decay
        naiveBG = self.BG.expect(self.DIA, self.IOB)

        # Compute BG deviation based on CGM readings and expected BG due to IOB
        # decay
        [deltaBG, BGI, expectedBGI] = self.BG.analyze(self.IOB, self.ISF)

        # Update eventual BG
        eventualBG = naiveBG + deltaBG

        # Compute BG difference with average target
        dBG = targetBG - eventualBG

        # Compute required dose
        dose = self.BG.dose(dBG, self.ISF, self.IDC)

        # Give user info
        print "BG target: " + str(targetBG) + " " + self.BG.u
        print "Current BG: " + str(BG) + " " + self.BG.u
        print "Current ISF: " + str(ISF) + " " + self.ISF.u
        print "Current IOB: " + str(IOB) + " " + self.IOB.u
        print "Naive eventual BG: " + str(naiveBG) + " " + self.BG.u
        print "Eventual BG: " + str(eventualBG) + " " + self.BG.u
        print "dBG: " + str(dBG) + " " + self.BG.u
        print "Recommended dose: " + str(dose) + " " + "U"

        # Look for conflictual info
        if (np.sign(BGI) == -1 and eventualBG > max(targetRangeBG) or
            np.sign(BGI) == 1 and eventualBG < min(targetRangeBG)):

            # Give user info
            print ("Conflictual information: BG decreasing/rising although " +
                   "expected to land higher/lower than target range.")

            # No recommendation
            #dose = 0

        # Return dose
        return dose



    def computeTB(self, dose):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTETB
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Compute TB to enact given a recommended insulin dose.
        """

        # Give user info
        print "Computing TB to enact..."

        # Get current data
        basal = self.basal.y[-1]

        # Define time to enact equivalent of dose (h)
        T = 0.5

        # Find required basal difference to enact over given time (round to
        # pump's precision)
        dB = dose / T

        # Compute TB to enact 
        TB = basal + dB

        # Give user info
        print "Current basal: " + str(basal) + " U/h"
        print "Required basal difference: " + str(dB) + " U/h"
        print "Temporary basal to enact: " + str(TB) + " U/h"
        print "Enactment time: " + str(T) + " h"

        # Convert enactment time to minutes
        T *= 60

        # Return TB recommendation
        return [TB, "U/h", T]



    def limitTB(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LIMITTB
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Limit too low/high TBs.
        """

        # Destructure TB
        [rate, units, duration] = TB

        # Negative TB rate
        if rate < 0:

            # Give user info
            print ("External action required: negative basal required. " +
                   "Eat something!")

            # Stop insulin delivery
            rate = 0

        # Positive TB
        elif rate > 0:

            # Get basal info
            basal = self.basal.y[-1]
            maxDailyBasal = self.basal.max
            maxBasal = self.max["Basal"]

            # Define max basal rate allowed (U/h)
            maxRate = min(4 * basal, 3 * maxDailyBasal, maxBasal)

            # Give user info
            print "Theoretical max basal: " + str(maxBasal) + " U/h"
            print "4x current basal: " + str(4 * basal) + " U/h"
            print "3x max daily basal: " + str(3 * maxDailyBasal) + " U/h"

            # TB exceeds max
            if rate > maxRate:

                # Give user info
                print ("External action required: maximal basal exceeded. " +
                       "Enact dose manually!")

                # Max it out
                rate = maxRate

        # No TB
        else:

            # Give user info
            print ("No modification to insulin dosage necessary.")

        # Return limited TB
        return [rate, units, duration]



    def snooze(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SNOOZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Snooze enactment of high TBs for a while after eating.
        """

        # Get last carbs
        lastCarbs = Reporter.getRecent(self.now, "treatments.json",
                                                 ["Carbs"], 1)

        # Destructure TB
        [rate, units, duration] = TB

        # Define snooze duration (h)
        snooze = 0.5 * self.DIA

        # Snooze criteria (no high temping after eating)
        if lastCarbs and rate > 0:

            # Get last meal time and format it to datetime object
            lastTime = lib.formatTime(max(lastCarbs))

            # Compute elapsed time since (h)
            d = (self.now - lastTime).total_seconds() / 3600.0

            # If snooze necessary
            if d < snooze:

                # Compute remaining time (m)
                T = int(round((snooze - d) * 60))

                # Give user info
                print ("Bolus snooze (" + str(snooze) + " h). If no more " +
                       "bolus is issued, looping will restart in " + str(T) +
                       " m.")

                # Snooze
                return True

        # Do not snooze
        return False



    def recommend(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECOMMEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Recommend a bolus based on latest BG and future target average, taking
        into account ISF step curve over the next DIA hours (assuming natural
        decay of insulin).
        """

        # Give user info
        print "Recommending treatment..."

        # Compute recommended dose
        dose = self.computeDose()

        # Compute corresponding TB
        TB = self.computeTB(dose)

        # Limit it
        TB = self.limitTB(TB)

        # Snoozing of TB enactment required?
        if self.snooze(TB):

            # No TB recommendation
            TB = None

        # If recommendation was not canceled
        if TB is not None:

            # Destructure TB
            [rate, units, duration] = TB

            # Give user info
            print ("Recommended TB: " + str(rate) + " " + units + " (" +
                                        str(duration) + " m)")

        # Return recommendation
        return TB



    def autosens(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            AUTOSENS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get last 24 hours of BGs
        BGs = Reporter.getRecent(self.now, "BG.json", [], 7, True)

        # Show them
        lib.printJSON(BGs)

        # Build BG profile for last 24 hours
        BGProfile = 0



    def export(self, now, hours = 24):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize reports
        reports = {"treatments": reporter.Report("treatments.json"),
                   "history": reporter.Report("history.json"),
                   "BG": reporter.Report("BG.json"),
                   "pump": reporter.Report("pump.json")}

        # Define past time
        past = now - datetime.timedelta(hours = hours)

        # Build net insulin profile for last 24 hours
        self.net.build(past, now, self.basal, self.TB, self.suspend,
                                                       self.resume)

        # Initialize net basals dict
        netBasals = {}

        # Loop over net insulin profile
        for t, y in zip(self.net.T, self.net.y):

            # Fill net basals dict
            netBasals[lib.formatTime(t)] = round(y, 2)

        # Get recent sensor statuses
        statuses = Reporter.getRecent(self.now, "history.json",
                                                ["CGM", "Sensor Statuses"])

        # Get recent calibrations
        calibrations = Reporter.getRecent(self.now, "history.json",
                                                    ["CGM", "Calibrations"])

        # Get recent boluses
        boluses = Reporter.getRecent(self.now, "treatments.json", ["Boluses"])

        # Get recent IOBs
        IOBs = Reporter.getRecent(self.now, "treatments.json", ["IOB"])

        # Fill treatments report
        reports["treatments"].update({
            "Net Basals": netBasals,
            "Boluses": boluses,
            "IOB": IOBs})

        # Ger recent history
        history = Reporter.getRecent(self.now, "history.json", [], 1)

        # Fill history report
        reports["history"].update(lib.mergeNDicts(history,
            {"CGM": {"Sensor Statuses": statuses,
                     "Calibrations": calibrations}}))

        # Get recent BGs
        BGs = Reporter.getRecent(self.now, "BG.json", [])

        # Fill BG report
        reports["BG"].update(BGs)

        # Fill pump report
        reports["pump"].update(Reporter.get("pump.json", []))

        # Loop over reports
        for report in reports.values():

            # Export it
            report.store(Reporter.exp.str)



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize plot
        mpl.rc("font", size = 10, family = "Ubuntu")
        fig = plt.figure(0, figsize = (10, 8))
        axes = [plt.subplot(221),
                plt.subplot(222),
                plt.subplot(223),
                plt.subplot(224)]

        # Define titles
        titles = ["BG", "Net Insulin Profile", "IOB", "COB"]

        # Define axis labels
        x = ["(h)"] * 4
        y = ["(" + self.BG.u + ")", "(U/h)", "(U)", "(g)"]

        # Define axis limits
        xlim = [[-self.DIA, self.DIA]] * 4
        ylim = [[2, 20], None, None, None]

        # Define subplots
        for i in range(4):

            # Set titles
            axes[i].set_title(titles[i], fontweight = "semibold")

            # Set x-axis labels
            axes[i].set_xlabel(x[i])

            # Set y-axis labels
            axes[i].set_ylabel(y[i])

            # Set x-axis limits
            axes[i].set_xlim(xlim[i])

        # Set y-axis limits
        axes[0].set_ylim(ylim[0])

        # Add BGs to plot
        axes[0].plot(self.BG.past.t, self.BG.past.y,
                     marker = "o", ms = 3.5, lw = 0, c = "red")

        # Add BG predictions to plot
        axes[0].plot(self.BG.t, self.BG.y,
                     marker = "o", ms = 3.5, lw = 0, c = "black")

        # Add net insulin profile to plot
        axes[1].step(self.net.t, np.append(0, self.net.y[:-1]),
                     lw = 2, ls = "-", c = "purple")

        # Add past IOB to plot
        axes[2].plot(self.IOB.past.t, self.IOB.past.y,
                     marker = "o", ms = 3.5, lw = 0, c = "orange")

        # Add IOB predictions to plot
        axes[2].plot(self.IOB.t, self.IOB.y,
                     lw = 2, ls = "-", c = "black")

        # Add COB to plot
        axes[3].plot([-self.DIA, 0], [0, 0],
                     lw = 2, ls = "-", c = "#99e500")

        # Add COB predictions to plot
        axes[3].plot([0, self.DIA], [0, 0],
                     lw = 2, ls = "-", c = "black")

        # Tighten up
        plt.tight_layout()

        # Show plot
        plt.show()



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now() - datetime.timedelta(days = 6)

    # Instanciate a calculator
    calculator = Calculator(now)

    # Run calculator
    calculator.run()

    # Export results
    #calculator.export(now)

    # Run autosens
    #calculator.autosens()

    # Show components
    calculator.show()

    # Export net insulin profile
    #calculator.export(now)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()

#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    calculator

    Author:   David Leclerc

    Version:  0.2

    Date:     09.10.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: Library used to make insulin dosing decisions based on various
              treatment profiles.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import numpy as np
import copy



# USER LIBRARIES
import fmt
import lib
import errors
import logger
import reporter



# Define instances
Logger = logger.Logger("calculator.py")
Reporter = reporter.Reporter()



# CONSTANTS
BG_HYPO_LIMIT       = 4.5 # (mmol/L)
BG_HYPER_LIMIT      = 8.5 # (mmol/L)
DOSE_ENACT_TIME     = 0.5 # (h)



def computeIOB(net, IDC):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTEIOB
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        The formula to compute IOB is given by:

            IOB = SUM_t' NET(t') * S_t' IDC(t) * dt

        where S represents an integral and t' the value of a given step in the
        net insulin profile.
    """

    # Initialize IOB
    IOB = 0

    # Decouple net insulin profile components
    t, y = net.t, net.y

    # Get number of steps
    n = len(t) - 1

    # Compute IOB
    for i in range(n):

        # Compute remaining IOB factor based on integral of IDC
        r = IDC.F(t[i + 1]) - IDC.F(t[i])

        # Compute active insulin remaining for current step
        IOB += r * y[i]

    # Give user info
    Logger.debug("IOB: " + fmt.IOB(IOB))

    # Return IOB
    return IOB



def computeDose(dBG, ISF, IDC):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTEDOSE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Compute dose (theoretical instant bolus) to bring back BG to target
        using ISF and IDC, based on the following formula:

            dBG = SUM_t' ISF(t') * dIDC(t') * D

        where dBG represents the desired BG variation, t' to the considered time
        step in the ISF profile, dIDC to the corresponding change in remaining
        active insulin over said step, and D to the necessary insulin dose. The
        dose can simply be taken out of the sum, since it is a constant
        (assuming a theoretical instant bolus).
    """

    # Initialize conversion factor between dose and BG difference to target
    f = 0

    # Get number of ISF steps
    n = len(ISF.t) - 1

    # Compute factor
    for i in range(n):

        # Compute step limits
        a = -ISF.t[i]
        b = -ISF.t[i + 1]

        # Update factor with current step
        f += ISF.y[i] * (IDC.f(b) - IDC.f(a))

    # Compute necessary dose (instant bolus)
    dose = dBG / f

    # Return dose
    return dose



def countValidBGs(pastBGs, age = 30, N = 2):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COUNTVALIDBGS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Count and make sure there are enough (>= N) BGs that can be considered
        valid (recent enough) for dosing decisions based on a given age (m).

        Note: it is assumed here that the end of the BG profile corresponds to
        the current time!
    """

    # Count how many BGs are not older than T
    n = np.sum(np.array(pastBGs.T) > pastBGs.end -
                                     datetime.timedelta(minutes = age))

    # Give user info
    Logger.debug("Found " + str(n) + " BGs within last " + str(age) + " m.")

    # Check for insufficient valid BGs
    if n < N:

        # Exit
        raise errors.MissingBGs()

    # Return count
    return n



def computeBGI(pastBGs):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTEBGI
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Compute dBG/dt a.k.a. BGI (mmol/L/h) using linear fit on most recent BGs.
    """

    # Count valid BGs
    n = countValidBGs(pastBGs, 30, 4)

    # Get fit over last minutes
    [m, b] = np.polyfit(pastBGs.t[-n:], pastBGs.y[-n:], 1)

    # Return fit slope, which corresponds to BGI
    return m



def linearlyProjectBG(pastBGs, dt):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        LINEARLYPROJECTBG
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        BG projection based on expected duration dt (h) of current BGI
        (mmol/L/h).
    """

    # Give user info
    Logger.info("Projection time: " + str(dt) + " h")

    # Compute derivative to use when predicting future BG
    BGI = computeBGI(pastBGs)

    # Get most recent BG
    BG0 = pastBGs.y[-1]

    # Predict future BG
    BG = BG0 + BGI * dt

    # Return BG linear projection and BGI
    return [BG, BGI]



def computeBGDynamics(pastBGs, futureBGs, BGTargets, IOB, ISF, dt = 0.5):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTEBGDYNAMICS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Compute BG related dynamics.

        dt:     time period over which current BGI is expected stay constant (h)
        BG:     blood glucose (mmol/L or mg/dL)
        BGI:    variation in blood glucose (mmol/L/h or mg/dL/h)
        expBG:  expected BG after dt based on natural IOB decay (mmol/L)
        expBGI: expected BGI based on current dIOB/dt and ISF (mmol/L/h)
        IOB:    insulin-on-board (U)
        ISF:    insulin sensibility factor (mmol/L/U)
    """

    # Give user info
    Logger.info("Computing BG dynamics...")

    # Read expected BG after natural decay of IOB
    expectedBG = futureBGs.y[-1]

    # Compute BG target by the end of insulin action
    BGTarget = np.mean(BGTargets.y[-1])

    # Compute BG assuming continuation of current BGI over dt (h)
    [shortProjectedBG, BGI] = linearlyProjectBG(pastBGs, dt)

    # Compute BG variation due to IOB decay (will only work if dt is a
    # multiple of predicted BG decay's profile timestep
    shortExpectedBG = futureBGs.y[futureBGs.t.index(dt)]

    # Compute deviation between expected and projected BG
    shortdBG = shortProjectedBG - shortExpectedBG

    # Compute expected BGI based on IOB decay
    expectedBGI = IOB.dydt[0] * ISF.y[0]

    # Compute deviation between expected and real BGI
    dBGI = BGI - expectedBGI

    # Compute eventual BG at the end of DIA
    eventualBG = expectedBG + shortdBG

    # Compute difference with BG target
    dBGTarget = BGTarget - eventualBG

    # Give user info about current status
    Logger.info("Current BG: " + fmt.BG(pastBGs.y[-1]))
    Logger.info("Current IOB: " + fmt.IOB(IOB.y[0]))

    # Give user info about short (dt) BG projection
    Logger.info("Projection time: " + str(dt) + " h")
    Logger.info("Expected BG (dt): " + fmt.BG(shortExpectedBG))
    Logger.info("Projected BG (dt): " + fmt.BG(shortProjectedBG))
    Logger.info("dBG (dt): " + fmt.BG(shortdBG))

    # Give user info about long (DIA) BG projection
    Logger.info("Expected BG (DIA): " + fmt.BG(expectedBG))
    Logger.info("Eventual BG (DIA): " + fmt.BG(eventualBG))
    Logger.info("BG Target (DIA): " + fmt.BG(BGTarget))
    Logger.info("dBG to BG Target (DIA): " + fmt.BG(dBGTarget))

    # Give user info (BGI)
    Logger.info("Expected BGI: " + fmt.BGI(expectedBGI))
    Logger.info("Current BGI: " + fmt.BGI(BGI))
    Logger.info("dBGI: " + fmt.BGI(dBGI))

    # Return BG dynamics computations
    return {"BG": pastBGs.y[-1],
            "expectedBG": expectedBG,
            "shortExpectedBG": shortExpectedBG,
            "shortProjectedBG": shortProjectedBG,
            "shortdBG": shortdBG,
            "eventualBG": eventualBG,
            "BGTarget": BGTarget,
            "dBGTarget": dBGTarget,
            "expectedBGI": expectedBGI,
            "BGI": BGI,
            "dBGI": dBGI}



def computeTB(dose, basals):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTETB
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Compute TB to enact given current basal and recommended insulin dose.
    """

    # Give user info
    Logger.debug("Computing TB to enact...")

    # Get current basal
    basal = basals.y[-1]

    # Find required basal difference to enact over given time
    dB = dose / DOSE_ENACT_TIME

    # Compute TB to enact using the current basal and said required difference
    TB = basal + dB

    # Give user info
    Logger.info("Current basal: " + fmt.basal(basal))
    Logger.info("Required basal difference: " + fmt.basal(dB))
    Logger.info("Temporary basal to enact: " + fmt.basal(TB))
    Logger.info("Enactment time: " + str(DOSE_ENACT_TIME) + " h")

    # Return TB recommendation (in minutes)
    return [TB, "U/h", DOSE_ENACT_TIME * 60]



def limitTB(TB, basals, BG):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        LIMITTB
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Limit TB recommendations based on incoming hypos or exceeding of max
        basal according to simple security computation (see under).
    """

    # Destructure TB
    [rate, units, duration] = TB

    # Get current basal
    basal = basals.y[-1]

    # Negative TB rate
    if rate < 0 or BG <= BG_HYPO_LIMIT:

        # Give user info
        Logger.warning("Hypo prevention mode.")

        # Stop insulin delivery
        rate = 0

    # Positive TB
    elif rate > 0:

        # Compute maximum daily basal rate
        maxDailyBasal = max(basals.y)

        # Define max basal rate allowed (U/h)
        maxRate = min(4 * basal, 3 * maxDailyBasal, basals.max)

        # Give user info
        Logger.info("Theoretical max basal: " + fmt.basal(basals.max))
        Logger.info("4x current basal: " + fmt.basal(4 * basal))
        Logger.info("3x max daily basal: " + fmt.basal(3 * maxDailyBasal))

        # TB exceeds max
        if rate > maxRate:

            # Give user info
            Logger.warning("TB recommendation exceeds maximal basal and has " +
                           "thus been limited. Bolus would bring BG back to " +
                           "safe range more effectively.")

            # Max it out
            rate = maxRate

    # Return limited TB
    return [rate, units, duration]



def snooze(now, duration = 2):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        SNOOZE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Snooze enactment of TBs for a while after eating.
        FIXME: take carbs dynamics into consideration!
    """

    # Get last carbs
    lastCarbs = Reporter.getRecent(now, "treatments.json", ["Carbs"], 1)

    # Snooze criteria (no temping after eating)
    if lastCarbs:

        # Get last meal time
        lastTime = lib.formatTime(max(lastCarbs))

        # Compute elapsed time since last meal
        dt = (now - lastTime).total_seconds() / 3600.0

        # If snooze necessary
        if dt < duration:

            # Compute remaining time (m)
            t = int(round((duration - dt) * 60))

            # Give user info
            Logger.warning("Bolus snooze (" + str(duration) + " h). If no " +
                           "more bolus issued, high temping will resume in " +
                           str(t) + " m.")

            # Snooze
            return True

    # Do not snooze
    return False



def recommendTB(BGDynamics, basals, ISF, IDC):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        RECOMMENDTB
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Recommend a TB based on latest treatment information, predictions and
        security limitations.
    """

    # Give user info
    Logger.debug("Recommending TB...")

    # Compute necessary insulin dose to bring back eventual BG to target
    dose = computeDose(BGDynamics["dBGTarget"], ISF, IDC)

    # Compute corresponding TB
    TB = computeTB(dose, basals)

    # Limit it
    TB = limitTB(TB, basals, BGDynamics["BG"])

    # Snoozing of temping required?
    if snooze(basals.end):

        # No TB recommendation (back to programmed basals)
        TB = None

    # If recommendation was not canceled
    if TB is not None:

        # Destructure TB
        [rate, units, duration] = TB

        # Give user info
        Logger.info("Recommended TB: " + fmt.basal(rate) + " " +
                    "(" + str(duration) + " m)")

    # Return recommendation
    return TB



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime(2017, 9, 1, 23, 0, 0)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
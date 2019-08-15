#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    errors

    Author:   David Leclerc

    Version:  0.1

    Date:     03.03.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that contains all possible errors that can happen
              when running MeinKPS scripts.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import numpy as np
import matplotlib.pyplot as plt



# USER LIBRARIES
import fmt
import lib
import logger
import reporter



# Instanciate logger
Logger = logger.Logger("errors")



# CLASSES
class BaseError(Exception):

    def __init__(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize error info
        self.info = ""

        # Initialize error logging level
        self.level = "ERROR"

        # Convert arguments to strings
        self.args = [str(x) for x in args]

        # Define error
        self.define()

        # Log error
        self.log()



    def __repr__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            REPR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Representation of an error as a chain, going from itself, all the
            way up to its class ancestor, which succeeds the 'BaseError' class.
        """

        # Get class path
        path = [c.__name__ for c in self.__class__.__mro__]

        return " | ".join([p for p in
            reversed(path[:path.index("BaseError")])])



    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Define error logging level and info, using arguments passed when the
            error was raised. This method has to be implemented for each error.
        """

        raise NotImplementedError



    def log(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOG
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Log error with according level
        Logger.log(self.level, repr(self) + ": " + self.info)



class LoggableError(BaseError):

    def __init__(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Loggable errors are not only logged in the 'run.log' file, but also
            counted in an 'errors.json' dated report.

            Note: Reporter errors cannot be counted, since some cases (e.g.
                  missing branches) lead to stack overflows.
        """

        # Get current day
        today = datetime.date.today()

        # Define and load report
        self.report = reporter.getReportByType(reporter.ErrorsReport, today,
            strict = False)

        # Initialize error
        super(LoggableError, self).__init__(*args)



    def __repr__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            REPR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Representation of an error as a chain, going from itself, all the
            way up to its class ancestor, which succeeds the 'LoggableError'
            class.
        """

        # Get class path
        path = [c.__name__ for c in self.__class__.__mro__]

        return " | ".join([p for p in
            reversed(path[:path.index("LoggableError")])])



    def log(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOG
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Log error
        super(LoggableError, self).log()

        # Update error stats
        self.report.increment(repr(self).split(" | "), False)
        self.report.store()






class StickError(LoggableError):
    pass

class RadioError(StickError):
    pass

class PacketError(RadioError):
    pass

class PumpError(LoggableError):
    pass

class CGMError(LoggableError):
    pass

class ProfileError(LoggableError):
    pass

class ReporterError(BaseError):
    pass






# Loop errors
class NotEnoughBGs(LoggableError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "CRITICAL"

        # Define error info
        self.info = ("Not enough BGs found in the last " + self.args[2] + " " +
            "minutes to take action. Found: " + self.args[0] + ". Needed: " +
            self.args[1] + ".")



# Stick errors
class NoStick(StickError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "CRITICAL"

        # Define error info
        self.info = "No stick detected. Are you sure it's plugged in?"



class UnknownFrequencyRange(StickError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error info
        self.info = ("RF range to scan for does not correspond to any known " +
            "region: " + fmt.frequencyRange(self.args[0], self.args[1]))



class RadioRegisterWriteFail(StickError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "CRITICAL"

        # Define error info
        self.info = "Radio register not updated correctly."



# Radio errors
class RadioTimeout(RadioError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "DEBUG"

        # Define error info
        self.info = "Timeout"



class RadioNoData(RadioError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "DEBUG"

        # Define error info
        self.info = "No Data"



class RadioInterrupted(RadioError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "DEBUG"

        # Define error info
        self.info = "Interrupted"



class UnsuccessfulRadioCommand(RadioError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error info
        self.info = "Radio command was unsuccessful."



# Packet errors
class UnknownPacketRecipient(PacketError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "WARNING"

        # Define error info
        self.info = "Unknown packet."



class CorruptedPumpPacket(PacketError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "DEBUG"

        # Define error info
        self.info = ("Unmatched bits before end-of-packet (corrupted " +
                     "packet): " + self.args[0])



class NotEnoughPumpPacketBytes(PacketError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "DEBUG"

        # Define error info
        self.info = ("Not enough bytes received. Expected: " + self.args[0] +
                     ". Received: " + self.args[1] + ".")



class MissingPumpPacketBits(PacketError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "CRITICAL"

        # Define error info
        self.info = ("Impossible to encode number of bytes which isn't a " +
                     "multiple of 8: " + self.args[0])



class BadPumpPacketEnding(PacketError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "DEBUG"

        # Define error info
        self.info = ("Last bits do not correspond to expectation (0101): " +
                     self.args[0])



# Pump errors
class NoPump(PumpError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "CRITICAL"

        # Define error info
        self.info = ("No pump detected. Are you sure it's nearby and " +
                     "battery level is not too low?")



class BadPumpRecord(PumpError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "DEBUG"

        # Define error info
        self.info = ("Invalid pump history record.")



class TBFail(PumpError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "CRITICAL"

        # Define error info
        self.info = ("New TB could not be correctly set.")



class BadTBRate(PumpError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error info
        self.info = ("TB rate (" + str(self.args[0]["Rate"]) + " " +
                     self.args[0]["Units"] + ") must be within theoretical " +
                     "limits of [0, 35] U/h or [0, 200] %.")



class BadTBDuration(PumpError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error info
        self.info = ("TB duration (" + str(self.args[0]["Duration"]) + " m) " +
                     "is incorrect. The latter must be a multiple of 30.")



class PumpStatusAbnormal(PumpError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error info
        self.info = ("Pump status is abnormal.")



class PumpStatusBolusing(PumpError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error info
        self.info = ("Pump is bolusing.")



class PumpStatusSuspended(PumpError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error info
        self.info = ("Pump is suspended.")



# CGM errors
class NoCGM(CGMError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "CRITICAL"

        # Define error info
        self.info = "No CGM detected. Are you sure it's plugged in?"



# Reporter errors
class InvalidBranch(ReporterError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error info
        self.info = "Branch is invalid: " + self.args[0]



class MissingBranch(ReporterError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "DEBUG"

        # Define error info
        self.info = self.args[0] + " has no branch: " + self.args[1]



class NoOverwriting(ReporterError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error info
        self.info = "Cannot overwrite " + self.args[0] + " at " + self.args[1]



class InvalidFTPReport(ReporterError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error logging level
        self.level = "CRITICAL"

        # Define error info
        self.info = "Invalid FTP report."



class MismatchedLimits(ProfileError):

    def define(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define error info
        self.info = "Cannot operate on profiles: mismatched start/end limits."



def flattenErrors(errors, result = {}):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        FLATTENERRORS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Using a JSON object with an error tree for each available day, store the
        daily count for each error type in the given result JSON object.
    """

    # Loop over keys
    for key in errors:

        # Key leads to another dict object: dive deeper
        if type(errors[key]) is dict:
            flattenErrors(errors[key], result)

        # Otherwise: add count to result
        else:

            # Key does not exist yet: initialize it
            if key not in result:
                result[key] = []

            # Add count
            result[key] += [errors[key]]

    # Return merged errors (will only be accessible at top-level of recursion)
    return result



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~­
    """

    # Get current date
    today = datetime.date.today()

    # Get flattened monthly error counts (each error has an array of counts, no
    # more dates)
    flattenedErrors = flattenErrors(reporter.getMonthlyErrors(today))
    
    # Show them
    print lib.JSONize(flattenedErrors)

    # Filter some errors out
    filteredErrors = {k: v for k, v in flattenedErrors.iteritems()
        if k != "BadPumpRecord" and
           k != "RadioTimeout" and
           k != "NoCGM"}

    # Sort errors
    errors = sorted(filteredErrors.keys())

    # Compute stats
    avgs = [np.mean(filteredErrors[e]) for e in errors]
    stds = [np.std(filteredErrors[e]) for e in errors]
    mins = np.array([min(filteredErrors[e]) for e in errors])
    maxs = np.array([max(filteredErrors[e]) for e in errors])

    # Create error bars: min to max count
    plt.errorbar(errors,
        avgs,
        [avgs - mins, maxs - avgs],
        fmt = ".k", ecolor = "orange", lw = 1, uplims = True, lolims = True)

    # Create error bars: average centered, extending +/- standard deviation
    plt.errorbar(errors,
        avgs,
        stds,
        fmt = "ok", ecolor = "black", lw = 3, uplims = True, lolims = True)

    # Show graph
    plt.show()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
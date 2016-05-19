#! /usr/bin/python



"""
================================================================================
TITLE:    readInsuLinx

AUTHOR:   David Leclerc

VERSION:  0.1

DATE:     18.04.2016

LICENSE:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

OVERVIEW: This is a script that allows to retrieve blood sugar levels
          from the Freestyle InsuLinx glucometer. It is based on the
          PyUSB library and is a work of reverse-engineering the USB
          communication protocols of the FreeStyle InsuLinx from Abbott
          Diabetes Care.

NOTES:    ...
================================================================================
"""



# LIBRARIES
import datetime
import usb
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import numpy as np



# DEFINITIONS
LOGS_ADDRESS = '/home/david/Documents/MeinKPS/insulinxLogs.txt'
NOW          = datetime.datetime.now()



class insulinx:

    # INSULINX CHARACTERISTICS
    VENDOR                  = 0x1a61
    PRODUCT                 = 0x3460
    N_CONFIGURATIONS        = [1]
    N_INTERFACES            = [2]
    N_ENDPOINTS             = [1, 2]
    KERNEL_BOUND            = True
    REQUEST_TYPES           = [0x0021, 0x0081]
    REQUEST_COMMAND         = 0x0009
    REQUEST_VALUE           = 0x0200
    REQUEST_INDEX           = 0
    REQUEST_LENGTH          = 64
    REQUEST_TIMEOUT         = 50
    REQUEST_ASK_INITIALIZE  = [[0x0004, 0x0000], [0x0005, 0x0000], \
                              [0x0015, 0x0000],  [0x0001, 0x0000]]
    REQUEST_ASK_DATE        = [0x0060] + [ord(x) for x in '\n$date?\r\n']
    REQUEST_ASK_TIME        = [0x0060] + [ord(x) for x in '\n$time?\r\n']
    REQUEST_ASK_SERIAL      = [0x0060] + [ord(x) for x in '\n$serlnum?\r\n']
    REQUEST_ASK_SOFTWARE    = [0x0060] + [ord(x) for x in '\n$swver?\r\n']
    REQUEST_ASK_NAME        = [0x0060] + [ord(x) for x in '\n$ptname?\r\n']
    REQUEST_ASK_RESULTS     = [0x0060] + [ord(x) for x in '\n$result?\r\n']
    RAW_RESPONSE_STATUS     = [31, 37]
    RAW_RESPONSE_IGNORE     = [ord(x) for x in '\"']
    RAW_RESPONSE_DONE       = [ord(x) for x in 'CMD OK']
    RAW_RESPONSE_LENGTH     = 64
    REPORT_LENGTH           = 14
    REPORT_SUGAR_NONE       = 6
    REPORT_SUGAR_DAY        = 3
    REPORT_SUGAR_MONTH      = 2
    REPORT_SUGAR_YEAR       = 4
    REPORT_SUGAR_HOUR       = 5
    REPORT_SUGAR_MINUTE     = 6
    REPORT_SUGAR            = 13
    REPORT_SUGAR_CONVERSION = 0.0555



    def getUSBHandle(self):

        """
        ========================================================================
        GETHANDLE
        ========================================================================
        This is a method that generates a USB handle for the InsuLinx.
        """

        self.usb_handle = usb.core.find(idVendor = self.VENDOR, idProduct = self.PRODUCT)

        if self.usb_handle != None:
            print 'InsuLinx was found.'

        else:
            sys.exit('InsuLinx could not be found.')



    def start(self):

        """
        ========================================================================
        START
        ========================================================================
        This is a method that detaches the InsuLinx from the kernel and sets its
        configuration for the upcoming communications.
        """

        # Detach kernel
        interface_index = 0

        for i in range(self.N_CONFIGURATIONS[0]):
            for j in range(self.N_INTERFACES[i]):
                if self.usb_handle.is_kernel_driver_active(interface_index):
                    print 'Detaching InsuLinx from kernel...'

                    try:
                        self.usb_handle.detach_kernel_driver(interface_index)
                        self.KERNEL_BOUND = False
                        print 'InsuLinx was successfully detached.'

                        interface_index += 1

                    except usb.core.USBError:
                        sys.exit('Could not detach InsuLinx.')

        # Set configuration
        self.usb_handle.set_configuration()
        print 'InsuLinx was successfully configured.'



    def stop(self):

        """
        ========================================================================
        STOP
        ========================================================================
        This is a method that closes all communications with the InsuLinx and
        resets it.
        """

        # Release resources
        usb.util.dispose_resources(self.usb_handle)
        print 'Resources of InsuLinx released.'

        # Reattach OS kernel
        if self.KERNEL_BOUND == False:
            self.usb_handle.attach_kernel_driver(0)
            print 'InsuLinx reattached to kernel.'

        # Reset device
        self.usb_handle.reset()
        print 'InsuLinx reset.'



    def sendWriteRequest(self, request):

        """
        ========================================================================
        SENDWRITEREQUEST
        ========================================================================
        This is a method that sends a write request to the InsuLinx, asking to
        get and prepare some specific data in its storage.
        """

        try:
            self.usb_handle.ctrl_transfer(self.REQUEST_TYPES[0], \
                self.REQUEST_COMMAND, \
                self.REQUEST_VALUE, \
                self.REQUEST_INDEX, \
                request, \
                self.REQUEST_TIMEOUT)

        except usb.core.USBError:
            sys.exit('There was a problem while communicating with the InsuLinx.')



    def sendReadRequest(self):

        """
        ========================================================================
        SENDREADREQUEST
        ========================================================================
        This is a method that sends a read request to the InsuLinx, asking to
        get the data corresponding to a precedently sent write request.
        """

        try:
            self.raw_response = np.array(self.usb_handle.read(self.REQUEST_TYPES[1], \
                self.REQUEST_LENGTH, \
                self.REQUEST_TIMEOUT), int) # Raw response is saved to object in order to be used later

            self.raw_response_status = [x for x in self.raw_response[self.RAW_RESPONSE_STATUS[0] : self.RAW_RESPONSE_STATUS[1]]]

        except usb.core.USBError:
            sys.exit('There was a problem while communicating with the InsuLinx.')



    def initializeCommunication(self):

        """
        ========================================================================
        INITIALIZECOMMUNICATION
        ========================================================================
        This is a method that initializes the communication between the host and
        the InsuLinx, based on a reverse-engineered USB protocol.
        """

        n_initialize_requests = len(self.REQUEST_ASK_INITIALIZE)

        for i in range(n_initialize_requests):
            self.sendWriteRequest(self.REQUEST_ASK_INITIALIZE[i])

        for i in range(n_initialize_requests):
            self.sendReadRequest()

        print 'Initialized communication with the InsuLinx.'



    def getRawResponses(self):

        """
        ========================================================================
        GETRAWRESPONSES
        ========================================================================
        This is a method that continuously reads the raw responses coming from
        the InsuLinx until no one is being sent anymore.
        """

        self.raw_responses = []
        self.n_raw_responses = 0

        print 'Acquiring data on InsuLinx...'

        while True:
            self.sendReadRequest()

            if self.raw_response_status == self.RAW_RESPONSE_DONE:
                print 'Data successfully acquired.'
                break

            else:
                self.raw_responses.append(self.raw_response)
                self.n_raw_responses += 1



    def parseRawResponses(self):

        """
        ========================================================================
        PARSERAWRESPONSES
        ========================================================================
        This is a method that takes the raw responses coming from the InsuLinx
        and parses them for easier data treatment.
        """

        print 'Parsing received data...'

        self.responses = []
        self.n_responses = 0

        for i in range(self.n_raw_responses):
            raw_response = self.raw_responses[i]

            # Make sure the raw response is correct
            if len(raw_response) != self.RAW_RESPONSE_LENGTH:
                pass

            elif raw_response[0] == self.RAW_RESPONSE_IGNORE: # Those are erroneous answers?
                pass

            else:
                response = np.trim_zeros(raw_response, 'b')
                response = ''.join([chr(x) for x in response])
                response = response.replace('\r', '')\
                    .replace('\n', '')\
                    .replace('\'', '')\
                    .replace('\"', '')\
                    .replace('`', '')\
                    .replace('%', '')\
                    .replace('#', '')\
                    .replace('&', '')\
                    .replace('+', '')\
                    .replace('*', '')\
                    .replace('(', '')\
                    .replace(')', '')\
                    .replace('\x00', '')\
                    .replace('\x01', '')\
                    .replace('\x02', '')\
                    .replace('\x03', '')\
                    .replace('\x04', '')\
                    .replace('\x05', '')\
                    .replace('\x06', '')\
                    .replace('\x07', '')\
                    .replace('\x08', '')\
                    .replace('\x09', '')\
                    .split(',')

                response = filter(None, response)
                response = np.array(response, int)
                response = np.delete(response, -1) # Two last elements are irrelevant
                response = np.delete(response, -1)

                if len(response) != self.REPORT_LENGTH:
                    pass

                elif response[0] == self.REPORT_SUGAR_NONE: # Those do not correspond to blood sugar measurements
                    pass

                else:
                    self.responses.append(response)
                    self.n_responses += 1



    def loadResponses(self):

        """
        ========================================================================
        LOADRESPONSES
        ========================================================================
        This is a method that loads the previously saved parsed responses of the
        InsuLinx from a file called insulinxLogs.txt.
        """

        print 'Loading data...'

        self.saved_responses = []
        self.n_saved_responses = 0

        with open(LOGS_ADDRESS, 'r') as f:
            logs = f.readlines()
            n_logs = len(logs)

        for i in range(n_logs):
            self.saved_responses.append(np.array(logs[i].replace('\n', '').split(' '), int))
            self.n_saved_responses += 1

        print 'Loaded ' + str(self.n_saved_responses) + ' response(s).'



    def saveResponses(self):

        """
        ========================================================================
        SAVERESPONSES
        ========================================================================
        This is a method that saves the latest parsed responses of the Insulinx
        into a file called insulinxLogs.txt.
        """

        print 'Saving parsed data...'

        self.new_responses = []
        self.n_new_responses = 0

        # Checking for already existing entries (This could be optimized...)
        for i in range(self.n_responses):            
            response = self.responses[i]
            is_response_saved = False

            for j in range(self.n_saved_responses):
                saved_response = self.saved_responses[j]

                if np.all(response == saved_response):
                    is_response_saved = True
                    break

            if is_response_saved == True:
                pass

            else:
                # Add new response to new response array
                self.saved_responses.append(response)
                self.new_responses.append(response)
                self.n_saved_responses += 1
                self.n_new_responses += 1

        # Save new responses to log file
        self.saved_responses.sort(key = lambda x: x[1])
        self.new_responses.sort(key = lambda x: x[1])

        for i in range(self.n_new_responses):
            new_response = self.new_responses[i]

            with open(LOGS_ADDRESS, 'a') as f:
                np.savetxt(f, new_response, newline = ' ', fmt = '%i')
                f.seek(0, 2) # Delete last empty character
                f.truncate(f.tell() - 1)
                f.write('\n')

        print 'Saved ' + str(self.n_new_responses) + ' new response(s).'



    def getBloodSugarLevels(self):

        """
        ========================================================================
        GETBLOODSUGARLEVELS
        ========================================================================
        This is a method that takes the parsed responses of the InsuLinx, and
        extracts the blood sugar levels from them.
        """

        print 'Extracting blood sugar levels...'

        self.sugar_times = np.array([], object)
        self.sugar_levels = np.array([], float)

        for i in range(self.n_saved_responses):
            report_entry = self.saved_responses[i]

            sugar_time = datetime.datetime(2000 +\
                report_entry[self.REPORT_SUGAR_YEAR],\
                report_entry[self.REPORT_SUGAR_MONTH],\
                report_entry[self.REPORT_SUGAR_DAY],\
                report_entry[self.REPORT_SUGAR_HOUR],\
                report_entry[self.REPORT_SUGAR_MINUTE])
            sugar_level = self.REPORT_SUGAR_CONVERSION * report_entry[self.REPORT_SUGAR]

            self.sugar_times = np.append(self.sugar_times, sugar_time)
            self.sugar_levels = np.append(self.sugar_levels, sugar_level)



    def plotBloodSugarLevels(self, title, color):

        """
        ========================================================================
        PLOTBLOODSUGARLEVELS
        ========================================================================
        This is a method that takes the extracted blood sugar levels and plots
        them on the user screen.
        """

        # Generate plot
        print 'Plotting blood sugar levels...'

        # Define font
        mpl.rc('font', family = 'Ubuntu')

        # Define figure
        fig = plt.figure(0)
        fig.set_facecolor('white')
        fig.set_edgecolor('white')
        
        # Define subplots
        sp = plt.subplot(111, aspect = 1.0)
        sp.plot(self.sugar_times, self.sugar_levels, color = color, linewidth = 1.25)
        sp.set_axis_bgcolor('black')
        sp.grid(color = 'grey')
        sp.set_title(title, weight = 'bold', fontsize = 15)
        sp.set_xlabel('Time (days)', weight = 'demibold')
        sp.set_ylabel('Blood Sugar Levels (mmol/L)', weight = 'demibold')
        sp.xaxis.set_major_locator(dates.DayLocator(interval = 15)) # 15 days interval on x axis
        sp.xaxis.set_major_formatter(dates.DateFormatter('%d.%m.%Y'))

        # Tighten figure
        fig.tight_layout()

        # Show plot
        plt.show()



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    This is the main loop to be executed by the script.
    """

    # Generate instance of InsuLinx
    my_insulinx = insulinx()

    # Get InsuLinx a handle
    my_insulinx.getUSBHandle()

    # Start InsuLinx
    my_insulinx.start()

    # Initialize communication
    my_insulinx.initializeCommunication()

    # Get sugar levels
    my_insulinx.sendWriteRequest(my_insulinx.REQUEST_ASK_RESULTS)
    my_insulinx.getRawResponses()
    my_insulinx.parseRawResponses()
    my_insulinx.loadResponses()
    my_insulinx.saveResponses()
    my_insulinx.getBloodSugarLevels()

    # Generate plot of sugar levels
    my_insulinx.plotBloodSugarLevels('My Blood Sugar Levels Over the Last Few Months', 'red')

    # Stop InsuLinx
    my_insulinx.stop()

    # End of script
    print 'Done!'



# Run script when called from terminal
if __name__ == '__main__':
    main()

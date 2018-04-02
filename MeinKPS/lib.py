#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    lib

    Author:   David Leclerc

    Version:  0.1

    Date:     24.05.2016

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that contains user-defined functions to make the
              communications with the CareLink stick easier.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import os
import usb
import copy
import json
import datetime
import math
import numpy as np



# USER LIBRARIES
import errors



# CONSTANTS
# CRC8
CRC8_TABLE = [0, 155, 173, 54, 193, 90, 108, 247,
              25, 130, 180, 47, 216, 67, 117, 238,
              50, 169, 159, 4, 243, 104, 94, 197,
              43, 176, 134, 29, 234, 113, 71, 220,
              100, 255, 201, 82, 165, 62, 8, 147,
              125, 230, 208, 75, 188, 39, 17, 138,
              86, 205, 251, 96, 151, 12, 58, 161,
              79, 212, 226, 121, 142, 21, 35, 184,
              200, 83, 101, 254, 9, 146, 164, 63,
              209, 74, 124, 231, 16, 139, 189, 38,
              250, 97, 87, 204, 59, 160, 150, 13,
              227, 120, 78, 213, 34, 185, 143, 20,
              172, 55, 1, 154, 109, 246, 192, 91,
              181, 46, 24, 131, 116, 239, 217, 66,
              158, 5, 51, 168, 95, 196, 242, 105,
              135, 28, 42, 177, 70, 221, 235, 112,
              11, 144, 166, 61, 202, 81, 103, 252,
              18, 137, 191, 36, 211, 72, 126, 229,
              57, 162, 148, 15, 248, 99, 85, 206,
              32, 187, 141, 22, 225, 122, 76, 215,
              111, 244, 194, 89, 174, 53, 3, 152,
              118, 237, 219, 64, 183, 44, 26, 129,
              93, 198, 240, 107, 156, 7, 49, 170,
              68, 223, 233, 114, 133, 30, 40, 179,
              195, 88, 110, 245, 2, 153, 175, 52,
              218, 65, 119, 236, 27, 128, 182, 45,
              241, 106, 92, 199, 48, 171, 157, 6,
              232, 115, 69, 222, 41, 178, 132, 31,
              167, 60, 10, 145, 102, 253, 203, 80,
              190, 37, 19, 136, 127, 228, 210, 73,
              149, 14, 56, 163, 84, 207, 249, 98,
              140, 23, 33, 186, 77, 214, 224, 123]

# CRC16
CRC16_TABLE = [0, 4129, 8258, 12387, 16516, 20645, 24774, 28903,
               33032, 37161, 41290, 45419, 49548, 53677, 57806, 61935,
               4657, 528, 12915, 8786, 21173, 17044, 29431, 25302,
               37689, 33560, 45947, 41818, 54205, 50076, 62463, 58334,
               9314, 13379, 1056, 5121, 25830, 29895, 17572, 21637,
               42346, 46411, 34088, 38153, 58862, 62927, 50604, 54669,
               13907, 9842, 5649, 1584, 30423, 26358, 22165, 18100,
               46939, 42874, 38681, 34616, 63455, 59390, 55197, 51132,
               18628, 22757, 26758, 30887, 2112, 6241, 10242, 14371,
               51660, 55789, 59790, 63919, 35144, 39273, 43274, 47403,
               23285, 19156, 31415, 27286, 6769, 2640, 14899, 10770,
               56317, 52188, 64447, 60318, 39801, 35672, 47931, 43802,
               27814, 31879, 19684, 23749, 11298, 15363, 3168, 7233,
               60846, 64911, 52716, 56781, 44330, 48395, 36200, 40265,
               32407, 28342, 24277, 20212, 15891, 11826, 7761, 3696,
               65439, 61374, 57309, 53244, 48923, 44858, 40793, 36728,
               37256, 33193, 45514, 41451, 53516, 49453, 61774, 57711,
               4224, 161, 12482, 8419, 20484, 16421, 28742, 24679,
               33721, 37784, 41979, 46042, 49981, 54044, 58239, 62302,
               689, 4752, 8947, 13010, 16949, 21012, 25207, 29270,
               46570, 42443, 38312, 34185, 62830, 58703, 54572, 50445,
               13538, 9411, 5280, 1153, 29798, 25671, 21540, 17413,
               42971, 47098, 34713, 38840, 59231, 63358, 50973, 55100,
               9939, 14066, 1681, 5808, 26199, 30326, 17941, 22068,
               55628, 51565, 63758, 59695, 39368, 35305, 47498, 43435,
               22596, 18533, 30726, 26663, 6336, 2273, 14466, 10403,
               52093, 56156, 60223, 64286, 35833, 39896, 43963, 48026,
               19061, 23124, 27191, 31254, 2801, 6864, 10931, 14994,
               64814, 60687, 56684, 52557, 48554, 44427, 40424, 36297,
               31782, 27655, 23652, 19525, 15522, 11395, 7392, 3265,
               61215, 65342, 53085, 57212, 44955, 49082, 36825, 40952,
               28183, 32310, 20053, 24180, 11923, 16050, 3793, 7920]



# FUNCTIONS
def derivate(x, t):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        DERIVATE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Vectorize input
    x = np.array(x)
    t = np.array(t)

    # Compute deltas
    dx = x[1:] - x[:-1]
    dt = t[1:] - t[:-1]

    # Evaluate derivative
    D = dx / dt

    # Return derivative
    return list(D)



def integrate(x, t, args):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        INTEGRATE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This is a module that approximates the integral I of a given function x from
    a to b, given an equally spaced time vector t. In order to do that, it uses
    the Simpson method, and uses said time vector to evaluate the number n of
    intervals and the integration step h.
    """

    # Read limits of integral
    a = t[0]
    b = t[-1]

    # Delete last t to not add contribution of [b, b + h] to the integral!
    t = t[0:-1]

    # Read number of steps to integrate on
    n = len(t)

    # Compute integration step
    h = (b - a) / float(n)

    # Evaluate definite integral I of x from a to b
    I = np.sum(h/6 * (x(t, args) +
                      x(t + h/2, args) * 4 +
                      x(t + h, args)))

    # Give user info
    print "I[" + str(a) + ", " + str(b) + "] = " + str(I)

    # Return result of definite integral
    return I



def getPolyFitMax(x, y, n, N):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        GETPOLYFITMAX
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        f(x) = a_n * x^n + a_(n - 1) * x^(n - 1) + ... + a_0
    """

    # Generate nth-order polynomial fit
    a = np.polyfit(x, y, n)

    # Build x-axis
    x = np.linspace(x[0], x[-1], N)

    # Initialize y-axis
    y = np.zeros(N)

    # Loop through the n degrees of order
    for i in range(n):

        # Compute values on y-axis
        y += a[i] * x ** (n - i)

    # Find index of max
    index = np.argmax(y)

    # Return max
    return x[index]



def getMaxMiddle(x, y, threshold):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        GETMAXMIDDLE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get max
    yMax = np.max(y)

    # Initialize indices
    indices = []

    # Get indices or values near absolute max within threshold
    for i in range(len(x)):

        # Fits within threshold
        if y[i] >= (yMax - threshold):

            # Add index
            indices.append(i)

    # Get average index
    index = int(round(np.mean(indices)))

    # Return corresponding max
    return x[index]



def decodeTime(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        DECODETIME
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    second = x[0] & 63
    minute = x[1] & 63
    hour = x[2] & 31
    day = x[3] & 31
    month = ((x[0] & 192) >> 4) | ((x[1] & 192) >> 6)
    year = (x[4] & 127) + 2000

    return [year, month, day, hour, minute, second]



def formatTime(t):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        FORMATTIME
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Define time formats
    f = "%Y.%m.%d - %H:%M:%S"
    F = "%H:%M"

    # If datetime object
    if type(t) is datetime.datetime:

        t = datetime.datetime.strftime(t, f)

    # Otherwise
    else:

        # Try first format
        try:

            t = datetime.datetime.strptime(t, f)

        except:

            pass

        # Try second format
        try:

            t = datetime.datetime.strptime(t, F).time()

        except:

            pass

    # Return formatted time
    return t



def formatDate(t):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        FORMATDATE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # If datetime object
    if type(t) is datetime.datetime or type(t) is datetime.date:

        # Format date
        date = datetime.datetime.strftime(t, "%Y" + os.sep +
                                             "%m" + os.sep +
                                             "%d")

    # Otherwise
    else:

        # No date
        date = str(None)

    # Return formatted date
    return date



def normalizeTime(t, T):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        NORMALIZETIME
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Compare time to reference
    if t >= T:

        # Compute positive time difference (s)
        dt = (t - T).total_seconds()

    else:

        # Compute negative time difference (s)
        dt = -(T - t).total_seconds()

    # Convert time difference to hours
    dt /= 3600.0

    # Return time difference
    return dt



def encode(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ENCODE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    return [ord(i) for i in str(x).decode("HEX")]



def nMax(x, n = 1):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        NMAX
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get max possible number of output values
    n = min(n, len(x))

    # Initialize results
    X = []

    # Find n max values in x
    for i in range(n):

        # Get index of max value
        j = np.argmax(x)

        # Store value
        X.append(x[j])

        # Delete it from x
        del x[j]

    # Return results
    return X



def mergeDicts(base, new, n = 1):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MERGEDICTS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Note: dictionaries to merge must have same structure!
    """

    # On start
    if n == 1:

        # Check if dict given as input
        if type(new) is not dict:

            # Exit
            sys.exit("Only dicts can be merged.")

        # Copy base in order to not overwrite it
        base = copy.copy(base)

    # Loop over keys
    for key, value in new.items():

        # If dict/list
        if type(value) is dict:

            # If key does not exist in base
            if key not in base:

                # Generate new entry
                base[key] = {}

            # Dive in
            mergeDicts(base[key], value, n + 1)

        # Otherwise
        else:

            # If key already exists
            if key not in base:

                # Add key
                base[key] = value

            # Otherwise
            else:

                # Give user info
                print "Key already exists:"

                # Give user info
                print str(key) + ": " + str(value)

    # On end
    if n == 1:

        # Return it
        return base



def mergeNDicts(*args):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MERGENDICTS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Verify number of args
    if len(args) < 2:

        # Exit
        sys.exit("Feed at least 2 dictionaries to merge.")

    # Destructure dicts
    base, args = args[0], args[1:]

    # Loop on dicts
    for new in args:

        # Update base
        base = mergeDicts(base, new)

    # Give user info
    #print "New merged dictionary:"

    # Show it
    #printJSON(base)

    # Return updated base
    return base



def flatten(l):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        FLATTEN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    return [x for ll in l for x in ll]



def uniqify(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        UNIQIFY
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    return sorted(list(set(x)))



def hexify(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        HEXIFY
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    if type(x) is not list:
        x = [x]

    return ["{0:#04X}".format(y) for y in x]



def dehexify(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        DEHEXIFY
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    if type(x) is not list:
        x = [x]

    return [int(y, 16) for y in x]



def charify(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        CHARIFY
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    if type(x) is not list:
        x = [x]

    return ["." if (y < 32) | (y > 126) else chr(y) for y in x]



def XMLify(bytes):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        XMLIFY
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get number of bytes
    n = len(bytes)

    # Translate bytes
    bytes = translate(bytes)

    # Extract XML structure from bytes
    a = 0
    b = 0
    begun = False

    for i in range(n):

        if bytes[i] == "<" and not begun :
            a = i
            begun = True

        if bytes[i] == ">":
            b = i + 1

    return bytes[a:b]



def getByte(x, n):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        GETBYTE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This is a function that extracts the byte in position n of a integer x.
    """

    return (x >> (8 * n)) & 0xFF



def pack(x, order = ">", n = None):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        PACK
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This converts a natural number to its representation in bytes, given a
        minimal number of bytes to be returned in a certain order.
    """

    # Only natural numbers
    if x < 0 or int(x) != x:

        # Raise error
        raise ArithmeticError("Only natural numbers allowed.")

    # Compute minimum number of bytes required (no byte would not make sense)
    N = 1

    # Loop until number is covered
    while x >= 0xFF ** N:

        # Increase it
        N += 1

    # If number of wanted bytes not given
    if n is None:

        # Assign it minimum required
        n = N

    # If it is too small though
    elif n < N:

        # Raise error
        raise ArithmeticError("Minimum number of bytes required to represent " +
                              str(x) + ": " + str(N))

    # Initialize bytes and their string representation
    bytes = []
    bytes_ = []

    # Build bytes
    for i in range(n):

        # Compute ith byte
        bytes.insert(0, (x & (0xFF << (8 * i))) >> (8 * i))

    # Sort them according to given order
    # From MSB to LSB
    if order == ">":

        # Already ordered
        pass

    # From LSB to MSB
    elif order == "<":

        # Order
        bytes.reverse()

    # Otherwise
    else:

        # Raise error
        raise NotImplementedError("Unknown byte order.")

    # Build their string representation
    for b in bytes:

        # Convert byte to string
        byte = bin(b)[2:]

        # Fill with zeros
        while len(byte) != 8:

            # Add zero upfront
            byte = "0" + byte

        # Append byte
        bytes_.append(byte)

    # Return them
    return bytes



def unpack(bytes, order = ">"):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        UNPACK
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This is a function that converts a number expressed in an array of bytes
        to its decimal equivalent.
    """

    # Only natural numbers
    if np.any([not (int(b) == b and (0 <= b <= 0xFF)) for b in bytes]):

        # Raise error
        raise ArithmeticError("Invalid bytes to unpack in a number.")

    # Compute number of bytes
    n = len(bytes)

    # Initialize result
    x = 0

    # Unpack bytes in x
    for i in range(n):

        # From MSB to LSB
        if order == ">":

            # Add ith byte
            x += bytes[i] * 0x100 ** (n - 1 - i)

        # From LSB to MSB
        elif order == "<":

            # Add ith byte
            x += bytes[i] * 0x100 ** i

    # Return
    return x



def printJSON(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        PRINTJSON
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Print a dictionary using a particular JSON formatting.
    """

    print json.dumps(x, indent = 2, separators = (",", ": "), sort_keys = True)



def translate(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        TRANSLATE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This converts and returns the bytes received on the IN EP of a USB
        device.
    """

    return "".join([chr(y) for y in x])



def split(x, n):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        SPLIT
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This splits a string in groups of n characters and stores them in an
        array.
    """

    # Compute number of hexadecimal values within string
    N = int(math.ceil(len(x) / float(n)))

    # Return splitted string
    return [x[(n * i):(n * (i + 1))] for i in range(0, N)]



def checkIntWithinRange(byte, byteRange, error):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        CHECKINTWITHINRANGE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Test a byte to see if it is an integer and fits within given range.
        If not, raise input/output error.
    """

    # Test byte
    if not (int(byte) == byte and min(byteRange) <= byte <= max(byteRange)):

        # Raise error
        raise IOError(error)



def computeCRC8(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTECRC8
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Initialize CRC
    CRC = 0

    # Look for CRC in table
    for i in range(len(x)):

        # Compute it
        CRC = CRC8_TABLE[CRC ^ getByte(x[i], 0)]

    # Return CRC
    return CRC



def computeCRC16(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTECRC16
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Initialize CRC
    CRC = 0

    # Look for CRC in table
    for i in range(len(x)):

        # Compute it
        CRC = ((CRC * 256) & 65280) ^ CRC16_TABLE[((CRC / 256) & 255) ^ x[i]]

    # Return CRC
    return CRC & 65535



def newComputeCRC16(x):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        NEWCOMPUTECRC16
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Initialize CRC
    CRC = 65535

    # Look for CRC in table
    for i in range(len(x)):

        # Compute it
        CRC = (CRC16_TABLE[x[i] ^ CRC >> 8] ^ CRC << 8) & 65535

    # Return CRC
    return CRC



def getEP(configuration, direction, interface = 0, setting = 0):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        GETEP
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This finds a matching EP on a USB device given a configuration, a
        direction, an interface and a setting input, using the PyUSB library.
    """

    # Get direction
    # IN
    if direction == "IN":

        # Reassign it
        direction = usb.util.ENDPOINT_IN

    # OUT
    elif direction == "OUT":

        # Reassign it
        direction = usb.util.ENDPOINT_OUT

    # Otherwise
    else:

        # Raise error
        raise IOError("Bad EP direction: " + direction)

    # Return EP
    return usb.util.find_descriptor(configuration[(interface, setting)],
        custom_match = lambda e:
            usb.util.endpoint_direction(e.bEndpointAddress) == direction)
#! /usr/bin/python



"""
================================================================================
Title:    profile
Author:   David Leclerc
Version:  0.1
Date:     27.05.2016
License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)
Overview: ...
Notes:    ...
================================================================================
"""



# User-defined BG scale [mmol/l]
BG_SCALE = {"Extreme Low"  : 1.5,
            "Huge Low"     : 2.0,
            "Big Low"      : 2.5,
            "Low"          : 3.0,
            "Little Low"   : 3.5,
            "Tiny Low"     : 3.8,
            "Target Low"   : 4.0,
            "Target High"  : 7.0,
            "Tiny High"    : 8.0,
            "Little High"  : 10.0,
            "High"         : 12.0,
            "Big High"     : 15.0,
            "Huge High"    : 18.0,
            "Extreme High" : 20.0}

# Insulin to carbs ratios [U/(15g)]
IC = {"Morning"   : 3.0,
      "Afternoon" : 2.5,
      "Evening"   : 2.5,
      "Night"     : 2.5}

# Insulin sensitivity (or correction) factors [U/(mmol/l)]
ISF = {"Morning"   : 1.0,
       "Afternoon" : 1.0,
       "Evening"   : 1.0,
       "Night"     : 1.0}

# Duration of insulin action [h]
DIA = 4.0

# Time interval between BG readings [m]
BG_TIME_INTERVAL = 5.0

# Maximal allowed BG time-rate [(mmol/l)/h]
BG_MAX_RATE = 3.0



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    # Print out profile information
    print "User-defined BG scale [mmol/l]: " + str(BG_SCALE)
    print
    print "Insulin to carbs ratios [U/(15g)]: " + str(IC)
    print
    print "Insulin sensitivity factors [U/(mmol/l)]: " + str(ISF)
    print
    print "Duration of insulin action [h]: " + str(DIA)
    print
    print "Time interval between BG readings [m]: " + str(BG_TIME_INTERVAL)
    print
    print "Maximal allowed BG time-rate [(mmol/l)/m]: " + str(BG_MAX_RATE)
    print

    # End of script
    print "Done!"



# Run this when script is called from terminal
if __name__ == "__main__":
    main()

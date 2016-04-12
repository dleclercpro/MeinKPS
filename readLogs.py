"""

Title: parseLogs.py
Author: David Leclerc
Date: 12.04.16

"""



# Import libraries
import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as dates





# Define function to read Kahn reports
def readKahnReport(subject):

    # Read data from log
    print "Reading Kahn log..."
    log = "/home/david/Documents/MyAPS/Logs/data_" + str(subject) + ".txt"
    
    with open(log) as f:
        log_contents = f.readlines()

    n_log_entries = len(log_contents)

    # Parse data from logs
    print "Extracting blood sugar levels..."

    blood_sugar_times = np.zeros(n_log_entries, dtype = object)
    blood_sugar_levels = np.zeros(n_log_entries, dtype = float)

    for i in range(n_log_entries):

        # Parse entry
        log_entry = log_contents[i].replace("\n", "").split("\t")

        # Extract information from entry
        log_date = log_entry[0]
        log_time = log_entry[1]
        log_code = int(log_entry[2])
        log_value = 0.0555 * float(log_entry[3]) # Conversion from mg/dl to mmol/l
        log_timestamp = datetime.datetime.strptime(log_date + " " + log_time, \
            "%m-%d-%Y %H:%M")

        # Store plausible blood sugar levels
        if log_code > 35 and log_value > 0:
            blood_sugar_times[i] = log_timestamp
            blood_sugar_levels[i] = log_value

    # Delete array elements for leftout entries
    blood_sugar_times = blood_sugar_times[np.nonzero(blood_sugar_times)]
    blood_sugar_levels = blood_sugar_levels[np.nonzero(blood_sugar_levels)]

    return [blood_sugar_times, blood_sugar_levels]





# Define function to read Freestyle reports
def readFreestyleReport():

    # Read data from log
    print "Reading Freestyle log..."
    log = "/home/david/Documents/MyAPS/Logs/dataMe.txt"

    with open(log) as f:
        log_contents = f.readlines()    

    n_log_entries = len(log_contents) - 1 # Keeping header out of the count

    # Parse data from logs
    print "Extracting blood sugar levels..."

    blood_sugar_times = np.zeros(n_log_entries, dtype = object)
    blood_sugar_levels = np.zeros(n_log_entries, dtype = float)

    for i in range(1, n_log_entries):

        # Parse log entry
        log_entry = log_contents[i]

        for wrong_char in ["\x00", "\xff", "\xfe", "\r", "\n"]:
            log_entry = log_entry.replace(wrong_char, "")

        log_entry = log_entry.split("\t")

        # Extract information from entry
        log_value = 0.0555 * float(log_entry[10]) # Conversion from mg/dl to mmol/l
        log_timestamp = datetime.datetime(int("20" + log_entry[4]), \
            int(log_entry[2]), \
            int(log_entry[3]), \
            int(log_entry[5]), \
            int(log_entry[6]))

        # Store plausible blood sugar levels
        if log_value > 0:
            blood_sugar_times[i] = log_timestamp
            blood_sugar_levels[i] = log_value

    # Delete array elements for leftout entries
    blood_sugar_times = blood_sugar_times[np.nonzero(blood_sugar_times)]
    blood_sugar_levels = blood_sugar_levels[np.nonzero(blood_sugar_levels)]

    return [blood_sugar_times, blood_sugar_levels]





# Define function to generate graph of blood sugar levels (BSL)
def generateBSLGraph(blood_sugar_times, blood_sugar_levels, title, color):

    # Generate plot
    print "Generating plot of blood sugar levels..."

    # Define font
    matplotlib.rc("font", **{"family" : "Ubuntu"})

    # Define figure
    fig = plt.figure(0)
    fig.set_facecolor("white")
    fig.set_edgecolor("white")
    
    # Define subplots
    sp = plt.subplot(111, aspect = 1.0)
    sp.plot(blood_sugar_times, blood_sugar_levels, color = color, linewidth = 1.25)
    sp.set_axis_bgcolor("black")
    sp.grid(color = "grey")
    sp.set_title(title, weight = "bold", fontsize = 15)
    sp.set_xlabel("Time (days)", weight = "demibold")
    sp.set_ylabel("Blood Sugar Levels (mmol/L)", weight = "demibold")
    sp.xaxis.set_major_locator(dates.DayLocator(interval = 15))
    sp.xaxis.set_major_formatter(dates.DateFormatter("%d.%m.%Y"))

    # Tighten figure
    fig.tight_layout()

    # Show plot
    plt.show()





# Define main
def main():

    # Get blood sugar levels
    #[blood_sugar_times, blood_sugar_levels] = readKahnReport(1)
    [blood_sugar_times, blood_sugar_levels] = readFreestyleReport()

    # Plot blood sugar levels
    #generateBSLGraph(blood_sugar_times, \
        #blood_sugar_levels, \
        #"Blood Sugar Levels of Subject 1 Over the Course of 1991", \
        #"red")
    generateBSLGraph(blood_sugar_times, \
        blood_sugar_levels, \
        "My Blood Sugar Levels Over the Last Months", \
        "purple")

    # End of script
    print "Done!"





# Run script when called from terminal
if __name__ == "__main__":
    main()

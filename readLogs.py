"""

Title: parseLogs.py
Author: David Leclerc
Date: 11.04.16

"""



# Import libraries
import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as dates





# Define main
def main():

    # Read logs
    print "Reading logs..."
    log = "/home/david/Documents/MyAPS/Logs/data_1.txt"
    
    with open(log) as f:
        log_contents = f.readlines()

    n_log_entries = len(log_contents)



    # Extract data from logs
    print "Extracting blood sugar levels..."
    blood_sugar_levels = np.zeros(n_log_entries, dtype = float)
    blood_sugar_times = np.zeros(n_log_entries, dtype = object)

    for i in range(n_log_entries):

        log_entry = log_contents[i].replace("\n", "").split("\t")
        log_date = log_entry[0]
        log_time = log_entry[1]
        log_timestamp = datetime.datetime.strptime(log_date + " " + log_time, "%m-%d-%Y %H:%M")
        log_code = int(log_entry[2])
        log_value = 0.0555 * float(log_entry[3]) # Conversion from mg/dl to mmol/l

        # Only read plausible blood sugar levels
        if log_code > 35 and log_value >= 1.0:
            blood_sugar_levels[i] = log_value
            blood_sugar_times[i] = log_timestamp

    # Delete array elements for leftout entries
    blood_sugar_levels = blood_sugar_levels[np.nonzero(blood_sugar_levels)]
    blood_sugar_times = blood_sugar_times[np.nonzero(blood_sugar_times)]



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
    sp.plot(blood_sugar_times, blood_sugar_levels, color = "red", linewidth = 1.25)
    sp.set_axis_bgcolor("black")
    sp.grid(color = "grey")
    sp.set_title("Blood Sugar Levels of Subject 1 Over the Course of 1991", weight = "bold", fontsize = 15)
    sp.set_xlabel("Time (days)", weight = "demibold")
    sp.set_ylabel("Blood Sugar Levels (mmol/L)", weight = "demibold")
    sp.xaxis.set_major_locator(dates.DayLocator(interval = 15))
    sp.xaxis.set_major_formatter(dates.DateFormatter("%d.%m.%Y"))

    # Tighten figure
    fig.tight_layout()

    # Show plot
    plt.show()



    # End of script
    print "Done!"





# Run script when called from terminal
if __name__ == "__main__":
    main()

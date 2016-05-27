#! /usr/bin/python



"""
================================================================================
Title:    readNightscout
Author:   David Leclerc
Version:  0.1
Date:     26.05.2016
License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)
Overview: ...
Notes:    ...
================================================================================
"""



# Import libraries
import datetime
import requests
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as dates



# Define start of acquisition
now = datetime.datetime.now()



# Define Nightscout URL
url = "http://openaps30.herokuapp.com"



# Define BG scale
bg_scale_mmol_l = {"High" : 12.0, "Target High" : 7.0, "Target Low" : 4.0}
bg_scale_mg_dl = {i : int(18.0 * bg_scale_mmol_l[i]) for i in bg_scale_mmol_l}
bg_scale = {"mmol/l" : bg_scale_mmol_l, "mg/dl" : bg_scale_mg_dl}



# Define number of BG measurements wished
units = "mmol/l"
request = 1000



# Retrieve source code containing BG values to Nightscout API endpoint "ENTRIES"
source_code = requests.get(url + "/api/v1/entries?count=" + str(request)).text



# Extract BG values from source code
t = np.array([datetime.datetime.strptime(i[0], "%Y-%m-%dT%H:%M:%S.000Z")
    for i in [j.split("\t") for j in source_code.split("\n")]])
BG_mg_dl = np.array([i[2] for i in [j.split("\t")
    for j in source_code.split("\n")]], float)
BG_mmol_l = BG_mg_dl / 18.0
BG = {"mmol/l" : BG_mmol_l, "mg/dl" : BG_mg_dl}



# Actual number of measurements imported
count = len(t)



# Initialize plot
mpl.rc("font", size = 11, family = "Ubuntu")
fig = plt.figure(0, figsize = (12, 10))
sp = plt.subplot(111)

# Define plot title
sp.set_title("Last " + str(count) + " BG values imported from Nightscout" +
             " webpage " + url + ", starting on " + now.strftime("%Y.%m.%d") +
             " at " + now.strftime("%H:%M"), weight = "semibold")

# Define plot axis
sp.set_xlabel("Time", weight = "semibold")
sp.set_ylabel("BG (" + units + ")", weight = "semibold")

# Add grid to plot
sp.grid(color = "grey")

# Add target limits
sp.plot(t, bg_scale[units]["Target Low"] * np.ones(len(t)),
    ls = "--", lw = 1.5, c = "grey")
sp.plot(t, bg_scale[units]["Target High"] * np.ones(len(t)),
    ls = "--", lw = 1.5, c = "orange")
sp.plot(t, bg_scale[units]["High"] * np.ones(len(t)),
    ls = "--", lw = 1.5, c = "red")

# Plot BG values and corresponding times
sp.plot(t, BG[units], ls = "-", lw = 1.5, c = "black")

# Add time ticks to x-axis
sp.xaxis.set_major_locator(dates.HourLocator(interval = 3))
sp.xaxis.set_major_formatter(dates.DateFormatter("%H:%M"))

# Change background color of plot
#sp.set_axis_bgcolor("black")

# Format x-axis for beautiful displaying of dates!
for tick in sp.get_xticklabels():
    tick.set_rotation(45)

# Tighten everything up!
fig.tight_layout()

# Show plot
plt.show()

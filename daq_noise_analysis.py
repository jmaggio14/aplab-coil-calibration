"""
Author: Jeff Maggio
Date: May 27, 2019

Description:

    This file is a modifiable script to analyze the DAQ's read noise

    The code in this file reads in data that was collected in our coil
    testing setup, however the source of the signal was a function generator
    outputing a DC voltage:
        1) 50mV
        2) 150mV
        3) 500mV
        4) 2500mV

    **Only channel 1 is used**

Assumptions:
    1) The read noise is constant at all frequencies, this is not technically
    true, but is often a safe assumption to make especially at low frequency
    signals (<100khz)

    2) Read Noise is normally distrubuted, this is standard

    3) Signal Generator produces a perfect signal

    4) Channel 1 is representative of all channels


Data Format:
    Data must be in csv file shaped as such:

    timestamp (in seconds), channel1 Volts, channel2 Volts (unused), channel3 Volts (unused),
"""


import numpy as np
import matplotlib.pyplot as plt

FILENAME = "DAQ_noise_characterization/FG_50mv_dc.csv"
DC_VOLTAGE = 50e-3 #Volts

data = np.genfromtxt(FILENAME, skip_header=1, usecols=(1,), delimiter=",")

#subtract the DC voltage so we are only looking at the noise
data = data - DC_VOLTAGE

# find average and std
avg = np.mean(data)
std = np.std(data)

# plot the curve
fig = plt.figure()

plt.hist(data)
plt.axvline(avg,color='black')
plt.savefig(str(DC_VOLTAGE) + 'mv.png')
plt.show()

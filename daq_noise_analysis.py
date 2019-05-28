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
    (in practice, I observe a skew left)

    3) Signal Generator produces a perfect signal
    (checked with the oscilloscope)

    4) Channel 1 is representative of all channels


Data Format:
    Data must be in csv file shaped as such:

    timestamp (in seconds), channel1 Volts, channel2 Volts (unused), channel3 Volts (unused),
"""


import numpy as np
import matplotlib.pyplot as plt

FILENAMES = ["DAQ_noise_characterization/FG_DC_20mv.csv",
                "DAQ_noise_characterization/FG_DC_100mv.csv",
                "DAQ_noise_characterization/FG_DC_200mv.csv",
                "DAQ_noise_characterization/FG_DC_600mv.csv",
                "DAQ_noise_characterization/FG_DC_1000mv.csv",
                "DAQ_noise_characterization/FG_DC_2000mv.csv",
                "DAQ_noise_characterization/FG_DC_4000mv.csv",
                ]
#
DC_VOLTAGES = [20, 100, 200, 600, 1000, 2000, 4000] #millivolts


NUM_BINS = 100


means = []
stds = []
snrs = []
figs = []

for i,(fname,voltage) in enumerate(zip(FILENAMES,DC_VOLTAGES)):

    fig = plt.figure()
    # fig.add_subplot(3, 2, i+1)
    axes = plt.gca()

    print("computing plot for {}mv...".format(voltage))

    data = np.genfromtxt(fname, skip_header=1, usecols=(1,), delimiter=",")

    #convert to millivolts and subtract our voltage
    data = (data * 1000) - voltage

    # find average and std
    avg = np.mean(data)
    std = np.std(data)


    plt.hist(data, int(NUM_BINS))
    # plt.plot(data)

    plt.xlabel("Voltage (millivolts)")
    plt.ylabel("counts")
    plt.title("Histogram of deviations from given {}mv DC signal (DAQ - no amp)".format(voltage))

    # calculate std ticks
    deviations = [avg + (std*i) for i in range(-3,4)]
    axes.set_xticks(deviations)
    axes.set_xticklabels([str(round(dev,2)) + 'mv' for dev in deviations])

    plt.axvline(avg,color='black')

    means.append(avg)
    stds.append(std)
    snrs.append( avg / std )
    figs.append(fig.number)



# plt.savefig(str(voltage) + 'mv.svg')
for fig in figs:
    plt.figure(fig)
    plt.show()

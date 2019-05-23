"""
This is an attempted recreation of Zhetuo's calibration map


Some assumption that are made:
    1) optitrack and coil data are perfectly synced. This should in theory be true
    because optitrack triggers coil data collection

    2) a gaussian filter with a frequency sigma of 1 Hz is appropriate to separate
    out channels

    3)
"""


# first we need to import these
# to access Python's scientific processing package (a "toolbox")
import numpy as np
import scipy
from scipy import signal

COIL_FILENAME = None
OPTITRACK_FILENAME = None
FILTER_TYPE = 'gaussian' # 'butter' is also acceptable
FILTER_SIGMA = 1 # +/- hertz from nominal

# You may ignore this code
# this just lets us pass in data filenames via the command line
import argparse

parser = argparse.ArgumentParser()
parse.add_argument("--opti", default = None)
parse.add_argument("--coil", default = None)

args = parser.parse_args()

if args.opti:
    OPTITRACK_FILENAME = args.opti

if args.coil:
    COIL_FILENAME = args.coil

############################# REAL CODE STARTS HERE ############################

# read in data from csv files into numpy arrays
# SAMPLES IS ROWS, SAMPLE DATA IS COLUMNS
coil_data = np.genfromtxt(COIL_FILENAME, skip_header=1, delimiter=",")
optitrack_data = np.genfromtxt(OPTITRACK_FILENAME, skip_header=1, delimiter=",")

# coil data is now an array shaped like the following
# 1 | timestamp, coil1_Volts, coil2_Volts, coil3_Volts
# 2 | timestamp, coil1_Volts, coil2_Volts, coil3_Volts
# 3 | timestamp, coil1_Volts, coil2_Volts, coil3_Volts
# ...

# optirack data is now an array shaped like the following
# 1 | frame_index, timestamp, x, y, z, qx, qy, qz, qw
# 2 | frame_index, timestamp, x, y, z, qx, qy, qz, qw
# 3 | frame_index, timestamp, x, y, z, qx, qy, qz, qw
# ...


################################################################################
# STEP 1
# get the coil data into a workable format. We need to separate each frequency
# component
# I do this with a gaussian filter of sigma = 1HZ, with truncation at 4sigma

# remove the timestamps from the data
channels = coil_data[:,1:]
# calculate an FFT
channels_fft = np.fft.fft(channels, axis=0)

# construct a quick frequency filtering function for convienence
# uses scipy.signal.get_window to create the profile
def freq_filter(data, low, high, fs):
    """filters the data along axis=0 using a gaussian or butterworth filter to
    extract the correct frequency band

    Args:
        data (np.ndarray): the data to filter, shape can be arbitrary as long
            as samples is rows
        low (float): the low cutoff of the gaussian band
        high (float): the high cutoff of the gaussian band
        fs (float): the sampling frequency


    Returns:
        np.ndarray : the filtered data
        np.ndarray : an array detailing the filter's frequency response

    """


    window = signal.gaussian



    return freq_response

freq_12k =
freq_16k =
freq_20k =



# STEP 1 - downsample coil data to match the size of optitrack data
# this is significant downsampling 100,000 HZ --> 240 HZ (or 120HZ)
# for this, I simply averaged to downsample













#END

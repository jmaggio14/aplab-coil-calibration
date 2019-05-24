"""
This is an attempted recreation of Zhetuo's calibration map


Some assumption that are made:
    1) optitrack and coil data are perfectly synced. This should in theory be true
    because optitrack triggers coil data collection

    2)
"""
COIL_FILENAME = None
OPTITRACK_FILENAME = None
BUTTER_ORDER = 3 # small is more gaussian, large is more ideal

NOMINAL_12K_VOLTS = 1
NOMINAL_16K_VOLTS = 1
NOMINAL_20K_VOLTS = 1

SYS_PHASE_OFFSET_CH1 = 0
SYS_PHASE_OFFSET_CH2 = 0
SYS_PHASE_OFFSET_CH3 = 0

###################### SETUP CODE - CAN BE SAFELY IGNORED ######################

# first we need to import these to access Python's scientific
# processing package (a "toolbox")
import numpy as np
import scipy
from scipy import signal


# You may ignore this code
# this just lets us pass in data filenames via the command line
import argparse

parser = argparse.ArgumentParser()
parse.add_argument("--opti", default = None)
parse.add_argument("--coil", default = None)
parse.add_argument("--order", default = None)

parse.add_argument("--nom_12k", default = None)
parse.add_argument("--nom_16k", default = None)
parse.add_argument("--nom_20k", default = None)


parse.add_argument("--sys_phase1", default = None)
parse.add_argument("--sys_phase2", default = None)
parse.add_argument("--sys_phase3", default = None)

args = parser.parse_args()

# overwrite global variables if provided
if args.opti:
    OPTITRACK_FILENAME = args.opti
if args.coil:
    COIL_FILENAME = args.coil
if args.order:
    BUTTER_ORDER = args.order

if args.nom_12k:
    NOMINAL_12K_VOLTS = args.nom_12k
if args.nom_16k:
    NOMINAL_16K_VOLTS = args.nom_16k
if args.nom_20k:
    NOMINAL_20K_VOLTS = args.nom_20k


if args.sys_phase1:
    SYS_PHASE_OFFSET_CH1


############################# REAL CODE STARTS HERE ############################

# read in data from csv files into numpy arrays
# SAMPLES IS ROWS, SAMPLE DATA IS COLUMNS
coil_data = np.genfromtxt(COIL_FILENAME, skip_header=1, delimiter=",")
optitrack_data = np.genfromtxt(OPTITRACK_FILENAME, skip_header=1, delimiter=",")

# num samples / maximum timecode in the data
SAMPLING_FREQUENCY = coil_data.shape[0] / coil_data[0][-1]

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
# I do this with a butterworth filter of tuneable order with a typical
# cutoff of desired +/- 1hz

# construct a quick frequency filtering function for convienence
# uses scipy.signal.get_window to create the profile
def freq_filter(data, low, high, order, fs):
    """filters the data along axis=0 using butterworth filter to
    extract the correct frequency band

    Args:
        data (np.ndarray): the data to filter, shape can be arbitrary as long
            as samples is rows
        low (float): the low cutoff of the filter (in HZ)
        high (float): the high cutoff of the filter (in HZ)
        order (int): the order of the butterworth filter,
            this affects the shape of the filter frequency response
        fs (float): the sampling frequency


    Returns:
        np.ndarray : the filtered data
        np.ndarray : an array detailing the filter's frequency response
    """

    # convert low and high as fraction of the nyquist frequency
    nyquist = fs / 2
    low_ = low / nyquist
    high_ = high / nyquist

    # apply the butterworth filter
    b, a = signal.butter(order, [low_, high_], btype="band")
    # WARNING, THIS MAY APPLY A PHASE SHIFT
    # maybe use this instead? https://docs.scipy.org/doc/scipy-1.1.0/reference/generated/scipy.signal.filtfilt.html#scipy.signal.filtfilt
    filtered = signal.lfilter(b, a, data, axis=0)

    # calculate the frequency respone of the filter
    # check frequencies from 10K to 22K
    freq_to_check = np.linspace(10e3, 22e3, 2)
    w, h = signal.freqz(b, a, worN=freq_to_check, fs=fs)
    return filtered


# remove the timestamps from the data
channels = coil_data[:,1:]

# apply our butterworth filter
filtered_12k = freq_filter(channels, 12e3-1, 12e3+1, BUTTER_ORDER, SAMPLING_FREQUENCY)
filtered_16k = freq_filter(channels, 16e3-1, 16e3+1, BUTTER_ORDER, SAMPLING_FREQUENCY)
filtered_20k = freq_filter(channels, 20e3-1, 20e3+1, BUTTER_ORDER, SAMPLING_FREQUENCY)
# SAMPLES IS ROWS
# COIL INDEX IS COLUMNS


################################################################################
# STEP 2
# Amplitude calculation
# retreive the Amplitude of the waveform using hilbert transformation
# see: https://www.gaussianwaves.com/2017/04/extracting-instantaneous-amplitude-phase-frequency-hilbert-transform/
# and: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.hilbert.html

# ANALYSICAL SIG TEST
# analytical_sig = signal.hilbert(filtered, axis=0)
# amplitude = np.abs(analytical_sig)
# phase = np.angle(analytical_sig)

# FFT SIG TEST
fft_12k = np.fft.fft(filtered_12k, axis=0)
amplitude_12k = np.abs(fft_12k)
phase_12k = np.angle(fft_12k)

fft_16k = np.fft.fft(filtered_16k, axis=0)
amplitude_16k = np.abs(fft_16k)
phase_16k = np.angle(fft_16k)

fft_20k = np.fft.fft(filtered_20k, axis=0)
amplitude_20k = np.abs(fft_20k)
phase_20k = np.angle(fft_20k)


################################################################################
# STEP 3
# upsample optitrack data using nearest neighbor interpolation
# NOTE: this may be improved by looking at timesamples and matching up
# corresponding values - although I struggle to think of a fast way to do it

# TIMESAMPLE method - this is relatively ugly and inefficient,
# NOTE: a numpy.where approach would be much faster
# but it should still be a relatively fast relative to the rest of the pipeline
coil_timestamps = coil_data[:,0]
optitrack_timestamps = optitrack_data[:,1]
upsampled_frames = []
# this next variable is intended to increase speed - hopefully turn from O(n^2) closer to O(N)
coil_offset = 0

# loop through and duplicate optitrack data where timestamps match up
for i in range(optitrack_timestamps):
    for j in range(coil_offset, coil_timestamps.size):
        opti_t = optitrack_timestamps[i]
        coil_t = optitrack_timestamps[j]
        if coil_t <= opti_t:
            upsampled_frames.append(optitrack_data[i,:])
        else:
            coil_offset = j
            break

# convert from list to array
upsampled_opti = np.vstack(upsampled_frames)
# sanity check - make sure that the upsampled optirack data has the same number of samples
# as our amplitude array
assert upsampled_opti.shape[0] == amplitude.shape[0]


################################################################################
# STEP 4
# Calculate the rotation of each coil relative to each axis (nominal voltage)

# sanity check/warning - see if the nominal voltage is smaller than the maximum
# observed in the signal
# 12 Khz
max_12k = filtered_12k.max()
max_16k = filtered_16k.max()
max_20k = filtered_20k.max()
if max_12k > NOMINAL_12K_VOLTS:
    print("WARNING: 12Khz maximum ({}) is greater than the 12Khz Nominal ({})".format(max_12k, NOMINAL_12K_VOLTS))
    print("WARNING: reseting 12K nominal to {}".format(max_12k))
    NOMINAL_12K_VOLTS = max_12k

if max_16k > NOMINAL_16K_VOLTS:
    print("WARNING: 16Khz maximum ({}) is greater than the 16Khz Nominal ({})".format(max_16k, NOMINAL_16K_VOLTS))
    print("WARNING: reseting 16K nominal to {}".format(max_16k))
    NOMINAL_16K_VOLTS = max_16k

if max_20k > NOMINAL_20K_VOLTS:
    print("WARNING: 20Khz maximum ({}) is greater than the 20Khz Nominal ({})".format(max_20k, NOMINAL_20K_VOLTS))
    print("WARNING: reseting 20K nominal to {}".format(max_20k))
    NOMINAL_20K_VOLTS = max_20k


    # where theta is such that parallel at theta=90, perpendicular at theta=0
    # where nominal would be a calibration constant, collected when the coil is perfectly perpendicular
    #
    # coil_voltage = cos(theta) * nominal_voltage
    # cos(theta) = coil_voltage / nominal_voltage | (in other words, we normalize it)
    # theta = arccos( coil_voltage / nominal) | this gives us the abs(angle)
    #
    # we can use this to determine a normal vector component

# Divide by the nominal to normalize the data
amplitude_12k = amplitude_12k / NOMINAL_12K_VOLTS
amplitude_16k = amplitude_16k / NOMINAL_16K_VOLTS
amplitude_20k = amplitude_20k / NOMINAL_20K_VOLTS

# calculate each coils rotation relative to the field
theta_12k = np.arccos( amplitude_12k )
theta_16k = np.arccos( amplitude_16k )
theta_20k = np.arccos( amplitude_20k )
























#END

"""
RUEI PLEASE READ THIS!


Capture and Calibration Procedure
----------------------------------
(will become more detailed and fleshed out as we develop hardware)

1) Using an function generator, push a 16Khz through the channel 1 amp
    - using a T connector and an oscilloscope:
        * observe the waveforms for the amplified & raw signal
        * record the phase offset (amplified_phase - raw_phase)
        * this will become SYS_PHASE_OFFSET_CH1

    ***repeat for all channels***
    (maybe do this for each frequency? amps are wide band so they'll probably have a constant
    phase offset as a function of frequency)

2) using a to-be-made calibration box, align the measurment coil perpendicular
to the axis to be measured.
    - Run it through the filters we use in this file
    - Record the value (this will become our CALIBRATION_MAX)

3) align the coil parallel to the measurment axis
    - Run it through the filters we use in this file
    - Record the value (this will become our CALIBRATION_MIN)




Assumptions:
    1) optitrack and coil data are perfectly synced. (they are hardware synced,
    so this should be the case to within 1/optitrack_framerate )

    2) all three coils are perfectly orthagonal to each other

"""
COIL_FILENAME = None
OPTITRACK_FILENAME = None

BUTTER_ORDER = 3 # small is more gaussian, large is more ideal
BANDWIDTH = 2 # HZ

CALIBRATION_MAX_12K = 1
CALIBRATION_MAX_16K = 1
CALIBRATION_MAX_20K = 1

CALIBRATION_MIN_12K = 0
CALIBRATION_MIN_16K = 0
CALIBRATION_MIN_20K = 0

SYS_PHASE_OFFSET_CH1 = 0
SYS_PHASE_OFFSET_CH2 = 0
SYS_PHASE_OFFSET_CH3 = 0

###################### SETUP CODE - CAN BE SAFELY IGNORED ######################

# TODO: swap out global variables for a calibration file


# first we need to import these to access Python's scientific
# processing package (a "toolbox")
import numpy as np
import scipy
from scipy import signal, interpolate


# You may ignore this code
# this just lets us pass in data filenames via the command line
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--opti", default = None)
parser.add_argument("--coil", default = None)
parser.add_argument("--calib", default = None)


parser.add_argument("--filter-order", default = None)
parser.add_argument("--force-calibration", default = False)

args = parser.parse_args()

# overwrite global variables if provided
if args.opti:
    OPTITRACK_FILENAME = args.opti
if args.coil:
    COIL_FILENAME = args.coil

# TO DO LOAD - LOAD IN CALIBRATION FILE AND FURTHER DEFINE GLOBALS


############################# REAL CODE STARTS HERE ############################

# read in data from csv files into numpy arrays
# SAMPLES IS ROWS, SAMPLE DATA IS COLUMNS
coil_data = np.genfromtxt(COIL_FILENAME, skip_header=1, delimiter=",")
optitrack_data = np.genfromtxt(OPTITRACK_FILENAME, skip_header=1, delimiter=",")

# num samples / maximum timecode in the data
SAMPLING_FREQUENCY = coil_data.shape[0] / coil_data[0][-1]

# coil data is now an array shaped like the following (for 3 coils)
# all coil units in volts
# 1 | timestamp, coil1, coil2, coil3, ref_coil1, ref_coil2, ref_coil3
# 2 | timestamp, coil1, coil2, coil3, ref_coil1, ref_coil2, ref_coil3
# 3 | timestamp, coil1, coil2, coil3, ref_coil1, ref_coil2, ref_coil3
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
    freq_to_check = np.linspace(10e3, 22e3, 6000)
    w, h = signal.freqz(b, a, worN=freq_to_check, fs=fs)
    return filtered, (w, h)


# remove the timestamps from the data
channels = coil_data[:,1:]

# apply our butterworth filter
offset = BANDWIDTH / 2
filtered_12k, _ = freq_filter(channels, 12e3-offset, 12e3+offset, BUTTER_ORDER, SAMPLING_FREQUENCY)
filtered_16k, _ = freq_filter(channels, 16e3-offset, 16e3+offset, BUTTER_ORDER, SAMPLING_FREQUENCY)
filtered_20k, _ = freq_filter(channels, 20e3-offset, 20e3+offset, BUTTER_ORDER, SAMPLING_FREQUENCY)

# SAMPLES IS ROWS
# COIL INDEX IS COLUMNS


################################################################################
# STEP 2
# Amplitude calculation
# retreive the Amplitude of the waveform using a fourier transform
#
# maybe use analytical hilbert transformation?
# see: https://www.gaussianwaves.com/2017/04/extracting-instantaneous-amplitude-phase-frequency-hilbert-transform/
# and: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.hilbert.html

# ANALYSICAL SIG TEST - ignore
# analytical_sig = signal.hilbert(filtered, axis=0)
# amplitude = np.abs(analytical_sig)
# phase = np.angle(analytical_sig)

# FFT SIG TEST
fft_12k = np.fft.fft(filtered_12k, axis=0)
amplitude_12k = np.abs(fft_12k)
uncalib_phase_12k = np.angle(fft_12k)

fft_16k = np.fft.fft(filtered_16k, axis=0)
amplitude_16k = np.abs(fft_16k)
uncalib_phase_16k = np.angle(fft_16k)

fft_20k = np.fft.fft(filtered_20k, axis=0)
amplitude_20k = np.abs(fft_20k)
uncalib_phase_20k = np.angle(fft_20k)

# break up measurement and reference coil data into separate arrays
coil_amp_12k, ref_amp_12k = amplitude_12k[:,:3], amplitude_12k[:,3:]
coil_amp_16k, ref_amp_16k = amplitude_16k[:,:3], amplitude_16k[:,3:]
coil_amp_20k, ref_amp_20k = amplitude_20k[:,:3], amplitude_20k[:,3:]

# WE WILL DEAL WITH PHASE IN LATER STEPS



################################################################################
# STEP 3
# Calculate nominal rotation of the coil relative to the magnetic flux,
# This reduces our problem to one of four angles - see "Amplitude Ambiguity"
# diagram in the README for more information


# --------------------------------------------------------------------------------
## MICHELE AND RUEI
## you can probably skip these if-statements, they are for debugging. not for computation
# --------------------------------------------------------------------------------

# sanity check/warning - see if the calibration mins and maxes don't line up with
# what was observed in the signal
# find maxes
coil_max_12k = coil_amp_12k.max()
coil_max_16k = coil_amp_16k.max()
coil_max_20k = coil_amp_20k.max()
# find mins
coil_min_12k = coil_amp_12k.min()
coil_min_16k = coil_amp_16k.min()
coil_min_20k = coil_amp_20k.min()

# 12K
if coil_max_12k > CALIBRATION_MAX_12K:
    print("WARNING: observed 12Khz maximum ({}) is greater than the 12Khz Calibration Maximum ({})".format(coil_max_12k, CALIBRATION_MAX_12K))
    print("WARNING: reseting 12K nominal to {}".format(coil_max_12k))
    CALIBRATION_MAX_12K = coil_max_12k
if coil_min_12k < CALIBRATION_MIN_12K:
    print("WARNING: observed 12Khz minimum ({}) is less than the 12Khz Calibration Minimum ({})".format(coil_min_12k, CALIBRATION_MIN_12K))
    print("WARNING: reseting 12K minimum to {}".format(coil_min_12k))
    CALIBRATION_MIN_12K = coil_min_12k

# 16K
if coil_max_16k > CALIBRATION_MAX_16K:
    print("WARNING: observed 16Khz maximum ({}) is greater than the 16Khz Calibration Maximum ({})".format(coil_max_16k, CALIBRATION_MAX_16K))
    print("WARNING: reseting 16K nominal to {}".format(coil_max_16k))
    CALIBRATION_MAX_16K = coil_max_16k
if coil_min_16k < CALIBRATION_MIN_16K:
    print("WARNING: observed 16Khz minimum ({}) is less than the 16Khz Calibration Minimum ({})".format(coil_min_16k, CALIBRATION_MIN_16K))
    print("WARNING: reseting 16K minimum to {}".format(coil_min_16k))
    CALIBRATION_MIN_16K = coil_min_16k

# 20K
if coil_max_20k > CALIBRATION_MAX_20K:
    print("WARNING: observed 20Khz maximum ({}) is greater than the 20Khz Calibration Maximum ({})".format(coil_max_20k, CALIBRATION_MAX_20K))
    print("WARNING: reseting 20K nominal to {}".format(coil_max_20k))
    CALIBRATION_MAX_20K = coil_max_20k
if coil_min_20k < CALIBRATION_MIN_20K:
    print("WARNING: observed 20Khz minimum ({}) is less than the 20Khz Calibration Minimum ({})".format(coil_min_20k, CALIBRATION_MIN_20K))
    print("WARNING: reseting 20K minimum to {}".format(coil_min_20k))
    CALIBRATION_MIN_20K = coil_min_20k


# theta is such that parallel at theta=90, perpendicular at theta=0
# calibration max and min would be collected when the coil is perfectly perpendicular or parallel respectively
#
# coil_voltage = cos(theta) * nominal_voltage
# cos(theta) = coil_voltage / nominal_voltage | (in other words, we normalize it)
# theta = arccos( coil_voltage / nominal) | this gives us the abs(angle)
#
# we can use this to determine a normal vector component

# Normalize the amplitude
coil_amp_12k = (coil_amp_12k - CALIBRATION_MIN_12K) / (CALIBRATION_MAX_12K - CALIBRATION_MIN_12K)
coil_amp_16k = (coil_amp_16k - CALIBRATION_MIN_16K) / (CALIBRATION_MAX_16K - CALIBRATION_MIN_16K)
coil_amp_20k = (coil_amp_20k - CALIBRATION_MIN_20K) / (CALIBRATION_MAX_20K - CALIBRATION_MIN_20K)

# calculate each coils rotation relative to the field
# This will give us an angle between 0 and pi/2 (which is one of only 4
# possibilites)
theta_12k = np.arccos( coil_amp_12k )
theta_16k = np.arccos( coil_amp_16k )
theta_20k = np.arccos( coil_amp_20k )



################################################################################
# STEP 4
# Calibrate the phase information
#
# account for the phase offset inherent in system measurement
# this is usually caused by our amplifiers, which will have to be manually
# measured with an oscilloscope and recorded in our calibration file

# pull out the reference coil data before we forget about it
ref_phase_12k = uncalib_phase_12k[:,3:]
ref_phase_16k = uncalib_phase_16k[:,3:]
ref_phase_20k = uncalib_phase_20k[:,3:]

# it's easier here to stack all data into a single array and subtract our offset
# from the third axis which represents channels
uncalib_coil_phase = np.dstack( (uncalib_phase_12k[:,:3], uncalib_phase_16k[:,:3], uncalib_phase_20k[:,:3]) )
# ------------------------------------------------------------------------------
# this array only contains measurement coil data NOT reference coil data!!!!!!!
# ------------------------------------------------------------------------------

coil_phase_12k = uncalib_coil_phase[:,:,0] - SYS_PHASE_OFFSET_CH1
coil_phase_16k = uncalib_coil_phase[:,:,1] - SYS_PHASE_OFFSET_CH2
coil_phase_20k = uncalib_coil_phase[:,:,2] - SYS_PHASE_OFFSET_CH3
# SAMPLES IS ROWS
# COIL INDEX IS COLUMNS
# CHANNELS IS BANDS (third axis)


################################################################################
# STEP 5
# determine the direction of magnetic flux for each frequency
# this reduces our problem to **2 possibile solutions**
#
# with system phase accounted for in the calibration procedure, the reference
# coil and measurement coil phase should always be separated by a phase offset
# of 0 or pi/2
#
# we should therefore be able to digitize this signal and use this along with
# the theta calculated before to generate a unit vector indicating coil orientation
#
# if the flux is pass is passing through the coil back to front, then we are positve

# subtact the reference phase from the measured phase
relative_phase_12k = coil_phase_12k - ref_phase_12k
relative_phase_16k = coil_phase_16k - ref_phase_16k
relative_phase_20k = coil_phase_20k - ref_phase_20k

# ------------------------------------------------------------------------------
# MICHELE AND RUEI, PLEASE AUDIT ME HERE
# I could very well have made a mistake in this section
#
# how to account for a theoretical situation in which the relative phase
# is greater than pi/2? maybe mod by pi/2 or clip the array. This shouldn't happen, but might
# happen as a result of measurment error or bad calibration
# ------------------------------------------------------------------------------

# all phase between 0 and pi/4 --> 0
# all phase between pi/4 and pi/2 --> +1

# use integer division to binarize the signal between 0 and 1
# zeros in this case mean that the measurment coil is parallel to the flux
# everything in this array should be 0 or 1
direction_12k = (relative_phase_12k // (np.pi/2))
direction_16k =  (relative_phase_16k // (np.pi/2))
direction_20k =  (relative_phase_20k // (np.pi/2))

# 0 indicates the flux is going through the coil back to front
# 1 indicates the flux is going through the coil front to back (angular rotation of 180 degrees)
#
# in effect, this array represents the following (example data)
#        coil1      |       coil2       |     coil3
#     ------------------------------------------------
# 1)  front->back   |    back->front    |  front->back
# 2)  front->back   |    front->back    |  back->front
# 3)  front->back   |    front->back    |  front->back
# ...
#
# ROWS IS SAMPLES
# COLUMNS IS COILS

# combine amplitude-derived theta with our new direction information
# this should just be equal to amplitude * (direction * pi)
# the pi will rotate the value of theta 180 degrees and eliminate two possible
# solutions to the problem

theta_12k = theta_12k + (direction_12k * np.pi)
theta_16k = theta_16k + (direction_16k * np.pi)
theta_20k = theta_20k + (direction_20k * np.pi)
# ROWS IS SAMPLES
# COLUMNS IS COILS

# --------------------------------------------------------------------------------
# There are now two possible solutions to our problem, see figure 3 for
# the explanation why
# --------------------------------------------------------------------------------


################################################################################
# STEP 6
# Solve the coil rotation using a second orthagonal axis
#
# So far we have been computing every axis completely independently from one
# another. However to solve system, we'll need to check the relative phase of
# a second field and determine whether an addition 45 degree rotation is necessary

theta_12k = theta_12k * (direction_16k * np.pi/2)
theta_16k = theta_16k * (direction_20k * np.pi/2)
theta_20k = theta_20k * (direction_12k * np.pi/2)
# This now contains the coil rotation relative to the field lines








################################################################################
# STEP

# upsample optitrack data using nearest neighbor interpolation












#END

# Coil Calibration Process and Code walkthrough

The goal of this document is to walkthrough my processing code and describe my
methods in detail so they can be peer-reviewed.

## Intro

### Problem Statement

We have thus far been unable to get consistent and accurate results from our
BOSS coil system, which was first built by postdocs we have no current contact
with. Our assumption is that this is caused by a non-uniform magnetic field
along one or more axis.

**Therefore, the goal of this project is to map non-uniformities in the field.**

## Methods

### Equipment

#### Coil
**(MC-95)**

This our current workhorse coil. It has an unamplified response of roughly
10mv within the field. This is too small to accurately measure with the daq,
but we have been successful in amplifying it with very little noise to a level
that is adequately measurable.

**This coil is essentially zero-noise**

![mc-95](https://raw.githubusercontent.com/jmaggio14/aplab-coil-calibration/master/images/mc-95-coil.jpeg)

#### Amplifier
**THS3001**

We amplify the coil signals using these amplifier evaluation boards, and modify
their gain by swapping out a single surface-mount resistor in the feedback loop
of the amp.

![amps](https://raw.githubusercontent.com/jmaggio14/aplab-coil-calibration/master/images/amps.jpeg)

We've witnessed very little noise in these amplifiers - to the point where it
is safe to consider negligible in the face of the read noise introduced by the
DAQ. However, the input impedance of these amplifiers in unknown, this should be
a known parameter (and likely increased). see
[how this affects data collection here](https://www.electronics-tutorials.ws/amplifier/input-impedance-of-an-amplifier.html)

**These amplifiers are configured in Inverting Mode - they apply a predictable
phase shift of pi**

##### DAQ
(PCIE-6346)
This DAQ is capable of simultaneously sampling both the reference coils, and the
measurement coils.

All channels are measured at exactly the same instant

The daq introduces a significant, but not yet quantized read noise into all data
that we collect. It appears to be constant, which means that larger signals
have a higher SNR.

**The DAQ is the single greatest source of error in the data we've collected**


### Asumptions:
  1. optitrack and coil data are perfectly synced. (they are hardware synced,
  so this should be the case to within 1/optitrack_framerate )

  2. all three coils are perfectly orthagonal to each other.


#### NOTE:
For reasons that are best illustrated in diagrams later on, this code requires
**two coils at a minimum** to map the field.


### Processing Pipeline

#### Step 0
1. read in our Calibration file which contains values such as the system-measurement
phase shift, the expected maximum and minimum values of each coil, and finally
the order and the width of our butterworth frequency filter
the filter we would like to use,
2. read in data from our CSV data files, for the entirety of this pipeline. Data
is stored in 2D arrays, where **rows are samples (or time)** and
**columns is the coil index**

###### Data products:
  - calibration constants
  - raw data

#### Step 1
Filter out our desired frequencies using a butterworth bandpass filter

We apply a butterworth filter of tunable order and width to **both the reference
and measurement coil data**. This is done for 12, 16, and 20khz signals
respectively which leaves us with separate variables for each.

```python
# apply our butterworth filter
offset = BANDWIDTH / 2
filtered_12k, _ = freq_filter(channels, 12e3-offset, 12e3+offset, BUTTER_ORDER, SAMPLING_FREQUENCY)
filtered_16k, _ = freq_filter(channels, 16e3-offset, 16e3+offset, BUTTER_ORDER, SAMPLING_FREQUENCY)
filtered_20k, _ = freq_filter(channels, 20e3-offset, 20e3+offset, BUTTER_ORDER, SAMPLING_FREQUENCY)
```

###### Data products:
  - filter frequency responses (for later analysis / debugging)
  - 12k, 16k, & 20k voltages for every coil (raw X, Y, Z voltages)

#### Step 2
Calculate the amplitude of our signal as a function of time, and extract the
uncalibrated phase information

1. take the fft of our filtered measurement and reference data
2. retrieve amplitude using absolute value
3. Retrieve uncalibrated phase (this is phase with the phase shift of the amplifiers unaccounted for)

```python
fft_12k = np.fft.fft(filtered_12k, axis=0)
amplitude_12k = np.abs(fft_12k)
uncalib_phase_12k = np.angle(fft_12k)

fft_16k = np.fft.fft(filtered_16k, axis=0)
amplitude_16k = np.abs(fft_16k)
uncalib_phase_16k = np.angle(fft_16k)

fft_20k = np.fft.fft(filtered_20k, axis=0)
amplitude_20k = np.abs(fft_20k)
uncalib_phase_20k = np.angle(fft_20k)
```

![rotation](https://raw.githubusercontent.com/jmaggio14/aplab-coil-calibration/master/images/rotation.PNG)

However, we can't determine orientation with amplitude alone. There are four solvable
orientations for any given amplitude. We need more information...


###### Data products:
  - amplitude for measurement coil
  - uncalibrated raw phase of the measurement coil
  - ground truth phase of the reference coil


#### Step 3
We can now use the amplitude information to reduce the problem to four possible
orientations of the coil.

By normalizing the amplitude, the coil's orientation becames directly
proportional to the arctan()

**With any given value of amplitude, there are four possible solutions**.

```python
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
```

![amplitude problem](https://raw.githubusercontent.com/jmaggio14/aplab-coil-calibration/master/images/amplitude_problem.PNG)


#### Step 4
Calibrate the phase

We need to account for the system phase offset inherent in our system, for this
we once again rely on calibration constants.


1. Subtract pre-determined phase shift from each channel (this value would have
  to be determined using an oscilloscope prior to data collection)
  _this is currently done equally for all frequencies in each channel_

```python
# it's easier here to stack all data into a single array and subtract our offset
# from the third axis which represents channels
uncalib_coil_phase = np.dstack( (uncalib_phase_12k[:,:3], uncalib_phase_16k[:,:3], uncalib_phase_20k[:,:3]) )
# SAMPLES IS ROWS
# COIL INDEX IS COLUMNS
# CHANNELS IS BANDS (third axis)
# ------------------------------------------------------------------------------
# this array only contains measurement coil data NOT reference coil data!!!!!!!
# ------------------------------------------------------------------------------

coil_phase_12k = uncalib_coil_phase[:,:,0] - SYS_PHASE_OFFSET_CH1
coil_phase_16k = uncalib_coil_phase[:,:,1] - SYS_PHASE_OFFSET_CH2
coil_phase_20k = uncalib_coil_phase[:,:,2] - SYS_PHASE_OFFSET_CH3
```


This offset is caused primarily by the amplifiers, however a pi/2 offset is
also possible depending on the BNC connection wiring.


#### Step 5
Reduce the problem using relative phase

 - If the field lines pass through the coil back->front, then the measurement coil
will have the _same phase as the reference coil_

 - If the field lines pass through the coil front->back, then the measurement coil
will have a _phase shift of pi/2_

By calculating the relative phase between the two coils, we can reduce our problem
to two possible solutions

![relative phase](https://raw.githubusercontent.com/jmaggio14/aplab-coil-calibration/master/images/relative_phase.PNG)


```python
# subtact the reference phase from the measured phase
relative_phase_12k = coil_phase_12k - ref_phase_12k
relative_phase_16k = coil_phase_16k - ref_phase_16k
relative_phase_20k = coil_phase_20k - ref_phase_20k

# ------------------------------------------------------------------------------
# MICHELE AND RUEI, PLEASE AUDIT ME HERE
# I could very well have made a mistake in this section
#
# how to account for a theoretical situation in which the relative phase
# is greater than pi? maybe mod by pi or clip the array. This shouldn't happen, but might
# happen as a result of measurement error or bad calibration
# ------------------------------------------------------------------------------

# all phase between 0 and pi/2 --> 0
# all phase between pi/2 and pi --> +1

# use integer division to binarize the signal between 0 and 1
# zeros in this case mean that the measurement coil is parallel to the flux
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

rotation_12k = theta_12k + (direction_12k * np.pi)
rotation_16k = theta_16k + (direction_16k * np.pi)
rotation_20k = theta_20k + (direction_20k * np.pi)
# ROWS IS SAMPLES
# COLUMNS IS COILS
```


#### Step 6
Solve the system using a second orthogonal field

So far we have been computing every axis completely independently from one
another. However to solve system, we'll need to check the relative phase of
a second field and determine whether an addition 45 degree rotation is necessary

I'll let the figure do most of the talking here:


![two fields](https://raw.githubusercontent.com/jmaggio14/aplab-coil-calibration/master/images/two_fields.PNG)

```python
theta_12k = theta_12k * (direction_16k * np.pi/2)
theta_16k = theta_16k * (direction_20k * np.pi/2)
theta_20k = theta_20k * (direction_12k * np.pi/2)
# This now contains the coil rotation relative to the field lines

```



#### Step
Upsample optitrack data to match coil data using nearest-neighbors

1. compare timecodes between coil and optitrack data, and repeat optitrack frame
while looping through coil data until optitrack timecode is smaller than the
coil timecode

###### Data products:
- upsampled optitrack data

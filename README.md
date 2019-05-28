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

#### Step 1 _(line 118)_
Filter out our desired frequencies using a butterworth bandpass filter

We apply a butterworth filter of tunable order and width to **both the reference
and measurement coil data**. This is done for 12, 16, and 20khz signals
respectively which leaves us with separate variables for each.

###### Data products:
  - filter frequency responses (for later analysis / debugging)
  - 12k, 16k, & 20k voltages for every coil (raw X, Y, Z voltages)

#### Step 2 _(line 179)_
Calculate the amplitude of our signal as a function of time, and extract the
uncalibrated phase information

1. take the fft of our filtered measurement and reference data
2. retrieve amplitude using absolute value
3. Retrieve uncalibrated phase (this is phase with the phase shift of the amplifiers unaccounted for)


![rotation](https://raw.githubusercontent.com/jmaggio14/aplab-coil-calibration/master/images/rotation.PNG)

However, we can't determine orientation with amplitude alone. There are four solvable
orientations for any given amplitude. We need more information...


###### Data products:
  - amplitude for measurement coil
  - uncalibrated raw phase of the measurement coil
  - ground truth phase of the reference coil


#### Step 3 _(line 219)_
We can now use the amplitude information to reduce the problem to four possible
orientations of the coil.

By normalizing the amplitude, the coil's orientation becames directly
proportional to the arctan()

**With any given value of amplitude, there are four possible solutions**.


![amplitude problem](https://raw.githubusercontent.com/jmaggio14/aplab-coil-calibration/master/images/amplitude_problem.PNG)


#### Step 4 _(line 296)_
Calibrate the phase

We need to account for the system phase offset inherent in our system, for this
we once again rely on calibration constants.


1. Subtract pre-determined phase shift from each channel (this value would have
  to be determined using an oscilloscope prior to data collection)
  _this is currently done equally for all frequencies in each channel_


This offset is caused primarily by the amplifiers, however a pi offset is
also possible depending on the BNC connection wiring.


#### Step 5 _(line 322)_
Reduce the problem using relative phase

 - If the field lines pass through the coil back->front, then the measurement coil
will have the _same phase as the reference coil_

 - If the field lines pass through the coil front->back, then the measurement coil
will have a _phase shift of pi_

By calculating the relative phase between the two coils, we can reduce our problem
to two possible solutions

![relative phase](https://raw.githubusercontent.com/jmaggio14/aplab-coil-calibration/master/images/relative_phase.PNG)


#### Step 6 _(line 391)_
Solve the system using a second orthogonal field

So far we have been computing every axis completely independently from one
another. However to solve system, we'll need to check the relative phase of
a second field and determine whether an addition 45 degree rotation is necessary

I'll let the figure do most of the talking here:


![two fields](https://raw.githubusercontent.com/jmaggio14/aplab-coil-calibration/master/images/two_fields.PNG)


At this point, we should have a variable theta which represents the rotation
relative to the reference coil.

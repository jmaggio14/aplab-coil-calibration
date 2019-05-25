# Coil Calibration Process and Code walkthrough

The goal of this document is to walkthrough my processing code and describe my
methods in detail so they can be peer-reviewed.

If you have questions about to process, or believe I made a mistake. Please
bring it up with me.

## Methods

### Problem Statement

We have thus far been unable to get consistent and accurate results from our
BOSS coil system, which was first built by postdocs we have no current contact
with. Our assumption is that this is caused by a non-uniform magnetic field
along one or more axis.

**Therefore, the goal of this project is to map non-uniformities in the field.**



### Equipment

#### Coil
##### MC-95
This our current workhorse coil. It has an unamplified response of roughly
10mv within the field.

It's suboptimal for this frequency range, but we've been able to collect
effective low-noise measurements using  
###### JM - add image of orthagonal mount for coils

#### NOTE:
For reasons that are best illustrated in diagrams later on, this code requires
**two coils at a minimum** to map the field.

### Asumptions:
  1. optitrack and coil data are perfectly synced. (they are hardware synced,
  so this should be the case to within 1/optitrack_framerate )

  2. all three coils are perfectly orthagonal to each other.

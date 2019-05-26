import numpy as np
import math
import random


AXIS_FREQS = {'x':12e3, 'y':16e3, 'z':20e3}

def arcmin2radians(arcmin):
    return math.radians(arcmin / 60)

class DataGenerator():
    def __init__(self,
                    cal_max,
                    cal_min,
                    ref_coil_max=1,
                    ref_coil_min=0,
                    duration=60,
                    mean_read_noise=3e-3,
                    ncoils=3,
                    coil_sample_rate=1e5,
                    opti_sample_rate=1e5,
                    ):

        self.duration = duration
        self.mean_read_noise = mean_read_noise
        self.ncoils = 3
        self.coil_sample_rate = coil_sample_rate
        self.opti_sample_rate = opti_sample_rate



    def coil_data(self, axes, rates):
        data = []
        references = []
        for axis, rate in zip(axes, rates):
            # calculate the carrier wave (field) oscillations
            nsamples_coil = self.coil_sample_rate * self.duration
            max_phase = AXIS_FREQS[axis] * self.duration * 2 * np.pi

            phi = np.linspace(0, max_phase, nsamples)
            # calculate the reference coil output as a normalized
            reference = np.sin(phi).reshape( (nsamples,1) )
            max_emf = (reference * self.cal_max) + self.cal_min

            # calculate the effect of the coil rotation on the waveform
            max_rotation = rate * self.duration * 2 * np.pi
            theta = np.linspace(0, max_rotation, nsamples).reshape((nsamples, 1))
            rotation = np.sin(theta)

            # we now construct the sample data by multiplying our rotation_waveform
            # with our maximum emf as a function of time
            data.append( (rotation * max_emf) )

        return np.hstack( data ), reference

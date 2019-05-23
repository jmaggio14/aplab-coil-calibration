# first we need to import these
# to access Python's scientific processing package (a "toolbox")
import numpy as np
import scipy

COIL_FILENAME = None
OPTITRACK_FILENAME = None

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

# read in data from csv file into numpy arrays
coil_data = np.genfromtxt(COIL_FILENAME)

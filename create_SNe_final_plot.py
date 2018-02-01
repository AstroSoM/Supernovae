import subprocess
import glob
from SNe_final_plot import *

'''
Purpose:
--------
Create the  final frame
'''

#====================================================================================================
# SETUP!
# ------

# Filenames (SNe data, Milky Way data, rootname for all plots, output MIDI/WAV/MP3/MP4 files)
fdata = "/Users/salvesen/outreach/asom/supernovae/data/SNedata.h5"
fmway = "/Users/salvesen/outreach/asom/supernovae/data/milkyway.h5"
froot = "/Users/salvesen/outreach/asom/supernovae/results/plots/final_plot_"

# All other inputs
NsubBeats    = 4
tempo        = 74.80
maxDuration  = 2
date0        = [1950, 1, 1]
datef        = None
minNstd      = None
maxNstd      = None
base_octave  = 2
octave_range = 7

# Create an instance of the "supernovae" class
instSNe = supernovae(fdata=fdata, NsubBeats=NsubBeats, tempo=tempo, maxDuration=maxDuration, \
                     date0=date0, datef=datef, minNstd=minNstd, maxNstd=maxNstd)

#====================================================================================================
# PLOT!
# -----

# Plot the data
instSNe.plots(froot=froot, fmway=fmway)


import numpy as np
import pylab as plt
import datetime
import h5py
import re
from ChampagneSupernovaChords import *
from groupdates import *
from miditime.miditime import MIDITime
import matplotlib.font_manager as fm

'''
--> ONLY PLOT THE FINAL FRAME <--

Procedure:
----------
Step (1): Collect only the supernovae data from the specified date range and set a bunch of sonification inputs
Step (2): Sonify the data
Step (3): Plot the data

To Do List:
-----------
...specify the instrument to use to differentiate SN types (might need to specify a .cfg or .sf2 file in TiMidity as well)
    http://ccrma.stanford.edu/planetccrma/man/man5/timidity.cfg.5.html
    General MIDI: https://en.wikipedia.org/wiki/General_MIDI
    MyMIDI.addNote(track,channel,pitch,time,duration,volume)
    MIDIUtil docs: https://media.readthedocs.org/pdf/midiutil/1.1.3/midiutil.pdf <-- do we need to change the "bank", too? err...

Attributes:
-----------
These functions need to be called externally:
    sonify(fmidi="../results/song.mid", base_octave=2, octave_range=6)
    plots(froot="../results/plots/SNe_", fmway=None)

These helper functions are called from within the "supernovae" class:
    irankorder(note_octave, octave)
    ranklist(midiobj, chord, octave=4)
    mmax2Attack(thismmax, minAttack=0.0, maxAttack=127.0)
    mmax2Duration(thismmax)
    Nnotes(Nset)
    scatColor(thisSNtype)
    scatMark(thisSNtype)
    scatSize(thismmax, minSize=1.0)

Notes:
------
I decided to make all of the notes have the same attack (volume).
I felt that the different volumes were not easy to perceive as a listener and it is more important to be able to hear all of the notes being played.
This could be changed by swapping lines 555/556 below.
'''

#====================================================================================================
class supernovae:

#====================================================================================================
    def __init__(self, fdata="../data/SNedata.h5", NsubBeats=4, tempo=74.80, maxDuration=2, \
             date0=None, datef=None, minNstd=None, maxNstd=None):
        '''
        Inputs:
        -------
        fdata       - Filename for the SNe data (output of organizedate.py)
        NsubBeats   - Number of frames per beat, or number of sub-beats to cram into each beat (1 beat = 1 quarter note)
        tempo       - Tempo of the output song [beats per minute]
        maxDuration - Maximum duration of a note [beats (quarter notes)]

        date0       - Start date for the sonification in list format [year, month, day]
                      (set to None to use the first date in dataset; cannot be before 1900)
        datef       - End date for the sonification in list format [year, month, day]
                      (set to None to use the last date in dataset)

        minNstd     - Minimum bound to use on the number of standard deviations in the maximum apparent AB magnitude
        maxNstd     - Maximum bound to use on the number of standard deviations in the maximum apparent AB magnitude
    
        Notes:
        ------
        NsubBeats and the span of [date0,datef] determines the time binning for the SNe data.
        ...Increasing (decreasing) the number of sub-beats means that the time bins will be longer (shorter).
        ...Increasing (decreasing) the [date0,datef] range means that the time bins will be longer (shorter).
        We are sonifying apparent magnitudes, so minNstd is bright SNe and maxNstd is dim SNe
        '''
        # Collect the full set of organized SNe data with the initial filtering already applied
        # ...We do not use data for: 'time', 'name', 'host', 'z'
        f    = h5py.File(fdata, 'r')
        date = f['date'][:]  # Discovery date
        mmax = f['mmax'][:]  # Maximum apparent AB magnitude
        ra   = f['ra'][:]    # Right ascension
        dec  = f['dec'][:]   # Declination
        l    = f['l'][:] * -1.0  # Galactic longitude <-- THINGS ARE FLIPPED W/O THE -1 FACTOR
        b    = f['b'][:]     # Galactic latitude
        type = f['type'][:]  # Type classification (e.g., Ia, II)
        f.close()

        # Convert the start date into a datetime object
        if (date0 == None):
            # If unspecified, set date0 to the first entry in the dataset
            date0 = datetime.datetime.strptime(date[0], '%Y/%m/%d')
        else:
            y0, m0, d0 = date0
            date0 = datetime.datetime(year=y0, month=m0, day=d0)
        if (date0.year < 1900):
            print "\nERROR: The start date cannot be before 1900.\n"
            quit()

        # Convert the end date into a datetime object
        if (datef == None):
            # If unspecified, set datef to the last entry in the dataset
            datef = datetime.datetime.strptime(date[-1], '%Y/%m/%d')
        else:
            yf, mf, df = datef
            datef = datetime.datetime(year=yf, month=mf, day=df)

        # Number of days between the start and end dates
        Ndays = (datef - date0).days

        # Calculate the mean and standard deviation of the maximum apparent magnitude
        # Note: It is important to do this before chopping the dataset because we want the std for the full dataset
        mmax_min  = np.min(mmax)
        mmax_max  = np.max(mmax)
        mmax_mean = np.mean(mmax)
        mmax_std  = np.std(mmax)
        # If unspecified, calculate the min/max number of standard deviations away from the mean mmax
        if (minNstd == None): minNstd = (mmax_min - mmax_mean) / mmax_std
        if (maxNstd == None): maxNstd = (mmax_max - mmax_mean) / mmax_std
    
        # Truncate data before the start date and after the end date
        ikeep = []
        for i in np.arange(len(date)):
            thisdate = datetime.datetime.strptime(date[i], '%Y/%m/%d')
            if ((thisdate >= date0) and (thisdate <= datef)):
                ikeep.append(i)
        date = date[ikeep]
        mmax = mmax[ikeep]
        ra   = ra[ikeep]
        dec  = dec[ikeep]
        l    = l[ikeep]
        b    = b[ikeep]
        type = type[ikeep]

        # Chord progression for the song Champagne Supernova by Oasis
        chordprog = chords()
        Nbeats    = len(chordprog)  # Number of beats in the song (1 beat = 1 quarter note)

        # Number of frames to have in the dataset
        Nframes = Nbeats * NsubBeats

        # Determine the bin size (in number of days) for the SNe data
        binsize = float(Ndays) / float(Nframes)

        # Group SNe by binsize [days]
        datebins, idatebins = groupNdays(date=date, date0=date0, datef=datef, Ndays=binsize)

        # Check that the number of number of date bins equals the number of frames we expected to have in the dataset
        Ndatebins = len(idatebins)
        if (Nframes != Ndatebins):
            print "\nERROR: Number of time bins is different from the number of expected frames...\n"
            print "\n    ...Something unexpected happened with groupdates.groupNdays().\n"
            quit()

        # Simplify the SNe classifications
        # Types: Ia, II, Other, Unknown
        Ntype  = len(type)
        SNtype = [0] * Ntype
        for i in np.arange(Ntype):
            if (type[i] == 'Ia'):  SNtype[i] = 'Ia'
            if (type[i] == 'II'):  SNtype[i] = 'II'
            if (type[i] == 'nan'): SNtype[i] = 'Unknown'
            if (SNtype[i] == 0):   SNtype[i] = 'Other'

        # Number of SNe (by type) in each date bin
        NSN      = np.zeros(Nframes)
        NTypeIa  = np.zeros(Nframes)
        NTypeII  = np.zeros(Nframes)
        NOther   = np.zeros(Nframes)
        NUnknown = np.zeros(Nframes)
        for i in np.arange(Nframes):
            iset   = idatebins[i]
            Nset   = len(iset)
            NSN[i] = Nset
            if (Nset > 0):
                for j in np.arange(Nset):
                    thisType = SNtype[iset[j]]
                    if (thisType == 'Ia'): NTypeIa[i] += 1
                    if (thisType == 'II'): NTypeII[i] += 1
                    if (thisType == 'Other'): NOther[i] += 1
                    if (thisType == 'Unknown'): NUnknown[i] += 1

        # Determine some useful stats and print them out
        totalNSN    = len(date)
        maxNSN      = int(np.max(NSN))
        maxNTypeIa  = int(np.max(NTypeIa))
        maxNTypeII  = int(np.max(NTypeII))
        maxNOther   = int(np.max(NOther))
        maxNUnknown = int(np.max(NUnknown))
        print("\nHere are some stats...\n")
        print "    Total number of supernovae    : ", totalNSN
        print "    Most supernovae in a date bin : ", maxNSN
        print "        ...Type Ia : ", maxNTypeIa
        print "        ...Type II : ", maxNTypeII
        print "        ...Other   : ", maxNOther
        print "        ...Unknown : ", maxNUnknown
        print "    Number of days in a date bin   : ", '{:.2f}'.format(binsize)
        print "    Number of date bins (frames)   : ", Nframes
        print "    Number of beats in the song    : ", Nbeats
        print "    Number of sub-beats being used : ", float(Nframes) / float(Nbeats)
        print ""
        
        # Set the "self" variables that will be used later on:
        self.NsubBeats   = NsubBeats    # Number of sub-beats per beat (1 beat = 1 quarter note)
        self.tempo       = tempo        # Tempo [beats per minute]
        self.maxDuration = maxDuration  # Upper bound on how long a note is held [beats]
        self.minNstd     = minNstd      # Lower bound on number of standard deviations in mmax
        self.maxNstd     = maxNstd      # Upper bound on number of standard deviations in mmax
        self.date0       = date0        # Starting date (datetime object)
        self.datef       = datef        # Ending date (datetime object)
        self.Ndays       = Ndays        # Number of days between the start and end dates
        self.datebins    = datebins     # Date groups/bins (left edges)
        self.idatebins   = idatebins    # Indices for the SNe belonging in each date bin
        self.Nframes     = Nframes      # Number of frames (length of idatebins, also Nbeats x NsubBeats)
        self.Nbeats      = Nbeats       # Number of beats (quarter notes) in the song
        self.mmax        = mmax         # List of maximum apparent AB magnitudes for all SNe
        self.ra          = ra           # List of right ascensions for all SNe
        self.dec         = dec          # List of declinations for all SNe
        self.l           = l            # List of Galactic longitudes for all SNe
        self.b           = b            # List of Galactic latitudes for all SNe
        self.SNtype      = SNtype       # List of type classifications for all SNe
        self.mmax_mean   = mmax_mean    # Mean apparent magnitude for the full dataset
        self.mmax_std    = mmax_std     # Standard deviation in the apparent magnitude for the full dataset
        self.totalNSN    = totalNSN     # Total number of SNe in the dataset
        self.maxNSN      = maxNSN       # Maximum number of SNe in a single time bin

        
#====================================================================================================
#====================================================================================================
    # SONIFICATION HELPER FUNCTIONS

    #--------------------------------------------------
    # Starting from the specified octave, re-order the notes in note_list according to the following:
    # [octave, octave+1, octave-1, octave+2, ...] until there are no notes left in note_octave
    def irankorder(self, note_octave, octave):
        '''
        note_octave - Ordered list of octaves corresponding to the root/third/fifth/extra (e.g., [2,3,4,5,6])
        octave      - Starting octave from which to perform the rank-ordering
        '''
        # Return an empty list if the supplied note_octave is empty
        if (not note_octave): return []
    
        # Perform the index rank-ordering
        inote_rankorder = []
        doctave = 0
        inote0  = np.where(np.array(note_octave) == octave)[0]
        inote_rankorder.append(int(inote0[0]))
        doctave   = doctave + 1
        Ninote_hi = 1
        Ninote_lo = 1
        while ((Ninote_hi > 0) and (Ninote_lo > 0)):
            inote_hi  = np.where(np.array(note_octave) == (octave + doctave))[0]
            inote_lo  = np.where(np.array(note_octave) == (octave - doctave))[0]
            Ninote_hi = len(inote_hi)
            Ninote_lo = len(inote_lo)
            if (Ninote_hi > 0): inote_rankorder.append(int(inote_hi[0]))
            if (Ninote_lo > 0): inote_rankorder.append(int(inote_lo[0]))
            doctave = doctave + 1
        return inote_rankorder

    #--------------------------------------------------
    # Rank order the notes to draw from for the current chord
    # Start the ordering from the specified MIDI octave
    def ranklist(self, midiobj, chord, octave=4):
        '''
        Rank-order the avaialable notes in a musically pleasing way.
        '''
        # Loop through every possible MIDI note
        # Collect the list of notes contained within the chord
        Nmidi = 128
        note_list = []
        for i in np.arange(Nmidi):
            pct  = float(i) / float(Nmidi-1)
            note = midiobj.scale_to_note(scale_pct=pct, mode=chord)
            if (note not in note_list):
                note_list.append(note)
        Nnotes = len(note_list)

        # RE-ORDER THE NOTE LIST IN A MUSICALLY PLEASING WAY

        # Collect the names of the root, third, fifth, and an optional extra note in the chord
        root  = chord[0]
        third = chord[1]
        fifth = chord[2]
        if (len(chord) > 3): extra = chord[3]
        else: extra = None

        # Group the indices of note_list into root, third, fifth, extra and collect the octave numbers
        iroot_list   = []
        ithird_list  = []
        ififth_list  = []
        iextra_list  = []
        root_octave  = []
        third_octave = []
        fifth_octave = []
        extra_octave = []
        for i in np.arange(Nnotes):
            match       = re.match(r"([A-Z-#]+)([0-9]+)", note_list[i])
            splitNote   = match.groups()
            note_name   = splitNote[0]
            note_octave = int(splitNote[1])
            if (note_name == root):
                iroot_list.append(i)
                root_octave.append(note_octave)
            if (note_name == third):
                ithird_list.append(i)
                third_octave.append(note_octave)
            if (note_name == fifth):
                ififth_list.append(i)
                fifth_octave.append(note_octave)
            if (note_name == extra):
                iextra_list.append(i)
                extra_octave.append(note_octave)

        # Rank-order the root, third, fifth, extra as follows:
        # [root@octave, 3rd@octave, 5th@octave, root@octave+1, root@octave-1, 3rd@octave+1, 3rd@octave-1, ...
        # ... 5th@octave+1, 5th@octave-1, root@octave+2, ...] until there are no notes left in note_list
        iroot_ranklist  = self.irankorder(note_octave=root_octave, octave=octave)
        ithird_ranklist = self.irankorder(note_octave=third_octave, octave=octave)
        ififth_ranklist = self.irankorder(note_octave=fifth_octave, octave=octave)
        iextra_ranklist = self.irankorder(note_octave=extra_octave, octave=octave)

        # We now have the indices to accomplish the desired rank-ordering for the root, third, fifth, extra notes
        root_ranklist  = np.array(note_list)[np.array(iroot_list)[iroot_ranklist]]
        third_ranklist = np.array(note_list)[np.array(ithird_list)[ithird_ranklist]]
        fifth_ranklist = np.array(note_list)[np.array(ififth_list)[ififth_ranklist]]
        if (extra_octave): extra_ranklist = np.array(note_list)[np.array(iextra_list)[iextra_ranklist]]
        else:              extra_ranklist = []

        # Now put all of the notes in rank-ordered sets of [extra, root, third, fifth] by octaves
        note_ranklist = []
        Nroot  = len(root_ranklist)
        Nthird = len(third_ranklist)
        Nfifth = len(fifth_ranklist)
        Nextra = len(extra_ranklist)
        Ni     = np.max([Nroot, Nthird, Nfifth, Nextra])
        for i in np.arange(Ni):
            # When a chord has an extra 4th note, give it priority in the rank-ordered list of notes
            if (i < Nextra): note_ranklist.append(extra_ranklist[i])
            if (i < Nroot):  note_ranklist.append(root_ranklist[i])
            if (i < Nthird): note_ranklist.append(third_ranklist[i])
            if (i < Nfifth): note_ranklist.append(fifth_ranklist[i])
        '''
        # Alternative re-ordering of the note list: middle note is first, then alternate left/right of that
        imid   = int(Nnotes / 2)
        note_ranklist = []
        for i in np.arange(Nnotes):
            evenodd = i % 2
            if (evenodd == 0): j = imid + int(np.ceil(i+1)/2)
            if (evenodd == 1): j = imid - int(np.ceil(i+1)/2)
            note_ranklist.append(note_list[j])
        '''
        return note_ranklist

    #--------------------------------------------------
    # Convert mmax to an attack according to how many standard deviations it is away from the mean
    # Remember! Low mmax = bright; High mmax = dim <-- minNstd is brighter than maxNstd
    def mmax2Attack(self, thismmax, minAttack=0.0, maxAttack=127.0):
    
        # Number of standard deviations away from the mean (can be + or -)
        Nstd = (thismmax - self.mmax_mean) / self.mmax_std

        # Map Nstd to attack
        if ((Nstd <= self.maxNstd) and (Nstd >= self.minNstd)):  # Nstd is within the min/max bounds
            rangeNstd   = self.maxNstd - self.minNstd            # Range in Nstd
            normNstd    = (self.maxNstd - Nstd) / rangeNstd      # Normalized standard deviation, range [0,1]
            rangeAttack = maxAttack - minAttack                  # Range in attack
            thisAttack  = normNstd * rangeAttack + minAttack
        if (Nstd > self.maxNstd): thisAttack = minAttack         # Remember, maxNstd is DIM
        if (Nstd < self.minNstd): thisAttack = maxAttack         # Remember, maxNstd is BRIGHT
        return thisAttack

    #--------------------------------------------------
    # Convert mmax to a duration according to how many standard deviations it is away from the mean
    # Remember! Low mmax = bright; High mmax = dim <-- minNstd is brighter than maxNstd
    def mmax2Duration(self, thismmax):

        # The minimum duration is that of a "sub-beat"
        subBeat     = 1.0 / self.NsubBeats
        minDuration = subBeat

        # Number of standard deviations away from the mean (can be + or -)
        Nstd = (thismmax - self.mmax_mean) / self.mmax_std
    
        # Map Nstd to duration
        if ((Nstd <= self.maxNstd) and (Nstd >= self.minNstd)):  # Nstd is within the min/max bounds
            rangeNstd     = self.maxNstd - self.minNstd          # Range in Nstd
            normNstd      = (self.maxNstd - Nstd) / rangeNstd    # Normalized standard deviation, range [0,1]
            rangeDuration = self.maxDuration - minDuration       # Range in duration
            thisDuration  = normNstd * rangeDuration + minDuration
        if (Nstd > self.maxNstd): thisDuration = minDuration       # Remember, maxNstd is DIM
        if (Nstd < self.minNstd): thisDuration = self.maxDuration  # Remember, maxNstd is BRIGHT

        # Round thisDuration to a binned beat so that the duration is more musically pleasing
        beatBins     = np.linspace(minDuration, self.maxDuration, self.maxDuration/subBeat)
        iBeat        = np.argmin(np.abs(thisDuration - beatBins))
        thisDuration = beatBins[iBeat]
    
        return thisDuration

    #--------------------------------------------------
    # Determine the number of notes to play given "Nset" number of SNe
    # 1st note = SN  #1     <-- added 1 SN
    # 2nd note = SNe #2-3   <-- added 2 SNe
    # 3rd note = SNe #4-7   <-- added 4 SNe
    # 4th note = SNe #8-15  <-- added 8 SNe
    # 5th note = SNe #16-31 <-- added 16 SNe
    # etc...
    # Do not toss out any data
    # For instance, if there were X = 1-32 more straggler supernovae above, they would be represented as a 6th note
    # 6th note = SNe # 32-->(32+X-1) <-- added X SN(e)
    def Nnotes(self, Nset):
        if (Nset > 0):
            # Determine the number of notes to play
            Npowersof2 = 0
            thisNSN    = 0
            while (thisNSN < Nset):
                Npowersof2 += 1
                thisNSN     = int(np.sum([2**x for x in np.arange(Npowersof2)]))
            Nnotes = Npowersof2
            '''
            # Determine the number of stragglers (do not need this for anything, but was good for testing things)
            Nfull = 2**Nnotes - 1
            Nstragglers = Nset - int(np.sum([2**x for x in np.arange(Nnotes-1)]))
            if (Nset == Nfull): Nstragglers = 0
            '''
        else: Nnotes = 0
        return Nnotes

#====================================================================================================
    # SONIFICATION WITH MIDITIME
    def sonify(self, fmidi="../results/song.mid", base_octave=2, octave_range=6):
        '''
        Inputs:
        -------
        fmidi        - Name for the output MIDI file
        base_octave  - Lowest octave and starting point for collecting notes
        octave_range - Number of octaves to span in the sonification
        
        Notes:
        ------
        Choose different octaves for base, guitar, keys? Play around, see what sounds best.
        '''
        '''
        # Map the supernova type to a MIDI channel
        channels = [0] * Ntype
        for i in np.arange(Ntype):
            if (SNtype[i] == 'Ia'):      channels[i] = 0
            if (SNtype[i] == 'II'):      channels[i] = 1
            if (SNtype[i] == 'Unknown'): channels[i] = 2
            if (SNtype[i] == 'Other'):   channels[i] = 10  # <-- MIDI channel 10 is reserved for percussion
        '''
        # Sonification preferences
        key = ['A', 'B', 'C#', 'D', 'E', 'F#', 'G#']  # A major (...we never use this...)
        song_duration_min = self.Nbeats / self.tempo  # [minutes]
        song_duration_sec = song_duration_min * 60.0  # [seconds]

        # Annoyingly, we need the number of years between the start and end dates, but timedelta() cannot do this
        Nyears     = self.Ndays / 365.25         # <-- IS THIS BEING INEXACT CAUSING PROBLEMS FOR CALCULATING WHEN BEATS SHOULD OCCUR???
        sec_per_yr = song_duration_sec / Nyears  # [seconds per year]

        # Determine how many tracks we need (i.e., maximum number of notes)
        Ntracks = self.Nnotes(self.maxNSN)
  
        # Instantiate the MIDITime class
        mymidi = MIDITime(tempo=self.tempo, outfile=fmidi, seconds_per_year=sec_per_yr, base_octave=base_octave, octave_range=octave_range)

        # Content of the 2D list of lists allNotes[x][y]
        # NSN (j) Ntracks
        #                   x=0                               x=1                   ...>
        #   |  [[beat0,pitch0,attack0,duration0], [beat1,pitch1,attack1,duration1], ...] <-- j=0
        #   |  [[beat0,pitch0,attack0,duration0], [beat1,pitch1,attack1,duration1], ...] <-- j=1
        #   V  [[beat0,pitch0,attack0,duration0], [beat1,pitch1,attack1,duration1], ...] <-- j=2
        #                                                                                     :
        #      ----> Date Bins (x)                                                            :
        #                                                                                     V
        allNotes    = [[] for i in np.arange(Ntracks)]  # Ntracks sets of empty lists
        allChannels = [[] for i in np.arange(Ntracks)]  # Ntracks sets of empty lists

        # Loop through each date bin (frame) and collect the notes for each supernova in that date bin
        for i in np.arange(self.Nframes):

            # Current set of indices and its length (i.e., number of supernovae in the current date bin)
            iset = self.idatebins[i]
            Nset = len(iset)

            # Number of notes to play
            Nnotes = self.Nnotes(Nset=Nset)

            #--------------------------------------------------
            # If there are supernova(e) data for the current date bin...
            # ...determine the beat
            # ...determine the appropriate chord and collect a rank-ordered list of notes to draw from
            # ...check to make sure there are enough notes to draw from
            # ...sort the data by apparent magnitude, which we will need for the attack and duration
            if (Nnotes > 0):
   
                # --- BEAT --- #

                # Days elapsed since the current date bin (left edge)
                datenow     = self.datebins[i]
                daysElapsed = (datenow - self.date0).days
                thisBeat    = mymidi.beat(numdays=float(daysElapsed))  # <-- Why are these not more exact???

                # --- PITCH --- #

                # Chord corresponding to the current date bin
                ichord    = int(np.floor(i / self.NsubBeats))
                thischord = chordprog[ichord]

                # Rank order all of the available notes we can choose from based on thischord and the octave span
                note_ranklist = self.ranklist(midiobj=mymidi, chord=thischord)

                # Are there enough notes available to represent the current set of supernovae?
                Navail = len(note_ranklist)
                if (Navail < Nnotes):
                    print "\nThere are not enough notes to represent the current set of supernovae."
                    print "    # of notes available = ", Navail
                    print "    # of notes to play   = ", Nnotes
                    print "Try increasing the octave range to make more notes available.\n"
                    quit()
        
                # --- ATTACK & DURATION --- #

                # Sort the current SNe by their maximum apparent magnitude, mmax (smaller mmax is brighter)
                isort = np.argsort(self.mmax[iset])
                thismmax_list = []
                for j in np.arange(Nset):
                    iSN = iset[isort[j]]                  # Index for the current supernova (sorted by mmax)
                    thismmax_list.append(self.mmax[iSN])  # List of current supernova(e) ordered from brightest to faintest

                # Initialize/reset the left bound index for grouping the supernovae by mmax
                immaxL = 0
    
            #--------------------------------------------------

                # Initialize/reset the row index for the allNotes 2D list of lists
                irow = 0

                # Loop through each note to be played for the current date bin
                for j in np.arange(Nnotes):
        
                    # --- ATTACK & DURATION --- #
        
                    # Determine the right bound index for grouping the supernovae by mmax
                    if (j == (Nnotes-1)): immaxR = Nset
                    else: immaxR = np.sum([2**x for x in np.arange(j+1)])
                    thismmax_avg = np.mean(thismmax_list[immaxL:immaxR])
                    immaxL = immaxR

                    # Map thismmax_avg to thisAttack
                    #thisAttack = self.mmax2Attack(thismmax=thismmax_avg)
                    thisAttack = 127.0

                    # Map thismmax_avg to thisAttack
                    thisDuration = self.mmax2Duration(thismmax=thismmax_avg) # [beats]
            
                    # --- PITCH --- #

                    thisNote  = note_ranklist[j]
                    thisPitch = mymidi.note_to_midi_pitch(notename=thisNote)

                    # Need to collect all of the supernovae...and separate out different types...
                    #thisInstrument = instrument[iset[j]]

                    # --- APPEND [thisBeat, thisPitch, thisAttack, thisDuration] --- #

                    #if (SNtype[iset[j]] == 'II'): # <-- CAREFUL!!! WILL CHANGE THE LENGTH OF THE SONG, NEED TO THINK MORE...
            
                    # Append the note to the collection of allNotes
                    allNotes[irow].append([thisBeat, thisPitch, thisAttack, thisDuration])

                    # Append the channel to the collection of allChannels
                    thisChannel = 0  # Is channel 10 reserved for percussion?
                    allChannels[irow].append(thisChannel)

                    # On to the next row!
                    irow = irow + 1
    
        # Add each track to the sonification
        for i in np.arange(Ntracks):
            note_list = allNotes[i]
            chan_list = allChannels[i]
            thisNote_list = []
            for j in np.arange(len(note_list)):
                thisNote_list.append([note_list[j], chan_list[j]])
            mymidi.add_track(note_list=thisNote_list)

        # Output the MIDI file
        mymidi.save_midi()


#====================================================================================================
#====================================================================================================
    # PLOTTING HELPER FUNCTIONS

    # For YouTube production, determine the appropriate (xsize,ysize) for the figures (16:9 aspect)
    def XYsize(self, pixres, dpi):
        '''
        Inputs:
        -------
        pixres - Resolution (240, 360, 720, 1080, etc.)
        dpi    - Dots per inch
        '''
        aspect = 16.0 / 9.0
        Nxpix  = float(pixres) * aspect
        Nypix  = float(pixres)
        xsize  = Nxpix / dpi
        ysize  = Nypix / dpi
        return xsize, ysize
    
    # Set the color of a scatter plot point according to the supernova type (...kind of a gross name...)
    def scatColor(self, thisSNtype):
        if (thisSNtype == 'Ia'):      thisColor = '#ff000d'  #'xkcd:bright red'
        if (thisSNtype == 'II'):      thisColor = '#fffd01'  #'xkcd:bright yellow'
        if (thisSNtype == 'Unknown'): thisColor = '#0165fc'  #'xkcd:bright blue'
        if (thisSNtype == 'Other'):   thisColor = '#01ff07'  #'xkcd:bright green'
        return thisColor

    # Set the marker of a scatter plot point according to the supernova type (...kind of a gross name...)
    def scatMark(self, thisSNtype):
        if (thisSNtype == 'Ia'):      thisMark = 'd'
        if (thisSNtype == 'II'):      thisMark = '*'
        if (thisSNtype == 'Unknown'): thisMark = 'o'
        if (thisSNtype == 'Other'):   thisMark = 's'
        return thisMark

    #--------------------------------------------------
    # Convert mmax to marker size according to how many standard deviations it is away from the mean
    # Scale the marker area [pixels^2] like 2**|Nstd - maxNstd|
    # Remember! Low mmax = bright; High mmax = dim <-- minNstd is brighter than maxNstd
    def scatSize(self, thismmax, minSize=1.0):
    
        # Number of standard deviations away from the mean (can be + or -)
        Nstd = (thismmax - self.mmax_mean) / self.mmax_std

        # Map Nstd to marker size
        if (Nstd <= self.maxNstd): thisSize = minSize * 2.0**(self.maxNstd - Nstd)
        if (Nstd > self.maxNstd):  thisSize = minSize
        return thisSize

    '''
    # NOTE: We do not use the function scatSizeAlt() below, but it is an alternative to what we currently do...
    #      ...(i.e., sizing the markers according to the number of std's from the mean mmax)
    # Increase the area of the marker by factor of 2 for each factor of 10 increase in flux
    # (See Wikipedia page on Apparent Magnitude)
    def scatSizeAlt(self, thismmax, minSize=4.0, logF0=-8.0):
        F        = 100.0 / (100.0**(thismmax / 5.0)) # Flux [% Vega]
        logF     = np.log10(F)
        Fdiff    = logF - logF0
        thisSize = minSize * 2.0**Fdiff
        return thisSize
    '''

#====================================================================================================
    # PRODUCING THE PLOTS
    def plots(self, froot="../results/plots/SNe_", fmway=None):
        '''
        Inputs:
        -------
        froot - Root filename for all of the plots that will be generated
        fmway - Filename for the Milky Way panorama image data (output of milkyway.py)
                (If None, then the Milky Way background image is not plotted)
        '''
        
        # Plotting preferences
        dpi    = 300   # Resolution [dots per inch]
        pixres = 4320  # Number of y-pixels
        fres   = pixres / 1080.0
        lw     = 0.5*fres #1.0 * fres
        fsL    = 24*fres #36 * fres
        fsS    = 16*fres #24 * fres
        fsXS   = 8*fres #12 * fres
        left, right, bottom, top = 0.1, 0.9, 0.1, 0.9
        xsize, ysize = self.XYsize(pixres=pixres, dpi=dpi)
        minAlpha = 0.1  # Minimum transparency parameter
        maxAlpha = 1.0  # Maximum transparency parameter
        plt.rcParams['axes.linewidth'] = lw
        plt.rcParams['axes.edgecolor'] = 'white'
        plt.rcParams['axes.titlepad']  = 1.5*fsXS

        # Fonts
        jsansR  = fm.FontProperties(fname='../fonts/JosefinSans-Regular.ttf')
        jsansB  = fm.FontProperties(fname='../fonts/JosefinSans-Bold.ttf')
        jsansSB = fm.FontProperties(fname='../fonts/JosefinSans-SemiBold.ttf')
        jsansBI = fm.FontProperties(fname='../fonts/JosefinSans-BoldItalic.ttf')

        # Setup the plotting environment (with a black background)
        fig = plt.figure(figsize=(xsize, ysize), dpi=dpi)
        fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top)
        fig.patch.set_facecolor('black')

        # Axes object for the Hammer projection
        mwax = fig.add_subplot(111, projection='hammer')

        # Suppress everything having to do with the x- and y-axes
        mwax.xaxis.set_visible(False)
        mwax.yaxis.set_visible(False)
        
        #--------------------------------------------------
        # PLOT THE MILKY WAY PANORAMA IMAGE
        if (fmway != None):
            print("\nPlotting the Milky Way image...\n")

            # Get the Milky Way data for the Hammer-Aitoff projection
            f = h5py.File(fmway, 'r')
            lon_grid   = f['lon_grid'][:,:]
            lat_grid   = f['lat_grid'][:,:]
            rgb_grid   = f['rgb_grid'][:,:]
            colorTuple = f['colorTuple'].value
            f.close()

            # Plot the Milky Way panorama image
            # ...kinda slow, but imshow() does not work for non-rectangular projections
            mwax.pcolormesh(lon_grid, lat_grid*-1.0, rgb_grid[:,:,0], color=colorTuple, cmap='gray', vmin=0.0, vmax=1.0, clip_on=True, linewidth=0.0)

        #--------------------------------------------------
        #--------------------------------------------------
        # PLOT THE SUPERNOVAE
        print("\nPlotting each frame...\n")

        # Collect lists of the marker types, colors, sizes, and durations for each individual SN
        markShapes    = []
        markColors    = []
        markSizes     = []  # [pixels^2]
        markDurations = []  # [Nframes]
        for i in np.arange(self.totalNSN):
        
            thisSNtype = self.SNtype[i]
            thismmax   = self.mmax[i]
            markShapes.append(self.scatMark(thisSNtype=thisSNtype))
            markColors.append(self.scatColor(thisSNtype=thisSNtype))
            markSizes.append(self.scatSize(thismmax=thismmax, minSize=4.0)) #minSize=1.0

            # Determine thisDuration [beats] and multiply it by NsubBeats to get duration in units of [number of frames]
            thisDuration = int(self.mmax2Duration(thismmax=thismmax) * self.NsubBeats)
            markDurations.append(thisDuration)

        # Find the maximum number of frames any single SN will be plotted
        # ...This way we only have to scan the previous NmaxFrames when plotting previous SNe within the for loop below
        NmaxFrames = np.max(markDurations)
        
        # The SNe in the final frame will need to fade out, so we will plot an additional NmaxFrames
        imax = self.Nframes - 1  # <-- last index where we have data in the lists "datebins" and "idatebins"

        # Loop through the date increments
        icnt  = -1
        iold  = 0
        iprev = []
        for i in np.arange(self.Nframes + NmaxFrames):
    
            # Start a counter, which is used for:
            # ...knowing when to stop checking if there are SNe in the date bin
            # ...naming the output file
            icnt += 1
            # Do not let i exceed imax (when it does, we are just plotting the final NmaxFrames)
            if (i > imax): i = imax
            
            # Current set of indices and its length
            iset = self.idatebins[i]
            Nset = len(iset)
    
            # Create the axes object (we will get rid of it after each loop so we do not have to plot the Milky Way panorama every time)
            ax = fig.add_axes(mwax.get_position(), projection='hammer', frameon=False)

            #--------------------------------------------------
            # FADE OUT ANY PREVIOUS SUPERNOVAE
            # ...The brighter SNe linger/fade longer (mmax sets the duration [number of frames] each SN is plotted)

            # Determine how many past indices before i to consider for plotting past supernovae fading away
            if (i < NmaxFrames):
                ipast = 0                        # <-- Handles the first few frames
            if ((i >= NmaxFrames) and (i <= imax)):
                ipast = (i - NmaxFrames) + 1     # <-- Handles everything inbetween
            if (icnt > imax):
                ipast = (icnt - NmaxFrames) + 1  # <-- Handles the final fading out
                
            # All SNe from frames prior to the index ipast have already completely faded...
            # ...so only consider SNe that went off between indices ipast and i-1
            # ...but when we reach the end of dataset the end index is i, not i-1
    
            # Set of indices for all SNe that went off in this range and its length
            if (icnt <= imax): ipastSet = self.idatebins[ipast:i]    # <-- Notice we are NOT including the current date bin, we will plot these "new" SNe later
            if (icnt > imax):  ipastSet = self.idatebins[ipast:i+1]  # <-- Notice we ARE including the current date bin
            NpastSet = len(ipastSet)                                 # <-- Notice this is one less than NmaxFrames (or >1 less if i < NmaxFrames)

            # Loop through the previous NpastSet and plot the past SNe according to their durations
            for j in np.arange(NpastSet):
                
                # Indices for the SNe that went off in the frame corresponding to the current ipastSet[j]
                iSNpast = ipastSet[j]
    
                # Number of SNe that went off in this frame
                NSNpast = len(iSNpast)
                
                # Check that there are SNe, otherwise there is nothing to plot
                if (NSNpast > 0):
                    
                    # Number of frames back from the reference/"present" i-frame (Ex: j = 0 would be NpastSet frames in the past)
                    deltaFrames = NpastSet - j  # We are looping from deltaFrames = (Nmaxframes-1) --> 1
            
                    # Array of durations [number of frames] for the SNe in this frame
                    durations = np.array(markDurations)[iSNpast]
                    
                    # Loop through the SNe in the this frame
                    for k in np.arange(NSNpast):
                
                        # Index for the current SN
                        iSN = iSNpast[k]
                
                        # Duration [number of frames] for the current SN
                        if (icnt <= imax): thisDuration = durations[k]
                        if (icnt > imax):  thisDuration = durations[k] - (icnt - imax) + 1  # <-- Trick program into thinking we are advancing forward in time
                                                                                            # ... I do not fully understand this +1, but it works correctly
                        
                        # Only plot those SNe whose duration is longer than the number of frames back we are looking...
                        # ...otherwise they would have faded away by now
                        if (thisDuration > deltaFrames):
                            
                            # Determine the alpha transparency
                            deltaAlpha = (maxAlpha - minAlpha) / (thisDuration - 1.0)  # Incremental change in alpha between frames (evenly spaced)
                            thisAlpha  = maxAlpha - (deltaFrames * deltaAlpha)         # Alpha decreases by an increment deltaAlpha each frame forward in time
                            
                            # Plot this SN with the appropriate alpha transparency level
                            #ax.scatter(self.ra[iSN], self.dec[iSN], s=markSizes[iSN], c=markColors[iSN], marker=markShapes[iSN], alpha=thisAlpha, linewidths=0.0)
                            ax.scatter(self.l[iSN], self.b[iSN], s=markSizes[iSN], c=markColors[iSN], marker=markShapes[iSN], alpha=thisAlpha, linewidths=0.0)

            #--------------------------------------------------
            '''
            # Plot the SNe from the previous frame with faint markers (alpha = minAlpha)
            Nprev = len(iprev)
            if (Nprev > 0):
                for j in np.arange(Nprev):
                    #ax.scatter(self.ra[iprev[j]], self.dec[iprev[j]], s=markSizes[iprev[j]], c=markColors[iprev[j]], marker=markShapes[iprev[j]], alpha=minAlpha, linewidths=0.0)
                    ax.scatter(self.l[iprev[j]], self.b[iprev[j]], s=markSizes[iprev[j]], c=markColors[iprev[j]], marker=markShapes[iprev[j]], alpha=minAlpha, linewidths=0.0)
            '''
            
            # Check that there are SNe to plot (when icnt > imax, there are NOT new SNe to plot for the final NmaxFrames fading out frames)
            if ((Nset > 0) and (icnt <= imax)):
                
                # Have to loop over each scatter point because it does not accept a list of markers (I think)
                for j in np.arange(Nset):
                    ithisSN = iset[j]  # Index for the current SN
                    #ax.scatter(self.ra[ithisSN], self.dec[ithisSN], s=markSizes[ithisSN], c=markColors[ithisSN], marker=markShapes[ithisSN], alpha=maxAlpha, linewidths=0.0)
                    ax.scatter(self.l[ithisSN], self.b[ithisSN], s=markSizes[ithisSN], c=markColors[ithisSN], marker=markShapes[ithisSN], alpha=maxAlpha, linewidths=0.0)

                # Keep track of the indices for the SNe in the previous time bin (iprev) and the starting index for the next set (iold)
                iprev = iset
                iold  = iset[0] + Nset
            else:
                iprev = []
            
            '''
            # Plot all SNe so far with faint markers (alpha = minAlpha)
            if (iold > 0):
                for j in np.arange(iold):
                    #ax.scatter(self.ra[j], self.dec[j], s=markSizes[j], c=markColors[j], marker=markShapes[j], alpha=minAlpha, linewidths=0.0)
                    ax.scatter(self.l[j], self.b[j], s=markSizes[j], c=markColors[j], marker=markShapes[j], alpha=minAlpha, linewidths=0.0)
            '''
            
            # Title
            ax.set_title("Supernova Discoveries", fontsize=fsL, fontproperties=jsansB, color='w')

            # Print out the current date bin (centered)
            # ...only printing out the year here, but could print out the month and day if desired...
            datetimeL = self.datebins[i]
            datetimeR = self.datebins[i+1]
            datebinC  = datetimeL + (datetimeR-datetimeL)/2
            datestrC  = datebinC.strftime('%Y %b %d')
            yearstrC  = datestrC.split(' ')[0]
            monthstrC = datestrC.split(' ')[1]
            daystrC   = datestrC.split(' ')[2]
            datetxt   = "Year" + "\n" + yearstrC
            ax.text(0.0, 1.0, datetxt, fontsize=fsS, color='w', ha='center', va='center', transform=ax.transAxes, fontproperties=jsansR)
            #ax.text(0.5, 1.1, r"${\rm "+yearstrC+"}$", fontsize=24, color='w', ha='left', va='center', transform=ax.transAxes)
            #ax.text(0.5, 1.1, r"${\rm "+monthstrC+"}$", fontsize=24, color='w', ha='center', va='center', transform=ax.transAxes)
            #ax.text(0.5, 1.1, r"${\rm "+daystrC+"}$", fontsize=24, color='w', ha='right', va='center', transform=ax.transAxes)
    
            # Print out the cumulative number of SNe discovered so far
            cumNSN = iold
            SNetxt = "Count" + "\n" + '{:,}'.format(cumNSN)
            ax.text(1.0, 1.0, SNetxt, fontsize=fsS, color='w', ha='center', va='center', transform=ax.transAxes, fontproperties=jsansR)
            #ax.text(0.5, -0.075, "Supernovae Count", fontsize=18, color='w', ha='center', va='center', transform=ax.transAxes, fontproperties=jsansR)
            #ax.text(0.5, -0.175, r"${\rm "+'{:,}'.format(cumNSN)+"}$", fontsize=18, color='w', ha='center', va='center', transform=ax.transAxes, fontproperties=jsansR)

            # Print the AstroSoM title and web address on the figure
            emDash   = u'\u2014'
            textASOM = "Astronomy Sound of the Month" + "\n" + emDash + " AstroSoM.com " + emDash
            ax.text(0.5, -0.1, textASOM, fontsize=fsXS, color='w', ha='center', va='center', transform=ax.transAxes, fontproperties=jsansR)
            
            # Suppress everything having to do with the x- and y-axes
            ax.xaxis.set_visible(False)
            ax.yaxis.set_visible(False)
            
            # Output the figure
            #if (icnt == 1127):  # SN 1978A
            #    fout = froot + str(icnt).zfill(4) + '.jpg'
            #    fig.savefig(fout, facecolor=fig.get_facecolor(), edgecolor='none', dpi=dpi)
            
            # Clear the axis with the scatter plot points
            # ...do not clear the axis with the Milky Way panorama image...
            ax.clear()

            # Give a progress report every so often
            if ((icnt % 10) == 0):
                pctComplete = float(icnt+1) / float(self.Nframes + NmaxFrames) * 100
                print "    % Complete: ", '{:.1f}'.format(pctComplete)
            
        #--------------------------------------------------
        #--------------------------------------------------
        
        # For the final frame, plot all SNe in the dataset with faint markers (alpha = minAlpha/2)
        print("\nPlotting the final frame with all of the supernovae...\n")
        icnt2 = 0
        for i in np.arange(self.totalNSN):
            #ax.scatter(self.ra[i], self.dec[i], s=markSizes[i], c=markColors[i], marker=markShapes[i], alpha=minAlpha*0.5, linewidths=0.0)
            ax.scatter(self.l[i], self.b[i], s=markSizes[i], c=markColors[i], marker=markShapes[i], alpha=minAlpha*0.5, linewidths=0.0)
            #ax.scatter(self.ra[i], self.dec[i], s=markSizes[i], c=markColors[i], marker=markShapes[i], alpha=1.0, linewidths=0.0)
            #ax.scatter(self.l[i], self.b[i], s=markSizes[i], c=markColors[i], marker=markShapes[i], alpha=1.0, linewidths=0.0)
            if ((icnt2 % 100) == 0):
                pctComplete = float(icnt2+1) / float(self.totalNSN) * 100
                print "    % Complete: ", '{:.1f}'.format(pctComplete)
            icnt2 = icnt2 + 1

        # Print out the title, date range, total number of SNe, and AstroSoM title/website
        ax.set_title("Supernova Discoveries", fontsize=fsL, fontproperties=jsansB, color='w')
        datetxt = "Year" + "\n" + str(self.date0.year) + u'\u2013' + str(self.datef.year)
        ax.text(0.0, 1.0, datetxt, fontsize=fsS, color='w', ha='center', va='center', transform=ax.transAxes, fontproperties=jsansR)
        SNetxt = "Count" + "\n" + '{:,}'.format(self.totalNSN)
        ax.text(1.0, 1.0, SNetxt, fontsize=fsS, color='w', ha='center', va='center', transform=ax.transAxes, fontproperties=jsansR)
        emDash   = u'\u2014'
        textASOM = "Astronomy Sound of the Month" + "\n" + emDash + " AstroSoM.com " + emDash
        ax.text(0.5, -0.1, textASOM, fontsize=fsXS, color='w', ha='center', va='center', transform=ax.transAxes, fontproperties=jsansR)
        #ax.text(0.5, 1.1, r"${\rm "+str(self.date0.year)+" - "+str(self.datef.year)+"}$", fontsize=24, color='w', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        #ax.text(0.5, -0.075, r"${\rm Supernovae\ Count}$", fontsize=18, color='w', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        #ax.text(0.5, -0.175, r"${\rm "+'{:,}'.format(self.totalNSN)+"}$", fontsize=18, color='w', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)

        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        fout = froot + str(icnt+1).zfill(4) + '.jpg'
        fig.savefig(fout, facecolor=fig.get_facecolor(), edgecolor='none', dpi=dpi)
        
        # Close the plot object
        plt.close()


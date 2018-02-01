import subprocess
import glob
from SNe_sonify_plot import *

'''
Purpose:
--------
Create the audio and video content for the supernovae AstroSoM.
The output audio needs to be combined with the vocal track of Champagne Supernova.
The output audio and video files then need to be combined together with ffmpeg.
'''

#====================================================================================================
# SETUP!
# ------

# Filenames (SNe data, Milky Way data, rootname for all plots, output MIDI/WAV/MP3/MP4 files)
fdata = "/Users/salvesen/outreach/asom/supernovae/data/SNedata.h5"
fmway = "/Users/salvesen/outreach/asom/supernovae/data/milkyway.h5"
froot = "/Users/salvesen/outreach/asom/supernovae/results/plots/SNe_"
fmidi = "/Users/salvesen/outreach/asom/supernovae/results/sounds/SNe.mid"
fwav  = "/Users/salvesen/outreach/asom/supernovae/results/sounds/SNe.wav"
fmp3  = "/Users/salvesen/outreach/asom/supernovae/results/sounds/SNe.mp3"
fmp4  = "/Users/salvesen/outreach/asom/supernovae/results/plots/SNe.mp4"

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
# SONIFY!
# -------

# Sonify the data
instSNe.sonify(fmidi=fmidi, base_octave=base_octave, octave_range=octave_range)

# Convert the MIDI file to a WAV file
cmdwav = "timidity " + fmidi + " -Ow -o " + fwav
subprocess.call(cmdwav, shell=True)

#====================================================================================================
# PLOT!
# -----

# Plot the data
instSNe.plots(froot=froot, fmway=fmway)

# Determine the frame rate (fps)
beats_per_frame   = float(instSNe.Nbeats) / float(instSNe.Nframes)
beats_per_second  = instSNe.tempo / 60.0
frames_per_second = beats_per_second / beats_per_frame
print "Frames per second: ", frames_per_second
print ""

# Combine the individual frames to ereate an MP4 video
subprocess.call("rm " + fmp4, shell=True)
cmdmp4 = "ffmpeg -f image2 -framerate " + str(frames_per_second) + " -i " + froot + "%04d.png -s 1920x1080 -pix_fmt yuv420p " + fmp4
subprocess.call(cmdmp4, shell=True)


#====================================================================================================
# COMBINING AUDIO AND VIDEO FILES!
# --------------------------------

# Filenames
quiet_mp4 = "/Users/salvesen/outreach/asom/supernovae/results/sounds/vocals_quiet.mp4"
quiet_mp3 = "/Users/salvesen/outreach/asom/supernovae/results/sounds/vocals_quiet.mp3"
cut_mp3   = "/Users/salvesen/outreach/asom/supernovae/results/sounds/vocals_quiet_cut.mp3"
audio_mp3 = "/Users/salvesen/outreach/asom/supernovae/results/sounds/SNe_vocals.mp3"
movie_mp4 = "/Users/salvesen/outreach/asom/supernovae/results/sounds/SNe_movie.mp4"
delay_mp4 = "/Users/salvesen/outreach/asom/supernovae/results/supernovae.mp4"  # <-- Final product!

# Vocal track MP3 and MP4 files
vocals_mp3 = "/Users/salvesen/outreach/asom/supernovae/data/OasisChampagne\ Supernova\ Vocals.mp3"
vocals_mp4 = "/Users/salvesen/outreach/asom/supernovae/data/OasisChampagne\ Supernova\ Vocals.mp4"

# Remove pre-existing files that we are about to overwrite (or else ffmpeg prompts us)
cmd_rm = "rm " + fmp3 + " " + quiet_mp4 + " " + quiet_mp3 + " " + cut_mp3 + " " + audio_mp3 + " " + movie_mp4 + " " + delay_mp4
subprocess.call(cmd_rm, shell=True)

# Check the max_volume in the SNe.mp3 file
cmdV_SNe_wav = "ffmpeg -i " + fwav + " -af 'volumedetect' -vn -sn -dn -f null /dev/null"
subprocess.call(cmdV_SNe_wav, shell=True)
maxV_SNe_wav = -13.2  # [dB] <-- 0 would be normalized
# Normalize the audio in the fwav file by applying the appropriate gain
cmdN_fwav = "ffmpeg -i " + fwav + " -af 'volume=" + str(-maxV_SNe_wav) + "dB' " + fmp3  # <-- Also converting WAV to MP3
subprocess.call(cmdN_fwav, shell=True)
'''
# Alternatively...
cmdmp3 = "timidity -A100 -Ow -o - " + fmidi + " | lame - " + fmp3  # <-- Convert MIDI to MP3
subprocess.call(cmdmp3, shell=True)
cmdV_SNe_mp3 = "ffmpeg -i " + fmp3 + " -af 'volumedetect' -vn -sn -dn -f null /dev/null"
subprocess.call(cmdV_SNe_mp3, shell=True)
'''

# Check the max_volume in the vocals.mp4 file
cmdV_vocals_mp4 = "ffmpeg -i " + vocals_mp4 + " -af 'volumedetect' -vn -sn -dn -f null /dev/null"
subprocess.call(cmdV_vocals_mp4, shell=True)
maxV_vocals_mp4 = -2.2  # [dB] <-- 0 would be normalized
# Normalize the audio in the vocals_mp4 file by applying the appropriate gain
gain_offset = -0.0  # [dB] <-- Make it quieter than the fmp3 file
cmd_quiet_mp4 = "ffmpeg -i " + vocals_mp4 + " -af 'volume=" + str(-maxV_vocals_mp4 + gain_offset) + "dB' -c:v copy -c:a aac -b:a 192k " + quiet_mp4
subprocess.call(cmd_quiet_mp4, shell=True)

# Check that the gain was applied as expected to fmp3 and quiet_mp4
cmdV_SNe_mp3 = "ffmpeg -i " + fmp3 + " -af 'volumedetect' -vn -sn -dn -f null /dev/null"
subprocess.call(cmdV_SNe_mp3, shell=True)
cmdV_quiet_mp4 = "ffmpeg -i " + quiet_mp4 + " -af 'volumedetect' -vn -sn -dn -f null /dev/null"
subprocess.call(cmdV_quiet_mp4, shell=True)

# Extract only the audio (MP3) from the vocals_quiet.mp4 file
# (Note: I was having issues working with the MP3 file, so this is the workaround)
cmd_mp4_2_mp3 = "ffmpeg -i " + quiet_mp4 + " -b:a 192K -vn " + quiet_mp3
subprocess.call(cmd_mp4_2_mp3, shell=True)

# Remove the intro 10.4 seconds of the vocals_quiet.mp3 file
cmd_cut = "ffmpeg -ss 00:00:10.400 -i " + quiet_mp3 + " -acodec copy " + cut_mp3
subprocess.call(cmd_cut, shell=True)

# Merge SNe.mp3 and vocals_quiet_cut.mp3 into one audio MP3 file (of length of the longer of the two)
cmd_audio = "ffmpeg -i " + fmp3 + " -i " + cut_mp3 + " -filter_complex amix=inputs=2:duration=first:dropout_transition=0 -ac 2 -c:a libmp3lame -q:a 4 " + audio_mp3
subprocess.call(cmd_audio, shell=True)

# Combine the audio and video files
cmd_merge = "ffmpeg -i " + fmp4 + " -i " + audio_mp3 + " -c:v copy -c:a aac -strict experimental " + movie_mp4
subprocess.call(cmd_merge, shell=True)

# Delay the audio by a fraction of a second so that it syncs up with the video
cmd_delay = "ffmpeg -i " + movie_mp4 + " -itsoffset 0.600 -i " + movie_mp4 + " -map 0:v -map 1:a -vcodec copy -acodec copy " + delay_mp4
subprocess.call(cmd_delay, shell=True)

# Open the final product!
subprocess.call("open " + delay_mp4, shell=True)

#----------------------------------------------------------------------------------------------------
'''
# THIS APPROACH BELOW USING QuickTime7Pro NO LONGER WORKS, USING FFMPEG INSTEAD (SEE ABOVE)

# Quicktime-related filenames (buildFile, output MOV file)
fbld = "/Users/salvesen/outreach/asom/supernovae/results/plots/buildFile"
fmov = "/Users/salvesen/outreach/asom/supernovae/results/plots/SNe.mov"

# Write out the buildFile for making a Quicktime movie out of the individual image frames
# ...All of the frames have the same duration, which makes things easier...
beats_per_frame   = float(instSNe.Nbeats) / float(instSNe.Nframes)
beats_per_second  = instSNe.tempo / 60.0

seconds_per_frame = beats_per_frame / beats_per_second
duration          =  seconds_per_frame * 600.0  # Frame duration [units of 1/600 of a second]
fpngs = glob.glob(froot + "*.png")
f     = open(fbld, 'w')
for fplot in fpngs:
    line  = fplot + ' ' + str(duration) + '\n'
    f.write(line)
f.close()

# Stitch the frames together into a movie
print "\nStitching frames together as a QuickTime movie...\n"
cmdmov = "./makeQuicktime.py " + fbld + " " + fmov
subprocess.call(cmdmov, shell=True)
'''

''''
Output:
-------
Returns a list containing the chords (list of notes) for every beat (quarter note) in the song

Resources:
----------
Chord progression for Champagne Supernova by Oasis
    https://tabs.ultimate-guitar.com/o/oasis/champagne_supernova_ver2_crd.htm
Champagne Supernova (Vocals Only)
    https://www.youtube.com/watch?v=tTo-uCfe6gg
Champagne Supernova (Instrumental)
    https://www.youtube.com/watch?v=9yG5efiFJ-A
'''

# Chords
A = ['A', 'C#', 'E']
D = ['D', 'F#', 'A']
E = ['E', 'G#', 'B']
F = ['F', 'A', 'C']
G = ['G', 'B', 'D']
Fsm = ['F#', 'A', 'C#']
Asus2   = ['A', 'B', 'E']
Asus2G  = ['A', 'B', 'E', 'G']
Asus2Fs = ['A', 'B', 'E', 'F#']
Asus2E  = ['A', 'B', 'E']
Dmaj7Fs = ['D', 'F#', 'A', 'C#']

# Chord progressions in quarter note (beat) increments
intro   = [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4
verse1  = [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4
chorus1 = [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4
verse2  = [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4
chorus2 = [A]*4 + [G]*4 + [Dmaj7Fs]*4 + [E]*4 + [A]*4 + [G]*4 + [Dmaj7Fs]*4 + [E]*4
bridge1 = [G]*4 + [G]*4 + [A]*4 + [A]*4 + [G]*4 + [D]*4 + [E]*4 + [E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4
inter1  = [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4
verse3  = [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4
chorus3 = [A]*4 + [G]*4 + [Dmaj7Fs]*4 + [E]*4 + [A]*4 + [G]*4 + [Dmaj7Fs]*4 + [E]*4
bridge2 = [G]*4 + [G]*4 + [A]*4 + [A]*4 + [G]*4 + [D]*4 + [E]*4 + [E]*4
inter2  = [A]*4 + [G]*4 + [Fsm]*4 + [F]*2 + [G]*2 + [A]*4 + [G]*4 + [Fsm]*4 + [F]*2 + [G]*2 + [A]*4 + [G]*4 + [Fsm]*4 + [F]*2 + [G]*2 + [A]*4 + [G]*4 + [Fsm]*4 + [F]*2 + [G]*2 + [F]*2 + [G]*2 + [F]*2 + [G]*2 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4
verse4  = [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [F]*4 + [G]*4 + [A]*4 + [A]*4

# Chord progression for the entire song
chordprog = intro + verse1 + chorus1 + verse2 + chorus2 + bridge1 + inter1 + verse3 + chorus3 + bridge2 + inter2 + verse4

'''
# Use these for the YouTube version (which is longer than the vocals only track that I downloaded)
verse4  = [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [Asus2E]*4 + [Asus2]*4 + [Asus2G]*4 + [Asus2Fs]*4 + [F]*4 + [G]*4 + [A]*4 + [A]*4 + [A]*4 + [A]*4
outro   = [F]*4 + [G]*4 + [A]*4
chordprog = intro + verse1 + chorus1 + verse2 + chorus2 + bridge1 + inter1 + verse3 + chorus3 + bridge2 + inter2 + verse4 + outro
'''

def chords():
    return chordprog

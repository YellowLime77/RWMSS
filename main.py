#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests the audacity pipe.

Keep pipe_test.py short!!
You can make more complicated longer tests to test other functionality
or to generate screenshots etc in other scripts.

Make sure Audacity is running first and that mod-script-pipe is enabled
before running this script.

Requires Python 2.7 or later. Python 3 is strongly recommended.

"""

import os
import sys
import math
import time
import wave
import contextlib
from alive_progress import alive_bar
from alive_progress import alive_it
import subprocess
from midiutil.MidiFile import MIDIFile

if sys.platform == 'win32':
    print("pipe-test.py, running on windows")
    TONAME = '\\\\.\\pipe\\ToSrvPipe'
    FROMNAME = '\\\\.\\pipe\\FromSrvPipe'
    EOL = '\r\n\0'
else:
    print("pipe-test.py, running on linux or mac")
    TONAME = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
    FROMNAME = '/tmp/audacity_script_pipe.from.' + str(os.getuid())
    EOL = '\n'

os.startfile(u'C:/Users/matth/Desktop/Audacity.lnk')

print("Write to  \"" + TONAME +"\"")
while True:
    if not os.path.exists(TONAME):
        print(" ..does not exist.  Ensure Audacity is running with mod-script-pipe.")
        time.sleep(1)
    else:
        break

print("Read from \"" + FROMNAME +"\"")
while True:
    if not os.path.exists(FROMNAME):
        print(" ..does not exist.  Ensure Audacity is running with mod-script-pipe.")
        time.sleep(1)
    else:
        break

time.sleep(10)

print("-- Both pipes exist.  Good.")

TOFILE = open(TONAME, 'w')
print("-- File to write to has been opened")
FROMFILE = open(FROMNAME, 'rt')
print("-- File to read from has now been opened too\r\n")


def send_command(command):
    """Send a single command."""
    TOFILE.write(command + EOL)
    TOFILE.flush()

def get_response():
    """Return the command response."""
    result = ''
    line = ''
    while True:
        result += line
        line = FROMFILE.readline()
        if line == '\n' and len(result) > 0:
            break
    return result

def do_command(command):
    """Send one command, and return the response."""
    send_command(command)
    response = get_response()
    return response

def quick_test():
    """Example list of commands."""
    do_command('Help: Command=Help')
    do_command('Help: Command="GetInfo"')
    #do_command('SetPreference: Name=GUI/Theme Value=classic Reload=1')

def dohackeraudiostufflol():
    # create your MIDI object
    mf = MIDIFile(1)     # only 1 track
    track = 0   # the only track

    time = 0    # start at the beginning
    mf.addTrackName(track, time, "Pitch Track")
    mf.addTempo(track, time, int(tempo))

    # add some notes
    channel = 0
    volume = 100

    extra = 0

    for index, note in enumerate(notes):
        pitch = int(note[3])           # G4
        time = (float(note[0])/480) + extra            # start on beat 4
        duration = (float(note[1])/480) - extra         # 1 beat long
        try:
            if ((time + duration == float(notes[index+1][0]) / 480) and abs(pitch - int(notes[index+1][3])) >= 2):
                duration = duration - 0.03125
                mf.addNote(0, 0, math.floor((pitch + int(notes[index+1][3]))/2), time + duration, 0.0625, 100)
                #remove a little from end and add new note
                extra = 0.03125
            else:
                extra = 0
        except:
            print("")
        mf.addNote(track, channel, pitch, time, duration, volume)

    # write it to disk
    with open("pitch.mid", 'wb') as outf:
        mf.writeFile(outf)

    #os.startfile(os.getcwd() + "\\pitch.mid")

tempo = None
#startpos, length, lyric, note
notes = []

args = sys.argv

(do_command('SelectAll:'))
(do_command('RemoveTracks:'))

if len(args) == 1:
    openNotesFilename = input("Notes File (without '.txt'): ")
else:
    openNotesFilename = args[1]

with open(openNotesFilename + '.txt') as f:
    projectfile = f.readlines()

for index, line in enumerate(projectfile):
    if line.startswith("[#"):
        notes.append([projectfile[index+1][9:].replace("\n", ""), projectfile[index+2][7:].replace("\n", ""), projectfile[index+3][6:].replace("\n", ""), projectfile[index+4][5:].replace("\n", "")])
    elif line.startswith("Tempo="):
        tempo = projectfile[index][6:].replace("\n", "")
        tempoTime = 60/int(tempo)

#wavfilename(withending),alias,offset(crop to beginning),consonant(not stretched, relative to offset), cutoff(if positive its from the end, if negative it's from the offset), preutterance(before preutterance is not pitchcorrected, relative to offset), overlap(part before overlap is crossfaded with the previous note, relative to offset)
wavfilesinoto = []

if len(args) <= 2:
    voicebankName = input("Voicebank Name: ")
else:
    voicebankName = args[2]

with open(voicebankName + '/oto.ini', encoding='ISO-8859-1') as f:
    oto = f.readlines()

for index, line in enumerate(oto):
    propertieswithoutnewline = oto[index].split("=", 1)[1].split(",")
    propertieswithoutnewline[-1] = propertieswithoutnewline[-1][:-1]
    wavfilesinoto.append([oto[index].split("=", 1)[0]] + propertieswithoutnewline)

#bar = alive_bar(len(notes))

with alive_bar(len(notes), bar='notes') as bar:
    for index, note in enumerate(notes):
        for wavindex, wavfile in enumerate(wavfilesinoto):
            if wavfile[1] == note[2]:
                filename = os.getcwd() + "/{}/".format(voicebankName) + wavfile[0]
                with contextlib.closing(wave.open(filename,'r')) as f:
                    frames = f.getnframes()
                    rate = f.getframerate()
                    duration = (frames / float(rate)) * 1000
                    ("Duration: ", duration)
                do_command('Import2: Filename={}'.format(filename))

                trimStart = float(wavfile[2]) / 1000
                if float(wavfile[4]) < 0:
                    trimEnd = (abs(float(wavfile[4])) / 1000) + trimStart
                else:
                    trimEnd = (duration - float(wavfile[4])) / 1000
                (do_command('Select: Start={} End={} Track={}'.format(trimStart, trimEnd, index)))
                (do_command('Trim:'))
                (do_command('Select: Start=0 End={} Track={}'.format(trimStart, index)))
                (do_command('Delete:'))
                
                stretchStart = float(wavfile[3]) / 1000
                if float(wavfile[4]) < 0:
                    ("cutoff abs: {}, offset: {}".format(abs(float(wavfile[4])), float(wavfile[2])))
                    stretchEnd = abs(float(wavfile[4])) / 1000
                else:
                    stretchEnd = (duration - float(wavfile[4]) - float(wavfile[2])) / 1000

                (do_command('Select: Start={} End={} Track={}'.format(stretchStart, stretchEnd, index)))
                lengthInitial = stretchEnd - stretchStart
                lengthFinal = ((float(note[1]) * float(tempoTime)) / 480) - (float(wavfile[3])/1000)
                lengthFinalExtra = lengthFinal + 0.5
                stretchPercentage = (((lengthInitial - lengthFinalExtra)/lengthFinalExtra) * 100)
                
                if stretchPercentage < -95:
                    stretchPercentage = -95
                (do_command('ChangeTempo: Percentage={} SBSMS=1'.format(stretchPercentage)))

                if index + 1 >= len(notes):
                    (do_command('Select: Start=0 End={} Track={}'.format((float(note[1]) * float(tempoTime) / 480), index)))
                else:
                    for i, w in enumerate(wavfilesinoto):
                        if w[1] == notes[index + 1][2]:
                            (do_command('Select: Start=0 End={} Track={}'.format((float(note[1]) * float(tempoTime) / 480) + float(w[6]) / 1000, index)))
                            break
                (do_command('Trim:'))
                (do_command('Cut:'))
                (do_command('Select: Start={} End={} Track={}'.format(((float(note[0]) * float(tempoTime)) / 480), ((float(note[0]) * float(tempoTime)) / 480), index)))
                (do_command('Paste:'))

                if (index - 1) >= 0:
                    (do_command('Select: Start={} End={} Track={} TrackCount=2'.format(((float(note[0]) * float(tempoTime)) / 480), ((float(note[0]) * float(tempoTime)) / 480) + float(wavfile[6])/1000, index - 1)))
                    #time.sleep(10)
                    (do_command('CrossfadeTracks: type=ConstantGain curve=0 direction=Automatic'))

                    if notes[index - 1][0] + notes[index - 1][1] >= note[0]:
                        print("AAAAAAAAAA")
                        #do_command('NewMonoTrack:')


                bar()
                #time.sleep(2)
                break
do_command('SelectAll:')
do_command('MixAndRender:')
do_command('Normalize: PeakLevel=-10')
#time.sleep(5)
do_command('Select: Start=0 End=0.07')
do_command('Delete:')
do_command('SelectAll:')
do_command('Cut:')
do_command('Select: Start=0 End=0 Track=0')
do_command('Paste:')
do_command('Import2: Filename={}'.format(os.getcwd() + "/silence.wav"))
do_command('SelectAll:')
exportFileName = "audio.wav"
do_command('Export2: Filename={}'.format(os.getcwd() + "/" + exportFileName))

#do_command('Close:')

dohackeraudiostufflol()

os.system("C:/Users/matth/Downloads/vshifterle341/vshifterle341/vocalshifter_le.exe " + os.getcwd() + "/audio.wav " + os.getcwd() + "/pitch.mid")
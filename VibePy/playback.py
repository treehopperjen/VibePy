"""
playback.py
This is the playback module. It plays the stimulus
for the playback experiment. 
"""

import numpy as np
import soundfile as sf
import sounddevice as sd

def play_and_record(playback, fs, device, input_channel, output_channel):
    """
    play_and_record
    Uses the selected device to play a sound and record it stimultaneously.
    VibePy currently only supports single channel playbacks, therefore this 
    function assumes that input channel 1 and output channel 1 are used on the 
    audio interface.
    """
    # Play and record the playback sound
    recording = sd.playrec(playback, fs, device=device, input_mapping = [input_channel], 
            output_mapping = [output_channel])[:, 0]
    sd.wait()
    return recording

def main(filename, fs, device, input_channel, output_channel):
    print(f'Playing {filename}')
    stimulus, stimulus_fs = sf.read(filename)
    recorded_stimulus = play_and_record(stimulus, fs, device, input_channel, output_channel)
    return recorded_stimulus

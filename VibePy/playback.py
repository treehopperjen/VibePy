"""
playback.py
This is the playback module. It plays the stimulus for the playback experiment.
"""

import numpy as np
import soundfile as sf
import sounddevice as sd


def play_and_record(playback, fs, device, input_channel, output_channel,
                    with_padding=False):
    """
    play_and_record
    Uses the selected device to play a sound and record it simultaneously.
    VibePy currently only supports single channel playbacks, therefore this 
    function assumes that input channel 1 and output channel 1 are used on the 
    audio interface.
    """

    if with_padding:
        # If requested, add padding to the playback. Helps prevent it from
        # getting cut off in the recording
        padding = np.zeros(round(fs / 6))
        padded_playback = np.concatenate([playback, padding, padding])
    else:
        padded_playback = playback

    # Play and record the playback sound
    recording = sd.playrec(padded_playback, fs,
                           device=device,
                           input_mapping=[input_channel],
                           output_mapping=[output_channel])[:, 0]
    sd.wait()

    if with_padding:    # Fix the recording length
        diff_samps = len(recording) - len(playback)

        if diff_samps > 0:
            # If the recording was longer, trim it
            recording = recording[diff_samps:]

        elif diff_samps < 0:
            # If the recording was shorter, pad it with silence
            recording = np.concatenate([recording, np.zeros(diff_samps)])

    return recording


def main(filename, fs, device, input_channel, output_channel):
    print(f'Playing {filename}')
    stimulus, stimulus_fs = sf.read(filename)
    recorded_stimulus = play_and_record(stimulus, fs, device,
                                        input_channel, output_channel)
    return recorded_stimulus

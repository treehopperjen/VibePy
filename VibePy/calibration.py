"""
calibration.py
This is the calibration module. It calculates a multiplier to achieve the
target amplitude, and applies that multiplier to the stimulus.
"""

import soundfile as sf
import os
import numpy as np
from scipy import signal
from playback import play_and_record
from plotting import plot_waveforms, plot_amplitude_spectra


def generate_click(fs):
    """
    generate_click
    Uses the signal parameters provided by the user to generate 2 seconds of
    flat noise.
    """
    click = np.zeros(2 * fs)   
    click[round(len(click)/2)] = 1
    return click


def get_time_delay(fs, device, input_channel, output_channel):
    """
    get_time_delay
    Calculates the time delay by playing and recording a click.
    """
    # get click
    click = generate_click(fs)
    # play and record click
    recorded_click = play_and_record(
        click, fs, device, input_channel, output_channel,
        with_padding=True)

    # get time delay
    time_delay = np.argmax(recorded_click)-fs
    return time_delay


def get_peak_amplitude(recording, amp_conversion, time_delay):
    """
    get_peak_amplitude
    Determines the location and amplitude of the maximum amplitude (i.e., peak)
    in the recording of the stimulus. This step is necessary because the peak
    may not be at the exact location of the peak in the original stimulus.
    """
    # Finds peak location in playback
    recording_peak_location = \
        int(np.where(abs(recording) == max(abs(recording)))[0][0])
    playback_peak_location = recording_peak_location - time_delay
    # Calculates peak amplitude in engineering units
    recording_peak_amp = amp_conversion * max(abs(recording))
    return playback_peak_location, recording_peak_amp


def get_peak_segment(playback, peak_location, segment_size):
    """
    get_peak_segment
    Windows the maximum amplitude (i.e., peak) in the compensated stimulus. 
    """

    # Get the segment of the compensated stimulus that contains the peak
    segment = playback[peak_location-round(segment_size/2):
                       peak_location+round(segment_size/2)]

    # Apply a tapered window to the segment
    segment = segment * get_tapered_window(
        len(segment), round(segment_size / 8))
    return segment


def get_tapered_window(win_len, taper_len):
    """
    Create and return a rect window that's gradually tapered at the ends.
    """
    window = np.ones(win_len)
    ramp = np.linspace(0, np.pi, taper_len)
    window[0:taper_len] = 0.5 * np.sin(ramp - np.pi / 2) + 0.5
    window[win_len - taper_len:win_len] = 0.5 * np.cos(ramp) + 0.5

    return window


def generate_ladder(fs, segment, segment_size,
                    recording_peak_amp, target_peak_amp):
    """
    generate_ladder
    Returns an array of segments that increase in amplitude 
    and the start and end value of each segment in the ladder
    """

    # Calculate the maximum amplitude of the ladder (which should be greater
    # than the peak).
    # get the max amp of segment
    segment_max = max(abs(segment))  # isn't this the same as peak?
    # ensures that the step amps go above the max amp
    step_max = 1.25 * segment_max / (recording_peak_amp / target_peak_amp)

    # Create a vector of amplitude multipliers
    steps = np.linspace(0.01, step_max, 20)

    # Create the ladder of segments with increasing amplitude
    ladder_of_segments = np.concatenate([
        np.multiply(step, segment)
        for step in steps
    ])
    # Save the start x value and end x value of each ramp
    segment_locations = np.asarray([
        [step_idx * segment_size + 1, (step_idx + 1) * segment_size]
        for step_idx in range(len(steps))
    ], dtype=int)

    # Add silence to the beginning and end of the noise
    padding = np.zeros(round(fs))
    playback_ladder = np.concatenate([
        padding, ladder_of_segments, padding
    ])

    # Update the start and end locations of the segments to account for padding
    segment_locations += len(padding)

    return steps, playback_ladder, segment_locations


def find_peaks(recording_of_ladder, recording_segment_locations,
               amp_conversion):
    """
    find_peaks
    Returns a list of the peak amplitude in each segment
    """
    return [
        amp_conversion * max(abs(recording_of_ladder[start:end]))
        for start, end in recording_segment_locations
    ]

def get_amplitude_spectrum(sound, fs, nfft, lo_hi=None):
    """
    get_amplitude_spectrum
    Generates an amplitude spectrum of a selection of sound.
    """
    # `frequencies` is frequency samples of amplitude spectrum
    # `amplitudes` is power spectral density of amplitude spectrum
    frequencies, amplitudes = signal.welch(
        sound, fs, window='hamming',
        nperseg=nfft, scaling='spectrum', detrend=False)

    if lo_hi is not None:   # Limit bandwidth, if requested
        frequencies = frequencies[lo_hi[0]:lo_hi[1]]
        amplitudes = amplitudes[lo_hi[0]:lo_hi[1]]

    return frequencies, np.power(amplitudes, 0.5)

def frequency2samples(freq, fs, fft):
    """
    frequency2samples
    Converts Hz to samples
    """
    return int(np.floor(freq/(fs/fft)))

def main(fs, original_filename, device_num, input_channel, output_channel, 
         filename, target_amp, amp_conversion, fft, low_freq, high_freq):

    print(f'Calibrating {filename}')
    original_stimulus, original_fs = sf.read(original_filename)
    playback, playback_fs = sf.read(filename)

    # convert the units of low and high frequency from Hz to samples
    lo = frequency2samples(low_freq, fs, fft)
    hi = frequency2samples(high_freq, fs, fft)

    # calculate the time delay between the playback and recording
    time_delay = get_time_delay(fs, device_num, input_channel, output_channel)

    # play and record the compensated stimulus
    recording = play_and_record(
        playback, fs, device_num, input_channel, output_channel,
        with_padding=True)  # play filtered stimulus and record

    # determine the peak amplitude in the recording and find its location in
    # the playback
    playback_peak_location, recording_peak_amp = \
        get_peak_amplitude(recording, amp_conversion, time_delay)

    # get the segment in the playback containing the peak amplitude
    segment_size = 8192
    segment = get_peak_segment(playback, playback_peak_location, segment_size)

    # generate a ladder of segments that increase in amplitude
    steps, playback_ladder, playback_segment_locations = \
        generate_ladder(fs, segment, segment_size,
                        recording_peak_amp, target_amp)

    # play and record the ladder
    recording_of_ladder = play_and_record(
        playback_ladder, fs, device_num, input_channel, output_channel,
        with_padding=True)

    # Find the relationship between the multiplier and the recorded amplitude
    # --------------------------------------------------------------------------
    recording_segment_locations = \
        playback_segment_locations + time_delay  # segment locs within playback
    recording_peaks = find_peaks(
        recording_of_ladder, recording_segment_locations, amp_conversion)
    # Perform regression. Get slope (degree of 0) and y intercept (degree of 1)
    # of line of best fit
    polynomial = np.polyfit(recording_peaks, steps, 1)
    # Calculate the multiplier needed to achieve the target peak amplitude.
    # plug target amp in for x to find y (amp to play at to get the target amp)
    multiplier = np.polyval(polynomial, target_amp)

    # Apply the multiplier to the playback
    calibrated_playback = np.multiply(playback, multiplier)

    # play and record the calibrated playback
    recording_of_calibrated_playback = play_and_record(
        calibrated_playback, fs, device_num, input_channel, output_channel,
        with_padding=True)

    # Convert amplitude
    stim1 = original_stimulus * amp_conversion # stimulus
    stim2 = recording_of_calibrated_playback * amp_conversion # recording of calibrated stimylus
    stim3 = calibrated_playback * amp_conversion # calibrated stimulus
    amp_adjusted_stim1 = stim1 * (max(stim2)/max(stim1)) # equalize amplitudes to facilitate comparison of spectra

    # Determine peak
    measured_peak2 = round(max(abs(stim2)), 2)

    # Plot
    plot_waveforms(
        fs, stim1, stim2,
        'Amplitude',
        f'Waveform of Stimulus.',
        'Waveform of Recorded, Calibrated Stimulus.\n'
        f'Measured peak: {measured_peak2}.'
        f'Target: {target_amp}.')

    stim1_freq, stim1_amp = get_amplitude_spectrum(amp_adjusted_stim1, fs, fft, [lo, hi]) # stimulus
    stim2_freq, stim2_amp = get_amplitude_spectrum(stim2, fs, fft, [lo, hi]) # calibrated stimulus

    plot_amplitude_spectra(
            [stim1_freq, stim2_freq],
            [stim1_amp, stim2_amp],
            ['Stimulus', 'Calibrated Stimulus'])

    # save calibrated stimulus
    file_basename = os.path.splitext(filename)[0]
    calibrated_filename = f'calibrated_{file_basename}.wav'
    sf.write(calibrated_filename, calibrated_playback, fs)

    # check for clipping
    if max(abs(calibrated_playback)>=1):
        clipping_message = """NOTE: the saved stimulus file is clipped. 
            Consider re-running the compensation & calibration procedure after increasing 
            the amplifier gain or lowering the target amplitude."""
        print(clipping_message) 
    
    return multiplier, calibrated_filename

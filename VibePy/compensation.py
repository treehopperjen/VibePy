"""
compensation.py
This is the compensation module that generates a compensation filter
and applies the compensation filter to the stimulus.
"""

import numpy as np
import soundfile as sf
from scipy import signal
import os
from playback import play_and_record
from plotting import plot_waveforms, plot_amplitude_spectra
from calibration import get_tapered_window


def generate_noise(fs):
    """
    generate_noise
    Uses the signal parameters provided by the user to generate 2 seconds of
    white noise.
    """
    # Create 2 seconds of white noise
    white_noise = np.random.rand(2 * fs) - 0.5

    # Apply a tapered window to the noise
    white_noise = white_noise * get_tapered_window(
        len(white_noise), round(fs/5))

    # Add silence to the beginning and end of the noise
    padding = np.zeros(round(fs/6))
    noise = np.concatenate([
        padding,
        np.multiply(white_noise, 0.5),
        padding,
        padding,
        padding
    ])

    return noise


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


def get_compensation_filter(playback, recording, fs, nfft, lo, hi):
    """
    get_compensation_filter
    Generates digital filter that is the inverse of the unwanted filtering. The 
    digital filter is a fir (finite impulse response) filter, and here we use 
    a Type 1 filter. 
    """
    # Get amplitude spectra
    _, playback_amp = get_amplitude_spectrum(playback, fs, nfft)
    _, recording_amp = get_amplitude_spectrum(recording, fs, nfft)
    
    # This ratio is the inverse of the unwanted filtering
    amp_ratio = np.divide(playback_amp, recording_amp)
    # zero out of range frequencies
    if lo-1 > 0:
        amp_ratio[0:lo-1] = 0
    amp_ratio[hi+10: len(amp_ratio)] = 0
    
    # Make a frequency vector for the filter
    freq_vector = np.linspace(0, 1, len(amp_ratio))
    freq_vector = np.multiply(fs/2, freq_vector)
    
    # To produce a Type 1 filter
    compensation_filter = signal.firwin2(
        nfft + (nfft % 2 == 0),  # fft must be odd
        freq_vector, amp_ratio, fs=fs)

    return compensation_filter


def compensate(stimulus, compensation_filter):
    """
    compensate
    applies the digital filter to the stimulus and adjusts for clipping, if 
    necessary.
    """
    # Apply the digital filter to the stimulus 
    compensated_stimulus = signal.lfilter(compensation_filter, 1, stimulus)
    
    # If the compensated stimulus would clip, lower the overall amplitude
    if max(abs(compensated_stimulus)) > 1:
        compensated_stimulus = compensated_stimulus / (
                1.1 * max(abs(compensated_stimulus)))

    return compensated_stimulus


def main(fs, fft, low_freq, high_freq, device, input_channel, output_channel,
         stimulus_filename):
    """
    main
    is the starting point of execution in this script
    """

    stimulus, stimulus_fs = sf.read(stimulus_filename)
    # convert the units of low and high frequency from Hz to samples
    lo = frequency2samples(low_freq, fs, fft)
    hi = frequency2samples(high_freq, fs, fft)
    # generate 2 seconds of noise
    noise = generate_noise(fs)
    # set the playback sound to noise for the first compensation cycle
    playback = noise

    continue_compensating = True
    while continue_compensating == True:
        # play and record noise
        recording_of_noise = play_and_record(
            playback, fs, device, input_channel, output_channel,
            with_padding=True)
        # Plot
        plot_waveforms(
            fs, noise, recording_of_noise,
            'relative dB',
            'Waveform of Noise',
            'Waveform of Recorded Noise')
        # generate a digital filter that compensates for unwanted filtering
        compensation_filter = get_compensation_filter(
            noise, recording_of_noise, fs, fft, lo, hi)
        # apply the digital filter to the playback sound
        compensated_noise = compensate(playback, compensation_filter)

        # play and record the compensated noise
        recording_of_compensated_noise = play_and_record(
            compensated_noise, fs, device, input_channel, output_channel,
            with_padding=True)

        # Get amplitude spectra and plot
        stim1_freq, stim1_amp = get_amplitude_spectrum(noise, fs, fft, [lo, hi])
        stim2_freq, stim2_amp = get_amplitude_spectrum(
            recording_of_compensated_noise, fs, fft, [lo, hi])
        
        spectral_difference = stim1_amp - (stim2_amp + np.mean(stim1_amp) - np.mean(stim2_amp))
        max_diff = np.max(abs(spectral_difference))
        average_diff = np.mean(spectral_difference)
        print(f'\nDifference between spectra: \navgerage difference = {average_diff} dB \nmax difference = {max_diff} dB')

        plot_amplitude_spectra(
            [stim1_freq, stim2_freq],
            [stim1_amp, stim2_amp + np.mean(stim1_amp) - np.mean(stim2_amp)],
            ['Noise', 'Recorded, Compensated Noise'],
            f'Difference between spectra: avg difference = {float(f"{average_diff:.1g}"):g} dB, max difference = {float(f"{max_diff:.1g}"):g} dB')
        
        print("\nWould you like to compensate again? (y/n)")
        iterate_again = input()
        if iterate_again.lower() == 'y':
            playback = compensated_noise
        else:
            # get final digital filter that compensates for unwanted filtering
            final_compensation_filter = get_compensation_filter(
                compensated_noise, noise, fs, fft, lo, hi)

            # apply the digital filter to the playback stimulus
            print(f'\nCompensating {stimulus_filename}')
            compensated_stimulus = compensate(stimulus,
                                              final_compensation_filter)
            # play and record the compensated stimulus
            recording_of_compensated_stimulus = play_and_record(
                compensated_stimulus, fs, device, input_channel, output_channel,
                with_padding=True)

            # Get amplitude spectra and plot
            stim1_freq, stim1_amp = get_amplitude_spectrum(
                stimulus, fs, fft, [lo, hi])
            stim2_freq, stim2_amp = get_amplitude_spectrum(
                recording_of_compensated_stimulus, fs, fft, [lo, hi])
            plot_amplitude_spectra(
                [stim1_freq, stim2_freq],
                [stim1_amp, stim2_amp],
                ['Stimulus', 'Recorded, Compensated Stimulus'])
            plot_waveforms(
                fs, stimulus, recording_of_compensated_stimulus,
                'relative dB',
                'Waveform of Stimulus',
                'Waveform of Recorded, Compensated Stimulus')

            # save compensated stimulus
            file_basename = os.path.splitext(stimulus_filename)[0]
            compensated_filename = f'compensated_{file_basename}.wav'
            sf.write(compensated_filename, compensated_stimulus, fs)
            continue_compensating = False

    return compensation_filter, compensated_filename

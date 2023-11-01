"""
compensation.py
This is the compensation module that generates a compensation
filter and applies the compensation filter to the stimulus.
"""

import numpy as np
import soundfile as sf
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from scipy import signal

def generate_noise(fs):
    """
    generate_noise
    Uses the signal parameters provided by the user to generate 2 seconds of white 
    noise.
    """
    # Create 2 seconds of white noise
    white_noise = np.random.rand(2 * fs) - 0.5
    # Create a window and gradually taper it at the beginning and end
    window = np.ones(len(white_noise))
    ramp = np.linspace(0, np.pi, round(fs/5))
    window[0:len(ramp)] = 0.5*np.sin(ramp-np.pi/2) + 0.5
    window[len(window) - len(ramp) : len(window)] = 0.5 * np.cos(ramp) + 0.5
    # Apply the window to the noise
    white_noise = white_noise * window
    # Add silence to the beginning and end of the noise
    padding = np.zeros(round(fs/6))
    noise = []
    noise = np.append(noise, padding)
    noise = np.append(noise, white_noise)
    noise = np.append(noise, padding)
    noise = np.append(noise, padding)
    noise = np.append(noise, padding)
    noise = np.multiply(noise, 0.5)
    return noise

def play_and_record(playback, fs, device, input_channel, output_channel):
    """
    play_and_record
    Uses the selected device to play a sound and record it stimultaneously.
    VibePy currently only supports single channel playbacks, therefore this 
    function assumes that input channel 1 and output channel 1 are used on the 
    audio interface.
    """
    # add padding to the playback so that it doesn't get cut off in the recording
    padding = np.zeros(round(fs/6))
    lengthened_playback = []
    lengthened_playback = np.append(lengthened_playback, playback)
    lengthened_playback = np.append(lengthened_playback, padding)
    lengthened_playback = np.append(lengthened_playback, padding)
    
    # Play and record the playback sound
    recording = sd.playrec(lengthened_playback, fs, device=device, input_mapping = [input_channel], 
            output_mapping = [output_channel])[:, 0]
    sd.wait()
    recording = equalize_length(playback, recording)
    return recording

def equalize_length(playback, recording):
    """
    equalize_length
    Equalizes the length (number of samples) of the playback and recording.
    """
    adjusted_recording = recording
    # If the recording is longer, shorten the recording
    if len(recording) > len(playback):
        difference = len(recording) - len(playback)
        adjusted_recording = recording[difference: len(recording)]
    # If the recording is shorter, lengthen the recording with silence
    elif len(recording) < len(playback):
        adjusted_recording = np.zeros(len(playback))
        adjusted_recording[0:len(recording)] = recording
    return adjusted_recording

def get_amplitude_spectrum(sound, fs, fft, lo, hi):
    """
    get_amplitude_spectrum
    Generates an amplitude spectrum of a selection of sound.
    """
    # Frequencies is frequency samples of amplitude spectrum
    # Amplitudes is power spectral density of amplitude spectrum
    frequencies, amplitudes = signal.welch(sound, fs, window='hamming', 
            nperseg=fft, scaling='spectrum', detrend=False)
    return frequencies, amplitudes

def pxx2decibels(amplitude):
    """
    pxx2decibles
    Converts power spectral density to decibels.
    """
    return 20 * np.log10(amplitude)

def frequency2samples(freq, fs, fft):
    """
    frequency2samples
    Converts Hz to samples
    """
    return int(np.floor(freq/(fs/fft)))

def get_compensation_filter(playback, recording, fs, fft, lo, hi):
    """
    get_compensation_filter
    Generates digital filter that is the inverse of the unwanted filtering. The 
    digital filter is a fir (finite impulse response) filter, and here we use 
    a Type 1 filter. 
    """
    # Get amplitude spectra
    playback_freq, playback_amp = get_amplitude_spectrum(playback, fs, fft, lo, hi)
    recording_freq, recording_amp = get_amplitude_spectrum(recording, fs, fft, lo, hi)
    playback_amp = np.power(playback_amp, 0.5)
    recording_amp = np.power(recording_amp, 0.5)
    
    # This ratio is the inverse of the unwanted filtering
    amp_ratio = np.divide(playback_amp, recording_amp)
    # zero out of range frequencies
    amp_ratio[0:lo] = 0
    amp_ratio[hi+10: len(amp_ratio)] = 0
    
    # Make a frequency vector for the filter
    freq_vector = np.linspace(0, 1, len(amp_ratio))
    freq_vector = np.multiply(fs/2, freq_vector)
    
    # To produce a Type 1 filter, fft must be odd
    if fft % 2 == 0:
        compensation_filter = signal.firwin2(fft+1, freq_vector, amp_ratio, fs=fs)
    else:
        compensation_filter = signal.firwin2(fft, freq_vector, amp_ratio, fs=fs)

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
    if abs(max(compensated_stimulus)) > 1:
        compensated_stimulus = np.multiply(compensated_stimulus, np.divide(1, 1.1*abs(max(compensated_stimulus))))
    return compensated_stimulus

def plot_amplitude_spectra(stim1, stim1_name, stim2, stim2_name, fs, fft, lo, hi):
    """
    plot_amplitude_spectra
    plots amplitude spectra of two stimuli with frequency (Hz) on the x-axis and 
    relative decibels on the y-axis
    """
    # Get amplitude spectra
    stim1_freq, stim1_amp = get_amplitude_spectrum(stim1, fs, fft, lo, hi)
    stim1_freq, stim2_amp = get_amplitude_spectrum(stim2, fs, fft, lo, hi)
    stim1_amp = np.power(stim1_amp, 0.5)
    stim2_amp = np.power(stim2_amp, 0.5)
    
    # Determine the plot's y-axis range
    plt_min = min(stim2_amp[lo:hi])
    plt_max = max(stim2_amp[lo:hi])
    if min(stim1_amp[lo:hi]) < plt_min:
        plt_min = min(stim1_amp[lo:hi])
    if max(stim1_amp[lo:hi]) > plt_max:
        plt_max = max(stim1_amp[lo:hi])
    
    # Plot
    plt.rc('font',family='Arial')
    figure(figsize=(10,7))
    plt.plot(stim1_freq[lo:hi], pxx2decibels(stim1_amp[lo:hi]), label=stim1_name)
    plt.plot(stim1_freq[lo:hi], pxx2decibels(stim2_amp[lo:hi]), label=stim2_name)
    plt.ylim(pxx2decibels(plt_min), pxx2decibels(plt_max))
    plt.xlabel("frequency [Hz]", fontsize=13)
    plt.ylabel("relative amplitude (dB)", fontsize=13)
    plt.title("Amplitude spectra of " + stim1_name + " and " + stim2_name, fontsize=16)
    plt.legend(fontsize=12)
    plt.show()

def plot_waveforms(stim1, stim1_name, stim2, stim2_name, fs):
    """
    plot_waveforms
    plots vertically stacked waveforms of stimuli
    """
    
    # Convert samples to time
    time = np.linspace(0, (len(stim1) / fs), len(stim1))
    
    # Plot
    try:
        plt.rc('font',family='Arial')
    except:
        print('Could not generate figures using "Arial" font.')
    fig, axs = plt.subplots(2, 1, layout = 'constrained')
    fig.set_figwidth(10)
    fig.set_figheight(7)
    axs[0].plot(time, stim1)
    axs[0].set_xlabel('Time (s)', fontsize=13)
    axs[0].set_ylabel(f'relative dB', fontsize=13)
    axs[0].set_title(f'Waveform of {stim1_name}', fontsize=16)
    axs[1].plot(time, stim2)
    axs[1].set_xlabel('Time (s)', fontsize=13)
    axs[1].set_ylabel(f'relative dB', fontsize=13)
    axs[1].set_title(f'Waveform of {stim2_name}', fontsize=16)
    plt.show()

def main(fs, fft, low_freq, high_freq, device, input_channel, output_channel, stimulus_filename):
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
        recording_of_noise = play_and_record(playback, fs, device, input_channel, output_channel)
        plot_waveforms(noise, "Noise", recording_of_noise, "Recorded Noise", fs)
        # generate a digital filter that compensates for unwanted filtering
        compensation_filter = get_compensation_filter(noise, recording_of_noise, fs, fft, lo, hi)
        # apply the digital filter to the playback sound
        compensated_noise = compensate(playback, compensation_filter)

        # play and record the compensated noise
        recording_of_compensated_noise = play_and_record(compensated_noise, fs, device, input_channel, output_channel)
        plot_amplitude_spectra(noise, "Noise", recording_of_compensated_noise, "Recorded, Compensated Noise", fs, fft, lo, hi)
        
        print("\nWould you like to compensate again? (y/n)")
        iterate_again = input()
        if iterate_again == "Y" or iterate_again == 'y':
            playback = compensated_noise
        else:
            # get final digital filter that compensates for unwanted filtering
            final_compensation_filter = get_compensation_filter(compensated_noise, noise, fs, fft, lo, hi)
            # apply the digital filter to the playback stimulus
            print(f'\nCompensating {stimulus_filename}')
            compensated_stimulus = compensate(stimulus, final_compensation_filter)
            # play and record the compensated stimulus
            recording_of_compensated_stimulus = play_and_record(compensated_stimulus, fs, device, input_channel, output_channel)
            plot_amplitude_spectra(stimulus, "Stimulus", recording_of_compensated_stimulus, "Recorded, Compensated Stimulus", fs, fft, lo, hi)
            plot_waveforms(stimulus, "Stimulus", recording_of_compensated_stimulus, "Recorded, Compensated Stimulus", fs)

            # save compensated stimulus
            edited_filename = stimulus_filename.replace(".wav", "")
            compensated_filename = f'compensated_{edited_filename}.wav'
            sf.write(compensated_filename, compensated_stimulus, fs)
            continue_compensating = False

    return compensation_filter, compensated_filename
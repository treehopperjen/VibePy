"""
calibration.py
This is the calibration module. It calculates a multiplier
to achieve the target amplitude, and applies that multiplier
to the stimulus. 
"""

import soundfile as sf
import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from scipy import signal

def generate_click(fs):
    """
    generate_click
    Uses the signal parameters provided by the user to generate 2 seconds of flat noise.
    """
    click = np.zeros(2 * fs)   
    click[round(len(click)/2)] = 1
    return click

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

def get_time_delay(fs, device, input_channel, output_channel):
    """
    get_time_delay
    Calculates the time delay by playing and recording a click.
    """
    # get click
    click = generate_click(fs)
    # play and record click
    recorded_click = play_and_record(click, fs, device, input_channel, output_channel)
    sd.wait()
    # get time delay
    time_delay = np.argmax(recorded_click)-fs
    return time_delay

def frequency2samples(freq, fs, fft):
    return int(np.floor(freq/(fs/fft)))

def get_peak_amplitude(recording, amp_conversion, time_delay):
    """
    get_peak_amplitude
    Determines the location and amplitude of the maximum amplitude (i.e., peak)
    in the recording of the stimulus. This step is necessary because the peak
    may not be at the exact location of the peak in the original stimulus.
    """
    # Finds peak location in playback
    recording_peak_location = int(np.where(abs(recording) == max(abs(recording)))[0][0]) 
    playback_peak_location = recording_peak_location - time_delay
    # Calculates peak amplitude in engineering units
    recording_peak_amp = amp_conversion * max(abs(recording))
    return playback_peak_location, recording_peak_amp

def get_peak_segmentment(playback, peak_location, segment_size):
    """
    get_peak_segmentment
    Windows the maximum amplitude (i.e., peak) in the compensated stimulus. 
    """
    # Gets the segmentment of the compensated sitmulus that contains the peak
    segment = (playback[peak_location-round(segment_size/2):peak_location+round(segment_size/2)])
    # Create a window and gradually taper it at the beginning and end
    window = np.ones(len(segment))
    ramp = np.linspace(0, np.pi, round(segment_size/8))
    window[0:len(ramp)] = 0.5*np.sin(ramp-np.pi/2) + 0.5
    window[len(window) - len(ramp) : len(window)] = 0.5*np.cos(ramp) + 0.5
    # Apply the window to the segmentment
    segment = segment * window
    return segment

def generate_ladder(fs, segment, segment_size, recording_peak_amp, target_peak_amp):
    """
    generate_ladder
    Returns an array of segments that increase in amplitude 
    and the start and end value of each segment in the ladder
    """
    # Calculate the maximum amplitude of the ladder (which should be greater than the peak)
    segment_max = max(abs(segment)) # get the max amp of segmentment # isn't this the same as peak?
    step_max = 1.25 * segment_max / (recording_peak_amp / target_peak_amp) # ensures that the step amps go above the max amp
    # Create a vector of amplitude multipliers
    steps = np.linspace(0.01, step_max, 20)
    # Create the ladder of segments with increasing amplitude
    ladder_of_segments = []
    segment_locations = []
    step_counter = 0
    for i in steps:
        # Adjust the amplitude of each step and add it to the ladder (recall that the step will increase each iteration)
        amp_adjusted_segment = np.multiply(steps[step_counter], segment)
        ladder_of_segments = np.append(ladder_of_segments, amp_adjusted_segment)
        # Saves the start x value and end x value of each ramp in the ramp [(start, end), (start, end) ...]
        segment_start = step_counter * segment_size + 1
        segment_end = (step_counter + 1) * segment_size
        segment_locations.append([segment_start, segment_end])
        step_counter = step_counter + 1
    # Add silence to the beginning and end of the noise
    playback_ladder = []
    padding = np.zeros(round(fs)) 
    playback_ladder = np.append(playback_ladder, padding)
    playback_ladder = np.append(playback_ladder, ladder_of_segments)
    playback_ladder = np.append(playback_ladder, padding)
    # Update the start and end locations of the segmentments to account for padding
    for location in segment_locations:
        location[0] = int(location[0] + len(padding)) # update start
        location[1] = int(location[1] + len(padding)) # update end
    return steps, playback_ladder, segment_locations

def find_segments_in_recording(segment_locations, time_delay):
    """
    find_segments_in_recording
    Uses the segment locations in the played ladder and the time delay
    to calculate the segment locations in the recording
    """
    recording_segment_locations = []
    for segment in segment_locations:
        start = segment[0] + time_delay
        end = segment[1] + time_delay
        recording_segment_locations.append([start, end])
    return recording_segment_locations

def find_peaks(recording_of_ladder, recording_segment_locations, amp_conversion):
    """
    find_peaks
    Returns an array of the peak amplitude in each segment
    """
    recording_peaks = []
    for segment in recording_segment_locations:
        start = segment[0]
        end = segment[1]
        this_segment = recording_of_ladder[start:end] # gets each segmentment from recording
        recording_peaks.append(amp_conversion * max(abs(this_segment))) # gets max amp value in hardware units, and adds to list
    return recording_peaks

def perform_regression(steps, recording_peaks):
    return np.polyfit(recording_peaks, steps, 1) # returns slope (degree of 0) and y intercept (degree of 1) of line of best fit

def get_amplitude_multiplier(polynomial, target_amp):
    return np.polyval(polynomial, target_amp) # plugs target amp in for x to find y (the amp to play at to get the target amp)

def calibrate_amplitude(playback, multiplier):
    """
    calibrate_amplitude
    applies the amplitude multiplier to the stimulus
    """
    return np.multiply(playback, multiplier)

def plot_waveforms(stim1, stim1_name, stim2, stim2_name, fs, target_amp, amp_conversion, amp_units):
    """
    plot_waveforms
    plots vertically stacked waveforms of stimuli
    """
    
    # Convert amplitude
    stim1 = amp_conversion * stim1
    stim2 = amp_conversion * stim2

    # Determine peak
    measured_peak1 = round(max(abs(stim1)), 2)
    measured_peak2 = round(max(abs(stim2)), 2)

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
    axs[0].set_xlabel('time (s)', fontsize=13)
    axs[0].set_ylabel(f'amplitude', fontsize=13)
    axs[0].set_title(f'Waveform of {stim1_name}. \nMeasured peak: {measured_peak1}', fontsize=16)
    axs[1].plot(time, stim2)
    axs[1].set_xlabel('time (s)', fontsize=13)
    axs[1].set_ylabel(f'amplitude', fontsize=13)
    axs[1].set_title(f'Waveform of {stim2_name}. \nMeasured peak: {measured_peak2}. Target: {target_amp} ', fontsize=16)
    plt.show()

def main(fs, fft, low_freq, high_freq, device_num, input_channel, output_channel, filename, target_amp, amp_conversion, amp_units):
    print(f'Calibrating {filename}')

    playback, playback_fs = sf.read(filename)
    # convert the units of low and high frequency from Hz to samples
    lo = frequency2samples(low_freq, fs, fft)
    hi = frequency2samples(high_freq, fs, fft)
    # calculate the time delay between the playback and recording
    time_delay = get_time_delay(fs, device_num, input_channel, output_channel)

    # play and record the compensated stimulus
    recording = play_and_record(playback, fs, device_num, input_channel, output_channel) # play filtered stimulus and record

    # determine the peak amplitude in the recording and find its location in the playback
    playback_peak_location, recording_peak_amp = get_peak_amplitude(recording, amp_conversion, time_delay)
    # get the segment in the playback containing the peak amplitude
    segment_size = 8192
    segment = get_peak_segmentment(playback, playback_peak_location, segment_size)
    # generate a ladder of segments that increase in amplitude
    steps, playback_ladder, playback_segment_locations = generate_ladder(fs, segment, segment_size, recording_peak_amp, target_amp)

    # play and record the ladder
    recording_of_ladder = play_and_record(playback_ladder, fs, device_num, input_channel, output_channel)

    # find the relationship between the multiplier and the recorded amplitude
    recording_segment_locations = find_segments_in_recording(playback_segment_locations, time_delay)
    recording_peaks = find_peaks(recording_of_ladder, recording_segment_locations, amp_conversion)
    polynomial = perform_regression(steps, recording_peaks)
    # calculate the multiplier needed to achieve the target peak amplitude
    multiplier = get_amplitude_multiplier(polynomial, target_amp)
    # apply the multiplier to the playback
    calibrated_playback = calibrate_amplitude(playback, multiplier)

    # play and record the calibrated playback
    recording_of_calibrated_playback = play_and_record(calibrated_playback, fs, device_num, input_channel, output_channel)
    plot_waveforms(playback, 'Stimulus', recording_of_calibrated_playback, f'Recorded, Calibrated Stimulus', fs, target_amp, amp_conversion, amp_units)
    
    # save calibrated stimulus
    edited_filename = filename.replace(".wav", "")
    calibrated_filename = f'calibrated_{edited_filename}.wav'
    sf.write(calibrated_filename, calibrated_playback, fs)
    
    return multiplier, calibrated_filename

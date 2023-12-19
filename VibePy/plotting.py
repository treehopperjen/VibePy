"""
plotting.py
This is the plotting module. It plots graphs with a common style.
"""

import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Arial'   # Set this (once) globally


def plot_waveforms(fs, stim1, stim2, ylabel, title1, title2):
    """
    plot_waveforms
    plots vertically stacked waveforms of stimuli
    """

    # Convert samples to time
    time = np.linspace(0, (len(stim1) / fs), len(stim1))

    fig, axs = plt.subplots(2, 1, layout='constrained')
    fig.set_figwidth(10)
    fig.set_figheight(7)
    axs[0].plot(time, stim1)
    axs[0].set_xlabel('Time (s)', fontsize=13)
    axs[0].set_ylabel(ylabel, fontsize=13)
    axs[0].set_title(title1, fontsize=16)
    axs[1].plot(time, stim2)
    axs[1].set_xlabel('Time (s)', fontsize=13)
    axs[1].set_ylabel(ylabel, fontsize=13)
    axs[1].set_title(title2, fontsize=16)
    plt.show()


def plot_amplitude_spectra(freqs, amps, names):
    """
    plot_amplitude_spectra
    plots amplitude spectra of stimuli with frequency (Hz) on the x-axis and
    relative decibels on the y-axis
    """

    # Determine the plot's y-axis range
    plt_min = min([min(amp) for amp in amps])
    plt_max = max([max(amp) for amp in amps])

    # Plot
    plt.figure(figsize=(10, 7))
    for freq, amp, name in zip(freqs, amps, names):
        plt.plot(freq, 20 * np.log10(amp), label=name)
    plt.ylim(20 * np.log10(plt_min), 20 * np.log10(plt_max))
    plt.xlabel('Frequency [Hz]', fontsize=13)
    plt.ylabel('Relative amplitude (dB)', fontsize=13)
    plt.title('Amplitude spectra of ' +
              ', '.join([name for name in names[:-1]]) +
              f' and {names[-1]}', fontsize=16)
    plt.legend(fontsize=12)
    plt.show()

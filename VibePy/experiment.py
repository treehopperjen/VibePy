"""
This is the model -  all the data and functions that manipulate the data.
It passes information to the viewmodel. 
"""

import compensation
import calibration
import playback


# EXPERIMENT
class Experiment:
    def __init__(self, experiment_name):
        self.name = experiment_name
        self.audiointerface = None
        self.transducers = None
        self.stimulus = None
        self.compensation_filter = None
        self.compensated_filename = None
        self.calibration_mulitplier = None
        self.calibrated_filename = None

    def set_audiointerface(self, device_num):
        self.audiointerface = device_num

    def set_transducers(self, input_channel, output_channel, sensor_type):
        self.transducers = TransducerPair(
            input_channel, output_channel, sensor_type)

    def set_stimulus(self, filename, fs, fft, low_freq, high_freq, target_amp):
        self.stimulus = Stimulus(
            filename, fs, fft, low_freq, high_freq, target_amp)

    def generate_compensation_filter(self):
        # get parameters
        filename = self.stimulus.get_filename()
        fs, fft = self.stimulus.get_sampling_parameters()
        low_freq, high_freq = self.stimulus.get_frequency_parameters()
        device_num = self.audiointerface
        input_channel, output_channel = self.transducers.get_channels()

        # run compensation to get filter
        self.compensation_filter, self.compensated_filename = \
            compensation.main(
                fs, fft, low_freq, high_freq,
                device_num, input_channel, output_channel, filename)

    def generate_calibration_multiplier(self):
        # use the compensated file if there is one, if not use the original file
        if self.compensated_filename is not None:
            filename = self.compensated_filename
        else:
            filename = self.stimulus.get_filename()
        # get parameters
        fs, fft = self.stimulus.get_sampling_parameters()
        # low_freq, high_freq = self.stimulus.get_frequency_parameters()
        device_num = self.audiointerface
        input_channel, output_channel = self.transducers.get_channels()
        target_amp = self.stimulus.get_amplitude_parameter()
        amp_conversion = self.transducers.get_sensor_conversion()
        amp_units = self.transducers.get_sensor_units()
        # run calibration to get multiplier
        self.calibration_mulitplier, self.calibrated_filename = \
            calibration.main(
                fs,
                device_num, input_channel, output_channel, filename,
                target_amp, amp_conversion, amp_units)

    def play_for_experiment(self):
        # use the calibrated file if there is one, if not use the compensated
        # file, if not use the original file
        if self.calibrated_filename is not None:
            filename = self.calibrated_filename
        elif self.compensated_filename is not None:
            filename = self.compensated_filename
        else:
            filename = self.stimulus.get_filename()
        # get parameters
        fs, fft = self.stimulus.get_sampling_parameters()
        # low_freq, high_freq = self.stimulus.get_frequency_parameters()
        device_num = self.audiointerface
        input_channel, output_channel = self.transducers.get_channels()
        # run playback to play vibrational stimulus
        playback.main(filename, fs, device_num, input_channel, output_channel)

    def __str__(self):
        return (f"""
{self.name}

Hardware Parameters
Audiointerface device num: {self.audiointerface}{
            '' if self.transducers is None else self.transducers}

Stimulus and Signal Parameters{
            '' if self.stimulus is None else self.stimulus}"""
                )


class TransducerPair:

    sensor_options = [
        [0, 'accelerometer 100 mV/G (1x gain)', 'm/s^2', 98],
        [1, 'accelerometer 100 mV/G (10x gain)', 'm/s^2', 9.8],
        [2, 'accelerometer 100 mV/G (100x gain)', 'm/s^2', 0.98],
        [3, 'laser 2.5 mm/s/V', 'mm/s', 2.5],
        [4, 'laser 5 mm/s/V', 'mm/s', 5],
        [5, 'laser 25 mm/s/V', 'mm/s', 25],
        [6, 'uncalibrated sensor mV', 'mV', 1000]
    ]

    def __init__(self, input_channel, output_channel, sensor_type):
        self.input_channel = input_channel    # sensor channel
        self.output_channel = output_channel  # playback device channel
        self.sensor_type = sensor_type

    def get_channels(self):
        return self.input_channel, self.output_channel

    def get_sensor_units(self):
        units = ''
        for option in TransducerPair.sensor_options:
            if self.sensor_type == option[1]:
                units = option[2]
        return units

    def get_sensor_conversion(self):
        conversion = 0
        for option in TransducerPair.sensor_options:
            if self.sensor_type == option[1]:
                conversion = option[3]
        return conversion

    def __str__(self):
        sensor_amp_units = self.get_sensor_units()
        sensor_amp_conversion = self.get_sensor_conversion()
        return(f"""
Sensor channel: {self.input_channel}
Playback device channel: {self.output_channel}
Sensor: {self.sensor_type}
Sensor units: {sensor_amp_units}
Sensor amplitude conversion: {sensor_amp_conversion}"""
               )


class Stimulus:
    def __init__(self, filename, fs, fft, low_freq, high_freq, target_amp):
        self.filename = filename
        self.fs = fs
        self.fft = fft
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.target_amp = target_amp

    def get_filename(self):
        return self.filename

    def get_sampling_parameters(self):
        return self.fs, self.fft

    def get_frequency_parameters(self):
        return self.low_freq, self.high_freq

    def get_amplitude_parameter(self):
        return self.target_amp

    def __str__(self):
        return(
            f"""
Stimulus file: {self.filename}
fs: {self.fs}
fft: {self.fft}
low frequency: {self.low_freq}
high frequency: {self.high_freq}
""" +
            '' if self.target_amp is None else
            f'target amplitude: {self.target_amp}'
               )

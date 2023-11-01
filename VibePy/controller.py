"""
This is the viewmodel. It passes information between 
the view (the part that the user interacts with) and
the model (the data and functions). 
"""

import experiment as e

class Controller():
    def __init__(self, experiment_name, compensate, calibrate, playback):
        self.experiment = e.Experiment(experiment_name)

    def add_audiointerface(self, device_num):
        self.experiment.set_audiointerface(device_num)

    def add_transducers(self, input_channel, output_channel, sensor_type):
        self.experiment.set_transducers(input_channel, output_channel, sensor_type)
    
    def add_stimulus(self, filename, fs, fft, low_freq, high_freq, target_amp):
        self.experiment.set_stimulus(filename, fs, fft, low_freq, high_freq, target_amp)

    def get_compensation_filter(self):
        self.experiment.generate_compensation_filter()

    def get_calibration_multiplier(self):
        self.experiment.generate_calibration_multiplier()

    def play_stimulus(self):
        self.experiment.play_for_experiment()

    def get_experiment(self):
        return self.experiment

    
    
# VIEW TO MODEL
# add setup
# - input: input channel, output channel, sensor
# - experiment.new_setup

# add new stimulus
# - input: filename, fs, fft, target amp*
# - experiment.new_stimulus

# add experimental unit
# - input: setup id, stimulus id
# - experiment.new_experimental_unit

# get compensation filters 
# - input: none?
# experiment.generate_compensation_filters
# - output: plot

# calibrate amplitude

# play stimuli

# MODEL TO VIEW

# get setups

# get stimuli

# get experimental units
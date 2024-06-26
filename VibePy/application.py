"""
This is the view - the part that the user interacts with.
It passes information between the user and the viewmodel.  
"""

import sys
from os import path
import sounddevice as sd
from controller import Controller
from experiment import TransducerPair
from datetime import datetime


# PRINT FORMATTING
tab = '> '                      # tab-ish
ln = '\n'                       # new line
divider = '---------------'     # divider


def main():
    print(f'{ln}{divider} Welcome to VibePy! {divider}{ln}')
    
    print(f'{ln}GENERAL EXPERIMENT PARAMETERS {divider}{ln}')
    # Initialize experiment
    experiment_name = request_experiment_name()
    compensate, calibrate, playback = request_experiment_actions()
    controller = Controller(experiment_name)
    
    provide_param_file = request_provide_param_file()
    
    if provide_param_file:
        param_file_name = request_param_file_name()
        
        # Get parameters from a file
        if not path.exists(param_file_name):
            print(f'{ln}{param_file_name} does not exist. Enter parameters below. ')
            provide_param_file = False
        else:
            input_device_num = int(get_testing_parameter(param_file_name, 'input_device_num'))
            output_device_num = int(get_testing_parameter(param_file_name, 'output_device_num'))
            device_num = (input_device_num, output_device_num)
            controller.add_audiointerface(device_num)

            input_channel = int(get_testing_parameter(param_file_name, 'input_channel'))
            output_channel = int(get_testing_parameter(param_file_name, 'output_channel'))
            sensor_number = int(get_testing_parameter(param_file_name, 'sensor_number'))
            sensor_type = get_sensor_type(sensor_number)
            controller.add_transducers(input_channel, output_channel, sensor_type)

            stimulus_filename = get_testing_parameter(param_file_name, 'stimulus_filename')
            fs = int(get_testing_parameter(param_file_name, 'fs'))
            fft = int(get_testing_parameter(param_file_name, 'fft'))
            low_freq = int(get_testing_parameter(param_file_name, 'low_freq'))
            high_freq = int(get_testing_parameter(param_file_name, 'high_freq'))
            target_amp = float(get_testing_parameter(param_file_name, 'target_amp'))
            controller.add_stimulus(stimulus_filename, fs, fft,
                                    low_freq, high_freq, target_amp)

    # Get parameters from user
    if not provide_param_file:
        print(f'{ln}HARDWARE PARAMETERS {divider}{ln}')
        input_device_num, output_device_num = request_audiointerface()
        device_num = (input_device_num, output_device_num)
        controller.add_audiointerface(device_num)

        input_channel = request_input_channel(input_device_num)
        output_channel = request_output_channel(output_device_num)
        sensor_number = request_sensor()
        sensor_type = get_sensor_type(sensor_number)
        sensor_amp_units = get_sensor_units(sensor_number)
        controller.add_transducers(input_channel, output_channel, sensor_type)

        print(f'{ln}STIMULUS & SIGNAL PARAMETERS {divider}{ln}')
        stimulus_filename = request_simulus_file()
        fs, fft, low_freq, high_freq, target_amp = \
            request_signal_parameters(sensor_amp_units, calibrate)
        controller.add_stimulus(stimulus_filename, fs, fft,
                                low_freq, high_freq, target_amp)

    print(f'{ln}{divider} Experiment Description {divider}{ln}')
    print(controller.get_experiment())

    if continue_request() is not True:
        print('Goodbye.')
        sys.exit()

    if compensate: 
        print(f'{ln}{divider} Measuring and compensating for unwanted filtering'
              f'{divider}{ln}')
        controller.get_compensation_filter()

    if calibrate:
        print(f'{ln}{divider} Calibrating amplitude {divider}{ln}')
        controller.get_calibration_multiplier()
    
    if playback:
        print(f'{ln}{divider} Playing vibrational stimulus {divider}{ln}')
        controller.play_stimulus()


def request_experiment_name():
    experiment_name = input(f'Experiment name: ')
    if experiment_name == "":
        experiment_name = datetime.now().strftime("%d%m%Y %H: %M: %S")
    return experiment_name


def request_experiment_actions():
    print(f'{ln}Do you want to... (y/n)')
    compensate = input(f'{tab}Measure and compensate for unwanted filtering? ')
    calibrate = input(f'{tab}Calibrate playback amplitude? ')
    playback = input(f'{tab}Play vibrational stimuli? ')

    compensate = compensate.lower() == 'y'
    calibrate = calibrate.lower() == 'y'
    playback = playback.lower() == 'y'

    # if compensate:
    #     print("compensate", compensate)
    # if calibrate:
    #     print("calibrate", calibrate)
    # if playback:
    #     print("playback", playback)
    
    return compensate, calibrate, playback

def request_provide_param_file():
    provide_param_file = input(f'{ln}Do you want to use a saved parameters file?: ')
    provide_param_file = provide_param_file.lower() == 'y'
    return provide_param_file

def request_param_file_name():
    param_file_name = input(f'Parameters file name: ')
    return param_file_name

def request_audiointerface():
    print(f'Find your audio device(s) below...\n', sd.query_devices())
    print(f'{ln}If you are using the same device for input and output'
          ' (e.g. audio interface), enter that number for both.')
    input_device_num = int(input(f'{ln}Input device number: '))
    output_device_num = int(input(f'Output device number: '))
    return input_device_num, output_device_num


def request_output_channel(output_device_num):
    max_out = sd.query_devices()[output_device_num].get('max_output_channels')
    output_channel = int(input(f'{tab}Playback device channel ({max_out} available): '))
    return output_channel


def request_input_channel(input_device_num):
    max_in = sd.query_devices()[input_device_num].get('max_input_channels')
    input_channel = int(input(f'{ln}{tab}Sensor channel ({max_in} available): '))
    return input_channel


def request_sensor():
    print(f'{ln}Find the sensor type you are using below...')
    print('\n'.join([str(x[0]) + ". " + x[1]
                     for x in TransducerPair.sensor_options]))

    sensor_number = int(input(f'{ln}{tab}Enter sensor type number: '))
    return sensor_number


def request_simulus_file():
    return input(f'Enter the name of playback stimulus file: ')


def request_signal_parameters(sensor_amp_units, do_calibrate):
    print(f'{ln}Enter signal parameters of the playback stimulus...')
    fs = int(input(f'{tab}sampling rate: '))
    fft = int(input(f'{tab}fft size: '))
    low_freq = int(input(f'{tab}low frequency: '))
    high_freq = int(input(f'{tab}high frequency: '))

    if do_calibrate:
        target_amp = float(
            input(f'{tab}target amplitude in {sensor_amp_units}: '))
    else:
        target_amp = None

    return fs, fft, low_freq, high_freq, target_amp


def get_sensor_type(sensor_number):
    return TransducerPair.sensor_options[sensor_number][1]


def get_sensor_units(sensor_number):
    return TransducerPair.sensor_options[sensor_number][2]


def continue_request():
    cont = input(f'{ln}Do you want to continue? (y/n) ')
    return cont.lower() == 'y'


def get_testing_parameter(file_name, parameter):

    try:
        with open(file_name) as file:

            for line in file:
                try:
                    parameter_name, _, rhs = line.split(' ')
                    if parameter_name == parameter:
                        return rhs.replace('\n', '')
                except Exception as exc:
                    pass

            # Reached end of file. Complain!
            print(f'Could not find {parameter} in testing_parameters.txt.\n'
                  'Add a new line to testing_parmaeters.txt as '
                  f'{parameter} = your value.', file=sys.stderr)

    except Exception as exc:
        print(f'Error reading {file_name}: {exc}', file=sys.stderr)

    return 0    # Requested param wasn't found or there was an error
            

if __name__ == "__main__":
    main()

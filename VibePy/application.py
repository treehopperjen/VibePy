"""
This is the view - the part that the user interacts with.
It passes information between the user and the viewmodel.  
"""

import sounddevice as sd
import controller as c

# OPTIONS
device_options = sd.query_devices()

sensor_options = [[0, 'accelerometer 100 mV/G (1x gain)', 'm/s^2', 98],
     [1, 'accelerometer 100 mV/G (10x gain)', 'm/s^2', 9.8],
     [2, 'accelerometer 100 mV/G (100x gain)', 'm/s^2', 0.98],
     [3, 'laser 2.5 mm/s/V', 'mm/s', 2.5],
     [4, 'laser 5 mm/s/V', 'mm/s', 5],
     [5, 'laser 25 mm/s/V', 'mm/s', 25],
     [6, 'uncalibrated sensor mV', 'mV', 1000]]

# EXPERIMENT PARAMETERS
experiment_name = ''
compensate = False # maybe change these to dictionary?
calibrate = False
playback = False

device_num = 0

input_channel = 0
output_channel = 0
sensor_type = ''
sensor_amp_units = ''

stimulus_filename = ''
fs = 0
fft = 0
low_freq = 0
high_freq = 0
target_amp = 0

# PRINT FORMATTING
tab = '> ' # tab-ish
ln = '\n' # new line
divider = '---------------' # divider

def main():
    print(f'{ln}{divider} Welcome to VibePy! {divider}{ln}')
    
    print(f'{ln}GENERAL EXPERIMENT PARAMETERS {divider}{ln}')
    experiment_name = request_experiment_name()
    compensate, calibrate, playback = request_experiment_actions()
    controller = c.Controller(experiment_name, compensate, calibrate, playback) # initalizes experiment
    
    if experiment_name == 'testing':
        device_num = int(get_testing_parameter('device_num'))
        controller.add_audiointerface(device_num)

        input_channel = int(get_testing_parameter('input_channel'))
        output_channel = int(get_testing_parameter('output_channel'))
        sensor_number = int(get_testing_parameter('sensor_number'))
        sensor_type = get_sensor_type(sensor_number)
        controller.add_transducers(input_channel, output_channel, sensor_type)

        stimulus_filename = get_testing_parameter('stimulus_filename')
        fs = int(get_testing_parameter('fs'))
        fft = int(get_testing_parameter('fft'))
        low_freq = int(get_testing_parameter('low_freq'))
        high_freq = int(get_testing_parameter('high_freq'))
        target_amp = float(get_testing_parameter('target_amp'))
        controller.add_stimulus(stimulus_filename, fs, fft, low_freq, high_freq, target_amp)

    else:
        print(f'{ln}HARDWARE PARAMETERS {divider}{ln}')
        device_num = request_audiointerface()
        controller.add_audiointerface(device_num)

        input_channel, output_channel = request_transducer_channels()
        sensor_number = request_sensor()
        sensor_type = get_sensor_type(sensor_number)
        sensor_amp_units = get_sensor_units(sensor_number)
        controller.add_transducers(input_channel, output_channel, sensor_type)

        print(f'{ln}STIMULUS & SIGNAL PARAMETERS {divider}{ln}')
        stimulus_filename = request_simulus_file()
        fs, fft, low_freq, high_freq, target_amp = request_signal_parameters(sensor_amp_units)
        controller.add_stimulus(stimulus_filename, fs, fft, low_freq, high_freq, target_amp)

    print(f'{ln}{divider} Experiment Description {divider}{ln}')
    print(controller.get_experiment())

    if continue_request() is not True:
        print('Goodbye.')
        exit()

    if compensate: 
        print(f'{ln}{divider} Measuring and compensating for unwanted filtering {divider}{ln}')
        controller.get_compensation_filter()

    if calibrate:
        print(f'{ln}{divider} Calibrating amplitude {divider}{ln}')
        controller.get_calibration_multiplier()
    
    if playback:
        print(f'{ln}{divider} Playing vibrational stimulus {divider}{ln}')
        controller.play_stimulus()

def request_experiment_name():
    experiment_name = input(f'Experiment name: ')
    return experiment_name

def request_experiment_actions():
    print(f'{ln}Do you want to... (y/n)')
    compensate = input(f'{tab}Measure and compensate for unwanted filtering? ')
    calibrate = input(f'{tab}Calibrate playback amplitude? ') # but cant calibrate if you dont compensate first?
    playback = input(f'{tab}Play vibrational stimuli? ')

    if compensate == 'Y' or compensate == 'y':
        compensate = True
        print("compensate", compensate)
    else:
        compensate = False

    if calibrate == 'Y' or calibrate == 'y':
        print("calibrate", calibrate)
        calibrate = True
    else:
        calibrate = False
    
    if playback == 'Y' or playback == 'y':
        print("playback", playback)
        playback = True
    else: 
        playback = False
    
    return compensate, calibrate, playback

def request_audiointerface():
    print(f'Find your audio interface below...\n', device_options)
    device_num = int(input(f'{ln}{tab}Enter audio interface device number: '))
    return device_num

def request_transducer_channels():
    print(f'{ln}Enter the channel numbers your are using on your audio interface...')
    output_channel = int(input(f'{tab}Playback device channel: '))
    input_channel = int(input(f'{tab}Sensor channel: '))
    return input_channel, output_channel

def request_sensor():
    print(f'{ln}Find the sensor type you are using below...')
    sensor_names = [str(x[0]) + ". " + x[1] for x in sensor_options]
    print(*sensor_names, sep = '\n')
    sensor_number = int(input(f'{ln}{tab}Enter sensor type number: '))
    return sensor_number

def request_simulus_file():
    stimulus_filename = input(f'Enter the name of playback stimulus file: ')
    return stimulus_filename

def request_signal_parameters(sensor_amp_units):
    print(f'{ln}Enter signal parameters of the playback stimulus...')
    fs = int(input(f'{tab}sampling rate: '))
    fft = int(input(f'{tab}fft size: '))
    low_freq = int(input(f'{tab}low frequency: '))
    high_freq = int(input(f'{tab}high frequency: '))
    if calibrate == True:
        target_amp = float(input(f'{tab}target amplitude in {sensor_amp_units}: '))
    else:
        target_amp = None
    return fs, fft, low_freq, high_freq, target_amp

def get_sensor_type(sensor_number):
    sensor_type = sensor_options[sensor_number][1]
    return sensor_type

def get_sensor_units(sensor_number):
    sensor_amp_units = sensor_options[sensor_number][2]
    return sensor_amp_units

def continue_request():
    cont = input(f'{ln}Do you want to continue? (y/n) ')
    if cont == 'Y' or cont == 'y':
        cont = True
    else:
        cont = False
    return cont

def get_testing_parameter(parameter):
    value = 0
    try:
        file = open('testing_parameters.txt')
    except:
        print('Could not read testing_parameters.txt')
    try:
        for line in file:
            line_parts = line.split(' ')
            parameter_name = line_parts[0]
            if parameter_name == parameter:
                value = line_parts[2].replace("\n", "")

    except:
        print(f'Could not find {parameter} in testing_parameters.txt. \nAdd a new line to testing_parmaeters.txt as {parameter} = your value.')
    return value
            


if __name__ == "__main__":
    main()
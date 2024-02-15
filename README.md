
# VibePy

Implementation of the tool described in

> [INSERT CITATION]

for performing vibrational playback experiments.

The tool offers features for -
- measuring and compensating for undesired filtering,
- calibrating playback amplitude, and
- playing back vibrational stimuli.

Instructions for setting up the tool and using these features are described below. If you use VibePy (in entirety or in part), we request that you please cite the article cited above. 

### Getting started
- Download python3 which is freely available at https://www.python.org/
- [Download](https://docs.github.com/en/get-started/quickstart/downloading-files-from-github) or [clone](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) the VibePy repository 
    `git clone https://github.com/treehopperjen/VibePy.git`
- Install the required python packages listed in [requirements.txt](https://github.com/treehopperjen/VibePy/blob/96d738a79f68ac0a0e58b7517245666b043cd249/requirements.txt)
    `pip3 install -r requirements.txt`
- Run `application.py`

### Using VibePy
VibePy is a command-line interface application that is run from `application.py`. First, enter parameters of the experiment (see the article cited above) and then select which features to use. The features can be used individually or together. When used together, they will execute in the following order:

    1. Measure and compensate for filtering
    2. Calibrate playback amplitude
    3. Play back vibrational stimuli

**Measure and compensate for filtering**

This module measures undesired filtering by the playback device and substrate, and then generates a digital filter (i.e., compensation filter) that is the inverse of the undesired filtering. This compensation filter can then be applied to a stimulus before it is played for the experiment, such that the detected stimulus has the same frequency characteristics as the intended stimulus. 

The code for this module is in [compensation.py](https://github.com/treehopperjen/VibePy/blob/96d738a79f68ac0a0e58b7517245666b043cd249/VibePy/compensation.py) and works iteratively by:

- Playing and recording two seconds of noise
- Measuring the filtering of the noise
- Compensating for filtering by generating the digital filter
- Applying the digital filter to the noise to create compensated noise
- Playing and recording the compensated noise to evaluate whether the digital filter worked

**Evaluation:** If the compensation filter is accurate, the shape of the amplitude spectra of the original noise and the recorded, compensated noise should match. Otherwise, another round of compensation may be necessary to fine-tune the compensation filter. Note that the overall amplitude of the noise and the recorded, compensated noise may differ because playback amplitude has not been calibrated yet. 

**Calibrate playback amplitude**

This module calibrates the amplitude of the playback stimulus by estimating an amplitude multiplier that can be applied to the stimulus to match the peak amplitude of the played stimulus to the target amplitude. 

The code for this module is in [calibration.py](https://github.com/treehopperjen/VibePy/blob/96d738a79f68ac0a0e58b7517245666b043cd249/VibePy/calibration.py) and works by:

- Playing and recording the stimulus (or compensated stimulus, if available)
- Locating the recorded peak amplitude in the stimulus and extracting it
- Generating a ladder of modulated peaks that increase in amplitude
- Playing and recording the ladder of modulated peaks
- Using the recording of the peaks to estimate the multiplier

**Play vibrational stimuli**

This module plays and records the stimulus. It will automatically play the most updated version of the stimulus if it is available (i.e., compensated, calibrated, or compensated/calibrated stimulus).  

The code for this module is in [playback.py](https://github.com/treehopperjen/VibePy/blob/96d738a79f68ac0a0e58b7517245666b043cd249/VibePy/playback.py)


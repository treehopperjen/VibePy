
# VibePy

Implementation of the tool described in

> [INSERT CITATION]

for performing vibrational playback experiments.

The tool offers features for -
- measuring and compensating for undesired filtering,
- calibrating playback amplitude, and
- playing back vibrational stimuli.

Instructions for setting up the tool and using these features are described below. If you use VibePy (in entirety or in part), we request that you please cite the aforementioned article. 

### Getting started
- Download python3 which is freely available at https://www.python.org/
- Clone the VibePy repository 
    `clone https://github.com/treehopperjen/VibePy.git`
- Install the required python packages listed in requirements.txt 
    `pip3 install -r requirements.txt`
- Run `application.py`

### Using VibePy

VibePy is a command-line interface application that is run from `application.py`. First, enter parameters of the experiment (which are described in the article cited above) and then select which features to use. The features can be used individually or together. When used together, they will execute in the following order:

    1. Measure and compensate for filtering
    2. Calibrate playback amplitude
    3. Play back vibrational stimuli

**Measure and compensate for filtering**

This module measures undesired filtering by the playback device and substrate, and then generates a digital filter (i.e. compensation filter) that is the inverse of the undesired filtering. This compensation filter can then be applied to a stimulus before it is played for the experiment, such that the detected stimulus has the same frequency characteristics as the intended stimulus. 

The code for this module is in `compensate.py` and works iteratively by:

- Playing and recording two seconds of noise
- Measuring the filtering of the noise
- Compensating for filtering by generating the digital filter
- Applying the digital filter to the noise to create compensated noise
- Playing and recording the compensated noise to evaluate whether the digital filter worked

**Evaluate:** If the compensation filter is accurate, the shape of the amplitude spectra of the original noise and the recorded, compensated noise should match. Otherwise, another round of compensation may be necessary to fine-tune the compensation filter. *See the article cited above for more details.* 

**Calibrate playback amplitude**

This module calibrates the amplitude of the playback stimulus by estimating an amplitude multiplier that can be applied to the stimulus to match the peak amplitude of the played stimulus to the target amplitude. 

The code for this module is in `calibrate.py` and works by:

- Playing and recording the stimulus (or compensated stimulus, if available)
- Locating the recorded peak amplitude in the stimulus and extracting it
- Generating a ladder of modulated peaks that increase in amplitude
- Playing and recording the ladder of modulated peaks
- Using the recording of the peaks to estimate the multiplier

**Play vibrational stimuli**

This module plays and records the stimulus. It will use the compensated, calibrated, or compensated/calibrated stimulus if it is available. 

The code for this module is in `playback.py`


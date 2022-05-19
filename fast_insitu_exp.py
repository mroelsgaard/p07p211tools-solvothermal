#!/usr/bin/python3
"""
 MartinR 22.09.2021

 script to run insitu experiment controlling detector, and monitoring counters
 and HPLC pump and logs to file.

"""
from PyTango import *
import time
import datetime
import sys
import os
import numpy as np
from random import randint

# counter methods
from counters import *

# TODO: use logging module
#import logging


from pilatus import pilatus_detector
from liveview import Liveview

from insitu_exp import *


if __name__ == "__main__":
    if sys.version_info[0] == 2:
        """
         this does not work in python2, so quit if that is the case..
        """
        print(f'Python version: {sys.version_info}')
        print('Quitting, use Python3!')
        sys.exit()

    if len(sys.argv) < 2:
        print('Usage: ./insitu_exp.py filename exposure(seconds) length(seconds)')
        print('Filenames will be filename-xxxxx.tif in /gpfs/current/raw/pilatus/filename/')
        print('Ctrl+C to stop the experiment again')
        sys.exit()

    exp = experiment()

    # get rid of first argument if it is python
    if sys.argv[0] == 'python':
        sys.argv.pop(0)
    
    exp.filename = sys.argv[1]
    if exp.filename == 'test':
        rn = randint(1,1000)
        exp.filename = f'test_{rn:05d}'

    exp.exposure = float(sys.argv[2])
    print(exp.exposure)
    exp.length = float(sys.argv[3])

    exp.sprint(f'Experiment folder/filename: {exp.filename}')
    exp.sprint(f'Experiment exposure time: {exp.exposure}')

    liveview = Liveview()

    # write header to top of the log_file
    exp.pre_experiment()
   
    curr_path =  f'/gpfs/current/raw/pilatus2/{exp.filename}'
    if os.path.exists(curr_path):
        exp.sprint('Folder/filename already exists! Exiting, please find a new name!')
        sys.exit()

    nb_of_frames = int(exp.length/exp.exposure)

    # setup detector config and wait for 5 seconds before starting
    exp.fileidx = 0 # set to 0 here, +1 for every time
    exp.dev_detector.setup_pilatus(filename=exp.filename, 
                       exp_time=exp.exposure,
                       n_frames = nb_of_frames # run this script continously in a loop
                        )
    exp.sprint('Ready to start the experiment now. Starting in 5 seconds. Please check values!')
    exp.rTimer(5)

    # create object to start, stop and check liveview
    first = True
    try:
        # start experiment

        # check if liveview running
        if liveview.running():
            liveview.stop()
            exp.sprint('Liveview was running, and was stopped.')

        # create infinite loop that is interrupted by ctrl+c
        while True:
            """
             sample shot area!
            """
            exp.sprint(60*'-')
            t0 = time.perf_counter()
            exp.reset_cntrs()

            # get fileindex from pilatus
            #exp.fileidx += 1
            exp.fileidx = exp.dev_detector.get_file_idx()
            
            #exp.sprint('t reset: {time.perf_counter()-t0}') 
            exp.timer_start(exp.dev_timer_1) # start hardware timer
            # take shot, returns filename
            # blocks thread untill detector has not been in DevState.RUNNING
            # for approx. 5 ms
            #exp.sprint('t before pil: {time.perf_counter()-t0}') 

            # stat acquisition
            if first:
                first = False
                fname = exp.dev_detector.start_pilatus()
            
            # read timers asap
            count01 = exp.read_cntr(exp.dev_counter_01)
            count07 = exp.read_cntr(exp.dev_counter_07)
            petra_current = exp.dev_petra_globals.read_attribute('BeamCurrent').value
            pressure = exp.dev_hplc.read_attribute('Pressure').value

            temp_ctrl = exp.read_temp_ctrl() # channel C on LKS
            temp_sample = exp.read_temp_sample() # used for housing most of the time. Channel D
            #exp.sprint(f't after devs: {time.perf_counter()-t0}') 

            exp.sprint(f'Idx: {exp.fileidx} Counts: c01 {count01} and c07 {count07} (file: {fname}_{exp.fileidx:05d})')
            exp.sprint(f'Pressure: {pressure} PSI')
            exp.sprint(f'Temperature control: {temp_ctrl} C, sample/housing: {temp_sample} C')
            #exp.sprint(f't after write: {time.perf_counter()-t0}') 

            # build string for log_file
            s = ''
            for val in [exp.fileidx, count01, count07, fname, 
                        pressure, temp_ctrl, temp_sample, t0]:
                s += f'{val}\t'
            #exp.sprint(f't after string build: {time.perf_counter()-t0}') 
            exp.write_log(s) 
            #exp.sprint(f't after log written: {time.perf_counter()-t0}') 

            # write a few metadatas per exposure (above takes 10-20 ms, so not above 100 Hz)
            time.sleep(exp.exposure/4)
            exp.sprint(f'Data written. Time spent: {time.perf_counter()-t0}')
    
    except KeyboardInterrupt:
        exp.sprint('Keyboard intterupt! Wait for detector, do not double ctrl-C!')
        exp.dev_detector.stop_pilatus()
        exp.dev_detector.wait_for_detector()
        graceful_exit()

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

class experiment:
    # import functions for motors and counter
    #from motor import *

    def __init__(self):

        self.dev_detector =                   pilatus_detector('tango://hasep211eh:10000/p211/pilatus/300k_cdte')
        # use ramdisk or directly gpfs?
        self.dev_detector.useRamdisk = True

        self.dev_absorber =                   DeviceProxy('tango://hasep211eh:10000/p211/vme/diff_absorber')
        self.dev_stage_x =                DeviceProxy('tango://hasep211eh:10000/p211/motor/exp.25')
        self.dev_stage_y =                DeviceProxy('tango://hasep211eh:10000/p211/motor/exp.25')
        self.dev_stage_z =                DeviceProxy('tango://hasep211eh:10000/p211/motor/exp.25')
        self.dev_timer_1   =              DeviceProxy('tango://hasep211eh:10000/p211/mdgg8/exp.01')
        self.dev_counter_01      =              DeviceProxy('tango://hasep211eh:10000/p211/counter/exp.01')
        self.dev_counter_07      =              DeviceProxy('tango://hasep211eh:10000/p211/counter/exp.07')
        self.dev_petra_globals    =       DeviceProxy('tango://haspp07eh2:10000/petra/globals/keyword')
        self.dev_lakeshore      =              DeviceProxy('tango://hasep211eh:10000/p211/gpib/eh.03')
        self.dev_hplc                  = DeviceProxy('tango://haspp02oh1:10000/p02/hplcpump/exp.01')

        self.log_file = f'insitulogs/log_{time.strftime("%Y%m%d-%H%M%S")}'
        self.sprint(f'Logfile created: {self.log_file}')

        self.filename = 'nofilename'
        self.exposure = 1 # time exposure in seconds

    def sprint(self, txt: str):
        # function which prints to screen and then to file
        # input: string
        stamp = time.time()
        print(f'{time.strftime("%Y%m%d-%H%M%S")}\t{txt}')
        #return self.write_log(txt, stamp) # we don't want to print everything to log_file here, but handle that with writeLog
        return

    def write_log(self, txt: str, stamp=time.time()):
        # write to log_file in append mode
        with open(self.log_file, 'a') as f:
            a = f'{stamp}\t{txt}\n'
            f.write(a)
        return

    def rTimer(self, t):
        # progress bar
        # will wait for t seconds, and print 60*! while waiting.
        sys.stdout.write('!')
        dt = float(t)/60
        for i in range(60):
            time.sleep(dt)
            sys.stdout.write('=')
            sys.stdout.flush()
        print('!')
        return



    def read_temp_ctrl(self, channel="C"):
        """
         read temperature of lakeshore channel (default C
            which is the control-loop (in stream thermocouple))
        """
        temp = self.dev_lakeshore.command_inout(f"GPIBWriteRead",f'9,KRDG?{channel}')
        temp = temp.strip(';\r\n')
        temp =  np.float(temp)
        return temp

    def read_temp_sample(self):
        """
         read temperature of lakeshore channel D
            which is the sample/heater housing thermocouple
        """
        return self.read_temp_ctrl(channel='D')

    def pre_experiment(self):
        """
         prints a list of positions to the top of the file prior to the experiment
        """
        properties = {
        #TODO: why was this here? "energy":
        "gap": 'p211/attributemotor/gap',
        "sbm_updown": 'p211/motor/oh.01',
        "sbm_bender": 'p211/motor/oh.02',
        "sbm_yaw": 'p211/motor/oh.03',
        "sbm_roll": 'p211/motor/oh.04',
        "sbm_pitch": 'p211/motor/oh.05',
        "sbm_inout": 'p211/motor/oh.06',
        "pilatus_sample": 'p211/vme/pilatus2m_sample',
        "sliti_left": 'p211/motor/exp.07',
        "sliti_right": 'p211/motor/exp.08',
        "sliti_bottom": 'p211/motor/exp.09',
        "sliti_top": 'p211/motor/exp.10',
        "slitpb_left": 'p211/motor/exp.12',
        "slitpb_right": 'p211/motor/exp.13',
        "slitpb_bottom":'p211/motor/exp.14',
        "slitpb_top": 'p211/motor/exp.15',
        "zcs": 'p211/motor/exp.19',
        "xcs": 'p211/motor/exp.20',
        "xs": 'p211/motor/exp.25',
        "ys": 'p211/motor/exp.24',
        "zs": 'p211/motor/exp.26',      
        "omes": 'p211/motor/exp.21',
        "chis": 'p211/motor/exp.22',
        "phis": 'p211/motor/exp.23',
        "xdt": 'p211/motor/exp.53',
        "ydt": 'p211/motor/exp.54',
        "zdt": 'p211/motor/exp.55',
        "x2dt": 'p211/motor/exp.58',
        "z2dt": 'p211/motor/exp.59',
        "om2dt": 'p211/motor/exp.60',
        "xheater": 'p211/motor/exp.61',
        "zheater": 'p211/motor/exp.62',
        "zcam": 'p211/motor/exp.63',
        "xbox": 'p211/motor/exp.68',
        "ybox": 'p211/motor/exp.69',
        "zbox": 'p211/motor/exp.70',
        }
        
        # init
        self.write_log('HEADER START')
        self.write_log(f'Started at: {datetime.datetime.now()}')
        for prop, dev in properties.items():
            """
            | run through all the properties and get their position
            """
            position = self.get_position(dev)
            self.write_log(f'{prop}:\t{position}')
        self.write_log('END HEADER')
        return

    def get_position(self, dev, db='tango://hasep211eh:10000/'):
        """
         returns the Position of a dev (with DeviceProxy adress as input)
        """
        proxy = DeviceProxy(f'{db}{dev}')
        return proxy.read_attribute('Position').value


    def reset_cntrs(self):
        """
         reset all counters
        """
        # reset tng counters as list
        for c in [self.dev_counter_01, self.dev_counter_07]:#self.cntrsList:
            self.reset_cntr(c)


    def reset_cntr(self,dev):
        """
         resets counter to 0
        """
        dev.Reset()
        return

    def read_cntr(self,dev):
        """
         reads a counter value
         return as float
        """
        return dev.read_attribute('Counts').value

    def timer_read_sampletime(self, dev):
        """
         reads the current sampletime from tng counter
        """
        return dev.read_attribute('SampleTime').value

    def timer_set_sampletime(self,dev, sampletime):
        """
         sets a sampletime on tng counter
        """
        dev.write_attribute('SampleTime', float(sampletime))
        return

    def timer_start(self,dev):
        """
         starts a counter device
        """
        dev.Start()
        return
    def timer_stop(self, dev):
        """
         stops a counter device
        """
        dev.Stop()
        return


def graceful_exit():
    # stop things without destroying stuff, and restart scripts
    exp.sprint('You have interrupted by the keyboard. Stopping...')

    time.sleep(exp.exposure+2)


    liveview.start()
    exp.sprint('liveview restarted')


    sys.exit()


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
                        pressure, temp_ctrl, temp_sample]:
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

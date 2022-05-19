#!/usr/bin/env python3

import sys
import PyTango
from liveview import Liveview 
import time
import logging

dev_pilatus  = PyTango.DeviceProxy("tango://hasep211eh:10000/p211/pilatus/300k_cdte")
liveview = Liveview()

logger = logging.getLogger('detector')
logging.basicConfig(level=logging.INFO)

def setup_pilatus(filename='test', exp_time=1, n_frames=1):
    """
    | input
    | directory is defined below
    
    """
    logger.info(f'Setting up pilatus with {filename}, exposure time: {exp_time}, and no. of frames: {n_frames}')

    dev_pilatus.write_attribute("FileStartNum",1)

    # subtract 1 millisecond for readout to obtain totaltime	
    dev_pilatus.write_attribute("ExposureTime", exp_time-0.001)
    dev_pilatus.write_attribute("ExposurePeriod", exp_time+0.001)



    """
     write to {ramdiskdir}/{filename}/{filename}-xxxxx.tif
    """
    directory = f"/ramdisk/current/raw/pilatus2/{filename}"
    dev_pilatus.write_attribute("FileDir", directory)
    dev_pilatus.write_attribute("FilePrefix",filename)	


    dev_pilatus.write_attribute("NbFrames", n_frames)


def check_liveview():
    # checks if liveview is running and stop it
    # if that is the case. Returns without liveview running
    if liveview.running():
        # 
        logger.info('Liveview was on, stopping it!')
        liveview.stop()

        # wait a bit
        time.sleep(2)

    return
    

def start_pilatus():
    # send start to detector dserver
    logger.info('Starting pilatus')
    dev_pilatus.StartStandardAcq()


if __name__ == '__main__':
    """
     being run as script, so figure out
     parameters from sys.argv
    """

    if sys.argv[0] == 'python':
        # if being run with python prefix remove first sys.argv
        sys.argv.pop(0)
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        exp_time = float(sys.argv[2])

    if len(sys.argv) >= 2:
        # probably user wants to define how many images to acquire
        n_frames = int(sys.argv[3])

    check_liveview()
    setup_pilatus()
    start_pilatus()

    # restart liveview
    liveview.start()
    logger.info('Liveview restarted')

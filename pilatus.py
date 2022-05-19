#!/usr/bin/env python3

import sys
from PyTango import DeviceProxy, DevState
from liveview import Liveview 
import time
import logging


logger = logging.getLogger('detector')
logging.basicConfig(level=logging.INFO)


class pilatus_detector:
    liveview = Liveview()
    filename: str
    def __init__(self, addr):
        self.dev_pilatus = DeviceProxy(addr)
        self.filename = ''
    def setup_pilatus(self, filename='test', exp_time=1, n_frames=1):
        """
        | input
        | directory is defined below
        
        """
        # update filename
        self.filename = filename

        # cannot change settings while running, hence need another check
        self.check_liveview()
        logger.info(f'Setting up pilatus with {self.filename}, exposure time: {exp_time}, and no. of frames: {n_frames}')

        self.dev_pilatus.write_attribute("FileStartNum",1)

        # subtract 1 millisecond for readout to obtain totaltime	
        self.dev_pilatus.write_attribute("ExposureTime", exp_time-0.001)
        self.dev_pilatus.write_attribute("ExposurePeriod", exp_time+0.001)



        """
         write to {ramdiskdir}/{filename}/{filename}-xxxxx.tif
        """
        directory = f"/ramdisk/current/raw/pilatus2/{filename}"
        print(directory)
        self.dev_pilatus.write_attribute("FileDir", directory)
        self.dev_pilatus.write_attribute("FilePrefix",self.filename)	


        self.dev_pilatus.write_attribute("NbFrames", n_frames)


    def check_liveview(self):
        # checks if liveview is running and stop it
        # if that is the case. Returns without liveview running
        if self.liveview.running():
            # 
            logger.info('Liveview was on, stopping it!')
            self.liveview.stop()

            # wait a bit
            time.sleep(2)

        return
        

    def start_pilatus(self):
        # send start to detector dserver
        logger.info('Starting pilatus')
        self.dev_pilatus.StartStandardAcq()
        return self.filename

    def stop_pilatus(self):
        logger.info('Stopping pilatus')
        self.dev_pilatus.StopAcq()
        return

    def wait_for_detector(self):
        while self.dev_pilatus.state()==DevState.RUNNING:
            time.sleep(0.001)
        return

    def get_file_idx(self):
        return self.dev_pilatus.FileStartNum
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

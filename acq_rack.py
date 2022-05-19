#!/usr/bin/env python3
#

import sys
import time
import PyTango

from liveview import liveview

devpilatus  = PyTango.DeviceProxy("p211/pilatus/300k_cdte")
xbox        = PyTango.DeviceProxy('p211/motor/exp.68')

exp_filenames  = [str(f) for f in sys.argv[1].split(',')]
exp_positions = [float(f) for f in sys.argv[2].split(',')]
exp_time  = float(sys.argv[3])
exp_nbframes = int(sys.argv[4])



liveview = liveview()
# stop liveview if running
if liveview.running():
    liveview.stop()
    print('Liveview was running. Stopped it!')
    time.sleep(2)


# update PIL settings
devpilatus.ExposureTime = exp_time-0.002
devpilatus.ExposurePeriod = exp_time
devpilatus.FileStartNum = 1
devpilatus.NbFrames = exp_nbframes

# print some stuff
print('Filenames: {}'.format(exp_filenames))
print('Positions: {}'.format(exp_positions))

if len(exp_filenames) != len(exp_positions):
    print('Lengths are not the same! Exiting')
    sys.exit()

print('File exposure: {} s ({} Hz)'.format(exp_time, 1/exp_time))
print('File frames: {}'.format(exp_nbframes))
print('Starting acquisition in 5 seconds! Ctrl+C to cancel.')


time.sleep(5)

for pos in exp_positions:
    # move to pos
    time.sleep(2)

while True:
    try:
        for i, pos in enumerate(exp_positions):
            xbox.write_attribute('Position', float(pos))
            time.sleep(2)
            print('Moved there')
            exp_filedir = '/ramdisk/current/raw/pilatus2/{}'.format(exp_filenames[i])
            devpilatus.FileDir = exp_filedir
            devpilatus.FilePrefix = exp_filenames[i]

            time.sleep(1)
            print('acq now')
            devpilatus.StartStandardAcq()
            while devpilatus.state() == PyTango.DevState.RUNNING:
                time.sleep(5)
                print('Still running')
        print('DONE')
        liveview.start()
        sys.exit()

    except KeyboardInterrupt:
        print('Interrupted by keyboard. Stop acquistion')
        devpilatus.StopAcq()
        print('Starting liveview')
        liveview.start()
        sys.exit()

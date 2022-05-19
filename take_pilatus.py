import sys
import PyTango


devpilatus  = PyTango.DeviceProxy("tango://hasep211eh:10000/p211/pilatus/300k_cdte")

main_dirr = "/ramdisk/current/raw/pilatus2/"

directory  = sys.argv[0]
filename = sys.argv[1]
exptime = float(sys.argv[2])

devpilatus.write_attribute("FileStartNum",1)	
devpilatus.write_attribute("ExposureTime", exptime)
devpilatus.write_attribute("ExposurePeriod", exptime+0.001)
devpilatus.write_attribute("FileDir", main_dirr+directory)
devpilatus.write_attribute("FilePrefix",filename)	
devpilatus.write_attribute("NbFrames", 1.0)

devpilatus.StartStandardAcq()




from PyTango import DeviceProxy
import numpy as np

class lakeshore336:
    def __init__(self, addr='tango://hasep211eh:10000/p211/gpib/eh.03'):
        self.dev = DeviceProxy(addr)

    def read_temp(self, ch='C'):
        # read temperature from a channel
        # directly from GPIB
        response = self.dev.command_inout(f"GPIBWriteRead",f"9,KRDG?{ch}")
        response = response.strip(';\r\n')
        response =  np.float(response)
        return response

if __name__ == '__main__':
    # run as script, try to read a temperature reading and print it
    lks = lakeshore336()
    ch_c = lks.read_temp('C')
    ch_d = lks.read_temp('D')

    print(f'Channel C: {ch_c} K, Channel D: {ch_d}')

#!/usr/bin/python3
"""
 MartinR 24.09.2021

 class to handle liveview @ P21.1
"""

from pathlib import Path
import os

class Liveview:
    """
     class that holds liveview on hasep211eh

     ~/scan_active exists the live view is not running
     ~/scan_active !exists live view running
    """
    path = '/home/p211user/scan_active'
    def stop(self):
        # create scan_active as someone is about to do something..
        Path(self.path).touch()

    def start(self):
        # "scan is running" so remove scan_active
        os.remove(self.path)

    def running(self):
        # returns status as boolean
        return (not os.path.exists(self.path))

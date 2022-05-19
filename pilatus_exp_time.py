#!/usr/bin/env python
#
# rot_omes.py

import Spectra
import sys
import os
import string
import time, math

import numpy as np

import PyTango


devpilatus  = PyTango.DeviceProxy("p211/pilatus/300k_cdte")

exp_time  = float(sys.argv[0])

devpilatus.ExposureTime = exp_time
devpilatus.ExposurePeriod = exp_time + 0.03




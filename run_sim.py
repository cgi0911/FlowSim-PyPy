#!/usr/bin/python

"""
run_sim.py: Run simulation.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'




# Built-in modules
# Third-party modules
import netaddr as na
# User-defined modules
from sim.SimCore import *
from sim.SimEvent import *

if __name__ == '__main__':
    mySim = SimCore('config.py')
    #print mySim.__class__
    #print mySim.__doc__
    #print mySim.__init__.__doc__

    myEvent = FlowEnd(src_ip=na.IPAddress(1), dst_ip=na.IPAddress(2))
    print myEvent

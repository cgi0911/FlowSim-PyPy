#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
run_sim.py: Top-level Run simulation.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'




# Built-in modules
# Third-party modules
import netaddr as na
# User-defined modules
from sim.SimCore import *
from sim.SimEvent import *
from sim.SimFlow import *

if __name__ == '__main__':
    mySim = SimCore()
    #print mySim.__init__.__doc__
    mySim.display_topo_details()
    #mySim.main_course()

    #myEvent = EvFlowArrival(src_ip=na.IPAddress(1), dst_ip=na.IPAddress(2))
    #myEvent = EvFlowInstall(evtime=12345.0)
    #print myEvent

    #myFlow = SimFlow()
    #print myFlow

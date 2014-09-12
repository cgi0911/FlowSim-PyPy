#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
run_sim.py: Top-level Run simulation.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'




# Built-in modules
# Third-party modules
# User-defined modules
from sim.SimCore import *

if __name__ == '__main__':
    mySim = SimCore()
    mySim.main_course()
    # Run main course
    for fl in mySim.flows:
        print mySim.flows[fl]
    #for lk in mySim.topo.edges():
    #    print mySim.topo.edge[lk[0]][lk[1]]['item']
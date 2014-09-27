#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
run_sim.py: Top-level Run simulation.
"""
__author__      = ['Kuan-yin Chen', 'Kejiao Sui', 'Wei Lin']
__copyright__   = 'Copyright 2014, NYU-Poly'




# Built-in modules
import os
import sys

# ---- Copy config file to sim/SimConfig.py as specified ----
if (len(sys.argv) > 1):
    os.system("cp %s ./sim/SimConfig.py" %(sys.argv[1]))
    print "Reading config from: %s" %(sys.argv[1])
else:
    os.system("cp ./cfgs/default.txt ./sim/SimConfig.py")
    print "Reading config from: ./cfgs/default.txt"

# Third-party modules
# User-defined modules
from sim.SimCore import *
import sim.SimConfig as cfg

if __name__ == '__main__':
    mySim = SimCore()
    if (cfg.DO_PROFILING == True):
        fn_profile = os.path.join(cfg.LOG_DIR, 'profile_pstats.pstats')
        import cProfile
        print "Code performance profiling output to", fn_profile
        cProfile.run('mySim.main_course()', fn_profile)
    else:
        mySim.main_course()
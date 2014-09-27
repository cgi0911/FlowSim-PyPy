#!/usr/bin/python

"""config.py: Read variables from config file (which is actually a proper python script defining
variables), or default to config.txt in the working dir.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'


import sys
import imp
import os

# Read config file name
if (len(sys.argv) > 1):
    fn_config = sys.argv[1]
else:
    fn_config = './cfgs/default.txt'

# Create precompiled module file name. If the file exists, remove it.
# The actual precompiled file name is fn_precompile + 'c'
fn_precompile = os.path.join('./temp', os.path.split(fn_config)[-1])
if os.path.exists(fn_precompile + 'c'):
    print "Removing temp precompiled module file: %s" %(fn_precompile + 'c')
    os.remove(fn_precompile + 'c')

print "Reading config from: %s" %(fn_config)
myFile = open(fn_config)
global cfg
cfg = imp.load_source('cfg', fn_precompile, myFile)    # Load config file into a module named cfg
print "Config module loaded as:", cfg
myFile.close()


#!/usr/bin/python

"""config.py: Read variables from config file (which is actually a proper python script defining
variables), or default to config.txt in the working dir.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'


import sys
import imp

if (len(sys.argv) > 1):
    fn_config = sys.argv[1]
else:
    fn_config = './config.txt'

myFile = open(fn_config)
global cfg
cfg = imp.load_source('cfg', '', myFile)    # Load config file into a module named cfg
myFile.close()
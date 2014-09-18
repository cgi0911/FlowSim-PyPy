#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
multi_run.py: Distributed simulation tasks onto worker threads.
"""
__author__      = ['Kuan-yin Chen', 'Kejiao Sui', 'Wei Lin']
__copyright__   = 'Copyright 2014, NYU-Poly'


import os
import multiprocessing as mp

N_WORKERS = 3
TASKS = ['./cfgs/ecmp.txt', './cfgs/spf.txt', './cfgs/fe2.txt',\
         './cfgs/fe3.txt', './cfgs/fe4.txt', './cfgs/fe5.txt',\
         './cfgs/fe6.txt', './cfgs/fe7.txt', './cfgs/fe8.txt',\
         './cfgs/fe9.txt', './cfgs/fe10.txt']

def do_work(fn_config):
    cmd = "nohup ./run_sim.py " + fn_config + ' > ' + \
          fn_config.replace('.txt', '.nohup').replace('cfgs', 'nohups')
    print cmd
    os.system(cmd)


if __name__ == '__main__':
    myPool = mp.Pool(N_WORKERS)
    myPool.map(do_work, TASKS)


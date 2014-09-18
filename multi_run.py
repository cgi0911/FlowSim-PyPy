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
NOHUP_PATH = './nohups'

def do_work(task_queue):
    while True:
        fn_config = task_queue.get()
        if (fn_config == 'None'):
            break

        fn_nohup = os.path.join(NOHUP_PATH, os.path.split(fn_config)[-1].replace('.txt', '.nohup'))
        cmd = "nohup ./run_sim.py %s >%s " %(fn_config, fn_nohup)
        #cmd = "./run_sim.py %s" %(fn_config)
        print cmd
        os.system(cmd)

if __name__ == '__main__':
    task_queue = mp.Queue()
    for t in TASKS:
        task_queue.put(t)
    for i in range(N_WORKERS):
        task_queue.put('None')

    list_proc = []
    for i in range(N_WORKERS):
        list_proc.append(mp.Process(target=do_work, args=(task_queue,)))

    for p in list_proc:
        p.start()

    for p in list_proc:
        p.join()

    os.system("rm ./temp/*")

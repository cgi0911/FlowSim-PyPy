#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimFlowGen.py: The SDN controller class, capable of doing k-path routing.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

# Built-in modules
from heapq import heappush, heappop
import random as rd
# Third-party modules
import numpy as np
# User-defined modules
from config import *
from SimEvent import *


class SimFlowGen:
    """Flow Generator.

    Attributes:
        hosts (dict): Hosts database. Key: Host IP, Value: attached edge switch.
                      Directly copy-assigned during SimFlowGen.__init__()

    """
    def __init__(self, sim_core):
        self.hosts = sim_core.hosts


    def pick_dst(self, src):
        if (FLOW_DST_MODEL == 'uniform'):
            dst = self.pick_dst_uniform(src)
        else:
            # Default to 'uniform'
            dst = self.pick_dst_uniform(src)
        return dst


    def pick_dst_uniform(self, src):
        dst = ''
        while True:
            dst = rd.choice(self.hosts.keys())
            if (not self.hosts[dst] == self.hosts[src]):
                break
        return dst


    def get_flow_size(self):
        """Generate flow size according to specified random model.

        Args:

        Return:
            float64: Flow size. Although real-world flow sizes (in bytes) are integers,
                     We cast them to float64 for the sake of compatibility with functions using it.

        """
        ret = 0.0
        if (FLOW_SIZE_MODEL == 'uniform'):
            ret = self.get_flow_size_uniform(FLOW_SIZE_LOW, FLOW_SIZE_HIGH)
        else:
            # Default to 'uniform'
            ret = self.get_flow_size_uniform(FLOW_SIZE_LOW, FLOW_SIZE_HIGH)
        return ret


    def get_flow_size_uniform(self, low=FLOW_SIZE_LOW, high=FLOW_SIZE_HIGH):
        """Generate flow size according to uniform random model

        Args:
            low (float64): Lower bound
            high (float64): Upper bound

        Return:
            float64: Uniform random flow size, round to integral digit.

        """
        ret = np.random.uniform(low, high)
        ret = round(ret, 0)     # Round to integral digit
        return ret


    def get_flow_rate(self):
        """Generate flow rate according to specified random model.

        Args:

        Return:
            float64: Flow rate (bytes per second).

        """
        ret = 0.0
        if (FLOW_RATE_MODEL == 'uniform'):
            ret = self.get_flow_rate_uniform(FLOW_RATE_LOW, FLOW_RATE_HIGH)
        else:
            # Default to 'uniform'
            ret = get_flow_rate_uniform(FLOW_RATE_LOW, FLOW_RATE_HIGH)
        return ret


    def get_flow_rate_uniform(self, low=FLOW_SIZE_LOW, high=FLOW_SIZE_HIGH):
        """Generate flow rate according to uniform random model

        Args:
            low (float64): Lower bound
            high (float64): Upper bound

        Return:
            float64: Uniform random flow rate.

        """
        ret = np.random.uniform(low, high)
        return ret


    def gen_new_flow_with_src(self, src):
        dst = self.pick_dst(src)            # Pick a destination
        fsize = self.get_flow_size()    # Generate flow size
        frate = self.get_flow_rate()

        ret = EvFlowArrival(src_ip=src, dst_ip=dst, flow_size=fsize, flow_rate=frate)
        return ret


    def gen_init_flows(self, ev_queue):
        """When simulation starts, generate a set of initial flows.
        We generate exactly one initial flow for each source host.
        The initial flows, as EvFlowArrival events, will be enqueued to ev_queue

        Args:
            ev_queue (list of instances inherited from SimEvent): Event queue
        """
        if (FLOW_INTARR_MODEL == 'saturate'):
            for hst in self.hosts:
                ev_time = np.random.uniform(0.0, LATEST_INIT_FLOW_TIME)
                event = self.gen_new_flow_with_src(hst)
                heappush(ev_queue, (ev_time, event))
        else:
            pass



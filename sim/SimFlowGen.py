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
import netaddr as na
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


    def pick_dst(self, src_ip, sim_core):
        """Given src_ip, pick a dst_ip using specified random model.

        Args:
            src_ip (netaddr.IPAddress)
            sim_core (instance of SimCore)

        Extra Notes:
            sim_core is passed into this function because we need to check if the
            picked (src_ip, dst_ip) does not overlap with any flow in sim_core.

        """
        while True:
            if (cfg.FLOW_DST_MODEL == 'uniform'):
                dst_ip = self.pick_dst_uniform(src_ip)
            else:
                # Default to 'uniform'
                dst_ip = self.pick_dst_uniform(src_ip)
            if (not (src_ip, dst_ip) in sim_core.flows):
                break

        return dst_ip


    def pick_dst_uniform(self, src_ip):
        """Given src_ip, pick a dst_ip using uniform random model.

        Args:
            src_ip (netaddr.IPAddress)

        Extra Notes:
            src_ip and dst_ip will never be under the same edge node (switch).

        """
        dst_ip = 0
        while True:
            dst_ip = rd.choice(self.hosts.keys())
            if (not self.hosts[dst_ip] == self.hosts[src_ip]):
                break
        return dst_ip


    def get_flow_size(self):
        """Generate flow size according to specified random model.

        Args:

        Return:
            float64: Flow size. Although real-world flow sizes (in bytes) are integers,
                     We cast them to float64 for the sake of compatibility with functions using it.

        """
        ret = 0.0
        if (cfg.FLOW_SIZE_MODEL == 'uniform'):
            ret = self.get_flow_size_uniform(cfg.FLOW_SIZE_LOW, cfg.FLOW_SIZE_HIGH)
        else:
            # Default to 'uniform'
            ret = self.get_flow_size_uniform(cfg.FLOW_SIZE_LOW, cfg.FLOW_SIZE_HIGH)
        return ret


    def get_flow_size_uniform(self, low=cfg.FLOW_SIZE_LOW, high=cfg.FLOW_SIZE_HIGH):
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
        if (cfg.FLOW_RATE_MODEL == 'uniform'):
            ret = self.get_flow_rate_uniform(cfg.FLOW_RATE_LOW, cfg.FLOW_RATE_HIGH)
        else:
            # Default to 'uniform'
            ret = get_flow_rate_uniform(cfg.FLOW_RATE_LOW, cfg.FLOW_RATE_HIGH)
        return ret


    def get_flow_rate_uniform(self, low=cfg.FLOW_SIZE_LOW, high=cfg.FLOW_SIZE_HIGH):
        """Generate flow rate according to uniform random model

        Args:
            low (float64): Lower bound
            high (float64): Upper bound

        Return:
            float64: Uniform random flow rate.

        """
        ret = np.random.uniform(low, high)
        return ret


    def gen_new_flow_with_src(self, ev_time, src, sim_core):
        dst = self.pick_dst(src, sim_core)            # Pick a destination
        fsize = self.get_flow_size()    # Generate flow size
        frate = self.get_flow_rate()

        ret = EvFlowArrival(ev_time=ev_time, src_ip=src, dst_ip=dst, flow_size=fsize, flow_rate=frate)
        return ret


    def gen_init_flows(self, ev_queue, sim_core):
        """When simulation starts, generate a set of initial flows.
        We generate exactly one initial flow for each source host.
        The initial flows, as EvFlowArrival events, will be enqueued to ev_queue

        Args:
            ev_queue (list of instances inherited from SimEvent): Event queue
            sim_core (instance of SimCore): Simulation core
        """
        if (cfg.FLOW_INTARR_MODEL == 'saturate'):
            for hst in self.hosts:
                ev_time = np.random.uniform(0.0, cfg.LATEST_INIT_FLOW_TIME)
                event = self.gen_new_flow_with_src(ev_time, hst, sim_core)
                heappush(ev_queue, (ev_time, event))
        else:
            pass



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
import netaddr as na
# User-defined modules
import SimConfig as cfg
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
            if (cfg.FLOWGEN_SRCDST_MODEL == 'uniform'):
                dst_ip = self.pick_dst_uniform(src_ip)
            else:
                dst_ip = self.pick_dst_uniform(src_ip)  # Default to 'uniform'
            if (not (src_ip, dst_ip) in sim_core.flows):
                break   # Make sure src and dst host are not an existing flow

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
                break   # Make sure src and dst host are not within the same LAN
        return dst_ip


    def gen_flow_size_rate_bimodal(self):
        """Generate flow size according to bimodal random model

        Args:
            None. All parameters are from cfg.

        Return:
            float64: Bimodal flow size, round to integral digit.
            float64: Bimodal flow rate.

        """
        fsize = frate = 0.0
        roll_dice = rd.uniform(0, 1)     # Decide large or small flow

        if(roll_dice < cfg.FLOWGEN_SIZERATE_BIMODAL.PROB_LARGE_FLOW):
            fsize = rd.uniform(cfg.FLOWGEN_SIZERATE_BIMODAL.FLOW_SIZE_LARGE_LO,   \
                               cfg.FLOWGEN_SIZERATE_BIMODAL.FLOW_SIZE_LARGE_HI, )
            frate = rd.uniform(cfg.FLOWGEN_SIZERATE_BIMODAL.FLOW_RATE_LARGE_LO,   \
                               cfg.FLOWGEN_SIZERATE_BIMODAL.FLOW_RATE_LARGE_HI, )
        else:
            fsize = rd.uniform(cfg.FLOWGEN_SIZERATE_BIMODAL.FLOW_SIZE_SMALL_LO,   \
                               cfg.FLOWGEN_SIZERATE_BIMODAL.FLOW_SIZE_SMALL_HI, )
            frate = rd.uniform(cfg.FLOWGEN_SIZERATE_BIMODAL.FLOW_RATE_SMALL_LO,   \
                               cfg.FLOWGEN_SIZERATE_BIMODAL.FLOW_RATE_SMALL_HI, )
        fsize = round(fsize, 0)
        return fsize, frate


    def gen_flow_size_rate_uniform(self):
        """Generate flow size according to uniform random model

        Args:
            None. All parameters are from cfg.

        Return:
            float64: Uniform random flow size, round to integral digit.

        """
        fsize = round(rd.uniform(cfg.FLOWGEN_SIZERATE_UNIFORM.FLOW_SIZE_LO, \
                                 cfg.FLOWGEN_SIZERATE_UNIFORM.FLOW_SIZE_HI), 0)
        frate = rd.uniform(cfg.FLOWGEN_SIZERATE_UNIFORM.FLOW_RATE_LO, \
                           cfg.FLOWGEN_SIZERATE_UNIFORM.FLOW_RATE_HI)
        return fsize, frate


    def gen_flow_size_rate(self):
        """Generate flow size according to specified random model.

        Args:

        Return:
            float64: Flow size. Although real-world flow sizes (in bytes) are integers,
                     We cast them to float64 for the sake of compatibility with functions using it.

        """
        fsize = frate = 0.0

        if (cfg.FLOWGEN_SIZERATE_MODEL == 'uniform'):
            fsize, frate = self.gen_flow_size_rate_uniform()
        elif (cfg.FLOWGEN_SIZERATE_MODEL == 'bimodal'):
            fsize, frate = self.gen_flow_size_rate_bimodal()
        else:
            fsize, frate = self.gen_flow_size_rate_uniform()  # Default to 'uniform'
        return fsize, frate


    def gen_new_flow_with_src(self, ev_time, src_ip, sim_core):
        """
        """
        # Fixed src host. Pick a dst host.
        dst = self.pick_dst(src_ip, sim_core)
        # Generate flow size and rate.
        fsize, frate = self.gen_flow_size_rate()                # Generate flow size
        # Generate an EvFlowArrival event and return it.
        event = EvFlowArrival(ev_time=ev_time, src_ip=src_ip, dst_ip=dst, \
                              flow_size=fsize, flow_rate=frate)
        return event


    def gen_new_flow_arr_saturate(self, ev_time, src_ip, sim_core):
        """
        """
        new_ev_time = ev_time + cfg.FLOWGEN_ARR_SATURATE.NEXT_FLOW_DELAY
        new_EvFlowArrival = self.gen_new_flow_with_src(new_ev_time, src_ip, sim_core)
        return new_ev_time, new_EvFlowArrival


    def gen_new_flow_arr_const(self, ev_time, sim_core):
        """
        """
        hi = (1+cfg.FLOWGEN_ARR_CONST.CUTOFF) * 1.0/cfg.FLOWGEN_ARR_CONST.FLOW_ARR_RATE
        lo = (1-cfg.FLOWGEN_ARR_CONST.CUTOFF) * 1.0/cfg.FLOWGEN_ARR_CONST.FLOW_ARR_RATE
        new_intarr_time = rd.uniform(lo, hi)
        new_ev_time = ev_time + new_intarr_time

        if (cfg.FLOWGEN_SRCDST_MODEL == 'uniform'):
            new_src_ip  = rd.choice(self.hosts.keys())
        else:
            new_src_ip  = rd.choice(self.hosts.keys()) # Default to 'uniform'

        new_EvFlowArrival = self.gen_new_flow_with_src(new_ev_time, new_src_ip, sim_core)
        return new_ev_time, new_EvFlowArrival


    def gen_new_flow_arr_exp(self, ev_time, sim_core):
        """
        """
        new_intarr_time = rd.expovariate(lambd=cfg.FLOWGEN_ARR_EXP.FLOW_ARR_RATE)
        new_ev_time = ev_time + new_intarr_time

        if (cfg.FLOWGEN_SRCDST_MODEL == 'uniform'):
            new_src_ip  = rd.choice(self.hosts.keys())
        else:
            new_src_ip  = rd.choice(self.hosts.keys()) # Default to 'uniform'

        new_EvFlowArrival = self.gen_new_flow_with_src(new_ev_time, new_src_ip, sim_core)
        return new_ev_time, new_EvFlowArrival


    def gen_init_flows(self, ev_queue, sim_core):
        """When simulation starts, generate a set of initial flows.
        We generate exactly one initial flow for each source host.
        The initial flows, as EvFlowArrival events, will be enqueued to ev_queue

        Args:
            ev_queue (list of instances inherited from SimEvent): Event queue
            sim_core (instance of SimCore): Simulation core
        """
        if (cfg.FLOWGEN_ARR_MODEL == 'saturate'):
            # For each host, generate one flow with the host as its src host.
            # New flows will be generated upon EvFlowEnd
            for src_host in self.hosts:
                ev_time = rd.uniform(0.0, cfg.FLOWGEN_ARR_SATURATE.INIT_FLOWS_SPREAD)
                event   = self.gen_new_flow_with_src(ev_time, src_host, sim_core)
                heappush(ev_queue, (ev_time, event))
        elif (cfg.FLOWGEN_ARR_MODEL == 'const' or cfg.FLOWGEN_ARR_MODEL == 'exp'):
            # Generate a single new flow. New flows will be generated upon EvFlowArrival
            if (cfg.FLOWGEN_SRCDST_MODEL == 'uniform'):
                src_host    = rd.choice(self.hosts.keys())
            else:
                src_host    = rd.choice(self.hosts.keys())  # Default to 'uniform'
            ev_time     = 0.0
            event       = self.gen_new_flow_with_src(ev_time, src_host, sim_core)
            heappush(ev_queue, (ev_time, event))

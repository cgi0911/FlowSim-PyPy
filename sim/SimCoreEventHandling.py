#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimCore.py: Class SimCoreEventHandling, containing event handling codes for SimCore.
Inherited by SimCore.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

# Built-in modules
import os
import csv
from heapq import heappush, heappop
from math import ceil, log
from time import time
# Third-party modules
import networkx as nx
import netaddr as na
import pandas as pd
import numpy as np
# User-defined modules
from SimConfig import *
from SimCtrl import *
from SimFlowGen import *
from SimFlow import *
from SimSwitch import *
from SimLink import *
from SimEvent import *


class SimCoreEventHandling:
    """Event handling-related codes for SimCore class.
    """

    def handle_EvFlowArrival(self, ev_time, event):
        """Handle an EvFlowArrival event.
        1. Enqueue an EvPacketIn event after SW_CTRL_DELAY
        2. Add a SimFlow instance to self.flows, and mark the flow's status as 'requesting'

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.

        """
        self.n_EvFlowArrival += 1      # Increment the counter

        # Create SimFlow instance
        flow_obj    = SimFlow(  src_ip=event.src_ip, dst_ip=event.dst_ip, \
                                src_node=self.hosts[event.src_ip], \
                                dst_node=self.hosts[event.dst_ip], \
                                flow_size=event.flow_size, flow_rate=event.flow_rate, \
                                bytes_left=event.flow_size, \
                                arrive_time=ev_time, update_time=ev_time, \
                                status='requesting', resend=0)
        self.flows[(event.src_ip, event.dst_ip)] = flow_obj

        # EvPacketIn event
        new_ev_time = ev_time + cfg.SW_CTRL_DELAY
        new_EvPacketIn      = EvPacketIn(   ev_time=new_ev_time, \
                                            src_ip=event.src_ip, dst_ip=event.dst_ip, \
                                            src_node=self.hosts[event.src_ip], \
                                            dst_node=self.hosts[event.dst_ip]       )
        heappush(self.ev_queue, (new_ev_time, new_EvPacketIn))

        # If arrival model is "const" or "exp", generate a new flow and schedule an EvFlowArrival.

        if cfg.FLOWGEN_ARR_MODEL == 'const':
            new_ev_time, new_EvFlowArrival = self.flowgen.gen_new_flow_arr_const(    \
                                             ev_time, self)
            heappush(self.ev_queue, (new_ev_time, new_EvFlowArrival))
        elif cfg.FLOWGEN_ARR_MODEL == 'exp':
            new_ev_time, new_EvFlowArrival = self.flowgen.gen_new_flow_arr_exp(    \
                                             ev_time, self)
            heappush(self.ev_queue, (new_ev_time, new_EvFlowArrival))


    def handle_EvPacketIn(self, ev_time, event):
        """Handle an EvPacketIn event.
        1. The controller finds a path for the specified flow.
        2. If a feasible path is found, schedule a EvFlowInstall accordingly,
           after CTRL_SW_DELAY.
           If not, reject the PacketIn, and re-schedule a EvFlowArrival after
           REJECT_TIMEOUT.

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.

        """
        self.n_EvPacketIn += 1      # Increment the counter

        # The controller finds a path for the requesting flow
        path = self.ctrl.find_path(event.src_ip, event.dst_ip)

        if (path == []):
            if (cfg.SHOW_REJECTS > 0):
                print 'Flow (%s, %s) is rejected. No available path.' %(event.src_ip, event.dst_ip)
                print
            # Re-send this EvPacketIn after REJECT_TIMEOUT (don't forget SW_CTRL_DELAY!)
            new_ev_time = ev_time + cfg.REJECT_TIMEOUT + cfg.SW_CTRL_DELAY
            new_event   = EvPacketIn(   ev_time=new_ev_time, \
                                        src_ip=event.src_ip, dst_ip=event.dst_ip,
                                        src_node=event.src_node, dst_node=event.dst_node)
            heappush(self.ev_queue, (new_ev_time, new_event))
            # Increment flow's resend counter
            self.flows[(event.src_ip, event.dst_ip)].resend += 1
            # Increment loggin counter
            self.n_Reject += 1
        else:
            new_ev_time = ev_time + cfg.CTRL_SW_DELAY
            new_event   = EvFlowInstall(ev_time=new_ev_time, \
                                        src_ip=event.src_ip, dst_ip=event.dst_ip, \
                                        src_node=event.src_node, dst_node=event.dst_node, \
                                        path=path)
            heappush(self.ev_queue, (new_ev_time, new_event))


    def handle_EvFlowInstall(self, ev_time, event):
        """Handle an EvFlowInstall event.
        1. Double check if the chosen path is still feasible (no table overflow).
        2. If yes, SimSwitch instances on path will install flow entries.
           The controller will also register the entry. Mark the flow's status as 'active'.
        3. If not, reject the EvFlowInstall, and re-schedule a EvFlowArrival after
           REJECT_TIMEOUT (don't forget the SW_CTRL_DELAY).
        3. Update the SimCore's flow statistics.

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.

        """
        is_feasible = self.ctrl.is_feasible(event.path)

        if (is_feasible == True):
            # Register entries at SimSwitch & SimLink instances
            list_links                  = self.get_links_on_path(event.path)
            self.install_entries_to_path(event.path, list_links, event.src_ip, event.dst_ip)
            # Register flow entries at controller
            self.ctrl.install_entry(event.path, event.src_ip, event.dst_ip)
            # Update flow instance
            fl = (event.src_ip, event.dst_ip)
            flowobj             = self.flows[fl]
            flowobj.status      = 'active'
            flowobj.path        = event.path
            flowobj.links       = list_links
            for lk in list_links:
                self.linkobjs[lk].n_active_flows += 1
            self.n_active_flows += 1
            flowobj.install_time = event.ev_time
            # Recalculate flow rates
            self.sorted_flows_insert(flowobj.flow_rate, flowobj, fl)
            self.calc_flow_rates(ev_time)

        else:
            fl = (event.src_ip, event.dst_ip)
            if (cfg.SHOW_REJECTS > 0):
                print 'Flow %s is rejected. Overflow detected during installation' %(fl)
            # Re-schedule a new EvPacketIn event after REJECT_TIMEOUT
            new_ev_time = ev_time + cfg.REJECT_TIMEOUT + cfg.SW_CTRL_DELAY
            new_event = EvPacketIn( ev_time=new_ev_time, \
                                    src_ip=event.src_ip, dst_ip=event.dst_ip, \
                                    src_node=event.src_node, dst_node=event.dst_node)
            heappush(self.ev_queue, (new_ev_time, new_event))
            # Increment flow's resend counter
            self.flows[fl].resend += 1
            # Increment loggin counter
            self.n_Reject += 1


    def handle_EvFlowEnd(self, ev_time, event):
        """Handle an EvFlowEnd event.
        1. Schedule an EvIdleTimeout event, after IDLE_TIMEOUT.
        2. Mark the flow's status as 'idle'.
        3. Update the SimCore's flow statistics.
        4. Log flow stats if required.
        5. Generate new flows if required.

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.

        """
        self.n_EvFlowEnd += 1      # Increment the counter

        # Update flowobj to a finished state
        fl = (event.src_ip, event.dst_ip)
        flowobj             = self.flows[fl]
        flowobj.status      = 'finished'
        flowobj.end_time    = ev_time
        flowobj.update_time = ev_time
        flowobj.bytes_left  = 0.0
        flowobj.bytes_sent  = flowobj.flow_size
        flowobj.duration    = flowobj.end_time - flowobj.arrive_time
        flowobj.avg_rate    = flowobj.flow_size / (flowobj.end_time - flowobj.arrive_time)
        #for lk in self.get_links_on_path(flowobj.path):
        for lk in flowobj.links:
                self.linkobjs[lk].n_active_flows -= 1
        self.n_active_flows -= 1

        # Calculate the flow rates
        self.sorted_flows_remove(fl)
        self.calc_flow_rates(ev_time)

        # Schedule an EvIdleTimeout event
        new_ev_time         = ev_time + cfg.IDLE_TIMEOUT
        new_EvIdleTimeout   = EvIdleTimeout(ev_time=new_ev_time, \
                                            src_ip=event.src_ip, dst_ip=event.dst_ip )
        heappush(self.ev_queue, (new_ev_time, new_EvIdleTimeout))
        # If arrival model is "saturate", generate a new flow and schedule an EvFlowArrival.
        if cfg.FLOWGEN_ARR_MODEL == 'saturate':
            new_ev_time, new_EvFlowArrival = self.flowgen.gen_new_flow_arr_saturate(    \
                                             ev_time, event.src_ip, self)
            heappush(self.ev_queue, (new_ev_time, new_EvFlowArrival))


    def handle_EvIdleTimeout(self, ev_time, event):
        """Handle an EvIdleTimeout event.
        1. Remove the flow from self.flows.
        2. Remove the flow entries from path switches.
        3. Remove the flow entries from links along the path.

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.

        """
        self.n_EvIdleTimeout += 1      # Increment the counter

        fl      = (event.src_ip, event.dst_ip)
        flowobj = self.flows[fl]
        path    = flowobj.path
        list_links = flowobj.links
        flowobj.remove_time = ev_time
        flowobj.update_time = ev_time
        flowobj.status      = 'removed'

        # Log flow stats
        if (cfg.LOG_FLOW_STATS > 0):
            self.flow_stats_recs.append(self.log_flow_stats(flowobj))

        for nd in path:
            self.nodeobjs[nd].remove_flow_entry(event.src_ip, event.dst_ip)
            del self.ctrl.get_node_attr(nd, 'cnt_table')[fl]

        #for lk in self.get_links_on_path(path):
        for lk in list_links:
            self.linkobjs[lk].remove_flow_entry(event.src_ip, event.dst_ip)

        del self.flows[fl]


    def handle_EvHardTimeout(self, ev_time, event):
        """Handle an EvHardTimeout event.
        1.
        """

    def handle_EvPullStats(self, ev_time, event):
        """Handle an EvPullStats event.
        1. The central controller pulls stats.

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.


        """
        pass


    def handle_EvReroute(self, ev_time, event):
        """Handle an EvReroute event.
        1. The central controller does reroute.
        2. Update the SimCore's flow statistics.

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.


        """
        pass


    def handle_EvLogLinkUtil(self, ev_time, event):
        """
        """
        if (cfg.LOG_LINK_UTIL > 0):
            records = self.log_link_util(ev_time)
            self.link_util_recs.append(records[0])
            self.link_flows_recs.append(records[1])
            new_ev_time = ev_time + cfg.PERIOD_LOGGING
            heappush(self.ev_queue, (new_ev_time, EvLogLinkUtil(ev_time=new_ev_time)))


    def handle_EvLogTableUtil(self, ev_time, event):
        """
        """
        if (cfg.LOG_TABLE_UTIL > 0):
            self.table_util_recs.append(self.log_table_util(ev_time))
            new_ev_time = ev_time + cfg.PERIOD_LOGGING
            heappush(self.ev_queue, (new_ev_time, EvLogTableUtil(ev_time=new_ev_time)))

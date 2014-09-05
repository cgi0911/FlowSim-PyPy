#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimCore.py: Class SimCore, the core class of FlowSim simulator.
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
from config import *
from SimCtrl import *
from SimFlowGen import *
from SimFlow import *
from SimSwitch import *
from SimLink import *
from SimEvent import *


class SimCore:
    """Core class of FlowSim simulator.

    Attributes:
        sim_time (float64): Total simulation time
        timer (float64): Simulation timer, which keeps current time progress
        topo (networkx.Graph): An undirected graph to keep network topology
        ev_queue (list of 2-tuples): Event queue. Each element is a 2-tuple of (ev_time, event obj)
        nodes_df (pandas.DataFrame): A dataframe that contains switching nodes' names and params.
        links_df (pandas.DataFrame): A dataframe that contains links' names and params.
        hosts (dict of netaddr.IpAddress): Key is host IP, value is its edge switch
        flows (dict of 2-tuples): Key is 2-tuple of flow src/dst, value is its associated SimFlow
        link_util_recs (list of np.array): List of link utilization records.
        table_util_recs (list of np.array): List of table utilization records.
        flow_stats_recs (list of np.array): List of flow stats records.

    Extra Notes:
        topo.node[node]['item'] (SimSwitch): Edge switch instances in the topology.
        topo[node1][node2]['item'] (SimLink): Link instances in the topology.

    """

    def __init__(self):
        """Constructor of SimCore class.

        Args:

        Extra Notes:
            If not otherwise specified, all initial values come from config.py

        """
        # ---- Simulator timer and counters ----
        self.sim_time = SIM_TIME
        self.timer = 0.0
        self.ev_queue = []
        np.random.seed(int(time()*100))

        # ---- Parse CSV and set up topology graph's nodes and edges accordingly ----
        self.topo = nx.Graph()
        fn_nodes = os.path.join(DIR_TOPO, 'nodes.csv')
        fn_links = os.path.join(DIR_TOPO, 'links.csv')
        self.nodes_df = pd.read_csv(fn_nodes, index_col=False)
        self.links_df = pd.read_csv(fn_links, index_col=False)
        self.df_to_topo(self.nodes_df, self.links_df)   # Translate pd.DataFrame into networkx.Graph

        # ---- Create hosts, assign edge switches * IPs ----
        self.hosts = {}
        self.create_hosts()

        # ---- Simulator components ----
        # SimController: Currently assume one omniscient controller
        # SimFlowGen: One instance
        # SimSwitch instances are instantiated in df_to_topo
        # SimLink instances are instantitated in df_to_topo
        self.ctrl = SimCtrl(self)
        self.flowgen = SimFlowGen(self)

        # ---- Keeping flow records ----
        self.flows = {}     # Empty dict at first.

        # ---- Bookkeeping, framing and logging ----
        self.link_util_recs = []
        self.table_util_recs = []
        self.flow_stats_recs = []


    def display_topo(self):
        """Display topology (nodes and links only)
        """
        print 'Nodes:', self.topo.nodes()
        print
        print 'Links:', self.topo.edges()


    def display_topo_details(self):
        """Display topology - nodes and links along with parameters
        """
        for node in self.topo.nodes_iter():
            print self.topo.node[node]['item']

        for link in self.topo.edges_iter():
            print self.topo[link[0]][link[1]]['item']


    def df_to_topo(self, nodes_df, links_df):
        """Read the nodes and link dataframe row by row and translate into networkx.Graph.
        Referred by SimCore.__init__().
        """
        for myRow in nodes_df.iterrows():
            rowdict = dict(myRow[1])    # myRow is a 2-tuple: (index, dict of params)
            name = rowdict['name']
            self.topo.add_node(name, item=SimSwitch(**rowdict))

        for myRow in links_df.iterrows():
            rowdict = dict(myRow[1])
            node1, node2 = rowdict['node1'], rowdict['node2']
            self.topo.add_edge(node1, node2, item=SimLink(**rowdict))


    def create_hosts(self):
        """Create hosts, bind hosts to edge switches, and assign IPs.
        """
        base_ip = na.IPAddress('10.0.0.1')
        for nd in self.topo.nodes():
            n_hosts = self.topo.node[nd]['item'].n_hosts
            self.topo.node[nd]['item'].base_ip = base_ip
            self.topo.node[nd]['item'].end_ip = base_ip + n_hosts - 1
            for i in range(n_hosts):
                myIP = base_ip + i
                self.hosts[myIP] = nd
            base_ip = base_ip + 2 ** int(ceil(log(n_hosts, 2)))  # Shift base_ip by an entire IP segment


    def main_course(self):
        """The main course of simulation execution.

        Args:

        Returns:

        """
        # Step 1: Generate initial set of flows and queue them as FlowArrival events
        self.flowgen.gen_init_flows(self.ev_queue)        

        # Step 2: Initialize logging
        # self.init_logging()
        # Three logging branches: Link utilization, Table utilization and Flow stats
        #
        # During execution, we will keep each logging branch a list of records (np.array, structured).
        # Whenever we collect stats, it will append a record to the list.
        # At the end of execution, we will do pd.DataFrame.from_records to framize records at once,
        # to avoid repeatedly renewing dataframe
        # Will create a summary file at the end of execution.

        # Step 3: Set up k-path database

        # Step 4: Main loop of simulation
        while (self.timer <= self.sim_time):
            try:
                event_tuple = heappop(self.ev_queue)
                ev_time = event_tuple[0]
                event = event_tuple[1]
                ev_type = event.ev_type

                print event

                # ---- Handle Events ----
                # Handle EvFlowArrival
                if (ev_type == 'EvFlowArrival'):                    
                    self.handle_EvFlowArrival(ev_time, event)

                # Handle EvPacketIn
                elif (ev_type == 'EvPacketIn'):
                    self.handle_EvPacketIn(ev_time, event)

                # Handle EvFlowInstall
                elif (ev_type == 'EvFlowInstall'):
                    self.handle_EvFlowInstall(ev_time, event)
                # Handle EvFlowEnd
                # Handle EvIdleTimeout
                # Handle EvHardTimeout
                # Handle EvPullStats
            except:
                print ('heappop error!')
                break


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
        # Create SimFlow instance        
        flow_obj = SimFlow(src_ip=event.src_ip, dst_ip=event.dst_ip, \
                           src_node=self.hosts[event.src_ip], \
                           dst_node=self.hosts[event.dst_ip], \
                           flow_size=event.flow_size, flow_rate=event.flow_rate, \
                           bytes_left=event.flow_size, \
                           arrive_time=ev_time, update_time=ev_time, \
                           status='requesting' )
        self.flows[(event.src_ip, event.dst_ip)] = flow_obj

        # EvPacketIn event
        new_ev_time = ev_time + SW_CTRL_DELAY
        new_event = EvPacketIn(ev_time=new_ev_time, src_ip=event.src_ip, \
                               dst_ip=event.dst_ip) 
        heappush(self.ev_queue, (new_ev_time, new_event))        


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
        # The controller finds a path
        #path = self.ctrl.find_path()
        pass


    def handle_EvFlowInstall(self, ev_time, event):
        """Handle an EvFlowInstall event.
        1. Double check if there is any flow table overflow along the selected path.
        2. If not, SimSwitch instances on path will install flow entries. Mark the 
           flow's status as 'active'.
           If yes, reject the EvFlowInstall, and re-schedule a EvFlowArrival after
           REJECT_TIMEOUT.
        3. Update the SimCore's flow statistics.

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.

        """
        pass


    def handle_EvFlowEnd(self, ev_time, event):
        """Handle an EvFlowEnd event.
        1. Schedule an EvIdleTimeout event, after IDLE_TIMEOUT.
        2. Mark the flow's status as 'idle'.
        3. Update the SimCore's flow statistics.

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.

        """
        pass


    def handle_EvIdleTimeout(self, ev_time, event):
        """Handle an EvIdleTimeout event.
        1. Remove the flow from self.flows.
        2. Remove the flow entries from path switches.

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.

        """
        pass


    def handle_EvPullStats(self, ev_time, event):
        """Handle an EvPullStats event.
        1. The central controller

        Args:
            ev_time (float64): Event time
            event (Instance inherited from SimEvent): FlowArrival event

        Return:
            None. Will schedule events to self.ev_queue if necessary.


        """


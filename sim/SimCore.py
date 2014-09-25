#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimCore.py: Class SimCore, the core class of FlowSim simulator.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'


# Built-in modules
print "SimCore: Loading built-in modules."
import os
import csv
from heapq import heappush, heappop
from math import ceil, log
from time import time
# Third-party modules
print "SimCore: Loading third-party modules."
import networkx as nx
import netaddr as na
import pandas as pd
import numpy as np
import pprint as pp
# User-defined modules
print "SimCore: Loading user-defined modules."
from SimConfig import *
from SimCtrl import *
from SimFlowGen import *
from SimFlow import *
from SimSwitch import *
from SimLink import *
from SimEvent import *
from SimCoreEventHandling import *
from SimCoreLogging import *
from SimCoreCalculation import *


class SimCore(SimCoreCalculation, SimCoreEventHandling, SimCoreLogging):
    """Core class of FlowSim simulator.

    Attributes:
        sim_time (float64): Total simulation time
        timer (float64): Simulation timer, which keeps current time progress
        topo (networkx.Graph): An undirected graph to keep network topology
        ev_queue (list of 2-tuples): Event queue. Each element is a 2-tuple of (ev_time, event obj)
        nodes_df (pandas.DataFrame): A dataframe that contains switching nodes' names and params.
        links_df (pandas.DataFrame): A dataframe that contains links' names and params.
        hosts (dict of netaddr.IpAddress): Key is host IP, value is its edge switch
        flows (dict of 2-tuples): Key is 2-tuple of flow src/dst,
                                  Value is its associated SimFlow instance.
        link_util_recs (list of np.array): List of link utilization records.
        table_util_recs (list of np.array): List of table utilization records.
        flow_stats_recs (list of np.array): List of flow stats records.

    Extra Notes:
        topo.node[node]['item'] (SimSwitch): Edge switch instances in the topology.
        topo.edge[node1][node2]['item'] (SimLink): Link instances in the topology.

    """

    def __init__(self):
        """Constructor of SimCore class.

        Args:
            None. All attributes are expected to be initialized from config file.

        Extra Notes:
            If not otherwise specified, all initial values come from config.py

        """
        # ---- Simulator timer and counters ----
        self.sim_time = cfg.SIM_TIME
        self.timer = 0.0
        self.ev_queue = []
        np.random.seed(int(time()*100))

        # ---- Parse CSV and set up topology graph's nodes and edges accordingly ----
        self.topo = nx.Graph()
        self.nodes = []
        self.links = []
        self.nodeobjs = {}
        self.linkobjs = {}
        self.link_mapper = {}
        self.build_topo()   # Translate pd.DataFrame into networkx.Graph

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
        self.next_end_time = 999999.9   # Records next ending flow's estimated ending time
        self.next_end_flow = ('', '')   # Records next ending flow

        # ---- Constructor of base classes ----
        SimCoreLogging.__init__(self)


    def display_topo(self):
        """Display topology (nodes and links only)

        Args:
            None

        """
        print 'Nodes:', self.nodes
        print
        print 'Links:', self.links


    def display_topo_details(self):
        """Display topology - nodes and links along with parameters

        Args:
            None

        """
        for nd in self.nodes:
            print self.nodeobjs[nd]

        for lk in self.links:
            print self.linkobjs[lk]


    def build_topo(self):
        """Read the nodes and link dataframe row by row and translate into networkx.Graph.
        Referred by SimCore.__init__().

        Args:
            nodes_df (pandas.DataFrame): Data frame describing node and nodal attributes.
            edges_df (pandas.DataFrame): Data frame describing edge and edge attributes.

        Returns:
            None. self.topo is modified on site.

        """
        nodes_df = pd.read_csv(os.path.join(cfg.DIR_TOPO, 'nodes.csv'), index_col=False)
        links_df = pd.read_csv(os.path.join(cfg.DIR_TOPO, 'links.csv'), index_col=False)

        for myRow in nodes_df.iterrows():
            rowdict = dict(myRow[1])    # myRow is a 2-tuple: (index, dict of params)
            name = rowdict['name']
            self.topo.add_node(name)
            self.nodeobjs[name] = SimSwitch(**rowdict)

        for myRow in links_df.iterrows():
            rowdict = dict(myRow[1])
            node1, node2 = rowdict['node1'], rowdict['node2']
            self.topo.add_edge(node1, node2)
            self.linkobjs[(node2, node1)] = SimLink(**rowdict)
            self.linkobjs[(node1, node2)] = self.linkobjs[(node2, node1)]
                                                    # (node2, node1) and (node1, node2)
                                                    # Pointing to the same SimLink instance

        self.nodes = self.topo.nodes()
        self.links = self.topo.edges()

        for lk in self.links:
            self.link_mapper[lk] = lk
            self.link_mapper[(lk[1], lk[0])] = lk


    def get_node_attr(self, sw_name, attr_name):
        """Get switch (a.k.a. node) attribute by SW name and attribute name.

        Args:
            sw_name (string): Switch name
            attr_name (string): Attribute name

        Returns:
            Variable type: Switch attribute

        """
        ret = getattr(self.nodeobjs[sw_name], attr_name)
        return ret


    def set_node_attr(self, sw_name, attr_name, val):
        """Set sw (a.k.a. node) attribute by SW name and attribute name.

        Args:
            sw_name (string): Switch name
            attr_name (string): Attribute name
            val (variable type): Set value

        Returns:
            None

        """
        setattr(self.nodeobjs[sw_name], attr_name, val)

    def get_link_attr(self, node1, node2, attr_name):
        """Get link (a.k.a. edge) attribute by link node names and attribute name.

        Args:
            node1 (string): Name of link node 1
            node2 (string): Name of link node 2
                            Note that in nx.Graph, node1 and node2 are interchangeable.
            attr_name (string): Attribute name

        Returns:
            Variable type: Link attribute

        """
        ret = getattr(self.linkobjs[(node1, node2)], attr_name)
        return ret


    def set_link_attr(self, node1, node2, attr_name, val):
        """Set link (a.k.a. edge) attribute by link node names and attribute name.

        Args:
            node1 (string): Name of link node 1
            node2 (string): Name of link node 2
                            Note that in nx.Graph, node1 and node2 are interchangeable.
            attr_name (string): Attribute name
            val (variable type): Set value

        Returns:
            None

        """
        setattr(self.linkobjs[(node1, node2)], attr_name, val)


    def get_links_on_path(self, path):
        """Get a list of links along the specified path.

        Args:
            path (list of strings): List of node names along the path

        Returns:
            list of 2-tuples: List of links along the path, each represented by
                              a 2-tuple of node names.

        """
        ret = []

        for i in range(len(path)-1):
            ret.append(self.link_mapper[(path[i+1], path[i])])

        return ret


    def install_entries_to_path(self, path, links, src_ip, dst_ip):
        """Install flow entries to the specified path.

        Args:
            path (list of str): Path
            links (list of 2-tuples): Links along the path
            src_ip (netaddr.IPAddress)
            dst_ip (netaddr.IPAddress)

        Returns:
            None

        """
        for nd in path:
            self.nodeobjs[nd].install_flow_entry(src_ip, dst_ip)

        #for lk in self.get_links_on_path(path):
        for lk in links:
            flowobj = self.flows[(src_ip, dst_ip)]
            self.linkobjs[lk].install_entry(src_ip, dst_ip, flowobj)


    def create_hosts(self):
        """Create hosts, bind hosts to edge switches, and assign IPs.
        """
        base_ip = na.IPAddress('10.0.0.1')
        for nd in self.nodes:
            n_hosts = self.nodeobjs[nd].n_hosts
            self.nodeobjs[nd].base_ip = base_ip
            self.nodeobjs[nd].end_ip = base_ip + n_hosts - 1

            for i in range(n_hosts):
                myIP = base_ip + i
                self.hosts[myIP] = nd
            base_ip = base_ip + 2 ** int(ceil(log(n_hosts, 2)))  # Shift base_ip by an entire IP segment


    def main_course(self):
        """The main course of simulation execution.

        Args:
            None

        Returns:

        """
        self.exec_st_time = time()

        # Step 1: Generate initial set of flows and queue them as FlowArrival events
        self.flowgen.gen_init_flows(self.ev_queue, self)

        # Step 2: Initialize EvLogLinkUtil, EvLogTableUtil and EvReroute events
        if (cfg.LOG_LINK_UTIL > 0):
            heappush(self.ev_queue, (cfg.PERIOD_LOGGING, \
                                     EvLogLinkUtil(ev_time=cfg.PERIOD_LOGGING)))
        if (cfg.LOG_TABLE_UTIL > 0):
            heappush(self.ev_queue, (cfg.PERIOD_LOGGING, \
                                     EvLogTableUtil(ev_time=cfg.PERIOD_LOGGING)))
        if (cfg.DO_REROUTE > 0):
            heappush(self.ev_queue, (cfg.PERIOD_REROUTE, \
                                     EvReroute(ev_time=cfg.PERIOD_REROUTE)))

        # Step 3: Main loop of simulation
        print "Logging to folder: %s" %(cfg.LOG_DIR)
        print "Start simulation. Experiment name: %s" %(cfg.EXP_NAME)

        while (self.timer <= self.sim_time):
            if (self.ev_queue[0][0] < self.next_end_time):
                # Next event comes earlier than next flow end
                event_tuple     = heappop(self.ev_queue)
                ev_time         = event_tuple[0]
                event           = event_tuple[1]
                ev_type         = event.ev_type
            else:
                # Next flow end comes earlier than next event
                # Immediately schedule a EvFlowEnd event and handle it!
                ev_time         = self.next_end_time
                event           = EvFlowEnd(ev_time=ev_time, \
                                            src_ip=self.next_end_flow[0], \
                                            dst_ip=self.next_end_flow[1])
                ev_type         = 'EvFlowEnd'

            self.timer = self.ev_queue[0][0]    # Set timer to next event's ev_time

            if (cfg.SHOW_EVENTS > 0):
                print '%.6f' %(ev_time)
                print event

            # ---- Handle Events ----
            # Handle EvFlowArrival
            if   (ev_type == 'EvFlowArrival'):
                self.handle_EvFlowArrival(ev_time, event)

            # Handle EvPacketIn
            elif (ev_type == 'EvPacketIn'):
                self.handle_EvPacketIn(ev_time, event)

            # Handle EvFlowInstall
            elif (ev_type == 'EvFlowInstall'):
                self.handle_EvFlowInstall(ev_time, event)

            # Handle EvFlowEnd
            elif (ev_type == 'EvFlowEnd'):
                self.handle_EvFlowEnd(ev_time, event)

            # Handle EvIdleTimeout
            elif (ev_type == 'EvIdleTimeout'):
                self.handle_EvIdleTimeout(ev_time, event)

            # Handle EvHardTimeout
            # Handle EvPullStats
            # Handle EvReroute
            # Handle EvLogLinkUtil
            elif (ev_type == 'EvLogLinkUtil'):
                self.handle_EvLogLinkUtil(ev_time, event)

            # Handle EvLogTableUtil
            elif (ev_type == 'EvLogTableUtil'):
                self.handle_EvLogTableUtil(ev_time, event)

        # Finalize
        self.calc_flow_rates(self.sim_time)
        self.exec_ed_time = time()

        # Step 4: Dump list of records to pd.DataFrame, then to csv files
        if (cfg.LOG_LINK_UTIL > 0):
            self.dump_link_util()

        if (cfg.LOG_TABLE_UTIL > 0):
            self.dump_table_util()

        if (cfg.LOG_FLOW_STATS > 0):
            self.dump_flow_stats()

        if (cfg.LOG_CONFIG > 0):
            self.dump_config()

        if (cfg.LOG_SUMMARY > 0):
            self.dump_summary()

        if (cfg.SHOW_SUMMARY > 0):
            self.show_summary()






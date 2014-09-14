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
from config import *
from SimCtrl import *
from SimFlowGen import *
from SimFlow import *
from SimSwitch import *
from SimLink import *
from SimEvent import *
from SimCoreEventHandling import *
from SimCoreLogging import *


class SimCore(SimCoreEventHandling, SimCoreLogging):
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
        fn_nodes = os.path.join(cfg.DIR_TOPO, 'nodes.csv')
        fn_links = os.path.join(cfg.DIR_TOPO, 'links.csv')
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
        self.next_end_time = 999999.9   # Records next ending flow's estimated ending time
        self.next_end_flow = ('', '')   # Records next ending flow

        # ---- Bookkeeping, framing and logging ----
        self.link_util_recs = []
        self.table_util_recs = []
        self.flow_stats_recs = []
        if ( not os.path.exists(cfg.LOG_DIR) ):
            os.mkdir(cfg.LOG_DIR)
        self.fn_link_util = os.path.join(cfg.LOG_DIR, 'link_util.csv')
        self.fn_table_util = os.path.join(cfg.LOG_DIR, 'table_util.csv')
        self.fn_flow_stats = os.path.join(cfg.LOG_DIR, 'flow_stats.csv')
        self.col_table_util = ['time', 'mean', 'rmse', 'min', 'max', 'q1', 'q3', 'median'] + \
                              [str(nd) for nd in self.topo.nodes()]


    def display_topo(self):
        """Display topology (nodes and links only)

        Args:
            None

        """
        print 'Nodes:', self.topo.nodes()
        print
        print 'Links:', self.topo.edges()


    def display_topo_details(self):
        """Display topology - nodes and links along with parameters

        Args:
            None

        """
        for node in self.topo.nodes_iter():
            print self.topo.node[node]['item']

        for link in self.topo.edges_iter():
            print self.topo.edge[link[0]][link[1]]['item']


    def df_to_topo(self, nodes_df, links_df):
        """Read the nodes and link dataframe row by row and translate into networkx.Graph.
        Referred by SimCore.__init__().

        Args:
            nodes_df (pandas.DataFrame): Data frame describing node and nodal attributes.
            edges_df (pandas.DataFrame): Data frame describing edge and edge attributes.

        Returns:
            None. self.topo is modified on site.

        """
        for myRow in nodes_df.iterrows():
            rowdict = dict(myRow[1])    # myRow is a 2-tuple: (index, dict of params)
            name = rowdict['name']
            self.topo.add_node(name, item=SimSwitch(**rowdict))

        for myRow in links_df.iterrows():
            rowdict = dict(myRow[1])
            node1, node2 = rowdict['node1'], rowdict['node2']
            self.topo.add_edge(node1, node2, item=SimLink(**rowdict))


    def get_node_attr(self, sw_name, attr_name):
        """Get switch (a.k.a. node) attribute by SW name and attribute name.

        Args:
            sw_name (string): Switch name
            attr_name (string): Attribute name

        Returns:
            Variable type: Switch attribute

        """
        ret = getattr(self.topo.node[sw_name]['item'], attr_name)
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
        setattr(self.topo.node[sw_name]['item'], attr_name, val)

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
        ret = getattr(self.topo.edge[node1][node2]['item'], attr_name)
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
        setattr(self.topo.edge[node1][node2]['item'], attr_name, val)


    def get_links_in_path(self, path):
        """Get a list of links along the specified path.

        Args:
            path (list of strings): List of node names along the path

        Returns:
            list of 2-tuples: List of links along the path, each represented by
                              a 2-tuple of node names.

        """
        ret = []

        for i in range(len(path)-1):
            if (path[i], path[i+1]) in self.topo.edges():
                ret.append((path[i], path[i+1]))
            elif (path[i+1], path[i]) in self.topo.edges():
                ret.append((path[i+1], path[i]))

        return ret




    def install_entries_to_path(self, path, src_ip, dst_ip):
        """Install flow entries to the specified path.

        Args:
            path (list of string): Path of the flow
            src_ip (netaddr.IPAddress)
            dst_ip (netaddr.IPAddress)

        Returns:
            None

        """
        for nd in path:
            self.topo.node[nd]['item'].install_flow_entry(src_ip, dst_ip)

        for i in range(len(path)-1):
            #self.topo.edge[path[i]][path[i+1]]['item'].flows[(src_ip, dst_ip)] = \
            #    self.flows[(src_ip, dst_ip)]
            self.topo.edge[path[i]][path[i+1]]['item'].install_entry(src_ip, \
                            dst_ip, self.flows[(src_ip, dst_ip)])


    def create_hosts(self):
        """Create hosts, bind hosts to edge switches, and assign IPs.
        """
        base_ip = na.IPAddress('10.0.0.1')
        for nd in self.topo.nodes():
            n_hosts = self.topo.node[nd]['item'].n_hosts
            self.set_node_attr(nd, 'base_ip', base_ip)
            self.set_node_attr(nd, 'end_ip', base_ip + n_hosts - 1)

            for i in range(n_hosts):
                myIP = base_ip + i
                self.hosts[myIP] = nd
            base_ip = base_ip + 2 ** int(ceil(log(n_hosts, 2)))  # Shift base_ip by an entire IP segment


    def calc_flow_rates(self, ev_time):
        """Calculate flow rates (according to DevoFlow Algorithm 1).

        Args:
            None

        Returns:
            None. But will update flow and link statistics, as well as identify next ending
            flow and its estimated end time.

        """
        # The following local dicts have links as their keys (represented by 2-tuple of node names)
        # Values are either float64 (caps, unasgn_caps) or int (active_flows, unasgn_flows)
        link_bw = {}                # Value: maximum BW on that link
        link_unasgn_bw = {}         # Value: Unassigned BW on that link
        link_n_active_flows = {}    # Value: # of active flows on that link
        link_n_unasgn_flows = {}    # Value: # of unassigned flows on that link

        # The following local dicts have flows as their keys (represented by 2-tuple of IPs)
        flow_asgn = {}          # Value: boolean that signals whether the flow is assigned.
        flow_asgn_bw = {}       # Value: assigned BW for that flow

        # Initialization:
        for lk in self.topo.edges_iter():
            link_bw[lk] = self.get_link_attr(lk[0], lk[1], 'cap')
            link_unasgn_bw[lk] = link_bw[lk]
            link_n_active_flows[lk] = self.topo.edge[lk[0]][lk[1]]['item'].get_n_active_flows()
            link_n_unasgn_flows[lk] = link_n_active_flows[lk]

        for fl in self.flows:
            if (not self.flows[fl].status == 'active'):
                continue
            else:
                flow_asgn[fl] = False
                flow_asgn_bw[fl] = 0.0

        # ---- Start iterating over bottleneck links ----
        list_unfin_links = [lk for lk in self.topo.edges() if link_n_unasgn_flows[lk] > 0]
                                                        # List of links that are not yet processed
        earliest_end_time = 99999999.9  # Just a very large float number
        earliest_end_flow = ('', '')

        while (len(list_unfin_links) > 0):
            # Find the bottleneck link (link with minimum avg. BW for unassigned links)
            btneck_link = sorted(list_unfin_links, \
                                 key=lambda lk: link_unasgn_bw[lk]/link_n_unasgn_flows[lk], \
                                 reverse=False)[0]
            btneck_bw = link_unasgn_bw[btneck_link]/link_n_unasgn_flows[btneck_link]

            # Update all flows on bottleneck links
            for fl in self.get_link_attr(btneck_link[0], btneck_link[1], 'flows'):
                if (fl in flow_asgn):
                    if (flow_asgn[fl] == False):
                        # ---- Flow operations ----
                        # Write btneck_bw to flow
                        flow_asgn[fl] = True
                        flow_asgn_bw[fl] = btneck_bw
                        # Write updated statistics to flow: curr_rate, bytes_left, bytes_sent,
                        # update_time, etc.
                        self.flows[fl].bytes_left -= self.flows[fl].curr_rate * \
                                                     (ev_time - self.flows[fl].update_time)
                        self.flows[fl].bytes_sent = self.flows[fl].flow_size - \
                                                    self.flows[fl].bytes_left
                        self.flows[fl].update_time = ev_time
                        self.flows[fl].curr_rate = btneck_bw    # Update after...
                        # Calculate next ending flow and its estimated end time
                        est_end_time = ev_time + (self.flows[fl].bytes_left / \
                                       self.flows[fl].curr_rate)
                        if (est_end_time < earliest_end_time):
                            earliest_end_time = est_end_time
                            earliest_end_flow = fl

                        # ---- Link operations ----
                        # Update link unassigned BW and link unassigned flows along the path
                        path = self.flows[fl].path

                        for lk in self.get_links_in_path(path):
                            link_unasgn_bw[lk] = link_unasgn_bw[lk] - btneck_bw
                            link_n_unasgn_flows[lk] = link_n_unasgn_flows[lk] - 1
                            if (link_n_unasgn_flows[lk] == 0 or link_unasgn_bw[lk] == 0.0):
                                list_unfin_links.remove(lk)

        self.next_end_time = earliest_end_time
        self.next_end_flow = earliest_end_flow


    def main_course(self):
        """The main course of simulation execution.

        Args:
            None

        Returns:

        """
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
        while (self.timer <= self.sim_time):
            if (self.ev_queue[0][0] < self.next_end_time):
                # Next event comes earlier than next flow end
                event_tuple = heappop(self.ev_queue)
                ev_time = event_tuple[0]
                event = event_tuple[1]
                ev_type = event.ev_type
            else:
                # Next flow end comes earlier than next event
                # Schedule a EvFlowEnd event
                ev_time = self.next_end_time
                event = EvFlowEnd(ev_time=ev_time, \
                                  src_ip=self.next_end_flow[0], \
                                  dst_ip=self.next_end_flow[1])
                ev_type = 'EvFlowEnd'

            self.timer = ev_time

            if (cfg.SHOW_EVENTS > 0):
                print '%.6f' %(ev_time)
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
            elif (ev_type == 'EvFlowEnd'):
                self.handle_EvFlowEnd(ev_time, event)

            # Handle EvIdleTimeout
            elif (ev_type == 'EvIdleTimeout'):
                self.handle_EvIdleTimeout(ev_time, event)

            # Handle EvHardTimeout
            # Handle EvPullStats
            # Handle EvReroute

        # Step 4: Dump list of records to pd.DataFrame, then to csv files
        if (cfg.LOG_LINK_UTIL > 0):
            pass

        if (cfg.LOG_TABLE_UTIL > 0):
            df_table_util = pd.DataFrame.from_records(self.table_util_recs, \
                                                      columns=self.col_table_util)
            df_table_util.to_csv(self.fn_table_util, index=False, \
                                 quoting=csv.QUOTE_NONNUMERIC)

        if (cfg.LOG_FLOW_STATS > 0):
            df_flow_stats = pd.DataFrame.from_records(self.flow_stats_recs, \
                                                      columns=cfg.LOG_FLOW_STATS_FIELDS)
            df_flow_stats.to_csv(self.fn_flow_stats, index=False, \
                                 quoting=csv.QUOTE_NONNUMERIC)




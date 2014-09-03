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
# Third-party modules
import networkx as nx
import netaddr as na
import pandas as pd
# User-defined modules
from config import *
from SimCtrl import *
from SimFlowGen import *
from SimSwitch import *
from SimLink import *
from SimEvent import *


class SimCore:
    """Core class of FlowSim simulator.

    Attributes:
        sim_time (float64): Total simulation time
        timer (float64): Simulation timer, which keeps current time progress
        topo (networkx.Graph): An undirected graph to keep network topology
        ev_queue (list of 2-tuples): Event queue. Each element is a 2-tuple of (evtime, event obj)
        nodes_df (pandas.DataFrame): A dataframe that contains switching nodes' names and params.
        links_df (pandas.DataFrame): A dataframe that contains links' names and params.
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

        self.topo = nx.Graph()

        # ---- Parse CSV and set up topology graph's nodes and edges accordingly ----
        fn_nodes = os.path.join(DIR_TOPO, 'nodes.csv')
        fn_links = os.path.join(DIR_TOPO, 'links.csv')
        self.nodes_df = pd.read_csv(fn_nodes, index_col=False)
        self.links_df = pd.read_csv(fn_links, index_col=False)
        self.df_to_topo(self.nodes_df, self.links_df)   # Translate pd.DataFrame into networkx.Graph

        # ---- Simulator components ----
        # SimController: Currently assume one omniscient controller
        # SimFlowGen:
        # SimSwitch instances are instantiated in df_to_topo
        # SimLink instances are instantitated in df_to_topo
        self.ctrl = SimCtrl(self)
        self.flowgen = SimFlowGen()



        # ---- Generate hosts, assign IP addresses and map hosts to their edge switches ----

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


    def gen_init_flows(self):
        """Generate initial flows. Called at start of simulation loop.

        Args:

        Returns:

        """
        pass


    def main_course(self):
        """The main course of simulation execution.

        Args:

        Returns:

        """
        # Step 1: Generate initial set of flows and queue them as FlowArrival events
        self.gen_init_flows()

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
                event = heappop(ev_queue)
            except:
                print ('heappop error!')
            pass



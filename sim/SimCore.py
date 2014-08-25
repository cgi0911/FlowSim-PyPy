#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimCore.py: Class SimCore, the core class of FlowSim simulator.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'


# Built-in modules
import os
import csv
# Third-party modules
import networkx as nx
import netaddr as na
import pandas as pd
# User-defined modules
from config import *
from SimSwitch import *
from SimLink import *
from SimEvent import *


class SimCore:
    """Core class of FlowSim simulator.

    Attributes:
        topo (networkx.Graph): Network topology as an undirected graph.

    Extra Notes:
        topo.node[node]['item'] (SimSwitch): Edge switche in the topology.
        topo[node1][node2]['item'] (SimLink): Link in the topology.

    """

    def __init__(self):
        """Constructor of SimCore class.

        Args:
            sim_time (float64): Total simulation time
            timer (float64): Simulation timer, which keeps current time progress
            topo (networkx.Graph): An undirected graph to keep network topology
            nodes_df (pandas.DataFrame): A dataframe that contains switching nodes' names and params.
            links_df (pandas.DataFrame): A dataframe that contains links' names and params.

        Extra Notes:
            If not otherwise specified, all initial values come from config.py

        """
        self.sim_time = SIM_TIME
        self.timer = 0.0
        self.topo = nx.Graph()

        # ---- Parse CSV and set up topology graph's nodes and edges accordingly ----
        fn_nodes = os.path.join(DIR_TOPO, 'nodes.csv')
        fn_links = os.path.join(DIR_TOPO, 'links.csv')
        self.nodes_df = pd.read_csv(fn_nodes, index_col=False)
        self.links_df = pd.read_csv(fn_links, index_col=False)
        self.df_to_topo(self.nodes_df, self.links_df)   # Parsing function

        # ---- Generate hosts, assign IP addresses and map hosts to their edge switches ----


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
            print self.topo.edge[link[0]][link[1]]['item']


    def df_to_topo(self, nodes_df, links_df):
        """Parse the nodes and link dataframe (read from CSV files) into topology graph.
        """
        #self.topo.add_nodes_from(nodes_df['name'])
        #self.topo.add_edges_from(zip(links_df['node1'], links_df['node2']))
        for myRow in nodes_df.iterrows():
            rowdict = dict(myRow[1])
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
        # Step 2:


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
# User-defined modules
from config import *
import SimSwitch
import SimEvent



class SimCore:
    """Core class of FlowSim simulator.

    Attributes:
      topo (networkx.Graph): Network topology as an undirected graph.

    """

    def __init__(self, fn_config='config.py'):
        """Constructor of SimCore class.

        Args:
          fn_config (str): File name of configuration file.

        Extra Notes:
          topo[node]['item'] (SimSwitch): Edge switche in the topology.
          topo[node1][node2]['item'] (SimLink): Link in the topology.

        """
        # ---- Members ----
        self.topo = nx.Graph()      # Topology is undirected graph.
        # ---- Parsing CSV into Topology Graph ----

        # ---- Generate hosts and map hosts to their edge switches ----

        # ----





    def genInitFlows(self):
        """
        Generate initial flows. Called at start of simulation loop.
        """
        pass




    def __repr__(self):
        return ('Hello World! The instance ID is %d' % id(self) )




    def __str__(self):
        return 'Hello World!'




    def displayTopo(self):
        print self.topo
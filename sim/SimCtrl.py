#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimController.py: The SDN controller class, capable of doing k-path routing.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'


# Built-in modules
from time import *
# Third-party modules
import networkx as nx
import pprint as pp
# User-defined modules
from config import *


class SimCtrl:
    """SDN controller.

    Attributes:
        topo (networkx.Graph): Network topology as an undirected graph.
        path_db (dict): Path database. key: flow (2-tuple), value: list of paths.
                        Can be constructed by k-path, ECMP or shortest path.

    Extra Notes:


    """

    def __init__(self, sim_core):
        """Constructor of SimCtrl class.

        Args:
            sim_core (Instance of SimCore): Refers to simulation core module.

        """
        # ---- Initialize topology graph according to SimCore's topology ----
        self.topo = nx.Graph()
        self.topo.add_nodes_from(sim_core.topo.nodes())
        self.topo.add_edges_from(sim_core.topo.edges())

        # ---- Build k-path database ----
        self.path_db = self.setup_path_db()


    def setup_path_db(self, k=K_PATH, mode=ROUTING_MODE):
        """Build k-path database for all src-dst node pairs in topology.

        Args:
            k (int): Number of paths given for each source-destination pair.
            mode (string): A string signaling which algorithm (yen, shortest-only, etc.)
                           to be used for k-path setup.

        Return:
            path_db (dict): Path database.

        Extra Notes:
            - Currently supported routing modes:
              'yen': Yen's K-path algorithm
              'ecmp': Equal-cost multi-pathing
              'spf': Shortest-path-first

        """
        path_db = {}     # empty dict

        # Set up k paths for each src-dst node pair
        for src in sorted(self.topo.nodes()):
            for dst in sorted(self.topo.nodes()):
                if (not src == dst):
                    if (mode == 'yen'):
                        path_db[(src, dst)] = self.find_path_yen(src, dst, k=k)
                    elif (mode == 'ecmp'):
                        path_db[(src, dst)] = self.find_path_ecmp(src, dst)
                    elif (mode == 'spf'):
                        path_db[(src, dst)] = self.find_path_spf(src, dst)
                    else:
                        # Default to spf
                        path_db[(src, dst)] = self.find_path_spf(src, dst)

        return path_db


    def display_path_db(self):
        """Display path database in a formatted manner.
        Paths are sorted in the order of length.
        """
        for key in sorted(self.path_db.keys()):
            print "%s: %d paths" %(str(key), len(self.path_db[key]))
            for path in sorted(self.path_db[key], key=lambda x: len(x), reverse=False):
                print "    %s" %(str(path))
                pass
            print


    def find_path_yen(self, src, dst, k=K_PATH):
        """Yen's algorithm for building k-path.
        Please refer to Yen's paper.

        Args:
            src (string): Source node, which is an edge switch.
            dst (string): Dest node, also an edge switch. src != dst
            k (int): # of paths to find from src to dst

        return:
            list: list of k available paths from src to dst.
                  Each path is represented by a list of node names.
        """
        st_time = time()

        if (SHOW_K_PATH_CONSTRUCTION > 0):
            print "Finding %d paths from %s to %s" %(k, src, dst)

        confirmed_paths = []
        confirmed_paths.append( nx.shortest_path(self.topo, src, dst) )
        if (k <= 1):
            return confirmed_paths

        potential_paths = []

        for j in range(1, k):
            for i in range(0, len(confirmed_paths[j-1]) - 1):
                myTopo = nx.DiGraph(self.topo)      # Copy the topology graph
                myPath = confirmed_paths[j-1]
                spurNode = myPath[i]
                rootPath = myPath[0:i+1]

                l = len(rootPath)

                for p in confirmed_paths:
                    if (rootPath == p[0:l]):
                        if (myTopo.has_edge(p[l-1], p[l])):
                            myTopo.remove_edge(p[l-1], p[l])
                        else:
                            pass

                for q in rootPath[:-1]:
                    myTopo.remove_node(q)

                try:
                    spurPath = nx.shortest_path(myTopo, spurNode, dst)
                    totalPath = rootPath + spurPath[1:]
                    potential_paths.append(totalPath)
                except:
                    spurPath = []

                #if (not spurPath == []):
                #    totalPath = rootPath + spurPath[1:]
                #    potential_paths.append(totalPath)

            if (len(potential_paths) == 0):
                break

            potential_paths = sorted(potential_paths, key=lambda x: len(x) )
            confirmed_paths.append(potential_paths[0])
            potential_paths = []

        ed_time = time()

        if (SHOW_K_PATH_CONSTRUCTION > 0):
            print "%d-paths from %s to %s:" %(k, src, dst), confirmed_paths
            print "Time elapsed:", ed_time-st_time

        return confirmed_paths


    def find_path_ecmp(self, src, dst):
        """Find all lowest equal-cost paths from src to dst. The cost is hop count.

        Args:
            src (string): Source node, which is an edge switch.
            dst (string): Dest node, also an edge switch. src != dst

        return:
            list: list of all lowest equal-cost paths from src to dst.
                  Each path is represented by a list of node names.
        """
        ret = []
        for path in nx.all_shortest_paths(self.topo, src, dst):
            ret.append(path)
        return ret


    def find_path_spf(self, src, dst):
        """Find a shortest path from src to dst.

        Args:
            src (string): Source node, which is an edge switch.
            dst (string): Dest node, also an edge switch. src != dst

        return:
            list: list with only one element - shortest path from src to dst.
                  Each path is represented by a list of node names.
        """
        path = nx.shortest_path(self.topo, src, dst)
        return [path]



#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimCtrlPathDB.py:
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

# Built-in modules
from time import *
#import random as rd
#import os
# Third-party modules
import networkx as nx
# User-defined modules
import SimConfig as cfg


class SimCtrlPathDB:
    """
    """
    def setup_path_db(self):
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
        print "Building path database for all src-dst node pairs."
        path_db = {}     # empty dict

        # Set up k paths for each src-dst node pair
        for src in sorted(self.topo.nodes()):
            for dst in sorted(self.topo.nodes()):
                if (not src == dst):
                    if (cfg.PATHDB_MODE == 'all_shortest'):
                        path_db[(src, dst)] = self.build_pathdb_all_shortest(src, dst)
                    elif (cfg.PATHDB_MODE == 'kpath_yen'):
                        path_db[(src, dst)] = self.build_pathdb_kpath_yen(src, dst, k=cfg.K_PATH)
                    elif (cfg.PATHDB_MODE == 'one_shortest'):
                        path_db[(src, dst)] = self.build_pathdb_one_shortest(src, dst)
                    else:
                        path_db[(src, dst)] = self.build_pathdb_all_shortest(src, dst)  # default to all_shortest
        self.path_db = path_db

        # Build ECMP database if needed
        if (cfg.ROUTING_MODE == 'ecmp'):
            self.build_ecmp_db()

        # Logging the path database to file.
        if (cfg.LOG_PATH_DB > 0):
            fn = self.fn_path_db
            outfile = open(fn, 'wb')

            for sd_pair in path_db:
                pathset = path_db[sd_pair]
                sub_sum = 0.0
                n_paths = 0
                shortest_dist = 99999
                longest_dist = 0

                outfile.write('%s\n' %(str(sd_pair)))
                for pth in pathset:   outfile.write('    %s\n' %(str(pth)))
                
                n_paths         = len(pathset)
                avg_dist        = sum(len(pth) for pth in pathset) / float(n_paths)
                longest_dist    = max([len(pth)-1 for pth in pathset])
                shortest_dist   = min([len(pth)-1 for pth in pathset])

                outfile.write('    Distance of %d paths: shortest=%d  longest=%d  average=%.3f\n' \
                              %(n_paths, shortest_dist, longest_dist, avg_dist))
                outfile.write('\n\n')


        print "Finished building path database"
        


    def build_pathdb_kpath_yen(self, src, dst, k=cfg.K_PATH):
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

        if (cfg.SHOW_K_PATH_CONSTRUCTION > 0):
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

            if (len(potential_paths) == 0):
                break

            potential_paths = sorted(potential_paths, key=lambda x: len(x) )
            confirmed_paths.append(potential_paths[0])
            potential_paths = []

        ed_time = time()

        if (cfg.SHOW_K_PATH_CONSTRUCTION > 0):
            print "%d-paths from %s to %s:" %(k, src, dst), confirmed_paths
            print "Time elapsed:", ed_time-st_time

        return confirmed_paths


    def build_pathdb_all_shortest(self, src, dst):
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


    def build_pathdb_one_shortest(self, src, dst):
        """Find a shortest path from src to dst.

        Args:
            src (string): Source node, which is an edge switch.
            dst (string): Dest node, also an edge switch. src != dst

        return:
            list: list with only one element - shortest path from src to dst.
                  Each path is represented by a list of node names.
        """
        ret  = []
        path = nx.shortest_path(self.topo, src, dst)
        ret.append(path)
        return ret


    def build_ecmp_db(self):
        """
        """
        ecmp_db = {}
        for src, dst in self.path_db:
            if (not (src, dst) in ecmp_db):
                ecmp_db[(src, dst)] = {}
            for pth in self.path_db[(src, dst)]:
                for i in range(len(pth)-1):
                    nd = pth[i]
                    next_hop = pth[i+1]
                    if (not nd in ecmp_db[(src, dst)]):
                        ecmp_db[(src, dst)][nd] = [next_hop]
                    else:
                        ecmp_db[(src, dst)][nd].append(next_hop)

        self.ecmp_db = ecmp_db


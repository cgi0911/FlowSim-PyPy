#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimCtrlPathDB.py:
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

# Built-in modules
#from time import *
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
                    if (cfg.ROUTING_MODE == 'kpath_fe' or cfg.ROUTING_MODE == 'kpath'):
                        if (cfg.K_PATH_METHOD == 'yen'):
                            path_db[(src, dst)] = self.build_pathset_yen(src, dst, \
                                                                         k=cfg.K_PATH)
                        else:
                            path_db[(src, dst)] = self.build_pathset_yen(src, dst, \
                                                                         k=cfg.K_PATH)
                    elif (cfg.ROUTING_MODE == 'ecmp' or cfg.ROUTING_MODE == 'ecmp_fe'):
                        path_db[(src, dst)] = self.build_pathset_ecmp(src, dst)
                    elif (cfg.ROUTING_MODE == 'spf'):
                        path_db[(src, dst)] = self.build_pathset_spf(src, dst)
                    else:
                        # Default to spf
                        path_db[(src, dst)] = self.build_pathset_spf(src, dst)

        # Logging the path database to file.
        if (cfg.LOG_PATH_DB > 0):
            fn = self.fn_path_db
            outfile = open(fn, 'wb')

            for sd_pair in path_db:
                outfile.write('%s\n' %(str(sd_pair)))
                paths = path_db[sd_pair]
                sub_sum = 0.0
                n_paths = 0
                shortest_dist = 99999
                longest_dist = 0

                for pth in paths:
                    outfile.write('    %s\n' %(str(pth)))
                    lpth        =   len(pth)
                    sub_sum     +=  lpth
                    n_paths     +=  1
                    if (lpth < shortest_dist):
                        shortest_dist   = lpth
                    if (lpth > longest_dist):
                        longest_dist    = lpth
                avg_dist = float(sub_sum) / n_paths
                outfile.write('    Distance of %d paths: shortest=%d  longest=%d  average=%.3f\n' \
                              %(n_paths, shortest_dist, longest_dist, avg_dist))
                outfile.write('\n\n')


        print "Finished building path database"
        return path_db


    def build_pathset_yen(self, src, dst, k=cfg.K_PATH):
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


    def build_pathset_ecmp(self, src, dst):
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


    def build_pathset_spf(self, src, dst):
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
#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimController.py: The SDN controller class, capable of doing k-path routing.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'


# Built-in modules
from time import *
import random as rd
# Third-party modules
import networkx as nx
# User-defined modules
import SimConfig as cfg


class SimCtrl:
    """SDN controller.

    Attributes:
        topo (networkx.Graph): Network topology as an undirected graph.
        hosts (dict): Hosts database. Key: Host IP, Value: attached edge switch.
                      Directly copy-assigned during SimCtrl.__init__()
        path_db (dict): Path database. key: flow (2-tuple), value: list of paths.
                        Can be constructed by k-path, ECMP or shortest path.

    Extra Notes:


    """
    class NodeRec:
        """Record of node attributes at controller.
        """
        def __init__(self, nd, sim_core):
            """Constructor of NodeRec class.

            Args:
                sim_core (Instance of SimCore)
                nd (str): Node name
            """
            self.table_size     = sim_core.get_node_attr(nd, 'table_size')


    class LinkRec:
        """Record of link attributes at controller.
        """
        def __init__(self, lk, sim_core):
            """Constructor of LinkRec class.

            Args:
                sim_core (Instance of SimCore)
                lk (2-tuple of str): Link key, which is a 2-tuple of node names.
            """
            self.cap            = sim_core.get_link_attr(lk[0], lk[1], 'cap')
            self.usage          = 0.0
            self.util           = 0.0
            self.unasgn_bw      = self.cap
            self.flows          = []
            self.unasgn_flows   = []


    class FlowRec:
        """Record of flow attributes at controller.
        """
        def __init__(self, fl, sim_core):
            """Constructor of FlowRec class.

            """
            self.src_node       = fl[0]
            self.dst_node       = fl[1]
            self.path           = sim_core.flows[fl].path
            self.links          = sim_core.flows[fl].links
            self.cnt            = 0.0


    def __init__(self, sim_core):
        """Constructor of SimCtrl class.

        Args:
            sim_core (Instance of SimCore): Refers to simulation core module.

        Extra Notes:
            Note that the node/link states kept at controller may not be strictly
            synchronized with SimCore! The states kept at controller are acquired by
            pulling statistics from the network.

        """
        # ---- Initialize topology graph by copying SimCore's topology ----
        self.sim_core   = sim_core
        self.topo       = nx.Graph()
        self.topo.add_nodes_from(sim_core.topo.nodes())
        self.topo.add_edges_from(sim_core.topo.edges())
        self.noderecs   = {nd: SimCtrl.NodeRec(nd, sim_core) for nd in self.topo.nodes()}
        self.linkrecs   = {lk: SimCtrl.LinkRec(lk, sim_core) for lk in self.topo.edges()}
        self.flowrecs   = {}
        self.old_eleph_flows = {}

        # ---- Hosts database ----
        self.hosts      = sim_core.hosts        # Pass by assignment

        # ---- Build k-path database ----
        self.path_db    = self.setup_path_db()


    def __str__(self):
        return "Controller"


    def install_flow_entry(self, src_ip, dst_ip):
        """Install a flow entry (src_ip, dst_ip) as we've done at the SimSwitch instances.

        Args:
            path (list of string): Path of the flow, represented by a list of sw names.
            src_ip (netaddr.IPAddress)
            dst_ip (netaddr.IPAddress)

        """
        if (not (src_ip, dst_ip) in self.flowrecs):
            fl = (src_ip, dst_ip)
            self.flowrecs[fl]     = SimCtrl.FlowRec(fl, self.sim_core)


    def remove_flow_entry(self, src_ip, dst_ip):
        """
        """
        fl = (src_ip, dst_ip)

        if (fl in self.flowrecs):
            del self.flowrecs[fl]

        if (fl in self.old_eleph_flows):
            del self.old_eleph_flows[fl]


    def get_table_usage(self, nd):
        """
        """
        ret = len(self.sim_core.nodeobjs[nd].table)
        return ret


    def collect_counters(self, ev_time):
        """
        """
        for fl in self.flowrecs:
            flowobj                 = self.sim_core.flows[fl]
            self.flowrecs[fl].cnt   = flowobj.cnt
            flowobj.cnt             = 0.0
            flowobj.collect_time    = ev_time


    def comB(self):
        """Compute max-min fair BW, considering only flows in old_eleph_flows.
        """
        unproc_links                = []

        for lk in self.linkrecs:
            lkrec                   = self.linkrecs[lk]
            lkrec.unasgn_bw         = lkrec.cap
            lkrec.flows             = []
            lkrec.unasgn_flows      = []

        for fl in self.old_eleph_flows:
            for lk in self.flowrecs[fl].links:
                lkrec = self.linkrecs[lk]
                lkrec.flows.append(fl)
                lkrec.unasgn_flows.append(fl)
                if (not lk in unproc_links):
                    unproc_links.append(lk)

        while (len(unproc_links) > 0):
            btnk_link = ''
            btnk_bw   = float('inf')

            to_remove_unproc_links = []
            for lk in unproc_links:
                lkrec = self.linkrecs[lk]
                if (lkrec.unasgn_flows == []):
                    to_remove_unproc_links.append(lk)
                else:
                    bw_per_flow = lkrec.unasgn_bw / len(lkrec.unasgn_flows)
                    if (bw_per_flow < btnk_bw):
                        btnk_link = lk
                        btnk_bw   = bw_per_flow

            for lk in to_remove_unproc_links:   unproc_links.remove(lk)

            if (unproc_links == []):    break

            btnk_lkrec = self.linkrecs[btnk_link]
            for fl in btnk_lkrec.unasgn_flows:
                self.old_eleph_flows[fl] = btnk_bw
                for lk in self.flowrecs[fl].links:
                    lkrec = self.linkrecs[lk]
                    lkrec.unasgn_flows.remove(fl)
                    lkrec.unasgn_bw -= btnk_bw

            unproc_links.remove(btnk_link)


    def get_oab_on_link(self, lk):
        pass


    def do_reroute(self, ev_time):
        """
        """
        sorted_flows = sorted([fl for fl in self.flowrecs], \
                              key=lambda x: self.flowrecs[x].cnt, reverse=True)
        eleph_flows  = sorted_flows[:cfg.N_ELEPH_FLOWS]
        #for fl in eleph_flows: print ev_time, fl, self.flowrecs[fl].cnt, self.sim_core.flows[fl].collect_time, \
        #self.sim_core.flows[fl].status, self.sim_core.flows[fl].curr_rate
        #print len(eleph_flows)
        new_eleph_flows = [fl for fl in eleph_flows if (not fl in self.old_eleph_flows)]    # already sorted
        #print len(new_eleph_flows), len(self.old_eleph_flows)

        while (len(new_eleph_flows) > 0):
            # Compute max-min fair BW allocation (considering old_eleph_flows only)
            self.comB()
            # Pop the new eleph flow that has largest count
            fl = new_eleph_flows.pop(0)
            # Calculate OAB for each path
            # Commit path change of the selected new eleph flow
            # Add the selected flow to old_eleph_flows, and remove from new_eleph_flow
            self.old_eleph_flows[fl] = 0.0


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
                    if (cfg.ROUTING_MODE == 'tablelb'):
                        if (cfg.K_PATH_METHOD == 'yen'):
                            path_db[(src, dst)] = self.build_pathset_yen(src, dst, \
                                                                         k=cfg.K_PATH)
                        else:
                            path_db[(src, dst)] = self.build_pathset_yen(src, dst, \
                                                                         k=cfg.K_PATH)
                    elif (cfg.ROUTING_MODE == 'ecmp'):
                        path_db[(src, dst)] = self.build_pathset_ecmp(src, dst)
                    elif (cfg.ROUTING_MODE == 'spf'):
                        path_db[(src, dst)] = self.build_pathset_spf(src, dst)
                    else:
                        # Default to spf
                        path_db[(src, dst)] = self.build_pathset_spf(src, dst)

        print "Finished building path database"
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


    def is_feasible(self, path):
        """Check if path is feasible (without table overflow).
        """
        ret = True
        for nd in path:
            usage = self.get_table_usage(nd)
            table_size = self.noderecs[nd].table_size
            if (usage >= table_size):
                ret = False
                break
        return ret


    def find_path_ecmp(self, src_node, dst_node):
        """ECMP routing: randomly choose among several ECMP routes.

        Args:
            src_ip (netaddr.IPAddress)
            dst_ip (netaddr.IPAddress)

        Returns:
            list of strings: Chosen path
        """
        # First check for feasibility of path. Make sure no overflow.
        feasible_paths = [path for path in self.path_db[(src_node, dst_node)] \
                          if ( self.is_feasible(path) == True )]
        # Return a random choice
        try:
            return rd.choice(feasible_paths)
        except:
            return []   # No path available


    def find_path_tablelb(self, src_node, dst_node):
        """Table-aware routing: choose the path which yields lowest
        stdev of table util.

        Args:
            src_ip (netaddr.IPAddress)
            dst_ip (netaddr.IPAddress)

        Returns:
            list of strings: Chosen path
        """
        # First check for feasibility of path. Make sure no overflow.
        feasible_paths = [path for path in self.path_db[(src_node, dst_node)] \
                          if ( self.is_feasible(path) == True )]

        if (len(feasible_paths) == 1):
            return feasible_paths[0]

        # Find the best table LB path
        best_objval     = float('inf')  # Just a large float number
        best_path       = []

        for path in feasible_paths:
            objval = 0.0
            for nd in path:
                usage   =   self.get_table_usage(nd)
                size    =   self.get_node_attr(nd, 'table_size')
                objval  +=  float(size) / (size - usage)

            if (objval < best_objval):
                best_path = path

        return best_path    # Will return [] is no path available


    def find_path(self, src_ip, dst_ip):
        """Given src and dst IPs, find a feasible path in between.
        1. Path is selected according to routing mode.
        2. Path is described as a list of node names (strings).
        3. If no feasible path (due to table overflow), return [].

        Args:
            src_ip (netaddr.IPAddress)
            dst_ip (netaddr.IPAddress)

        Returns:
            list of strings: Chosen path

        """
        src_node = self.hosts[src_ip]
        dst_node = self.hosts[dst_ip]
        if (cfg.ROUTING_MODE == 'ecmp'):
            path = self.find_path_ecmp(src_node, dst_node)
        elif (cfg.ROUTING_MODE == 'tablelb'):
            path = self.find_path_tablelb(src_node, dst_node)
        else:
            path = self.find_path_ecmp(src_node, dst_node)
        return path


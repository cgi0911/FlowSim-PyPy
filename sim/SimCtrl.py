#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimCtrl.py: The SDN controller class, capable of doing k-path routing.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'


# Built-in modules
from time import *
import random as rd
import os
# Third-party modules
import networkx as nx
# User-defined modules
import SimConfig as cfg
from SimCtrlPathDB import *


class SimCtrl(SimCtrlPathDB):
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
            flowobj             = sim_core.flows[fl]
            self.src_node       = flowobj.src_node
            self.dst_node       = flowobj.dst_node
            self.path           = flowobj.path
            self.links          = flowobj.links
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

        # ---- Build path database ----
        if ( not os.path.exists(cfg.LOG_DIR) ):
            os.mkdir(cfg.LOG_DIR)
        self.fn_path_db = os.path.join(cfg.LOG_DIR, 'path_db.txt')  # Log file for path DB
        self.setup_path_db()  # Set up path DB


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
        """
        """
        lkrec   = self.linkrecs[lk]
        cap     = lkrec.cap
        flows   = lkrec.flows
        n_old_eleph     = len(self.old_eleph_flows)
        sorted_flows    = sorted(lkrec.flows, key=lambda x: self.old_eleph_flows[x], reverse=True)
        tilda_flows     = []

        for i in range(len(sorted_flows) - 1):
            fl = sorted_flows[i]
            bw = self.old_eleph_flows[fl]

            hat_bw  = 0.0
            hat_num = 0
            for j in range(i+1, len(sorted_flows)):
                x = sorted_flows[j]
                bw_x = self.old_eleph_flows[x]
                if (bw_x < bw):
                    hat_bw += bw_x
                    hat_num += 1

            if (bw >= (cap-hat_bw)/(n_old_eleph - hat_num + 1) ):
                tilda_flows.append(fl)

        sub_sum = sum(self.old_eleph_flows[fl] for fl in sorted_flows if not fl in tilda_flows)
        oab_link = (cap-sub_sum) / (len(tilda_flows)+1)

        return oab_link


    def get_maxmin_bw_on_link(self, lk):
        """
        """
        lkrec   = self.linkrecs[lk]
        cap     = lkrec.cap
        bw      = float(cap) / (len(lkrec.flows) + 1)

        return bw


    def get_oab_on_path(self, pth):
        """
        """
        links = self.sim_core.get_links_on_path(pth)
        oab_path = min([self.get_oab_on_link(lk) for lk in links])
        return oab_path


    def get_maxmin_bw_on_path(self, pth):
        """
        """
        links = self.sim_core.get_links_on_path(pth)
        maxmin_bw_path = min([self.get_maxmin_bw_on_link(lk) for lk in links])
        return maxmin_bw_path


    def get_best_reroute_path(self, path_set):
        """
        """
        if (cfg.REROUTE_ALGO == 'oab'):
            best_path = max(path_set, key=lambda x: self.get_oab_on_path(x))
        elif (cfg.REROUTE_ALGO == 'greedy'):
            best_path = max(path_set, key=lambda x: self.get_maxmin_bw_on_path(x))
        else:
            best_path = max(path_set, key=lambda x: self.get_maxmin_bw_on_path(x))
        return best_path


    def do_reroute(self, ev_time):
        """
        """
        if (cfg.ROUTING_MODE == 'spf' or cfg.K_PATH == 1):
            return

        sorted_flows = sorted([fl for fl in self.flowrecs], \
                              key=lambda x: self.flowrecs[x].cnt, reverse=True)
        eleph_flows  = sorted_flows[:cfg.N_ELEPH_FLOWS]
        if (cfg.RESET_ELEPHANT > 0):
            self.old_eleph_flows = {}
        new_eleph_flows = [fl for fl in eleph_flows if (not fl in self.old_eleph_flows)]    # already sorted

        while (len(new_eleph_flows) > 0):
            # Compute max-min fair BW allocation (considering old_eleph_flows only)
            self.comB()
            # Pop the new eleph flow that has largest count
            fl = new_eleph_flows.pop(0)
            # Calculate OAB for each path
            src     = self.flowrecs[fl].src_node
            dst     = self.flowrecs[fl].dst_node
            path_set = self.path_db[(src, dst)]
            best_path = self.get_best_reroute_path(path_set)
            # Commit path change of the selected new eleph flow
            flowobj = self.sim_core.flows[fl]
            if (not flowobj.path == best_path):
                old_path        = flowobj.path
                old_links       = flowobj.links
                new_path        = best_path
                new_links       = self.sim_core.get_links_on_path(best_path)
                # Remove flow from old path
                for lk in old_links:
                    linkobj = self.sim_core.linkobjs[lk]
                    linkobj.n_active_flows -= 1
                    linkobj.remove_flow_entry(fl[0], fl[1])
                for nd in old_path:
                    nodeobj = self.sim_core.nodeobjs[nd]
                    nodeobj.remove_flow_entry(fl[0], fl[1])

                # Install flow to new path
                self.sim_core.install_entries_to_path(new_path, new_links, fl[0], fl[1])
                flowobj.path = new_path
                flowobj.links = new_links
                for lk in new_links:
                    linkobj = self.sim_core.linkobjs[lk]
                    linkobj.n_active_flows += 1
                # Update controller
                self.flowrecs[fl].path = new_path
                # Increment counter
                flowobj.reroute += 1
                self.sim_core.n_rerouted_flows += 1

            self.old_eleph_flows[fl] = 0.0


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


    def find_path_random(self, src_node, dst_node):
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


    def find_path_fe(self, src_node, dst_node):
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
                size    =   self.noderecs[nd].table_size
                objval  +=  float(size) / (size - usage)

            if (objval < best_objval):
                best_path = path

        return best_path    # Will return [] is no path available


    def find_path_ecmp(self, src_node, dst_node):
        """
        """
        nd  = src_node
        path = []
        while True:            
            path.append(nd)
            if (nd == dst_node):
                break
            else:
                nd = rd.choice(self.ecmp_db[(src_node, dst_node)][nd])
        
        return path


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
        elif (cfg.ROUTING_MODE == 'random'):
            path = self.find_path_random(src_node, dst_node)
        elif (cfg.ROUTING_MODE == 'fe'):
            path = self.find_path_fe(src_node, dst_node)
        else:
            path = self.find_path_random(src_node, dst_node)    # default to 'random'
        return path


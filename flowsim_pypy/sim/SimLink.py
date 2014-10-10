#!/usr/bin/python
# -*- coding: utf-8 -*-

"""sim/SimSwitch.py: Class that keeps the forwarding table, and other parameters, of a switch.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

# Built-in modules
# Third-party modules
# User-defined modules
import SimConfig as cfg


class SimLink:
    """Class of a link in the network.

    Attributes:
        cap (float64): Capacity in Bps
        flows (list of 2-tuple of netaddr.IPAddress):
            Flows running on the link.
            Key: 2-tuple (src_ip, dst_ip)
            Value: A pointer to item at SimCore.flows.
    """

    def __init__(self, **kwargs):
        """
        """
        self.node1 = kwargs.get('node1', 'noname')
        self.node2 = kwargs.get('node2', 'noname')
        self.cap = kwargs.get('cap', 1e9) * cfg.CAP_UNIT if (not cfg.OVERRIDE_CAP)     \
                   else cfg.CAP_PER_LINK * cfg.CAP_UNIT
        self.flows = {}

        # These variables are used in calc_flow_rates
        self.unasgn_b       = self.cap
        self.n_active_flows = 0
        self.n_unsagn_flows = 0
        self.bw_per_flow    = 0.0
        self.processed      = False


    def __str__(self):
        """
        """
        ret =   'Link (%s, %s):\n'                    %(self.node1, self.node2) +     \
                '\tcap: %.6e\n'                       %(self.cap) +   \
                '\t# of registered flows:%d\n'        %(len(self.flows)) +  \
                '\t# of active flows:%d\n'            %(self.n_active_flows)+  \
                '\t# of idling flows:%d\n'            %(len([fl for fl in self.flows \
                                                           if self.flows[fl].status=='idle']))
        return ret


    def install_entry(self, src_ip, dst_ip, flow_item):
        """
        """
        self.flows[(src_ip, dst_ip)] = flow_item


    def get_n_active_flows(self):
        """Get number of active flows running on this link.

        Args:
            None

        Return:
            int: # of active flows

        """
        ret = 0
        ret = self.n_active_flows

        return ret


    def remove_flow_entry(self, src_ip, dst_ip):
        """
        """
        del self.flows[(src_ip, dst_ip)]

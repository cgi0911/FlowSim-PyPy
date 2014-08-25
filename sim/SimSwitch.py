#!/usr/bin/python
# -*- coding: utf-8 -*-

"""sim/SimSwitch.py: Class of switch profile the forwarding table, and other parameters, of a switch.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

# Built-in modules
# Third-party modules
# User-defined modules
from config import *


class SimSwitch:
    """Class of a switching node in the network.

    Attributes:
        table (dict: 2-tuple netaddr.IpAddress -> float64): Forwarding table
        tablesize (int): Maximum number of flow entries allowed in table
        n_hosts (int): Number of hosts connected with this edge switch.

    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'noname')
        self.table = {}     # key is 2-tuple (src_ip, dst_ip), value is byte counter

        self.table_size = kwargs.get('table_size', 1000) if (not OVERRIDE_TABLESIZE)    \
                          else TABLESIZE_PER_SW

        self.n_hosts = kwargs.get('n_hosts', 100) if (not OVERRIDE_N_HOSTS)     \
                       else N_HOSTS_PER_SW

    def __str__(self):
        ret = 'Switch name %s\n'                    %(self.name) + \
              '    table_size: %s\n'                %(self.table_size) + \
              '    n_hosts: %s\n'                   %(self.n_hosts) + \
              '    current # of entries: %s\n'      %(len(self.table))
        return ret

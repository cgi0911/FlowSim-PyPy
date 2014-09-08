#!/usr/bin/python
# -*- coding: utf-8 -*-

"""sim/SimSwitch.py: Class that keeps the forwarding table, and other parameters, of a switch.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

# Built-in modules
# Third-party modules
# User-defined modules
from config import *


class SimLink:
    """Class of a link in the network.

    Attributes:
      cap (float64): Capacity in Bps
      flows (list of 2-tuple of netaddr.IPAddress): Flows running on the link (may not be active)
    """

    def __init__(self, **kwargs):
        self.node1 = kwargs.get('node1', 'noname')
        self.node2 = kwargs.get('node2', 'noname')
        self.cap = kwargs.get('cap', 1e9) if (not cfg.OVERRIDE_CAP)     \
                   else cfg.CAP_PER_LINK
        self.flows = []

    def __str__(self):
        ret =   'Link (%s, %s):\n'                    %(self.node1, self.node2) +     \
                '\tcap: %.6e\n'                       %(self.cap) +   \
                '\t# of registered flows:%d\n'        %(len(self.flows)) +  \
                '\t# of active flows:%d\n'            %(len([fl for fl in self.flows \
                                                           if fl.status=='active']))+  \
                '\t# of idling flows:%d\n'            %(len([fl for fl in self.flows \
                                                           if fl.status=='idle']))
        return ret


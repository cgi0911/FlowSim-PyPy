#!/usr/bin/python
# -*- coding: utf-8 -*-

"""sim/SimEvent.py: Class for flow profile that records attributes and stats of individual flows.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'


# Built-in modules

# Third-party modules
import netaddr as na
# User-defined modules


class FlowProf:
    """Class for a flow profile. Will be referred by SimCore and Controller.

    Attributes:
      src_ip (netaddr.IPAddress)
      dst_ip (netaddr.IPAddress)
      src_node (str)
      dst_node (str)
      path (list of str)
      flow_size (float64): Total number of bytes to be transmitted
      flow_rate (float64): Maximum data rate for this flow (limited by source & dest)
      curr_rate (float64): Current data rate for this flow (limited by network)
      bytes_left (float64): Bytes not yet sent at current time
      bytes_sent (float64): Bytes already sent at current time
      status (str): Status of the flow ('requesting', 'active', 'idle')

    """

    def __init__(self,
                 src_ip=na.IPAddress(0),
                 dst_ip=na.IPAddress(0),
                 src_node='',
                 dst_node='',
                 path=[],
                 flow_size=0.0,
                 flow_rate=1.0,
                 curr_rate=0.0,
                 bytes_left=0.0,
                 bytes_sent=0.0,
                 status='requesting'):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_node = src_node
        self.dst_node = dst_node
        self.path = path
        self.flow_size = flow_size
        self.flow_rate = flow_rate
        self.curr_rate = curr_rate
        self.bytes_left = bytes_left
        self.bytes_sent = bytes_sent
        self.status = status

    def __str__(self):
        # Header is tuple of (src_ip, dst_ip); attribute name and value shown line by line
        ret = 'Flow (%s -> %s)\n'         %(self.src_ip, self.dst_ip) + \
              '    status: %s\n'        %(self.status) + \
              '    src_node: %s\n'      %(self.src_node) + \
              '    dst_node: %s\n'      %(self.dst_node) + \
              '    path: %s\n'          %(self.path) + \
              '    flow_size: %.6f\n'   %(self.flow_size) + \
              '    flow_rate: %.6f\n'   %(self.flow_rate) + \
              '    curr_rate: %.6f\n'   %(self.curr_rate) + \
              '    bytes_left: %.6f\n'  %(self.bytes_left) + \
              '    bytes_sent: %.6f\n'  %(self.bytes_sent)

        return ret



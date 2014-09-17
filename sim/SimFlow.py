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


class SimFlow:
    """Class for a flow profile. Will be referred by SimCore and Controller.

    Attributes:
        src_ip (netaddr.IPAddress)
        dst_ip (netaddr.IPAddress)
        src_node (str)
        dst_node (str)
        path (list of str)
        flow_size (float64): Total number of bytes to be transmitted
        flow_rate (float64): Maximum data rate for this flow (limited by source & dest) in Bps
        curr_rate (float64): Current data rate for this flow (limited by network) in Bps
        bytes_left (float64): Bytes not yet sent at current time
        bytes_sent (float64): Bytes already sent at current time
        status (str): Status of the flow ('requesting', 'active', 'idle')
        arrive_time (float64): Time when flow arrives at edge switch (before it is requested and installed)
        install_time (float64): Time when flow entries are installed to path switches
        end_time (float64): Time when flow transmission completes
        remove_time (float64): Time when flow entries are removed from path switches
        update_time (float64): Time when flow's status or rate is last updated
        duration (float64): Flow duration
        resend (int): # of resent EvPacketIn events before flow got admitted
        reroute (int): # of times this flow being rerouted

    Extra Notes:
        1. Possible flow status: 'requesting', 'active', 'idle'

    """

    def __init__(   self,
                    src_ip=na.IPAddress(0),
                    dst_ip=na.IPAddress(0),
                    src_node='',
                    dst_node='',
                    path=[],
                    flow_size=0.0,
                    flow_rate=0.0,
                    curr_rate=0.0,
                    avg_rate=0.0,
                    bytes_left=0.0,
                    bytes_sent=0.0,
                    status='requesting',
                    arrive_time = -1.0,
                    install_time = -1.0,
                    end_time = -1.0,
                    remove_time = -1.0,
                    update_time = -1.0,
                    duration = -1.0,
                    resend = 0,
                    reroute = 0
                ):
        """

        Extra Notes:
            For any time-related attributes, -1.0 means not decided.
        """
        self.src_ip         = src_ip
        self.dst_ip         = dst_ip
        self.src_node       = src_node
        self.dst_node       = dst_node
        self.path           = path
        self.flow_size      = flow_size
        self.flow_rate      = flow_rate
        self.curr_rate      = curr_rate
        self.avg_rate       = avg_rate
        self.bytes_left     = bytes_left
        self.bytes_sent     = bytes_sent
        self.status         = status
        self.arrive_time    = arrive_time
        self.install_time   = install_time
        self.end_time       = end_time
        self.remove_time    = remove_time
        self.update_time    = update_time
        self.duration       = duration
        self.resend         = resend
        self.reroute        = reroute

    def __str__(self):
        # Header is tuple of (src_ip, dst_ip); attribute name and value shown line by line
        ret =   'Flow (%s -> %s)\n'         %(self.src_ip, self.dst_ip) + \
                '    status: %s\n'          %(self.status) + \
                '    src_node: %s\n'        %(self.src_node) + \
                '    dst_node: %s\n'        %(self.dst_node) + \
                '    path: %s\n'            %(self.path) + \
                '    flow_size: %.6f\n'     %(self.flow_size) + \
                '    flow_rate: %.6f\n'     %(self.flow_rate) + \
                '    curr_rate: %.6f\n'     %(self.curr_rate) + \
                '    avg_rate: %.6f\n'      %(self.avg_rate) + \
                '    bytes_left: %.6f\n'    %(self.bytes_left) + \
                '    bytes_sent: %.6f\n'    %(self.bytes_sent) + \
                '    arrive_time: %.6f\n'   %(self.arrive_time) + \
                '    install_time: %.6f\n'  %(self.install_time) + \
                '    end_time: %.6f\n'      %(self.end_time) + \
                '    remove_time: %.6f\n'   %(self.remove_time) + \
                '    update_time: %.6f\n'   %(self.update_time) + \
                '    duration: %.6f\n'      %(self.duration) + \
                '    resend: %d\n'          %(self.resend) + \
                '    reroute: %d\n'         %(self.reroute)

        return ret



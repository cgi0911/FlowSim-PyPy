#!/usr/bin/python
# -*- coding: utf-8 -*-

"""sim/SimEvent.py: Define various event classes that are used for discrete event-based simulation.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'


# Built-in modules
import inspect
# Third-party modules
import netaddr as na
# User-defined modules
from config import *


class SimEvent:
    """Base class of events, which is going to be queued in event queue under SimCore.

    Attributes:
        ev_type (str): Explicitly illustrates the event's type
                  (FlowArrival, FlowEnd, CollectStats, etc.)
        ev_time (float64): Time of event occurence

    Extra Notes:
        1. Event types:
           FlowArrival, PacketIn, FlowInstall, FlowEnd,
           IdleTimeout, HardTimeout, CollectStats, DoReroute

    """

    def __init__(self, **kwargs):
        """Constructor of Event class. Will be overriden by child classes.
        """
        self.ev_type = kwargs.get('ev_type', 'notype')
        self.ev_time = kwargs.get('ev_time', 0.0)

    def __str__(self):
        ret = 'Event type: %s\n' %(self.ev_type)     # Header line shows event type
        ret += '    Event time: %.6f\n' %(self.ev_time)

        attrs = ([attr for attr in dir(self)
                  if not attr.startswith('__') and not attr=='ev_type'
                  and not attr=='ev_time'])
                                                    # Print attribute name and value line by line
        for attr in attrs:
            ret += '    %s: %s\n' %(attr, getattr(self, attr))
        return ret

    def __repr__(self):
        return str(self)


class EvFlowArrival(SimEvent):
    """Event that signals arrival of a flow, and will trigger a PacketIn event.

    Attributes:
        ev_type (str): 'EvFlowArrival'
        src_ip (netaddr.ip.IPAddress): Source IP
        dst_ip (netaddr.ip.IPAddress): Destination IP
        flow_size (float64): Number of bytes to be transmitted in this flow.
        flow_rate (float64): The maximum data rate (bytes per sec) this flow can transmit.
                             Currently not supported.
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, ev_type='EvFlowArrival', ev_time=kwargs.get('ev_time', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))
        self.flow_size = kwargs.get('flow_size', 0.0)
        self.flow_rate = kwargs.get('flow_rate', 0.0)


class EvPacketIn(SimEvent):
    """Event that signals an OpenFlow packet-in request's arrival at the controller.

    Attributes:
        ev_type (str): 'EvPacketIn'
        src_ip (netaddr.ip.IPAddress): Source IP
        dst_ip (netaddr.ip.IPAddress): Destination IP
        src_node (string): Source SW
        dst_node (string): Dest SW
        resend (int): Resend times
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, ev_type='EvPacketIn', ev_time=kwargs.get('ev_time', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))
        self.src_node = kwargs.get('src_node', 'unknown')
        self.dst_node = kwargs.get('dst_node', 'unknown')
        self.resend = 0


class EvFlowInstall(SimEvent):
    """Event that signals installation of a flow at switches along selected path.

    Attributes:
        ev_type (str): 'EvFlowInstall'
        src_ip (netaddr.ip.IPAddress): Source IP
        dst_ip (netaddr.ip.IPAddress): Destination IP
        src_node (string): Source SW
        dst_node (string): Dest SW
        path (list of str): An ordered list of switch names along the path.
        resend (int): Resend times
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, ev_type='EvFlowInstall', ev_time=kwargs.get('ev_time', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))
        self.src_node = kwargs.get('src_node', 'unknown')
        self.dst_node = kwargs.get('dst_node', 'unknown')
        self.path = kwargs.get('path', [])
        self.resend = 0


class EvFlowEnd(SimEvent):
    """Event that signals end of a flow, and will trigger a IdleTimeout event.

    Attributes:
        ev_type (str): 'EvFlowEnd'
        src_ip (netaddr.ip.IPAddress): Source IP
        dst_ip (netaddr.ip.IPAddress): Destination IP
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, ev_type='EvFlowEnd', ev_time=kwargs.get('ev_time', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))


class EvIdleTimeout(SimEvent):
    """Event that signals idle timeout of a flow and consequent removal of its entries.

    Attributes:
        ev_type (str): 'EvIdleTimeout'
        src_ip (netaddr.ip.IPAddress): Source IP
        dst_ip (netaddr.ip.IPAddress): Destination IP
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, ev_type='EvIdleTimeout', ev_time=kwargs.get('ev_time', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))


class EvHardTimeout(SimEvent):
    """Event that signals hard timeout of a flow and consequent re-request of its entries.

    Attributes:
        ev_type (str): 'EvHardTimeout'
        src_ip (netaddr.ip.IPAddress): Source IP
        dst_ip (netaddr.ip.IPAddress): Destination IP

    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, ev_type='EvHardTimeout', ev_time=kwargs.get('ev_time', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))


class EvPullStats(SimEvent):
    """Event that signals controller's pulling flow-level statistics.

    Attributes:
        ev_type (str): 'EvPullStats'
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, ev_type='EvPullStats', ev_time=kwargs.get('ev_time', 0.0))


class EvLogLinkUtil(SimEvent):
    """Event that signals the simulation core to log link utilizations.

    Attributes:
        ev_type (str): 'EvLogLinkUtil'
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, ev_type='EvLogLinkUtil', ev_time=kwargs.get('ev_time', 0.0))


class EvLogTableUtil(SimEvent):
    """Event that signals the simulation core to log link utilizations.

    Attributes:
        ev_type (str): 'EvLogLinkUtil'
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, ev_type='EvLogTableUtil', ev_time=kwargs.get('ev_time', 0.0))
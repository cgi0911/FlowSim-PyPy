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
      evtype (str): Explicitly illustrates the event's type
                  (FlowArrival, FlowEnd, CollectStats, etc.)

    Extra Notes:
        1. Event types:
           FlowArrival, FlowInstall, FlowEnd, IdleTimeout, HardTimeout, CollectStats, DoReroute

    """

    def __init__(self, evtype='VoidEventType'):
        """Constructor of Event class. Will be overriden by child classes.
        """
        self.evtype = evtype

    def __str__(self):
        ret = 'Event type: %s\n' %(self.evtype)     # Header line shows event type

        attrs = ([attr for attr in dir(self)
                  if not attr.startswith('__') and not attr=='evtype'])
                                                    # Print attribute name and value line by line
        for attr in attrs:
            ret += '    %s: %s\n' %(attr, getattr(self, attr))
        return ret

    def __repr__(self):
        return str(self)


class EvFlowArrival(SimEvent):
    """Event that signals arrival of a flow, and will trigger a PacketIn event.

    Attributes:
      evtype (str): 'FlowArrival'
      src_ip (netaddr.ip.IPAddress): Source IP
      dst_ip (netaddr.ip.IPAddress): Destination IP
      flow_size (float64): Number of bytes to be transmitted in this flow.
      flow_rate (float64): The maximum data rate (bytes per sec) this flow can transmit.
    """

    def __init__(self,
                 src_ip=na.IPAddress(0),
                 dst_ip=na.IPAddress(0),
                 flow_size=0.0,
                 flow_rate=1.0):
        SimEvent.__init__(self, 'FlowArrival')
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.flow_size = flow_size
        self.flow_rate = flow_rate


class EvPacketIn(SimEvent):
    """Event that signals an OpenFlow packet-in request's arrival at the controller.

    Attributes:
      evtype (str): 'PacketIn'
      src_ip (netaddr.ip.IPAddress): Source IP
      dst_ip (netaddr.ip.IPAddress): Destination IP
    """

    def __init__(self, src_ip=na.IPAddress(0), dst_ip=na.IPAddress(0)):
        SimEvent.__init__(self, 'PacketIn')
        self.src_ip = src_ip
        self.dst_ip = dst_ip


class EvFlowInstall(SimEvent):
    """Event that signals installation of a flow at switches along selected path.

    Attributes:
      evtype (str): 'FlowInstall'
      src_ip (netaddr.ip.IPAddress): Source IP
      dst_ip (netaddr.ip.IPAddress): Destination IP
      path (list of str): An ordered list of switch names along the path.
    """

    def __init__(self, src_ip=na.IPAddress(0), dst_ip=na.IPAddress(0),
                 path=[] ):
        SimEvent.__init__(self, 'FlowInstall')
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.path = path


class EvFlowEnd(SimEvent):
    """Event that signals end of a flow, and will trigger a IdleTimeout event.

    Attributes:
      evtype (str): 'FlowEnd'
      src_ip (netaddr.ip.IPAddress): Source IP
      dst_ip (netaddr.ip.IPAddress): Destination IP
    """

    def __init__(self, src_ip=na.IPAddress(0), dst_ip=na.IPAddress(0)):
        SimEvent.__init__(self, 'FlowEnd')
        self.src_ip = src_ip
        self.dst_ip = dst_ip


class EvIdleTimeout(SimEvent):
    """Event that signals idle timeout of a flow and consequent removal of its entries.

    Attributes:
      evtype (str): 'IdleTimeout'
      src_ip (netaddr.ip.IPAddress): Source IP
      dst_ip (netaddr.ip.IPAddress): Destination IP
    """

    def __init__(self, src_ip=na.IPAddress(0), dst_ip=na.IPAddress(0)):
        SimEvent.__init__(self, 'IdleTimeout')
        self.src_ip = src_ip
        self.dst_ip = dst_ip


class EvCollectStats(SimEvent):
    """Event that signals controller's pulling flow-level statistics.

    Attributes:
      evtype (str): 'CollectStats'
    """

    def __init__(self):
        SimEvent.__init__(self, 'CollectStats')
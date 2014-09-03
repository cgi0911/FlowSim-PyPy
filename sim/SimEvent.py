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
        evtime (float64): Time of event occurence

    Extra Notes:
        1. Event types:
           FlowArrival, PacketIn, FlowInstall, FlowEnd,
           IdleTimeout, HardTimeout, CollectStats, DoReroute

    """

    def __init__(self, **kwargs):
        """Constructor of Event class. Will be overriden by child classes.
        """
        self.evtype = kwargs.get('evtype', 'notype')
        self.evtime = kwargs.get('evtime', 0.0)

    def __str__(self):
        ret = 'Event type: %s\n' %(self.evtype)     # Header line shows event type
        ret += '    Event time: %.6f\n' %(self.evtime)

        attrs = ([attr for attr in dir(self)
                  if not attr.startswith('__') and not attr=='evtype'
                  and not attr=='evtime'])
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

    def __init__(self, **kwargs):
        SimEvent.__init__(self, evtype='FlowArrival', evtime=kwargs.get('evtime', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))
        self.flow_size = kwargs.get('flow_size', 0.0)
        self.flow_rate = kwargs.get('flow_rate', 0.0)


class EvPacketIn(SimEvent):
    """Event that signals an OpenFlow packet-in request's arrival at the controller.

    Attributes:
        evtype (str): 'PacketIn'
        src_ip (netaddr.ip.IPAddress): Source IP
        dst_ip (netaddr.ip.IPAddress): Destination IP
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, evtype='PacketIn', evtime=kwargs.get('evtime', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))


class EvFlowInstall(SimEvent):
    """Event that signals installation of a flow at switches along selected path.

    Attributes:
        evtype (str): 'FlowInstall'
        src_ip (netaddr.ip.IPAddress): Source IP
        dst_ip (netaddr.ip.IPAddress): Destination IP
        path (list of str): An ordered list of switch names along the path.
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, evtype='FlowInstall', evtime=kwargs.get('evtime', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))
        self.path = kwargs.get('path', [])


class EvFlowEnd(SimEvent):
    """Event that signals end of a flow, and will trigger a IdleTimeout event.

    Attributes:
        evtype (str): 'FlowEnd'
        src_ip (netaddr.ip.IPAddress): Source IP
        dst_ip (netaddr.ip.IPAddress): Destination IP
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, evtype='FlowEnd', evtime=kwargs.get('evtime', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))


class EvIdleTimeout(SimEvent):
    """Event that signals idle timeout of a flow and consequent removal of its entries.

    Attributes:
        evtype (str): 'IdleTimeout'
        src_ip (netaddr.ip.IPAddress): Source IP
        dst_ip (netaddr.ip.IPAddress): Destination IP
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, evtype='IdleTimeout', evtime=kwargs.get('evtime', 0.0))
        self.src_ip = kwargs.get('src_ip', na.IPAddress(0))
        self.dst_ip = kwargs.get('dst_ip', na.IPAddress(0))


class EvHardTimeout(SimEvent):
    """Event that signals hard timeout of a flow and consequent re-request of its entries.

    Attributes:

    """

    def __init__(self, **kwargs):
        pass


class EvCollectStats(SimEvent):
    """Event that signals controller's pulling flow-level statistics.

    Attributes:
      evtype (str): 'CollectStats'
    """

    def __init__(self, **kwargs):
        SimEvent.__init__(self, evtype='CollectStats', evtime=kwargs.get('evtime', 0.0))
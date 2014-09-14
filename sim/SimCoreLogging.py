#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimCore.py: Class SimCoreLogging, containing logging-related codes for SimCore.
Inherited by SimCore.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

# Built-in modules
import os
import csv
from heapq import heappush, heappop
from math import ceil, log
from time import time
# Third-party modules
import networkx as nx
import netaddr as na
import pandas as pd
import numpy as np
# User-defined modules
from config import *
from SimCtrl import *
from SimFlowGen import *
from SimFlow import *
from SimSwitch import *
from SimLink import *
from SimEvent import *


class SimCoreLogging:
    """
    """

    def rmse(self, myList):
        return 0.0

    def log_table_util(self, ev_time):
        """
        Extra Notes:
            Fields of a table util. record (in column order):
            - Time, mean, rmse, min, max, q1, q3, median
            - Table utilization of each node
        """
        ret = {'time': ev_time}
        list_util = []

        # Retrieve each node's utilization
        for nd in self.topo.nodes():
            nd_util = self.topo.node[nd]['item'].get_util()
            ret[nd] = nd_util
            list_util.append(nd_util)

        # Calculate statistics
        ret['mean'] = np.mean(list_util)
        ret['rmse'] = self.rmse(list_util)
        ret['min'] = np.mean(list_util)
        ret['max'] = np.max(list_util)
        ret['q1'] = np.percentile(list_util, 25)
        ret['q3'] = np.percentile(list_util, 75)
        ret['median'] = np.percentile(list_util, 50)

        return ret


    def log_flow_stats(self, flow_item):
        """
        """
        ret = {}

        for fld in cfg.LOG_FLOW_STATS_FIELDS:
            ret[fld] = getattr(flow_item, fld)

        return ret


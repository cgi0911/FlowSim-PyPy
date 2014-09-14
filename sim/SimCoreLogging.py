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

    def __init__(self):
        """Constructor of SimCoreLogging class.
        This constructor includes initialization codes for bookeeping and logging parts
        of SimCore.

        Args:
            None

        """
        # Lists for keeping records (link util., table util., and flow stats)
        self.link_util_recs = []
        self.table_util_recs = []
        self.flow_stats_recs = []

        # File paths and names for csv log files
        if ( not os.path.exists(cfg.LOG_DIR) ):
            os.mkdir(cfg.LOG_DIR)
        self.fn_link_util = os.path.join(cfg.LOG_DIR, 'link_util.csv')
        self.fn_table_util = os.path.join(cfg.LOG_DIR, 'table_util.csv')
        self.fn_flow_stats = os.path.join(cfg.LOG_DIR, 'flow_stats.csv')

        # Column names for csv log files
        self.col_link_util = ['time', 'mean', 'stddev', 'min', 'max', 'q1', 'q3', 'median', \
                              'throughput'] + \
                              [str(lk) for lk in self.topo.edges()]
        self.col_table_util = ['time', 'mean', 'stddev', 'min', 'max', 'q1', 'q3', 'median'] + \
                              [str(nd) for nd in self.topo.nodes()]


        # Byte counters for each link
        self.link_byte_cnt = {}
        for lk in self.topo.edges():
            self.link_byte_cnt[lk] = 0.0


    def log_link_util(self, ev_time):
        """
        """
        ret = {'time': np.round(ev_time, 3)}
        list_usage = []
        list_util = []

        # Iterate over all flows
        for fl in self.flows:
            if (not self.flows[fl].status == 'active'):
                continue

            links_on_path = self.get_links_on_path(self.flows[fl].path)
            bytes_sent = self.flows[fl].curr_rate * \
                         (ev_time - self.flows[fl].update_time)

            for lk in links_on_path:
                self.link_byte_cnt[lk] += bytes_sent

            self.flows[fl].bytes_sent += bytes_sent
            self.flows[fl].bytes_left -= bytes_sent
            self.flows[fl].update_time = ev_time

        for lk in self.link_byte_cnt:
            ret[str(lk)] = self.link_byte_cnt[lk] / \
                           (self.get_link_attr(lk[0], lk[1], 'cap') * cfg.PERIOD_LOGGING)

        list_usage = [self.link_byte_cnt[lk] for lk in self.link_byte_cnt]
        list_util = [ret[str(lk)] for lk in self.link_byte_cnt ]

        # Calculate statistics
        ret['mean'] = np.mean(list_util)
        ret['stddev'] = np.std(list_util)
        ret['min'] = np.mean(list_util)
        ret['max'] = np.max(list_util)
        ret['q1'] = np.percentile(list_util, 25)
        ret['q3'] = np.percentile(list_util, 75)
        ret['median'] = np.percentile(list_util, 50)
        ret['throughput'] = np.sum(list_usage) / cfg.PERIOD_LOGGING

        # Reset byte counters
        for lk in self.link_byte_cnt:
            self.link_byte_cnt[lk] = 0.0

        return ret


    def log_table_util(self, ev_time):
        """Log table utilization data. Called ever cfg.PERIOD_LOGGING.

        Extra Notes:
            Fields of a table util. record (in column order):
            - Time, mean, rmse, min, max, q1, q3, median
            - Table utilization of each node
        """
        ret = {'time': np.round(ev_time, 3)}
        list_util = []

        # Retrieve each node's utilization
        for nd in self.topo.nodes():
            nd_util = self.topo.node[nd]['item'].get_util()
            ret[nd] = nd_util
            list_util.append(nd_util)

        # Calculate statistics
        ret['mean'] = np.mean(list_util)
        ret['stddev'] = np.std(list_util)
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


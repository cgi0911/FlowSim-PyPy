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
from SimConfig import *
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
        self.fn_link_util   =   os.path.join(cfg.LOG_DIR, 'link_util.csv')
        self.fn_table_util  =   os.path.join(cfg.LOG_DIR, 'table_util.csv')
        self.fn_flow_stats  =   os.path.join(cfg.LOG_DIR, 'flow_stats.csv')
        self.fn_summary     =   os.path.join(cfg.LOG_DIR, 'summary.csv')
        self.fn_config      =   os.path.join(cfg.LOG_DIR, 'config.txt')

        # Column names for csv log files
        self.col_link_util = ['time', 'mean', 'stdev', 'min', 'max', 'q1', 'q3', 'median', \
                              'throughput'] + [str(lk) for lk in self.links]
        self.col_table_util = ['time', 'mean', 'stdev', 'min', 'max', 'q1', 'q3', 'median'] + \
                              [str(nd) for nd in self.nodes]
        self.col_flow_stats = ['src_ip', 'dst_ip', 'src_node', 'dst_node', 'flow_size', \
                               'bytes_sent', 'bytes_left', 'avg_rate', 'curr_rate', \
                               'arrive_time', 'install_time', 'end_time', 'remove_time', \
                               'update_time', 'duration', 'status', 'resend', 'reroute']
        # Column names for those who are going to be averaged and logged
        self.col_avg_link_util  =   ['mean', 'stdev', 'min', 'max', 'q1', 'q3', 'median', \
                                    'throughput'] + [str(lk) for lk in self.links]
        self.col_avg_table_util =   ['mean', 'stdev', 'min', 'max', 'q1', 'q3', 'median'] + \
                                    [str(nd) for nd in self.nodes]
        self.col_avg_flow_stats =   ['flow_size', 'avg_rate', 'resend', 'reroute']

        # Byte counters for each link
        self.link_byte_cnt = {}
        for lk in self.links:
            self.link_byte_cnt[lk] = 0.0

        # Parameters & counters for summary
        self.summary_message = ''   # A string that stores the whole summary message
        self.n_EvPacketIn = 0
        self.n_EvFlowArrival = 0
        self.n_EvFlowEnd = 0
        self.n_EvIdleTimeout = 0
        self.n_Reject = 0
        self.exec_st_time = self.exec_ed_time = self.exec_time = 0.0


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
                           (self.linkobjs[lk].cap * cfg.PERIOD_LOGGING)

        list_usage = [self.link_byte_cnt[lk] for lk in self.link_byte_cnt]
        list_util = [ret[str(lk)] for lk in self.link_byte_cnt ]

        # Calculate statistics
        ret['mean'] = np.mean(list_util)
        ret['stdev'] = np.std(list_util)
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
            nd_util = self.nodeobjs[nd].get_util()
            ret[nd] = nd_util
            list_util.append(nd_util)

        # Calculate statistics
        ret['mean'] = np.mean(list_util)
        ret['stdev'] = np.std(list_util)
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

        for fld in self.col_flow_stats:
            ret[fld] = getattr(flow_item, fld)

        return ret


    def dump_link_util(self):
        """
        """
        # Prepare a data frame from records
        df_link_util    = pd.DataFrame.from_records(self.link_util_recs, \
                                                    columns=self.col_link_util)

        # Calculate an average record
        avg_rec = {}
        for col in self.col_avg_link_util:
            avg_rec[col] = np.average(df_link_util[col][cfg.AVG_IGNORE_RECORDS+1:])
        df_link_util = df_link_util.append([{}, avg_rec], ignore_index=True)
                                            # Append an empty line, then avg record

        # Dump data frame to csv file
        df_link_util = df_link_util.to_csv(self.fn_link_util, index=False, \
                            quoting=csv.QUOTE_NONNUMERIC)


    def dump_table_util(self):
        """
        """
        # Prepare a data frame from records
        df_table_util   = pd.DataFrame.from_records(self.table_util_recs, \
                                                    columns=self.col_table_util)

        # Calculate an average record
        avg_rec = {}
        for col in self.col_avg_table_util:
            avg_rec[col] = np.average(df_table_util[col][cfg.AVG_IGNORE_RECORDS+1:])
        df_table_util = df_table_util.append([{}, avg_rec], ignore_index=True)
                                            # Append an empty line, then avg record

        df_table_util.to_csv(self.fn_table_util, index=False, \
                             quoting=csv.QUOTE_NONNUMERIC)


    def dump_flow_stats(self):
        """
        """
        # First, create records for all flows not yet removed from self.flows
        for fl in self.flows:
            self.flow_stats_recs.append(self.log_flow_stats(self.flows[fl]))

        df_flow_stats   = pd.DataFrame.from_records(self.flow_stats_recs, \
                                                    columns=self.col_flow_stats)
        df_flow_stats   = df_flow_stats.sort(['arrive_time'], ascending=True)

        # Calculate an average record
        avg_rec = {}
        for col in self.col_avg_flow_stats:
            avg_rec[col] = np.average(df_flow_stats[col])
        df_flow_stats = df_flow_stats.append([{}, avg_rec], ignore_index=True)
                                            # Append an empty line, then avg record

        df_flow_stats.to_csv(self.fn_flow_stats, index=False, \
                             quoting=csv.QUOTE_NONNUMERIC)


    def dump_summary(self):
        """
        """
        summary_file = open(self.fn_summary, 'w')

        self.summary_message += ('n_EvFlowArrival,%d\n'     %(self.n_EvFlowArrival))
        self.summary_message += ('n_EvPacketIn,%d\n'        %(self.n_EvPacketIn))
        self.summary_message += ('n_Reject,%d\n'            %(self.n_Reject))
        self.summary_message += ('n_EvFlowEnd,%d\n'         %(self.n_EvFlowEnd))
        self.summary_message += ('n_EvIdleTimeout,%d\n'     %(self.n_EvIdleTimeout))
        self.summary_message += ('exec_time,%.6f\n'         %(self.exec_ed_time - self.exec_st_time))

        summary_file.write(self.summary_message)


    def dump_config(self):
        """
        """
        os.system("cp %s %s" %(fn_config, self.fn_config))


    def show_summary(self):
        """
        """
        print
        print '-'*40
        print 'Summary:'
        print '-'*40

        for line in self.summary_message.split('\n'):
            words = line.split(',')
            if words[0] == '':
                continue
            else:
                print ' = '.join(words)

        print


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
from math import ceil
# Third-party modules
import numpy as np
import pprint as pp
# User-defined modules
import SimConfig as cfg


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
        self.link_util_recs     = []
        self.link_flows_recs    = []
        self.table_util_recs    = []
        self.flow_stats_recs    = []

        # File paths and names for csv log files
        if ( not os.path.exists(cfg.LOG_DIR) ):
            os.mkdir(cfg.LOG_DIR)
        self.fn_link_util   =   os.path.join(cfg.LOG_DIR, 'link_util.csv')
        self.fn_link_flows  =   os.path.join(cfg.LOG_DIR, 'link_flows.csv')
        self.fn_table_util  =   os.path.join(cfg.LOG_DIR, 'table_util.csv')
        self.fn_flow_stats  =   os.path.join(cfg.LOG_DIR, 'flow_stats.csv')
        self.fn_summary     =   os.path.join(cfg.LOG_DIR, 'summary.csv')
        self.fn_config      =   os.path.join(cfg.LOG_DIR, 'config.txt')

        # Column names for csv log files
        self.col_link_util  =   ['time', 'mean', 'stdev', 'min', 'max', 'q1', 'q3', 'median', \
                                'throughput'] + [str(lk) for lk in self.links]
        self.col_link_flows =   ['time', 'mean', 'stdev', 'min', 'max', 'q1', 'q3', 'median'] + \
                                [str(lk) for lk in self.links]
        self.col_table_util =   ['time', 'mean', 'stdev', 'min', 'max', 'q1', 'q3', 'median'] + \
                                [str(nd) for nd in self.nodes]
        self.col_flow_stats =   ['src_ip', 'dst_ip', 'src_node', 'dst_node', 'flow_size', \
                                 'bytes_sent', 'bytes_left', 'avg_rate', 'curr_rate', \
                                 'arrive_time', 'install_time', 'end_time', 'remove_time', \
                                 'update_time', 'duration', 'status', 'resend', 'reroute']
        # Column names for those who are going to be averaged and logged
        self.col_avg_link_util  =   ['mean', 'stdev', 'min', 'max', 'q1', 'q3', 'median', \
                                    'throughput'] + [str(lk) for lk in self.links]
        self.col_avg_link_flows =   ['mean', 'stdev', 'min', 'max', 'q1', 'q3', 'median'] + \
                                    [str(lk) for lk in self.links]
        self.col_avg_table_util =   ['mean', 'stdev', 'min', 'max', 'q1', 'q3', 'median'] + \
                                    [str(nd) for nd in self.nodes]
        self.col_avg_flow_stats =   ['flow_size', 'avg_rate', 'resend', 'reroute', 'duration']

        # Record column vectors
        self.col_vec_link_util  = {k: [] for k in self.col_link_util}
        self.col_vec_link_flows = {k: [] for k in self.col_link_flows}
        self.col_vec_table_util = {k: [] for k in self.col_table_util}
        self.col_vec_flow_stats = {k: [] for k in self.col_flow_stats}

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
        self.n_active_flows = 0
        self.exec_st_time = self.exec_ed_time = self.exec_time = 0.0

        # Register CSV dialect
        csv.register_dialect('flowsim', delimiter=',', quoting=csv.QUOTE_NONNUMERIC)


    def log_link_util(self, ev_time):
        """
        """
        ret_util    = {'time': round(ev_time, 3)}
        ret_flows   = {'time': round(ev_time, 3)}
        list_usage  = []
        list_util   = []
        list_flows  = []

        # Iterate over all flows, update these flows
        #for fl in self.flows:
            #if (not self.flows[fl].status == 'active'):     continue

            #flowobj = self.flows[fl]
            #est_end_time, bytes_sent = flowobj.update_flow(ev_time)
            #links_on_path = flowobj.links

            #for lk in links_on_path:
            #    self.link_byte_cnt[lk] += bytes_sent

        # Get link_util and link_flows info
        for lk in self.link_byte_cnt:
            ret_util[str(lk)]   =   self.link_byte_cnt[lk] / \
                                    (self.linkobjs[lk].cap * cfg.PERIOD_LOGGING)
            ret_flows[str(lk)]  =   self.linkobjs[lk].get_n_active_flows()

        # Make lists for averages
        list_usage  = [self.link_byte_cnt[lk] for lk in self.link_byte_cnt]
        list_util   = [ret_util[str(lk)] for lk in self.link_byte_cnt ]
        list_flows  = [ret_flows[str(lk)] for lk in self.link_byte_cnt]

        # Calculate statistics for link_util
        ret_util['mean']        = np.mean(list_util)
        ret_util['stdev']       = np.std(list_util)
        ret_util['min']         = np.min(list_util)
        ret_util['max']         = np.max(list_util)
        ret_util['q1']          = np.percentile(list_util, 25)
        ret_util['q3']          = np.percentile(list_util, 75)
        ret_util['median']      = np.percentile(list_util, 50)
        ret_util['throughput']  = np.sum(list_usage) / cfg.PERIOD_LOGGING
        # Calculate statistics for link_flows
        ret_flows['mean']       = np.mean(list_flows)
        ret_flows['stdev']      = np.std(list_flows)
        ret_flows['min']        = np.min(list_flows)
        ret_flows['max']        = np.max(list_flows)
        ret_flows['q1']         = np.percentile(list_flows, 25)
        ret_flows['q3']         = np.percentile(list_flows, 75)
        ret_flows['median']     = np.percentile(list_flows, 50)

        # Append to column vectors
        for k in ret_util:  self.col_vec_link_util[k].append(ret_util[k])
        for k in ret_flows: self.col_vec_link_flows[k].append(ret_flows[k])

        # Reset byte counters
        for lk in self.link_byte_cnt:
            self.link_byte_cnt[lk] = 0.0

        return ret_util, ret_flows


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
        ret['mean']     = np.mean(list_util)
        ret['stdev']    = np.std(list_util)
        ret['min']      = np.mean(list_util)
        ret['max']      = np.max(list_util)
        ret['q1']       = np.percentile(list_util, 25)
        ret['q3']       = np.percentile(list_util, 75)
        ret['median']   = np.percentile(list_util, 50)

        # Append to column vectors
        for k in ret:   self.col_vec_table_util[k].append(ret[k])

        return ret


    def log_flow_stats(self, flow_item):
        """
        """
        ret = {}

        for fld in self.col_flow_stats:
            ret[fld] = getattr(flow_item, fld)

        # Append to column vectors
        for k in ret:   self.col_vec_flow_stats[k].append(ret[k])

        return ret


    def dump_link_util(self):
        """
        """
        recs        = self.link_util_recs
        col_vecs    = self.col_vec_link_util
        wt          = csv.DictWriter(open(self.fn_link_util, 'wb'), \
                                     fieldnames=self.col_link_util, \
                                     dialect='flowsim')

        # Calculate an average record
        avg_rec = {}
        for col in self.col_avg_link_util:
            pos             = int(len(col_vecs[col]) * cfg.IGNORE_HEAD)
            temp            = col_vecs[col][pos:]
            avg_rec[col]    = float(sum(temp))/len(temp)
        avg_rec['time'] = 'average'

        # Write records to CSV writer line by line
        wt.writeheader()
        wt.writerows(recs)
        wt.writerow({})
        wt.writerow(avg_rec)


    def dump_link_flows(self):
        """
        """
        recs        = self.link_flows_recs
        col_vecs    = self.col_vec_link_flows
        wt          = csv.DictWriter(open(self.fn_link_flows, 'wb'), \
                                     fieldnames=self.col_link_flows, \
                                     dialect='flowsim')

        # Calculate an average record
        avg_rec = {}
        for col in self.col_avg_link_flows:
            pos             = int(len(col_vecs[col]) * cfg.IGNORE_HEAD)
            temp            = col_vecs[col][pos:]
            avg_rec[col]    = float(sum(temp))/len(temp)
        avg_rec['time'] = 'average'

        # Write records to CSV writer line by line
        wt.writeheader()
        wt.writerows(recs)
        wt.writerow({})
        wt.writerow(avg_rec)

    def dump_table_util(self):
        """
        """
        recs        = self.table_util_recs
        col_vecs    = self.col_vec_table_util
        wt          = csv.DictWriter(open(self.fn_table_util, 'wb'), \
                                     fieldnames=self.col_table_util, \
                                     dialect='flowsim')

        # Calculate an average record
        avg_rec = {}
        for col in self.col_avg_table_util:
            pos             = int(len(col_vecs[col]) * cfg.IGNORE_HEAD)
            temp            = col_vecs[col][pos:]
            avg_rec[col]    = float(sum(temp))/len(temp)
        avg_rec['time'] = 'average'

        # Write records to CSV writer line by line
        wt.writeheader()
        wt.writerows(recs)
        wt.writerow({})
        wt.writerow(avg_rec)


    def dump_flow_stats(self):
        """
        """
        recs        = self.flow_stats_recs
        col_vecs    = self.col_vec_flow_stats
        wt          = csv.DictWriter(open(self.fn_flow_stats, 'wb'), \
                                     fieldnames=self.col_flow_stats, \
                                     dialect='flowsim')

        # Records the flows that are not yet removed
        for fl in self.flows:
            recs.append(self.log_flow_stats(self.flows[fl]))

        # Calculate an average record
        avg_rec = {}
        for col in self.col_avg_flow_stats:
            temp            = [ele for ele in col_vecs[col] if (not ele == -1.0)]
            avg_rec[col]    = float(sum(temp))/len(temp)
        avg_rec['src_ip'] = 'average'

        # Write records to CSV writer line by line
        wt.writeheader()
        wt.writerows(recs)
        wt.writerow({})
        wt.writerow(avg_rec)


    def dump_summary(self):
        """
        """
        summary_file = open(self.fn_summary, 'w')

        self.summary_message += ('ROUTING_MODE,%s\n'        %(cfg.ROUTING_MODE))
        if (cfg.ROUTING_MODE == 'tablelb'):
            self.summary_message += ('    K_PATH,%s\n'          %(cfg.K_PATH))
            self.summary_message += ('    K_PATH_METHOD,%s\n'   %(cfg.K_PATH_METHOD))
        self.summary_message += ('DO_REROUTE,%s\n'          %(cfg.DO_REROUTE))
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
        os.system("cp ./sim/SimConfig.py %s" %(self.fn_config))


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


#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimCore.py: Class SimCoreCalculation, containing flow rate recalculation functions.
Inherited by SimCore.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

# Built-in modules
# Third-party modules
# User-defined modules
import SimConfig as cfg

class SimCoreCalculation:
    """Flow rate calculation-related codes for SimCore class.
    """
    def __init__(self):
        """
        """
        self.sorted_flows = []
            # A sorted list of flows (in ascending order of flow_rate)
            # Each element is a 3-tuple: (flow_rate, flowobj, flow_key)


    def sorted_flows_insert(self, flow_rate, flowobj, flow_key):
        """
        """
        # If source rate is unlimited, we can simply put an 'inf' in the sorted_flows list.
        if (cfg.SRC_LIMITED == 0):
            self.sorted_flows.append((float('inf'), flowobj, flow_key))
            return

        # Or else, we need to have the list sorted in ascending order of flow source rate.
        # Here we manually implement binary search.
        # Why? Although bisect library implemets the search algorithm, but it requires a
        # separated sorted_keys list, which is not what I wanted.
        lo  = 0
        hi  = len(self.sorted_flows)
        mid = 0
        while (lo < hi):    # O(log n)
            mid = (lo + hi) / 2     # Integer
            mid_rate = self.sorted_flows[mid][0]     # First element of the 3-tuple
            if (mid_rate < flow_rate):
                lo = mid + 1
            elif (mid_rate > flow_rate):
                hi = mid
            else:
                break

        self.sorted_flows.insert(mid, (flow_rate, flowobj, flow_key) )  # O(n)


    def sorted_flows_remove(self, flow_key):
        """
        """
        for i in range(len(self.sorted_flows)):
            # Since flow_rate may not be unique, I still implemented a linear search.
            # It's done only once per EvFlowEnd so doesn't matter much.
            if (self.sorted_flows[i][2] == flow_key):
                self.sorted_flows.pop(i)
                return


    def update_all_flows(self, ev_time):
        """
        """
        for fl in self.flows:
            flowobj = self.flows[fl]
            bytes_recent = flowobj.update_flow(ev_time)

            if (flowobj.status == 'active'):
                for lk in flowobj.links:
                    # Update link byte counters
                    self.link_byte_cnt[lk]  += bytes_recent


    #def calc_flow_rates_src_limited(self, ev_time):
    def calc_flow_rates(self, ev_time):
        """Calculate flow rates (according to DevoFlow Algorithm 1), but is aware of
        each flow's source rate constraints.

        Args:
            None

        Returns:
            None. But will update flow and link statistics, as well as identify next ending
            flow and its estimated end time.

        Extra Notes:
            - If cfg.SRC_LIMITED == 0, the source rate (recorded in self.sorted_flows) for
              each flow becomes float('inf'), so no need to worry about the source rate.

        """
        btnk_link = ('', '')        # Bottleneck link: defined by:
                                    #     argmin_{all links}
                                    #     {linkobj.unasgn_bw / linkobj.n_unasgn_flows}
        btnk_bw = float('inf')      # As shown above, bottleneck BW defined by -
                                    #     linkobj.unasgn_bw / linkobj.n_unasgn_flows
        n_unprocessed_links = 0
        n_unasgn_flows      = len(self.sorted_flows)
        self.next_end_time  = float('inf')
        self.next_end_flow  = ('', '')

        for fl_tuple in self.sorted_flows:
            fl_tuple[1].assigned    = False     # Reset "assigned" flag for every active flow

        # Initialize link variables and find first-round bottleneck link
        for lk in self.links:
            linkobj                 = self.linkobjs[lk]
            linkobj.unasgn_bw       = linkobj.cap
            linkobj.n_active_flows  = linkobj.get_n_active_flows()
            linkobj.n_unasgn_flows  = linkobj.n_active_flows
            linkobj.processed       = False
            if (linkobj.n_unasgn_flows > 0):
                linkobj.bw_per_flow     = linkobj.unasgn_bw / float(linkobj.n_unasgn_flows)
                if (linkobj.bw_per_flow < btnk_bw):
                    btnk_link   = lk
                    btnk_bw     = linkobj.bw_per_flow
                n_unprocessed_links += 1
            else:
                pass

        # Start assigning curr_rate to flows
        for mice_tuple in self.sorted_flows:
            mice_bw, mice_flowobj, mice_flowkey = mice_tuple

            if (mice_flowobj.assigned == True):
                continue

            recalc_btnk = False     # Flag for recalculation of global bottlneck

            # Case 1: BW assigned to flow(s) limited by the mice flow's own flow_rate
            if (mice_bw < btnk_bw):
                mice_flowobj.assign_bw(ev_time, mice_bw)

                for lk in mice_flowobj.links:
                    linkobj                 =   self.linkobjs[lk]
                    linkobj.unasgn_bw       -=  mice_bw
                    linkobj.n_unasgn_flows  -=  1

                    if (linkobj.n_unasgn_flows > 0):
                        linkobj.bw_per_flow     =   linkobj.unasgn_bw /             \
                                                    float(linkobj.n_unasgn_flows)
                        if (linkobj.bw_per_flow < btnk_bw):
                            btnk_link   = lk
                            btnk_bw     = linkobj.bw_per_flow
                    else:
                        n_unprocessed_links -= 1
                        if (lk == btnk_link):
                            recalc_btnk = True

                n_unasgn_flows -= 1

            # Case 2: BW assigned to flows(s) limited by max-min fair on btnk_link
            else:
                for fl in self.linkobjs[btnk_link].flows:
                    flowobj = self.flows[fl]

                    if (not flowobj.status == 'active'):    continue

                    elif (flowobj.assigned == True):        continue

                    else:
                        flowobj.assign_bw(ev_time, btnk_bw)

                        for lk in flowobj.links:
                            #self.link_byte_cnt[lk]  +=  bytes_sent_since_update
                            linkobj                 =   self.linkobjs[lk]
                            linkobj.unasgn_bw       -=  btnk_bw
                            linkobj.n_unasgn_flows  -=  1

                            if (linkobj.n_unasgn_flows > 0):
                                linkobj.bw_per_flow =   linkobj.unasgn_bw /             \
                                                        float(linkobj.n_unasgn_flows)
                                if (linkobj.bw_per_flow < btnk_bw):
                                    btnk_link   = lk
                                    btnk_bw     = linkobj.bw_per_flow
                            else:
                                if (lk == btnk_link):
                                    recalc_btnk = True
                                n_unprocessed_links -=  1

                    n_unasgn_flows -= 1

            if (n_unprocessed_links > 0 and recalc_btnk == True):
                btnk_link   = min([lk for lk in self.links \
                                  if self.linkobjs[lk].n_unasgn_flows > 0], \
                                  key=lambda x: self.linkobjs[x].bw_per_flow)
                btnk_bw     = self.linkobjs[btnk_link].bw_per_flow

        # Finally, get the estimated earliest-ending flow
        for tpl in self.sorted_flows:
            est = tpl[1].est_end_time
            if (est < self.next_end_time):
                self.next_end_time = est
                self.next_end_flow = tpl[2]
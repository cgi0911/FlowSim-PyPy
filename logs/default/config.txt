#!/usr/bin/python

"""config.txt: Configuration file. Contains the parameter needed.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

import os

# ---------------------------------------
# Frequently Used
# ---------------------------------------
EXP_NAME    = 'default'
DIR_TOPO    = './topologies/spain'
LOG_DIR     = os.path.join('./logs/', EXP_NAME)
SIM_TIME    = 120.0

DO_REROUTE  = 1              # Do elephant flow rerouting (please refer to paper draft)

ROUTING_MODE = 'ecmp'           # Supported routing modes:
                                # 'tablelb': Table load-balancing routing using k-path
                                #               (default to Yen's k-path algorithm)
                                # 'ecmp': Equal-cost multi-path
                                # 'spf': Shortest-path first
K_PATH = 2                      # Number of predefined path per src-dst pair
K_PATH_METHOD = 'yen'           # The algorithm used to set up k-path database

DO_PROFILING = True             # Do code profiling for this experiment

# ---------------------------------------
# Switch/link Initialization Parameters
# ---------------------------------------
OVERRIDE_TABLESIZE = True
TABLESIZE_PER_SW = 1000
OVERRIDE_N_HOSTS = True
N_HOSTS_PER_SW = 10
OVERRIDE_CAP = True
CAP_PER_LINK = 10.0
CAP_UNIT     = 1.0e9    # Gbps


# ----------------------------------------
# Screen Printing Options
# ----------------------------------------
SHOW_PROGRESS = 1
SHOW_EVENTS = 0
SHOW_REJECTS = 0
SHOW_K_PATH_CONSTRUCTION = 0
SHOW_LINK_CONGESTION = 0
SHOW_TABLE_OVERFLOW = 0
SHOW_FLOW_CALC = 0
SHOW_REROUTE = 0
SHOW_SUMMARY = 1

# ----------------------------------------
# Logging Options
# ----------------------------------------
LOG_CONFIG = 1
LOG_LINK_UTIL = 1
LOG_TABLE_UTIL = 1
LOG_FLOW_STATS = 1
LOG_SUMMARY = 1
IGNORE_HEAD = 0.3               # Ignore head (portion) rows when doing average



# ----------------------------------------
# Time-related Parameters
# ----------------------------------------
PERIOD_LOGGING = 0.100          # Period of doing link util and table util logging.

SW_CTRL_DELAY = 0.005           # Switch-to-controller delay
CTRL_SW_DELAY = 0.005           # Controller-to-switch delay
IDLE_TIMEOUT = 0.000            # Idle timeout
REJECT_TIMEOUT = 0.300          # Timeout for flow re-request if rejected due to overflow

PERIOD_REROUTE = 2.500          # Period of rerouting
PERIOD_COLLECT = 0.500          # Period of counter collection

# ----------------------------------------
# Reroute-related Parameters
# ----------------------------------------
N_ELEPH_FLOWS = 20

# ----------------------------------------
# Flow Generation Parameters
# ----------------------------------------
FLOWGEN_SRCDST_MODEL        = 'uniform'     # Model for flow source and destination
                                        # "uniform": Randomly pick one dst host that is not
                                        #   within source host's LAN.

FLOWGEN_SIZERATE_MODEL      = 'bimodal'     # Model for flow size and rate
                                        # "uniform": Size and rate are generated in uniform
                                        #   random manner.
                                        # "bimodal": First decide whether a new flow is
                                        #   large or small, then decide its size and rate
                                        #   accordingly.

FLOWGEN_ARR_MODEL           = 'const'    # Flow arrival model
                                        # "saturate": Each host will be the source of
                                        #   one and exactly one active flow. A new flow is
                                        #   fired after the previous one comes to an end.
                                        # "const": Flow arrival rate is a specified constant.
                                        # "exp": Flow inter-arrival time is exponentially distributed

SRC_LIMITED                 = 0          # If 1, flow rates are limited by its source rate.
                                        # If 0, flow can transmit as fast as possible subject to
                                        #   link capacity constraints and max-min fairness.

# Model parameters
class FLOWGEN_SIZERATE_UNIFORM:
    FLOW_SIZE_LO = 5e7
    FLOW_SIZE_HI = 10e7
    FLOW_RATE_LO = 5e6
    FLOW_RATE_HI = 10e6

class FLOWGEN_SIZERATE_BIMODAL:
    PROB_LARGE_FLOW = 0.1
    FLOW_SIZE_LARGE_LO = 3.0e9
    FLOW_SIZE_LARGE_HI = 3.0e9
    FLOW_RATE_LARGE_LO = 10.0e9
    FLOW_RATE_LARGE_HI = 10.0e9
    FLOW_SIZE_SMALL_LO = 1.0e7
    FLOW_SIZE_SMALL_HI = 1.0e7
    FLOW_RATE_SMALL_LO = 5.0e7
    FLOW_RATE_SMALL_HI = 5.0e7

class FLOWGEN_ARR_SATURATE:
    INIT_FLOWS_SPREAD = 1.0
    NEXT_FLOW_DELAY = 0.0

class FLOWGEN_ARR_CONST:
    FLOW_ARR_RATE = 200.0       # flows/sec
    CUTOFF = 0.1                # ratio to avg. inter-arrival time
                                # The inter-arrival time will be uniform randomly chosen
                                # in the interval of [AVG-CUTOFF*AVG, AVG+CUTOFF*AVG]

class FLOWGEN_ARR_EXP:
    FLOW_ARR_RATE = 250.0       # flows/sec, a.k.a. lambda

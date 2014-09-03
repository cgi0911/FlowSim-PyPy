#!/usr/bin/python

"""
config.py: Configuration file. Contains the parameter needed.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'


# ---- Frequently Used ----
DIR_TOPO = './topologies/geant'
SIM_TIME = 60.0


# ----
OVERRIDE_TABLESIZE = False
TABLESIZE_PER_SW = 1000
OVERRIDE_N_HOSTS = False
N_HOSTS_PER_SW = 100
OVERRIDE_CAP = True
CAP_PER_LINK = 1e9

# ----
ROUTING_MODE = 'ecmp'            # Supported routing modes:
                                # 'yen': Yen's k-path algo
                                # 'ecmp': Equal-cost multi-path
                                # 'spf': Shortest-path first
K_PATH = 4                      # Number of predefined path per src-dst pair
#K_PATH_METHOD = 'yen'           # The algorithm used to set up k-path database

# ---- Logging Options ----
SHOW_PROGRESS = 0
SHOW_EVENTS = 0
SHOW_K_PATH_CONSTRUCTION = 0
SHOW_LINK_CONGESTION = 0
SHOW_TABLE_OVERFLOW = 0
SHOW_FLOW_CALC = 0
SHOW_REROUTE = 0

LOG_PARAMS = 1
LOG_LINK_UTIL = 1
LOG_TABLE_UTIL =  1
LOG_FLOW_STATS = 1
LOG_SUMMARIES = 1
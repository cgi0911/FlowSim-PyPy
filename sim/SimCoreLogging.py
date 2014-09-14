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

	def log_flow_stats(self, flow_item):
		"""
		"""
		ret = {}

		for fld in cfg.LOG_FLOW_STATS_FIELDS:
			ret[fld] = getattr(flow_item, fld)

		return ret

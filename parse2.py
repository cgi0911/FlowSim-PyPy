#!/usr/bin/python

import os
import pandas as pd

LOG_DIR = './logs/saturate'
FN = 'summary.csv'
ROWNAME = 'n_EvPacketIn'

DIRS = ['spf', 'ecmp_noreroute', 'ecmp_reroute', 'ecmp_fe_noreroute', 'ecmp_fe_reroute',
        'k2_noreroute', 'k4_noreroute', 'k6_noreroute', 'k8_noreroute', 'k10_noreroute',
        'k2_reroute', 'k4_reroute', 'k6_reroute', 'k8_reroute', 'k10_reroute',
        'k2_fe_noreroute', 'k4_fe_noreroute', 'k6_fe_noreroute', 'k8_fe_noreroute', 'k10_fe_noreroute',
        'k2_fe_reroute', 'k4_fe_reroute', 'k6_fe_reroute', 'k8_fe_reroute', 'k10_fe_reroute',
        ]

#for myDir in sorted(os.listdir(LOG_DIR)):
for myDir in DIRS:
    try:
        df = pd.read_csv(os.path.join(LOG_DIR, myDir, FN), header=None, index_col=None)
    except IOError:
        print
        continue

    n_rows = df.shape[0]

    for i in range(n_rows):
        row_name = df.iloc[i][0]
        if (row_name == ROWNAME):
            try:
                val = float(df.iloc[i][1])
                #print '%-32s,%.3e' %(myDir, val)
                print '%.3e' %(val)
            except:
                val = df.iloc[i][1]
                #print '%-32s,%s' %(myDir, val)
                print '%s' %(val)
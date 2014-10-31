#!/usr/bin/python
# -*- coding: utf-8 -*-
"""sim/SimMath.py: Some math functions.
"""
__author__      = 'Kuan-yin Chen'
__copyright__   = 'Copyright 2014, NYU-Poly'

# Built-in modules
import math

def mean(lst):
    """Calculate mean of a list of numbers.

    Args:
        lst (list of numbers): The list of which the mean is to be calculated.
    """
    if (len(lst) == 0):
        print "SimMath.mean(): empty list!"
        return None

    mySum = math.fsum(lst)
    ret = mySum / float(len(lst))

    return ret


def percentile(lst, k):
    """Calculate k-th percentile of a list of numbers.

    Args:
        lst (list of numbers)
        k (float)
    """
    if (len(lst) == 0):
        print "SimMath.percentile(): Empty list!"
        return None

    slst = sorted(lst)
    q = float(len(slst)-1) * k / 100
    f = math.floor(q)
    c = math.ceil(q)
    if (f == c):
        return float(slst[int(k)])
    else:
        d0 = float(slst[int(f)] * (c-q))
        d1 = float(slst[int(c)] * (q-f))
        return d0+d1


def std(lst):
    """Calculate STDEV of a list of numbers.

    Args:
        lst (list of numbers)
    """
    if (len(lst) == 0):
        print "SimMath.std(): empty list!"
        return None

    if (len(lst) == 1):
        return 0.0

    myMean = math.fsum(lst) / float(len(lst))
    sqerr_list = []
    for myNum in lst:
        sqerr_list.append((float(myNum)-myMean)**2)
    msqerr = math.fsum(sqerr_list) / float(len(sqerr_list))
    ret = math.sqrt(msqerr)

    return ret

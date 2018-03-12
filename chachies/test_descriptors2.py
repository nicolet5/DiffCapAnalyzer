import descriptors

import scipy.signal
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import peakutils
from lmfit import models
import chachifuncs as ccf
import os
import glob

a = 'data/testCaseData/7_24_13_1C_Cycle-Cycle11Clean.xlsx'
b = 'data/testCaseData/7_24_13_1C_Cycle-Cycle11Clean.xlsx'
c = 'data/testCaseData/7_24_13_1C_Cycle-Cycle11Clean.xlsx'
d = 'data/testCaseData/CS2_33_10_04_10-Cycle8Clean.xlsx'
e = 'data/testCaseData/CS2_33_10_04_10-Cycle10Clean.xlsx'
f = 'data/testCaseData/CS2_33_12_23_10-Cycle3Clean.xlsx'
g = 'data/testCaseData/CS2_33_12_23_10-Cycle12Clean.xlsx'

def test_ML_generate_is_given_a_real_file():
    """ tests loading something that isn't Excel data"""
    try:
        descriptors.ML_generate('test.xsls')
        #should fail because this file doesn't exist in the test path
    except (AssertionError):
        pass
    else:
        raise Exception ('Exception not handled by asserts')

    return


def test_ML_generate_is_given_a_number_as_input():
    """tests passing something that isn't a string"""
    try:
        descriptors.ML_generate(5)
        #should fail because 5 is not a string.
    except (AssertionError):
        pass
    else:
        raise Exception ('Exception not handled by asserts')

    return


def test_df_generate_is_fed_c_or_d():
    """test passing something that isn't c or d (charge or discharge)"""
    try:
        descriptors.process.df_generate(a,'asdf')
        #should fail because asdf is not c or d!
    except (AssertionError):
        pass
    else:
        raise Exception ('Exception not handled by asserts')

    return

def test_df_generate_spits_out_a_dataframe():
    #assert that df_generate spits out a pandas dataframe
    assert isinstance(descriptors.process.df_generate(b,'c'), pd.core.frame.DataFrame), 'This should be a pandas dataframe'

    return

# need to put all imports required for package 
#might need to change these
import descriptors
import chachifuncs

#outside imports
import scipy.signal
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import peakutils
from lmfit import models
import chachifuncs_sepcd as ccf
import os
import glob

from math import isclose
from pandas import ExcelWriter
import requests
import scipy.io
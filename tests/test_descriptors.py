from descriptors import peak_finder
from descriptors import cd_dataframe
from descriptors import label_gen
from descriptors import model_gen
from descriptors import model_eval
from descriptors import dfsortpeakvals

import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from pandas.testing import assert_frame_equal
import scipy.signal

from pprint import pprint

test_cycle1_df =  pd.DataFrame({
					   'Cycle_Index': [1,1,1,1,1, 1, 1],
					   'Data_Point': [0, 1, 2, 3, 4, 5, 6],
					   'Voltage(V)': [4, 8, 16, 8, 4, 3.5, 3],
					   'Current(A)': [2, 4, 6, 8, 12, 14, 16], 
					   'Discharge_Capacity(Ah)': [10, 0, 30, 0, 10, 0, 30],
					   'Charge_Capacity(Ah)':  [0, 20, 0, 10, 0, 20, 0],
					   'Step_Index': [1, 0, 1, 0, 1, 0, 1],
					   	'dV': [0.5, 0.4, 0.3, 0.2, 0.1, 0.1, 0.1], 
					   'dQ': [0.6, 0.7, 0.8, 0.9, 1.0, 1.0, 1.0],
					   'Smoothed_dQ/dV': [7, 7.1, 8, 7.1, 7.0, 6.9, 6.8]})
test_cycle2_df = pd.DataFrame({
					   'Cycle_Index': [2,2,2],
					   'Data_Point': [5, 6, 7],
					   'Voltage(V)': [-16, -8, -4],
					   'Current(A)': [-6, -8, -12], 
					   'Discharge_Capacity(Ah)': [-30, -0, -10],
					   'Charge_Capacity(Ah)':  [-0, -10, -0],
					   'Step_Index': [1, 0, 1], 
					   'dV': [-0.5, -0.4, -0.3], 
					   'dQ': [-0.6, -0.7, -0.8],
					   'Smoothed_dQ/dV': [-7, -7.1, -7.2]})

test_import_dictionary = {'test_battery-CleanCycle1': test_cycle1_df, 
						  'test_battery-CleanCycle2': test_cycle2_df}
test_datatype = 'ARBIN'

def test_peak_finder(): 
	"""Tests that the correct indices, voltage, and dq/dv value 
	are returned for peaks found with peak_finder"""
	result = peak_finder(test_cycle1_df, 'c', 5, 3, test_datatype, 5, 0.4)
	assert len(result) == 3
	peak_indices = result[0]
	peak_sigx_volts = result[1]
	peak_heights = result[2]
	assert peak_indices == [2] 
	# one peak should be found at the second index
	assert type(peak_sigx_volts) == list
	assert type(peak_heights) == list
	assert peak_heights == [8]
	assert peak_sigx_volts == [16]
	return 

def test_cd_dataframe(): 
	"""Tests the cd funciton returns the values for the
	dQdV series of the dataframe"""
	c_result = cd_dataframe(test_cycle1_df['Voltage(V)'], 
						  test_cycle1_df['Smoothed_dQ/dV'], 
						  'c')
	c_sigx = c_result[0]
	c_sigy = c_result[1]
	assert list(c_sigx) == [4, 8, 16, 8, 4, 3.5, 3]
	assert list(c_sigy) == [7, 7.1, 8, 7.1, 7.0, 6.9, 6.8]

	d_result = cd_dataframe(test_cycle1_df['Voltage(V)'], 
						  test_cycle1_df['Smoothed_dQ/dV'], 
						  'd')
	d_sigx = d_result[0]
	d_sigy = d_result[1]
	assert list(d_sigx) == [4, 8, 16, 8, 4, 3.5, 3]
	# if this is a discharge cycle the dq/dv should be
	# opposite sign
	assert list(d_sigy) == [-7, -7.1, -8, -7.1, -7.0, -6.9, -6.8]

def test_label_gen(): 
	"""Tests that the labels gneerated for descriptors
	are accurate"""
	test_index = 42
	result = label_gen(test_index)
	center = result[0]
	sigma = result[1]
	amplitude = result[2]
	fraction = result[3]
	comb = result[4]

	assert center == 'a42_center'
	assert sigma == 'a42_sigma'
	assert amplitude == 'a42_amplitude'
	assert fraction == 'a42_fraction'
	assert comb == 'a42_'


def test_model_gen(): 
	"""Tests that a model is generated for the
	given test data"""
	par_result, mod_result, i_result = model_gen(
										test_cycle1_df['Voltage(V)'], 
					  					test_cycle1_df['Smoothed_dQ/dV'], 
					   					'c', [2], 1, 0.4)
	assert par_result is not None
	assert mod_result is not None
	assert i_result == [2]


def test_model_eval(): 
	"""Tests that the model is evaluated on the data """
	par_result, mod_result, i_result = model_gen(
									test_cycle1_df['Voltage(V)'], 
				  					test_cycle1_df['Smoothed_dQ/dV'], 
				   					'c', [2], 1, 0.4)
	model = model_eval(test_cycle1_df['Voltage(V)'], 
						test_cycle1_df['Smoothed_dQ/dV'], 
						'c', par_result, mod_result)
	assert model is not None

def test_dfsortpeakvals(): 
	test_df = pd.DataFrame({
		'c_center_1':[32],
		'c_height_1': [12],
		'c_area_1':[22], 
		'c_sigma_1':[3], 
		'c_amp_1':[11], 
		'c_fwhm_1':[2], 
		'c_fract_1':[21], 
		'c_rawheight_1':[14]
		})

	result = dfsortpeakvals(test_df, 'c')
	expected = pd.DataFrame({
		'c_center_1':[32],
		'c_height_1': [12],
		'c_area_1':[22], 
		'c_sigma_1':[3], 
		'c_amp_1':[11], 
		'c_fwhm_1':[2], 
		'c_fract_1':[21], 
		'c_rawheight_1':[14], 
		'sortedloc-c-1':[32], 
		'sortedheight-c-1':[12], 
		'sortedarea-c-1':[22], 
		'sortedSIGMA-c-1':[3], 
		'sortedamplitude-c-1': [11], 
		'sortedfwhm-c-1':[2], 
		'sortedfraction-c-1':[21], 
		'sortedactheight-c-1':[14]
		})
	assert result.equals(expected)

def test_dfsortpeakvals_sorting(): 
	test_df = pd.DataFrame({
		'c_center_1':[32, 35],
		'c_height_1': [12, 6],
		'c_area_1':[22, 10], 
		'c_sigma_1':[3, 2], 
		'c_amp_1':[11, 12], 
		'c_fwhm_1':[2, 3], 
		'c_fract_1':[21, 0.5], 
		'c_rawheight_1':[14, 6],
		'c_center_2':[15, 32.005],
		'c_height_2': [8, 12.005],
		'c_area_2':[8, 22.005], 
		'c_sigma_2':[8, 3.005], 
		'c_amp_2':[8, 11.005], 
		'c_fwhm_2':[8, 2.005], 
		'c_fract_2':[8, 21.005], 
		'c_rawheight_2':[8, 14.005]
		})

	result = dfsortpeakvals(test_df, 'c').astype('float64')
	# assert list(result.loc[:,('sortedloc-c-1')]) == [15, None]
	# assert list(result.loc[:,('sortedloc-c-2')]) == [32, 32.005]
	# assert list(result.loc[:,('sortedloc-c-3')]) == [None, 35]

	expected = pd.DataFrame({
		'c_center_1':[32, 35],
		'c_height_1': [12, 6],
		'c_area_1':[22, 10], 
		'c_sigma_1':[3, 2], 
		'c_amp_1':[11, 12], 
		'c_fwhm_1':[2, 3], 
		'c_fract_1':[21.0, 0.5], 
		'c_rawheight_1':[14, 6],
		'c_center_2':[15.000, 32.005],
		'c_height_2': [8.000, 12.005],
		'c_area_2':[8.000, 22.005], 
		'c_sigma_2':[8.000, 3.005], 
		'c_amp_2':[8.000, 11.005], 
		'c_fwhm_2':[8.000, 2.005], 
		'c_fract_2':[8.000, 21.005], 
		'c_rawheight_2':[8.000, 14.005],
		'sortedloc-c-1': [15, None], 
		'sortedheight-c-1': [8, None],
		'sortedarea-c-1':[8, None],
		'sortedSIGMA-c-1':[8, None],
		'sortedamplitude-c-1':[8, None],
		'sortedfwhm-c-1':[8, None],
		'sortedfraction-c-1':[8, None],
		'sortedactheight-c-1':[8, None],
		'sortedloc-c-2': [32, 32.005],
		'sortedheight-c-2': [12, 12.005],
		'sortedarea-c-2':[22, 22.005],
		'sortedSIGMA-c-2':[3, 3.005],
		'sortedamplitude-c-2':[11, 11.005],
		'sortedfwhm-c-2':[2, 2.005],
		'sortedfraction-c-2':[21, 21.005],
		'sortedactheight-c-2': [14, 14.005],
		'sortedloc-c-3': [None, 35],
		'sortedheight-c-3': [None, 6],
		'sortedarea-c-3':[None, 10],
		'sortedSIGMA-c-3': [None, 2],
		'sortedamplitude-c-3':[None, 12],
		'sortedfwhm-c-3': [None, 3],
		'sortedfraction-c-3': [None, 0.5],
		'sortedactheight-c-3': [None, 6]
		}).astype('float64')
	assert_frame_equal(result, expected, check_names=False)
	# for column in result.columns: 
	# 	print(column)
	# 	pprint(result[column])
	# 	assert list(result.loc[:, (column)]) == list(expected.loc[:,(column)])
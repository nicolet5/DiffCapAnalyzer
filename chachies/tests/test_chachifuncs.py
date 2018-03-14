from chachies import chachifuncs as ccf
import os
import pandas as pd

#### Functions to test:
# component functions: get_data, sep_cycles, save_sep_cycles_xlsx, calc_dv_dqdv, drop_0_dv, sep_char_dis, my_savgolay
# sub wrapper functions: load_sep_cycles, clean_calc_sep_smooth, get_clean_cycles, get_clean_sets
# overall function: get_all_data

#############################
# Component Functions Tests
#############################

def test_get_data():
	""" tests getting the data all from one folder path into a dictionary"""
	try:
		ccf.get_data(1)
		#should fail because input for get_data must be a string.
	except (AssertionError):
		pass
	else:
		raise Exception ('Exception not handled by Asserts.')

def test_sep_cycles():
	""" tests function to separate cycles """
	#dataframe = pd.read_excel('test.xsls',1) #test should raise an error
	dataframe = [1,2,3]
	#test should pass if test generates an AssertionError
	try:
		ccf.sep_cycles(dataframe)
	except (AssertionError):
		pass
	else:
		raise Exception ("Exception not handled by Asserts")


def test_save_sep_cycles_xsls():
	"""tests function that saves separate cycles"""
	dataframe = pd.read_excel('data/test.xsls',1)
	cycle_dict = [dataframe,1,2]
	#should raise AssertionError. Inputs must be a dictionary, a battery name string, and a path as a string.
	try:
		ccf.save_sep_cycles_xlsx(cycle_dict, 'battery1', 'seperate_cycles/')
	except (AssertionError):
		pass
	else:
		raise Exception ("Exception not handled by Asserts")

def test_calc_dv_dqdv():
	"""Tests function that is calculating dv columns and dq/dv columns in the dataframe"""
	dataframe = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
	try:
		ccf.calc_dv_dqdv(dataframe)
		#should raise AssertionError because dataframe must have columns titled 'Voltage(V)', 'Charge_Capacity(Ah)', and 'Discharge_Capacity(Ah)'
	except (AssertionError):
		pass
	else:
		raise Exception ("Column labels exception not handled by asserts.")

def test_drop_0_dv():
	"""Tests that the dataframe put in has columns 'Current(A)' and 'dV'. This indicates the upstream function (calc_dv_dqdv) added the dv
	column correctly. """
	dataframe = pd.DataFrame({'dV': [0, 0.1, 0.2, 0.3], 'col2': [1, 3, 8, 3]})
	dataframe2 = pd.DataFrame({'Current(A)': [0, 0.1, 0.2, 0.3], 'col2': [1, 3, 8, 3]})
	try:
		ccf.drop_0_dv(dataframe)
		#should raise assertion error since the column 'Current(A)' doesn't exist in that dataframe
	except (AssertionError):
		pass
	else:
		raise Exception ("Column labels not containing 'Current(A)' exception not handled by asserts.")
	try:
		ccf.drop_0_dv(dataframe2)
	except (AssertionError):
		pass
	else:
		raise Exception ("Column labels not containing 'dV' exception not handled by asserts.")

def test_sep_char_dis():
	"""Tests that input is a dataframe with a column titled 'Discharge_dQ/dV' and a column titled 'Charge_dQ/dV', indicating upstream
	function drop_0_dv created those columns correctly."""
	dataframe = pd.DataFrame({'col1': [1, 2, 3], 'Discharge_dQ/dV': [3, 4, 5]})
	dataframe2 = pd.DataFrame({'col1': [1, 2, 3], 'Charge_dQ/dV': [3, 4, 5]})
	try:
		ccf.sep_char_dis(dataframe)
		#should raise an assertion error because Charge_dQ/dV doesn't exist in this dataframe.
	except (AssertionError):
		pass
	else:
		raise Exception ("Column labels not containing 'Charge_dQ/dV' exception not handled by asserts.")
	try:
		ccf.sep_char_dis(dataframe2)
	except (AssertionError):
		pass
	else:
		raise Exception ("Column labels not containing 'Discharge_dQ/dV' exception not handled by asserts.")

def test_my_savgolay():
	"""Tests the inputs of the my_savgolay function"""
	dataframe = pd.DataFrame({'dQ/dV': [1, 3, 4, 7, 3, 7, 21, 446, 32], 'col2': [21, 23, 42, 71, 38, 7, 21, 6, 2]})
	try:
		ccf.my_savgolay(dataframe, 4, 2)
		#should raise assertion because window length is not an odd number.
	except (AssertionError):
		pass
	else:
		raise Exception ("Windowlength must be odd exception not handled by asserts.")
	try:
		ccf.my_savgolay(dataframe, 5, 21)
		#should raise assertion because window length is less than the polyorder.
	except (AssertionError):
		pass
	else:
		raise Exception ("Polyorder must be less than windowlength exception not handled by asserts.")



##############################
# Sub Wrapper Functions Tests
##############################

def test_load_sep_cycles():
	""" Tests that the inputted file paths actually exist. (This function will NOT create a new directory if the paths don't exist -
	that is handled by the overall wrapper function.) """
	try:
		ccf.load_sep_cycles('NotARealFilePath/', 'AnotherNotARealFilePath/')
	except (AssertionError):
		pass
	else:
		raise Exception ('Not real file path exception not handled by assertion.')

def test_clean_calc_sep_smooth():
	""" Tests the input is a dataframe with columns with the correct names (dQ/dV, Current(A), Voltage(V))."""
	dataframe1 = pd.DataFrame({'dQ/dV': [1, 2, 4], 'col2:': [0, 2, 5], 'Voltage(V)': [6, 7, 8], 'Current(A)': [2, 3, 5], 'Discharge_Capacity(Ah)': [2, 1, 4], 'Charge_Capacity(Ah)': [1, 9, 14]})

	smooth_ch, smooth_dis = ccf.clean_calc_sep_smooth(dataframe1, 15, 3)
	assert 'Smoothed_dQ/dV' in smooth_ch.columns
	assert 'Smoothed_dQ/dV' in smooth_dis.columns
	assert not any(pd.isnull(smooth_ch['Smoothed_dQ/dV']))
	assert not any(pd.isnull(smooth_dis['Smoothed_dQ/dV']))
	#asserts there are no NaN values in the 'Smoothed_dQ/dV' column.

def test_get_clean_cycles():
	"""Tests the inputs for the function are real directory locations."""
	try:
		ccf.get_clean_cycles('NotARealFilePath/', 'AnotherNotARealFilePath/')
	except (AssertionError):
		pass
	else:
		raise Exception ('Not real file path exception not handled by asserts.')

def test_get_clean_sets():
	""" Tests the inputs for the function are real directory locations."""
	try:
		ccf.get_clean_cycles('NotARealFilePath/', 'AnotherNotARealFilePath/')
	except (AssertionError):
		pass
	else:
		raise Exception ('Not real file path exception not handled by asserts.')

########################
# Test Overall Wrapper
#######################

def test_get_all_data():
	""" Tests the inputs for get_all_data."""
	try:
		ccf.get_all_data('NotARealFilePath/', 'AnotherNotARealFilePath')
	except (AssertionError):
		pass
	else:
		raise Exception ('Note a real file path exception not handled by asserts.')

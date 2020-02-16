import numpy as np
import os
import pandas as pd

from diffcapanalyzer.chachifuncs import load_sep_cycles
from diffcapanalyzer.chachifuncs import get_clean_cycles
from diffcapanalyzer.chachifuncs import get_clean_sets
from diffcapanalyzer.chachifuncs import clean_calc_sep_smooth
from diffcapanalyzer.chachifuncs import init_columns
from diffcapanalyzer.chachifuncs import calc_dq_dqdv
from diffcapanalyzer.chachifuncs import drop_inf_nan_dqdv
from diffcapanalyzer.chachifuncs import sep_char_dis
from diffcapanalyzer.chachifuncs import my_savgolay
from diffcapanalyzer.chachifuncs import col_variables
from diffcapanalyzer.databasewrappers import parse_update_master
from diffcapanalyzer.databasewrappers import get_filename_pref
from diffcapanalyzer.databasewrappers import get_table_names
from diffcapanalyzer.databasefuncs import init_master_table


def test_load_sep_cycles(): 
	test_db = 'my_great_db.db'
	test_filename = 'my_great_data.xlsx'
	test_decoded_df = pd.DataFrame({
					   'Cycle_Index': [1,1,2,2,2],
					   'Data_Point': [0, 1, 2, 3, 4],
					   'Voltage(V)': [4, 8, 16, 8, 4],
					   'Current(A)': [2, 4, 6, 8, 12], 
					   'Discharge_Capacity(Ah)': [10, 0, 30, 0, 10],
					   'Charge_Capacity(Ah)':  [0, 20, 0, 10, 0],
					   'Step_Index': [1, 0, 1, 0, 1]})
	test_datatype = 'ARBIN'
	username = 'test user'
	# initialize database: 
	init_master_table(test_db)
	core_test_filename = get_filename_pref(test_filename)
	parse_update_master(core_test_filename, test_db, test_datatype, 
						test_decoded_df, username)
	# set up by adding raw data frame to database 
	result = load_sep_cycles(core_test_filename, test_db, test_datatype)
	# there are two cycles in this test data:
	assert list(result.keys()) == [1, 2]
	os.remove(test_db)
	return 

def test_get_clean_cycles(): 
	"""Tests that cycles are cleaned and saved in database"""	
	test_db = 'my_great_db.db'
	test_filename = 'my_great_data.xlsx'
	test_decoded_df = pd.DataFrame({
					   'Cycle_Index': [1,1,2,2,2],
					   'Data_Point': [0, 1, 2, 3, 4],
					   'Voltage(V)': [4, 8, 16, 8, 4],
					   'Current(A)': [2, 4, 6, 8, 12], 
					   'Discharge_Capacity(Ah)': [10, 0, 30, 0, 10],
					   'Charge_Capacity(Ah)':  [0, 20, 0, 10, 0],
					   'Step_Index': [1, 0, 1, 0, 1]})
	test_datatype = 'ARBIN'
	username = 'test user'
	# initialize database: 
	init_master_table(test_db)
	core_test_filename = get_filename_pref(test_filename)
	parse_update_master(core_test_filename, test_db, test_datatype, 
						test_decoded_df, username)
	# set up by adding raw data frame to database 
	cycle_dict = load_sep_cycles(core_test_filename, test_db, test_datatype)
	result = get_clean_cycles(cycle_dict, core_test_filename, test_db, 
						  test_datatype, windowlength = 9, polyorder = 3)
	assert core_test_filename + '-CleanCycle1' in get_table_names(test_db)
	assert type(result) == dict
	assert list(result.keys()) == [core_test_filename + '-CleanCycle1', 
								   core_test_filename + '-CleanCycle2']
	os.remove(test_db)

def test_get_clean_sets(): 
	test_db = 'my_great_db.db'
	test_filename = 'my_great_data.xlsx'
	test_decoded_df = pd.DataFrame({
					   'Cycle_Index': [1,1,2,2,2],
					   'Data_Point': [0, 1, 2, 3, 4],
					   'Voltage(V)': [4, 8, 16, 8, 4],
					   'Current(A)': [2, 4, 6, 8, 12], 
					   'Discharge_Capacity(Ah)': [10, 0, 30, 0, 10],
					   'Charge_Capacity(Ah)':  [0, 20, 0, 10, 0],
					   'Step_Index': [1, 0, 1, 0, 1]})
	test_datatype = 'ARBIN'
	username = 'test user'
	# initialize database: 
	init_master_table(test_db)
	core_test_filename = get_filename_pref(test_filename)
	parse_update_master(core_test_filename, test_db, test_datatype, 
						test_decoded_df, username)
	# set up by adding raw data frame to database 
	cycle_dict = load_sep_cycles(core_test_filename, test_db, test_datatype)
	clean_cycle_dict = get_clean_cycles(cycle_dict, core_test_filename, test_db, 
	    					  test_datatype, windowlength = 9, polyorder = 3)
	result = get_clean_sets(clean_cycle_dict, core_test_filename, test_db)
	assert type(result) == pd.DataFrame
	assert list(result['Cycle_Index'].unique()) == [1,2]
	os.remove(test_db)


def test_init_columns(): 
	test_decoded_df = pd.DataFrame({
					   'Cycle_Index': [1,1,1,1,1],
					   'Data_Point': [0, 1, 2, 3, 4],
					   'Voltage(V)': [4, 8, 16, 8, 4],
					   'Current(A)': [2, 4, 6, 8, 12], 
					   'Discharge_Capacity(Ah)': [10, 0, 30, 0, 10],
					   'Charge_Capacity(Ah)':  [0, 20, 0, 10, 0],
					   'Step_Index': [1, 0, 1, 0, 1]})
	result = init_columns(test_decoded_df, 'ARBIN')
	assert type(result) == pd.DataFrame
	assert 'dV' in list(result.columns)
	assert 'Discharge_dQ' in list(result.columns)
	assert 'Charge_dQ' in list(result.columns)

	
def test_drop_inf_nan_dqdv():
	test_decoded_df = pd.DataFrame({
					   'Cycle_Index': [1,1,1,1,1],
					   'Data_Point': [0, 1, 2, 3, 4],
					   'Voltage(V)': [4, 8, 16, 8, 4],
					   'Current(A)': [2, 4, 6, 8, 12], 
					   'Discharge_Capacity(Ah)': [10, 0, 30, 0, 10],
					   'Charge_Capacity(Ah)':  [0, 20, 0, 10, 0],
					   'Step_Index': [1, 0, 1, 0, 1],
					   'dV': [-1, -1.5, -1.6, 1, 2], 
					   'dQ/dV':[np.NaN, -0.01, np.inf, 1, 2]})
	result = drop_inf_nan_dqdv(test_decoded_df, 'ARBIN')
	assert result.equals(pd.DataFrame({
					   'Cycle_Index': [1,1,1],
					   'Data_Point': [1, 3, 4],
					   'Voltage(V)': [8, 8, 4],
					   'Current(A)': [4, 8, 12], 
					   'Discharge_Capacity(Ah)': [0, 0, 10],
					   'Charge_Capacity(Ah)':  [20, 10, 0],
					   'Step_Index': [0, 0, 1],
					   'dV': [ -1.5, 1, 2], 
					   'dQ/dV':[-0.01, 1, 2]}))


def test_colvariables():
	result_a = col_variables('ARBIN')
	assert result_a == ('Cycle_Index','Data_Point', 'Voltage(V)','Current(A)', 
						'Discharge_Capacity(Ah)','Charge_Capacity(Ah)','Step_Index')
	result_b = col_variables('MACCOR')
	assert result_b == ('Cycle_Index','Rec','Voltage(V)','Current(A)',
						'Cap(Ah)','Cap(Ah)','Md')
	try: 
		result_x = col_variables('not a real datatype')
	except (AssertionError): 
		pass
	else: 
		raise Exception ('Valid datatype not being checked')

def test_clean_calc_sep_smooth():
	"""Tests function that is calculating dv columns and dq/dv columns in the dataframe"""
	dataframe = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
	try:
		clean_calc_sep_smooth(dataframe, 'ARBIN', 12, 3)
		#should raise AssertionError because dataframe must have columns titled 'Voltage(V)', 'Charge_Capacity(Ah)', and 'Discharge_Capacity(Ah)'
	except (AssertionError):
		pass
	else:
		raise Exception ("Column labels exception not handled by asserts.")

def test_calc_dq_dqdv():
	"""Tests function that is calculating dv columns and dq/dv columns in the dataframe"""
	dataframe = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
	try:
		calc_dq_dqdv(dataframe, 'NOT A REAL DATATYPE')
		#should raise AssertionError because dataframe must have columns titled 'Voltage(V)', 'Charge_Capacity(Ah)', and 'Discharge_Capacity(Ah)'
	except (AssertionError):
		pass
	else:
		raise Exception ("Incorrect datatype exception not handled by asserts.")


def test_sep_char_dis():
	"""Tests that input is a dataframe with a column titled 'Discharge_dQ/dV' and a column titled 'Charge_dQ/dV', indicating upstream
	function drop_0_dv created those columns correctly."""
	dataframe = pd.DataFrame({'col1': [1, 2, 3], 'col2': [3, 4, 5]})
	try:
		sep_char_dis(dataframe, 'ARBIN')
		#should raise an assertion error because Charge_dQ/dV doesn't exist in this dataframe.
	except (AssertionError):
		pass
	else:
		raise Exception ("Column labels not containing 'Charge_dQ/dV' exception not handled by asserts.")

def test_my_savgolay():
	"""Tests the inputs of the my_savgolay function"""
	dataframe = pd.DataFrame({'dQ/dV': [1, 3, 4, 7, 3, 7, 21, 446, 32], 
							  'col2': [21, 23, 42, 71, 38, 7, 21, 6, 2]})
	try:
		my_savgolay(dataframe, 4, 2)
		#should raise assertion because window length is not an odd number.
	except (AssertionError):
		pass
	else:
		raise Exception ("Windowlength must be odd exception not handled by asserts.")
	try:
		my_savgolay(dataframe, 5, 21)
		#should raise assertion because window length is less than the polyorder.
	except (AssertionError):
		pass
	else:
		raise Exception ("Polyorder must be less than windowlength exception not handled by asserts.")



# ##############################
# # Sub Wrapper Functions Tests
# ##############################

# def test_load_sep_cycles():
# 	""" Tests that the inputted file paths actually exist. (This function will NOT create a new directory if the paths don't exist -
# 	that is handled by the overall wrapper function.) """
# 	try:
# 		ccf.load_sep_cycles('NotARealFilePath/', 'AnotherNotARealFilePath/')
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Not real file path exception not handled by assertion.')

# def test_clean_calc_sep_smooth():
# 	""" Tests the input is a dataframe with columns with the correct names (dQ/dV, Current(A), Voltage(V))."""
# 	dataframe1 = pd.DataFrame({'dQ/dV': [1, 2, 4], 'col2:': [0, 2, 5], 'Voltage(V)': [6, 7, 8], 'Current(A)': [2, 3, 5], 'Discharge_Capacity(Ah)': [2, 1, 4], 'Charge_Capacity(Ah)': [1, 9, 14]})

# 	smooth_ch, smooth_dis = ccf.clean_calc_sep_smooth(dataframe1, 15, 3)
# 	assert 'Smoothed_dQ/dV' in smooth_ch.columns
# 	assert 'Smoothed_dQ/dV' in smooth_dis.columns
# 	assert not any(pd.isnull(smooth_ch['Smoothed_dQ/dV']))
# 	assert not any(pd.isnull(smooth_dis['Smoothed_dQ/dV']))
# 	#asserts there are no NaN values in the 'Smoothed_dQ/dV' column.

# def test_get_clean_cycles():
# 	"""Tests the inputs for the function are real directory locations."""
# 	try:
# 		ccf.get_clean_cycles('NotARealFilePath/', 'AnotherNotARealFilePath/')
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Not real file path exception not handled by asserts.')

# def test_get_clean_sets():
# 	""" Tests the inputs for the function are real directory locations."""
# 	try:
# 		ccf.get_clean_cycles('NotARealFilePath/', 'AnotherNotARealFilePath/')
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Not real file path exception not handled by asserts.')

# ########################
# # Test Overall Wrapper
# #######################

# def test_get_all_data():
# 	""" Tests the inputs for get_all_data."""
# 	try:
# 		ccf.get_all_data('NotARealFilePath/', 'AnotherNotARealFilePath')
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Note a real file path exception not handled by asserts.')

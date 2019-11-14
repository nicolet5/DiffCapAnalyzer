from descriptors import get_descriptors

from descriptors import dflists_to_dfind
# from descriptors import process

# from process import df_generate
# from descriptors.process import imp_all
# from descriptors.process import pd_create
# from descriptors.process import pd_update
# from descriptors.process import dict_2_list
# from descriptors.process import imp_one_cycle

# from descriptors.fitters import descriptor_func
# from descriptors.fitters import cd_dataframe
# from descriptors.fitters import peak_finder
# from descriptors.fitters import label_gen
# from descriptors.fitters import model_gen
# from descriptors.fitters import model_eval
# from descriptors.fitters import dfsortpeakvals

import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import scipy.signal

# a = 'data/testCaseData/7_24_13_1C_Cycle-Cycle11Clean.xlsx'
# b = 'data/testCaseData/7_24_13_1C_Cycle-Cycle11Clean.xlsx'
# c = 'data/testCaseData/7_24_13_1C_Cycle-Cycle11Clean.xlsx'
# d = 'data/testCaseData/CS2_33_10_04_10-Cycle8Clean.xlsx'
# e = 'data/testCaseData/CS2_33_10_04_10-Cycle10Clean.xlsx'
# f = 'data/testCaseData/CS2_33_12_23_10-Cycle3Clean.xlsx'
# g = 'data/testCaseData/CS2_33_12_23_10-Cycle12Clean.xlsx'

test_cycle1_df =  pd.DataFrame({
					   'Cycle_Index': [1,1,1,1,1],
					   'Data_Point': [0, 1, 2, 3, 4],
					   'Voltage(V)': [4, 8, 16, 8, 4],
					   'Current(A)': [2, 4, 6, 8, 12], 
					   'Discharge_Capacity(Ah)': [10, 0, 30, 0, 10],
					   'Charge_Capacity(Ah)':  [0, 20, 0, 10, 0],
					   'Step_Index': [1, 0, 1, 0, 1],
					   	'dV': [0.5, 0.4, 0.3, 0.2, 0.1], 
					   'dQ': [0.6, 0.7, 0.8, 0.9, 1.0],
					   'dQ/dV': [7, 7.1, 7.2, 7.3, 7.4]})
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
					   'dQ/dV': [-7, -7.1, -7.2]})

test_import_dictionary = {'test_battery-CleanCycle1': test_cycle1_df, 
						  'test_battery-CleanCycle2': test_cycle2_df}

# def test_df_generate_is_fed_c_or_d():
# 	"""test passing something that isn't c or d (charge or discharge)"""
# 	try:
# 		process.df_generate(test_import_dictionary,'asdf', 
# 					'ARBIN', 21, 3)
# 		#should fail because asdf is not c or d!
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')

# 	return

# def test_df_generate_spits_out_a_dataframe():
# 	#assert that df_generate spits out a pandas dataframe
# 	assert isinstance(process.df_generate(test_import_dictionary,'c', 
# 								  'ARBIN', 21, 3), 
# 					 pd.core.frame.DataFrame), \
# 			 'This should be a pandas dataframe'
# 	return

# def test_df_generate_behaves_well():
# 	"""test passing something that isn't a string or c or d (charge or discharge)"""
# 	try:
# 		process.df_generate(test_import_dictionary,'asdf','ARBIN', 21, 3)
# 		#should fail because asdf is not c or d!
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')

# 	try:
# 		process.df_generate(3,'c', 'ARBIN', 21, 3)
# 		#should fail because 3 is not a dict
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')
# 	return

# def test_imp_one_cycle():
# 	"""tests loading something that isn't Excel data"""
# 	try:
# 		descriptors.process.imp_one_cycle('test.xsls', 'c', 7, "bob's battery" )
# 		#should fail because this file doesn't exist in the test path
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')

# 	return


# def test_descriptor_func():
# 	"""test the input is a single column of Voltage or smoothed dQ/dV data"""
# 	df = pd.DataFrame({"Voltage(V)":[1,2,3], "Smoothed_dQ/dV": [4,5,6]})
# 	proper_V = df['Voltage(V)']
# 	proper_dqdv = df["Smoothed_dQ/dV"]

# 	try:
# 		descriptors.fitters.descriptor_func(df, proper_dqdv,'c',7,"bob's batteries")
# 		#should raise assertion error since the column for voltage is bigger has more than one column
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ("exception not handled by asserts.")
# 	try:
# 		descriptors.fitters.descriptor_func(proper_V, df,'c',7,"bob's batteries")
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ("exception not handled by asserts.")

# 	return


# def test_cd_dataframe():
# 	df = pd.DataFrame({"Voltage(V)":[1,2,3], "Smoothed_dQ/dV": [4,5,6]})
# 	proper_V = df['Voltage(V)']
# 	proper_dqdv = df["Smoothed_dQ/dV"]
# 	try:
# 		descriptors.fitters.cd_dataframe(proper_V,proper_dqdv, 'd')
# 		#this should fail because if dqdv is negative, it is probably discharge data and we want to flip to be positive for peak finding
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ("Exception not handled by asserts")

# 	return


# def test_peak_finder():
# 	"""test the input is a single column of Voltage or smoothed dQ/dV data"""
# 	df = pd.DataFrame({"Voltage(V)":[1,2,3], "Smoothed_dQ/dV": [4,5,6]})
# 	proper_V = df['Voltage(V)']
# 	proper_dqdv = df["Smoothed_dQ/dV"]
# 	try:
# 		descriptors.fitters.peak_finder(df, proper_dqdv,'c')
# 		#should raise assertion error since the dataset is too small to fit peaks
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ("exception not handled by asserts.")

# 	return


# def test_label_gen():
# 	"""make sure a number is the input and a string is the output"""
# 	try:
# 		descriptors.fitters.label_gen("not a number")
# 		#should fail because this only works with numbers
# 	except (AssertionError):
# 		pass
# 	else:
# 			raise Exception("Exception not handled by asserts")
# 	return

# def test_imp_all_behaves_well():
# 	"""test passing something that isn't a string or c or d (charge or discharge)"""
# 	try:
# 		descriptors.process.imp_all(a,"str",'asdf')
# 		#should fail because asdf is not c or d!
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')

# 	try:
# 		descriptors.process.imp_all(3,"str",'c')
# 		#should fail because 3 is not a file!
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')

# 	try:
# 		descriptors.process.imp_all(a,7,'c')
# 		#should fail because 7 is not a str for the battery name
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')

# 	return

# def test_pd_create():
# 	"""test passing something that isn't a string or c or d (charge or discharge)"""
# 	try:
# 		descriptors.process.pd_create('asdf')
# 		#should fail because asdf is not c or d!
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')

# 	return

# def test_pd_update():
# 	"""test to make sure pd_update takes the appropriate inputs"""
# 	mydict = {1:2,3:4}
# 	mydf = pd.DataFrame([1,2,3])
# 	try:
# 		descriptors.process.pd_update(mydf,"not a dict")
# 		#should fail because "not a dict" is not a dict!
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')

# 	try:
# 		descriptors.process.pd_update("not a dataframe",mydict)
# 		#should fail because "not a dict" is not a dict!
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')

# 	return

# def test_dict_2_list():
# 	"""make sure this only takes dictionaries as input"""
# 	try:
# 		descriptors.process.dict_2_list("not a dict")
# 		#should fail since "not a dict" is not a dict!
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')
# 	return


# def test_imp_one_cycle():
# 	"""tests loading something that isn't Excel data"""
# 	try:
# 		descriptors.process.imp_one_cycle('test.xsls', 'c', 7, "bob's battery" )
# 		#should fail because this file doesn't exist in the test path
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ('Exception not handled by asserts')

# 	return


# def test_descriptor_func():
# 	"""test the input is a single column of Voltage or smoothed dQ/dV data"""
# 	df = pd.DataFrame({"Voltage(V)":[1,2,3], "Smoothed_dQ/dV": [4,5,6]})
# 	proper_V = df['Voltage(V)']
# 	proper_dqdv = df["Smoothed_dQ/dV"]

# 	try:
# 		descriptors.fitters.descriptor_func(df, proper_dqdv,'c',7,"bob's batteries")
# 		#should raise assertion error since the column for voltage is bigger has more than one column
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ("exception not handled by asserts.")
# 	try:
# 		descriptors.fitters.descriptor_func(proper_V, df,'c',7,"bob's batteries")
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ("exception not handled by asserts.")

# 	return


# def test_cd_dataframe():
# 	df = pd.DataFrame({"Voltage(V)":[1,2,3], "Smoothed_dQ/dV": [4,5,6]})
# 	proper_V = df['Voltage(V)']
# 	proper_dqdv = df["Smoothed_dQ/dV"]
# 	try:
# 		descriptors.fitters.cd_dataframe(proper_V,proper_dqdv, 'd')
# 		#this should fail because if dqdv is negative, it is probably discharge data and we want to flip to be positive for peak finding
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ("Exception not handled by asserts")

# 	return


# def test_peak_finder():
# 	"""test the input is a single column of Voltage or smoothed dQ/dV data"""
# 	df = pd.DataFrame({"Voltage(V)":[1,2,3], "Smoothed_dQ/dV": [4,5,6]})
# 	proper_V = df['Voltage(V)']
# 	proper_dqdv = df["Smoothed_dQ/dV"]
# 	try:
# 		descriptors.fitters.peak_finder(df, proper_dqdv,'c')
# 		#should raise assertion error since the dataset is too small to fit peaks
# 	except (AssertionError):
# 		pass
# 	else:
# 		raise Exception ("exception not handled by asserts.")

# 	return


# def test_label_gen():
# 	"""make sure a number is the input and a string is the output"""
# 	try:
# 		descriptors.fitters.label_gen("not a number")
# 		#should fail because this only works with numbers
# 	except (AssertionError):
# 		pass
# 	else:
# 			raise Exception("Exception not handled by asserts")

# 	return

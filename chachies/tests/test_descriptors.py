import chachifuncs as ccf
import descriptors
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import scipy.signal

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

def test_imp_all_behaves_well():
	"""test passing something that isn't a string or c or d (charge or discharge)"""
	try:
		descriptors.process.imp_all(a,"str",'asdf')
		#should fail because asdf is not c or d!
	except (AssertionError):
		pass
	else:
		raise Exception ('Exception not handled by asserts')

	try:
		descriptors.process.imp_all(3,"str",'c')
		#should fail because 3 is not a file!
	except (AssertionError):
		pass
	else:
		raise Exception ('Exception not handled by asserts')

	try:
		descriptors.process.imp_all(a,7,'c')
		#should fail because 7 is not a str for the battery name
	except (AssertionError):
		pass
	else:
		raise Exception ('Exception not handled by asserts')

	return

def test_pd_create():
	"""test passing something that isn't a string or c or d (charge or discharge)"""
	try:
		descriptors.process.pd_create('asdf')
		#should fail because asdf is not c or d!
	except (AssertionError):
		pass
	else:
		raise Exception ('Exception not handled by asserts')

	return

def test_pd_update():
	"""test to make sure pd_update takes the appropriate inputs"""
	mydict = {1:2,3:4}
	mydf = pd.DataFrame([1,2,3])
	try:
		descriptors.process.pd_update(mydf,"not a dict")
		#should fail because "not a dict" is not a dict!
	except (AssertionError):
		pass
	else:
		raise Exception ('Exception not handled by asserts')

	try:
		descriptors.process.pd_update("not a dataframe",mydict)
		#should fail because "not a dict" is not a dict!
	except (AssertionError):
		pass
	else:
		raise Exception ('Exception not handled by asserts')

	return

def test_dict_2_list():
	"""make sure this only takes dictionaries as input"""
	try:
		descriptors.process.dict_2_list("not a dict")
		#should fail since "not a dict" is not a dict!
	except (AssertionError):
		pass
	else:
		raise Exception ('Exception not handled by asserts')
	return


def test_imp_one_cycle():
	"""tests loading something that isn't Excel data"""
	try:
		descriptors.process.imp_one_cycle('test.xsls', 'c', 7, "bob's battery" )
		#should fail because this file doesn't exist in the test path
	except (AssertionError):
		pass
	else:
		raise Exception ('Exception not handled by asserts')

	return


def test_descriptor_func():
	"""test the input is a single column of Voltage or smoothed dQ/dV data"""
	df = pd.DataFrame({"Voltage(V)":[1,2,3], "Smoothed_dQ/dV": [4,5,6]})
	proper_V = df['Voltage(V)']
	proper_dqdv = df["Smoothed_dQ/dV"]

	try:
		descriptors.fitters.descriptor_func(df, proper_dqdv,'c',7,"bob's batteries")
		#should raise assertion error since the column for voltage is bigger has more than one column
	except (AssertionError):
		pass
	else:
		raise Exception ("exception not handled by asserts.")
	try:
		descriptors.fitters.descriptor_func(proper_V, df,'c',7,"bob's batteries")
	except (AssertionError):
		pass
	else:
		raise Exception ("exception not handled by asserts.")

	return


def test_cd_dataframe():
	df = pd.DataFrame({"Voltage(V)":[1,2,3], "Smoothed_dQ/dV": [4,5,6]})
	proper_V = df['Voltage(V)']
	proper_dqdv = df["Smoothed_dQ/dV"]
	try:
		descriptors.fitters.cd_dataframe(proper_V,proper_dqdv, 'd')
		#this should fail because if dqdv is negative, it is probably discharge data and we want to flip to be positive for peak finding
	except (AssertionError):
		pass
	else:
		raise Exception ("Exception not handled by asserts")

	return


def test_peak_finder():
	"""test the input is a single column of Voltage or smoothed dQ/dV data"""
	df = pd.DataFrame({"Voltage(V)":[1,2,3], "Smoothed_dQ/dV": [4,5,6]})
	proper_V = df['Voltage(V)']
	proper_dqdv = df["Smoothed_dQ/dV"]
	try:
		descriptors.fitters.peak_finder(df, proper_dqdv,'c')
		#should raise assertion error since the dataset is too small to fit peaks
	except (AssertionError):
		pass
	else:
		raise Exception ("exception not handled by asserts.")

	return


def test_label_gen():
	"""make sure a number is the input and a string is the output"""
	try:
		descriptors.fitters.label_gen("not a number")
		#should fail because this only works with numbers
	except (AssertionError):
		pass
	else:
			raise Exception("Exception not handled by asserts")

	return

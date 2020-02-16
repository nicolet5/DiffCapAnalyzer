import dash_html_components as html
import pandas as pd
import sqlite3 as sql
import numpy as np
import os

from diffcapanalyzer.app_helper_functions import check_database_and_get_creds
from diffcapanalyzer.app_helper_functions import decoded_to_dataframe
from diffcapanalyzer.app_helper_functions import pop_with_db
from diffcapanalyzer.app_helper_functions import get_model_dfs
from diffcapanalyzer.app_helper_functions import generate_model
from diffcapanalyzer.databasewrappers import process_data
from diffcapanalyzer.databasewrappers import get_filename_pref


test_db = 'tests/test_data/test_db.db'
test_filename = 'tests/test_data/test_data.csv'
test_datatype = 'ARBIN'
test_filename_mac = 'tests/test_data/test_data_mac.csv'
test_datatype_mac = 'MACCOR'
test_username = 'Mr. Foo Bar'
decoded_dataframe = decoded_to_dataframe(None, test_datatype, test_filename)
decoded_dataframe_mac = decoded_to_dataframe(None, test_datatype_mac, test_filename_mac)

if os.path.exists(test_db): 
	os.remove(test_db)

def test_check_databases_and_get_creds():
	"""testing that a new database is created called test_new.db
	and that the new database has the default username + password
	pair """
	test_new_database = 'test_new.db'
	assert not os.path.exists('test_new.db')

	valid_usernames_passwords = check_database_and_get_creds(test_new_database)

	assert valid_usernames_passwords == [['Example User', 'password']]
	assert os.path.exists('test_new.db')
	
	os.remove('test_new.db')
	assert not os.path.exists('test_new.db')

	return


def test_pop_with_db():
	"""test that the clean and raw dataframes are 
	returned from this function from a file'"""

	process_data(test_filename, test_db, decoded_dataframe, 
					   test_datatype, test_username)

	df_clean, df_raw = pop_with_db(test_filename, test_db)

	assert df_clean is not None
	assert type(df_clean) == pd.DataFrame

	assert df_raw is not None
	assert type(df_raw) == pd.DataFrame

	assert 'Smoothed_dQ/dV' in df_clean.columns
	os.remove(test_db)
	return 

def test_pop_with_db_for_maccor():
	"""test that the clean and raw dataframes are 
	returned from this function from a file'"""

	process_data(test_filename_mac, test_db, decoded_dataframe_mac, 
					   test_datatype_mac, test_username)

	df_clean, df_raw = pop_with_db(test_filename_mac, test_db)

	assert df_clean is not None
	assert type(df_clean) == pd.DataFrame

	assert df_raw is not None
	assert type(df_raw) == pd.DataFrame

	assert 'Smoothed_dQ/dV' in df_clean.columns
	os.remove(test_db)
	return 

def test_get_model_dfs(): 
	"""This tests that the model results returned make sense 
	with respect to each other. First tests types of returned 
	variables, and also checks that the number of peaks found 
	in either charge or discharge sections correspond to the
	number of unique prefixes in the model vals dictionary."""


	process_data(test_filename, test_db, decoded_dataframe, 
					   test_datatype, test_username)

	df_clean, df_raw = pop_with_db(test_filename, test_db)
	cyc = 1
	lenmax = len(df_clean)
	peak_thresh = 0.7
	new_df_mody, model_c_vals, model_d_vals, \
	peak_heights_c, peak_heights_d = get_model_dfs(df_clean, 
												   test_datatype,
												   cyc, lenmax,
												   peak_thresh)

	assert type(new_df_mody) == pd.DataFrame
	assert type(model_c_vals) == dict and type(model_d_vals) == dict
	assert type(peak_heights_c) == list 
	assert type(peak_heights_d) == list

	# There should be at least a base_amplitude, base_center, base_fwhm, and base sigma for all cycles
	for key in ['base_amplitude', 'base_center', 'base_fwhm', 'base_height', 'base_sigma']:
		assert key in model_c_vals.keys()
		assert key in model_d_vals.keys()
		assert type(model_c_vals[key]) in (np.float64, np.float32, float, int)
		assert type(model_d_vals[key]) in (np.float64, np.float32, float, int)
		
	# There should be one peak height in peak_heights_cd for each unique key 
	for item in [[model_d_vals, peak_heights_d], [model_c_vals, peak_heights_c]]: 
		pref_list = []
		for key in item[0].keys():
			pref = key.split('_')[0]
			pref_list.append(pref)
			pref_set = set(pref_list)
		assert len(pref_set) - 1 == len(item[1])
		# minus one because of 'base' prefix
	os.remove(test_db)
	return 

def test_get_model_dfs_for_maccor(): 
	"""This tests that the model results returned make sense 
	with respect to each other. First tests types of returned 
	variables, and also checks that the number of peaks found 
	in either charge or discharge sections correspond to the
	number of unique prefixes in the model vals dictionary."""


	process_data(test_filename_mac, test_db, decoded_dataframe_mac, 
					   test_datatype_mac, test_username)

	df_clean, df_raw = pop_with_db(test_filename_mac, test_db)
	cyc = 1
	lenmax = len(df_clean)
	peak_thresh = 0.7
	new_df_mody, model_c_vals, model_d_vals, \
	peak_heights_c, peak_heights_d = get_model_dfs(df_clean, 
												   test_datatype_mac,
												   cyc, lenmax,
												   peak_thresh)

	assert type(new_df_mody) == pd.DataFrame
	assert type(model_c_vals) == dict and type(model_d_vals) == dict
	assert type(peak_heights_c) == list 
	assert type(peak_heights_d) == list

	# There should be at least a base_amplitude, base_center, base_fwhm, and base sigma for all cycles
	for key in ['base_amplitude', 'base_center', 'base_fwhm', 'base_height', 'base_sigma']:
		assert key in model_c_vals.keys()
		assert key in model_d_vals.keys()
		assert type(model_c_vals[key]) in (np.float64, np.float32, float, int)
		assert type(model_d_vals[key]) in (np.float64, np.float32, float, int)
		
	# There should be one peak height in peak_heights_cd for each unique key 
	for item in [[model_d_vals, peak_heights_d], [model_c_vals, peak_heights_c]]: 
		pref_list = []
		for key in item[0].keys():
			pref = key.split('_')[0]
			pref_list.append(pref)
			pref_set = set(pref_list)
		assert len(pref_set) - 1 == len(item[1])
		# minus one because of 'base' prefix
	os.remove(test_db)
	return 

def test_generate_model(): 
	"""Tests that three new tables are generated in the database 
	in the process of generating the model. Acutal model generation
	functions are tested further outside of this wrapper."""
	peak_thresh = 0.7
	
	process_data(test_filename, test_db, decoded_dataframe, 
					   test_datatype, test_username)
	filename_pref = get_filename_pref(test_filename)
	df_clean, df_raw = pop_with_db(test_filename, test_db)

	feedback = generate_model(df_clean, filename_pref, 
							  peak_thresh, test_db)
	assert type(feedback) == str
	names_list = get_table_names(test_db)

	list_new_tables =  ['-ModPoints', 'ModParams', '-descriptors']
	for i in list_new_tables: 
		assert filename_pref + i in names_list
	os.remove(test_db)
	return

def test_generate_model_for_maccor(): 
	"""Tests that three new tables are generated in the database 
	in the process of generating the model. Acutal model generation
	functions are tested further outside of this wrapper."""
	peak_thresh = 0.7
	
	process_data(test_filename_mac, test_db, decoded_dataframe_mac, 
					   test_datatype_mac, test_username)
	filename_pref = get_filename_pref(test_filename_mac)
	df_clean, df_raw = pop_with_db(test_filename_mac, test_db)

	feedback = generate_model(df_clean, filename_pref, 
							  peak_thresh, test_db)
	assert type(feedback) == str
	names_list = get_table_names(test_db)

	list_new_tables =  ['-ModPoints', 'ModParams', '-descriptors']
	for i in list_new_tables: 
		assert filename_pref + i in names_list
	os.remove(test_db)
	return

# Supporting functions: 
def get_table_names(database): 
	"""Returns all the names of tables that exist in the database"""
	if os.path.exists(database): 
		con = sql.connect(database)
		c = con.cursor()
		names_list = []
		for row in c.execute("""SELECT name FROM sqlite_master WHERE type='table'""" ):
			names_list.append(row[0])
		con.close()
	return names_list
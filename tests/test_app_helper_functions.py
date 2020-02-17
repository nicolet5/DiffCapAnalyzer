import dash_html_components as html
import pandas as pd
import sqlite3 as sql
import numpy as np
import os

from diffcapanalyzer.app_helper_functions import check_database_and_get_creds
from diffcapanalyzer.app_helper_functions import decoded_to_dataframe
from diffcapanalyzer.app_helper_functions import pop_with_db
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
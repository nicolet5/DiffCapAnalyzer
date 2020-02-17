import os
import pandas as pd

from diffcapanalyzer.databasewrappers import process_data
from diffcapanalyzer.databasewrappers import parse_update_master
from diffcapanalyzer.databasewrappers import macc_chardis
from diffcapanalyzer.databasewrappers import if_file_exists_in_db
from diffcapanalyzer.databasewrappers import get_db_filenames
from diffcapanalyzer.databasewrappers import get_filename_pref
from diffcapanalyzer.databasewrappers import get_table_names
from diffcapanalyzer.descriptors import generate_model
from diffcapanalyzer.descriptors import param_dicts_to_df
from diffcapanalyzer.app_helper_functions import decoded_to_dataframe
from diffcapanalyzer.databasefuncs import get_file_from_database


test_db = 'tests/test_data/test_db.db'
test_filename = 'tests/test_data/test_data.csv'
test_datatype = 'ARBIN'
test_username = 'Example User'
decoded_dataframe = decoded_to_dataframe(None, test_datatype, test_filename)

def test_process_data():
	"""Tests the process data function adds the correct
	datatables to the database."""
	ans = process_data(test_filename, test_db, decoded_dataframe, test_datatype, test_username)
	# shouldn't return anything:
	assert ans == None 
	names_list = get_table_names(test_db)
	assert 'master_table' in names_list
	list_new_tables =  ['Raw', '-CleanCycle1', '-Cycle1', 'CleanSet']
	for i in list_new_tables: 
		assert get_filename_pref(test_filename)+ i in names_list
	os.remove(test_db)
	return

def test_parse_update_master(): 
	"""Tests the parse update master function"""
	process_data(test_filename, test_db, decoded_dataframe, 
					   test_datatype, test_username)
	core_test_filename = get_filename_pref(test_filename)
	ans = parse_update_master(core_test_filename, test_db, 
							  test_datatype, decoded_dataframe,
							  test_username)
	assert ans == None 
	master_table = get_file_from_database('master_table', test_db)
	name = get_filename_pref(test_filename)
	assert name +'Raw' in list(master_table['Raw_Data_Prefix'])
	assert name  + 'CleanSet' in list(master_table['Cleaned_Data_Prefix'])
	assert name + '-CleanCycle' in list(master_table['Cleaned_Cycles_Prefix'])
	assert name + '-descriptors' in list(master_table['Descriptors_Prefix'])
	os.remove(test_db)
	return 

def test_macc_chardis(): 
	"""tests that the macc_chardis function gives the 
	right output depending on the string in the Md column 
	in a dataframe."""
	test_df= pd.DataFrame({'ColX':[0, 1, 2], 
						   'Md': ['D', 'C', 'Something else']})
	test_row1 = test_df.iloc[0]
	test_row2 = test_df.iloc[1]
	test_row3 = test_df.iloc[2]
	assert macc_chardis(test_row1) == -1
	assert macc_chardis(test_row2) == 1
	assert macc_chardis(test_row3) == 1
	return 

def test_if_file_exists_in_db(): 
	"""Tests the if_file_exists_in_db function gives the 
	correct result when there is a file that does exist in 
	the test database, when ther is a file that does not 
	exist in the database, and when there is a database name 
	given for a database that does not exist."""
	process_data(test_filename, test_db, decoded_dataframe,
				 test_datatype, test_username)
	answer = if_file_exists_in_db(test_db, test_filename)
	assert answer == True
	answer2 = if_file_exists_in_db(test_db, 'ThisFileDoesNotExist.csv')
	assert answer2 == False
	assert if_file_exists_in_db('NotaRealDB.db', test_filename) == False
	assert if_file_exists_in_db('NotaRealDB.db', 'ThisFileDoesNotExist.csv') == False
	os.remove(test_db)
	return 

def test_get_db_filenames(): 
	"""Tests that the list of table names for one 
	specific user are returned accurately"""
	test_db = 'test_database.db'
	test_filename1 = 'file1.csv'
	decoded_dataframe1 = pd.DataFrame({'Cycle_Index': [1, 1, 2], 
									  'Data_Point': [0, 1, 2], 
									  'Voltage(V)': [0.3, 0.4, 0.5], 
									  'Current(A)': [1.5, 1.4, 1.3], 
									  'Discharge_Capacity(Ah)': [0, 0, 0], 
									  'Charge_Capacity(Ah)': [10, 20, 30], 
									  'Step_Index': [1, 1, 1]})
	test_datatype1 =  'ARBIN'
	test_username1 = 'User1'

	test_filename2 = 'file2.csv'
	decoded_dataframe2 = pd.DataFrame({'Cycle_Index': [1, 1, 1], 
								  'Data_Point': [10, 11, 12], 
								  'Voltage(V)': [10.3, 10.4, 10.5], 
								  'Current(A)': [11.5, 11.4, 11.3], 
								  'Discharge_Capacity(Ah)': [0, 10, 10], 
								  'Charge_Capacity(Ah)': [110, 120, 130], 
								  'Step_Index': [0, 0, 0]})
	test_datatype2 = 'ARBIN'
	test_username2 = 'User2'

	process_data(test_filename1, test_db, decoded_dataframe1, test_datatype1, test_username1)
	process_data(test_filename2, test_db, decoded_dataframe2, test_datatype2, test_username2)

	names_list1 = get_db_filenames(test_db, test_username1)
	assert names_list1 == ['file1']

	names_list2 = get_db_filenames(test_db, test_username2)
	assert names_list2 == ['file2']
	os.remove("test_database.db")
	return 
	

def test_get_filename_pref():
	"""Tests that the filename to be attached to the file 
	in the database is parsed out of the path and extension 
	nicely."""
	foo1 = 'Directory1/Directory2/anotherDirectory/real_filename.csv'
	foo2 = 'dir100/myfilefoo.someextension'
	foo3 = 'myfilename.csv'
	foo4 = 'foo'

	assert get_filename_pref(foo1) == 'real_filename'
	assert get_filename_pref(foo2) == 'myfilefoo'
	assert get_filename_pref(foo3) == 'myfilename'
	assert get_filename_pref(foo4) == 'foo'
	return 

def test_get_table_names():
	"""Tests that the correct table names are returned"""
	# first make sure all data is processed
	process_data(test_filename, test_db, decoded_dataframe,
				 test_datatype, test_username)
	new_peak_thresh = 0.7
	core_filename = get_filename_pref(test_filename)
	df_clean = get_file_from_database(core_filename+'CleanSet', test_db)
	feedback = generate_model(df_clean,core_filename, new_peak_thresh, test_db)
	assert core_filename + 'ModParams' in get_table_names(test_db)
	param_dicts_to_df(core_filename + 'ModParams', test_db)

	names_list = get_table_names(test_db)
	expected_list = ['master_table', 'test_data-CleanCycle1', 
					 'test_data-Cycle1', 'test_data-ModPoints',
					 'test_data-descriptors','test_dataCleanSet', 
					 'test_dataModParams', 'test_dataRaw', 
					 'test_dataUnalteredRaw','users']
	assert set(names_list) == set(expected_list)
	os.remove(test_db)
	return
from databasefuncs import update_database_newtable
from databasefuncs import get_file_from_database
from databasefuncs import update_master_table
from databasefuncs import init_master_table

import os
import pandas as pd
import sqlite3 as sql

def test_update_database_newtable():
	df = pd.DataFrame({'A': [1, 2, 3], 
					   'B': [10, 20, 30], 
					   'C': [100, 200, 300]})
	upload_filename = 'my_amazing_file'
	database_name = 'amazing_database.db'
	update_database_newtable(df, upload_filename, database_name)
	assert 'my_amazing_file' in get_table_names(database_name)

	os.remove('amazing_database.db')
	return

def test_get_file_from_database():
	df = pd.DataFrame({'A': [1, 2, 3], 
					   'B': [10, 20, 30], 
					   'C': [100, 200, 300]})
	upload_filename = 'my_other_amazing_file'
	database_name = 'another_amazing_database.db'
	update_database_newtable(df, upload_filename, database_name)
	assert os.path.exists('another_amazing_database.db')
	result = get_file_from_database('my_other_amazing_file', 
								    'another_amazing_database.db')
	assert pd.DataFrame.equals(result, df)
	neg_result = get_file_from_database('something_else', 
										'another_amazing_database.db')
	assert neg_result == None
	os.remove('another_amazing_database.db')
	return


def test_update_master_table():
	init_master_table('amazing_database2.db')
	update_dict = {'Dataset_Name': 'my_dataset', 
				   'Raw_Data_Prefix': 'raw', 
				   'Cleaned_Data_Prefix': 'clean', 
				   'Cleaned_Cycles_Prefix': 'cycles', 
				   'Descriptors_Prefix': 'desc'}
	user_name = 'fooname'
	update_master_table(update_dict, 'amazing_database2.db', 
						user_name)
	test_df = get_file_from_database('master_table', 'amazing_database2.db')
	expected = pd.DataFrame({
				   'Dataset_Name': ['my_dataset'], 
				   'Raw_Data_Prefix': ['raw'], 
				   'Cleaned_Data_Prefix': ['clean'], 
				   'Cleaned_Cycles_Prefix': ['cycles'], 
				   'Descriptors_Prefix': ['desc'], 
				   'Username': ['fooname']})
	assert pd.DataFrame.equals(test_df, expected)

	neg_result = update_master_table(None, 'amazing_database2.db', 
									 user_name)
	assert neg_result == [{}]

	os.remove('amazing_database2.db')
	return

def test_init_master_table():
	init_master_table('new_database.db')
	assert os.path.exists('new_database.db')
	init_table = get_file_from_database('master_table',
										'new_database.db')
	expected_cols = ['Dataset_Name', 
				   'Raw_Data_Prefix', 
				   'Cleaned_Data_Prefix', 
				   'Cleaned_Cycles_Prefix', 
				   'Descriptors_Prefix', 
				   'Username']
	assert init_table.empty
	assert set(expected_cols) == set(init_table.columns)
	os.remove('new_database.db')
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
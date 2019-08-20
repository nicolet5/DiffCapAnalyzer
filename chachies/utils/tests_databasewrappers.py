
from databasewrappers import *

test_db = 'test_db.db'
test_filename = 'test_data.xlsx'
test_datatype = 'ARBIN'
test_username = 'Example User'

def test_process_data():
	"""Tests the process data function adds the correct
	datatables to the database."""
	decoded_dataframe = pd.read_excel(test_filename, 1)
	ans = process_data(test_filename, test_db, decoded_dataframe, test_datatype, test_username)
	# shouldn't return anything:
	assert ans == None 
	names_list = get_table_names(test_db)
	assert 'master_table' in names_list
	list_new_tables =  ['Raw', '-CleanCycle1', '-Cycle1', 'CleanSet']
	for i in list_new_tables: 
		assert get_filename_pref(test_filename)+ i in names_list
	return

def test_parse_update_master(): 
	"""Tests the parse update master function"""
	decoded_dataframe = pd.read_excel(test_filename, 1)
	ans = parse_update_master(test_filename, test_db, test_datatype, decoded_dataframe, test_username)
	assert ans == None 
	master_table = dbfs.get_file_from_database('master_table', test_db)
	name = get_filename_pref(test_filename)
	print(master_table)
	print(name)
	assert name +'Raw' in list(master_table['Raw_Data_Prefix'])
	assert name  + 'CleanSet' in list(master_table['Cleaned_Data_Prefix'])
	assert name + '-CleanCycle' in list(master_table['Cleaned_Cycles_Prefix'])
	assert name + 'ModParams-descriptors' in list(master_table['Descriptors_Prefix'])
	return 

def test_macc_chardis(): 
	"""tests that the macc_chardis function gives the 
	right output depending on the string in the Md column 
	in a dataframe."""
	test_df= pd.DataFrame({'ColX':[0, 1, 2], 'Md': ['D', 'C', 'Something else']})
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
	answer = if_file_exists_in_db(test_db, test_filename)
	assert answer == True
	answer2 = if_file_exists_in_db(test_db, 'ThisFileDoesNotExist.csv')
	assert answer2 == False
	assert if_file_exists_in_db('NotaRealDB.db', test_filename) == False
	assert if_file_exists_in_db('NotaRealDB.db', 'ThisFileDoesNotExist.csv') == False
	return 

def test_get_db_filenames(): 
	"""Tests that the list of table names for one 
	specific user are returned accurately"""
	test_db = 'test_database.db'
	test_filename1 = 'file1.xlsx'
	decoded_dataframe1 = pd.DataFrame({'Cycle_Index': [1, 1, 2], 
									  'Data_Point': [0, 1, 2], 
									  'Voltage(V)': [0.3, 0.4, 0.5], 
									  'Current(A)': [1.5, 1.4, 1.3], 
									  'Discharge_Capacity(Ah)': [0, 0, 0], 
									  'Charge_Capacity(Ah)': [10, 20, 30], 
									  'Step_Index': [1, 1, 1]})
	test_datatype1 =  'ARBIN'
	test_username1 = 'User1'

	test_filename2 = 'file2.xlsx'
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

	return 
	

def test_my_pseudovoigt():
	"""Tests that output of pseudovoigt is as expected"""
	fit2 = my_pseudovoigt(x = 3, cent = 3, amp = 0 , fract = 0.3, sigma = 0.1)
	assert fit2 == [0]
	fit2 = my_pseudovoigt(x = 4, cent = 2, amp = 1, fract = 0.1, sigma = 0.05)
	assert fit2 != [0]
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
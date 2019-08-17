
from databasewrappers import *

test_db = 'test_database.db'
test_filename = 'ExampleData.xlsx'
test_datatype = 'ARBIN'
test_username = 'Example User'

def test_process_data():
	"""Tests the process data function adds the correct
	datatables to the database."""
	decoded_dataframe = pd.read_excel(test_filename, 1)
	ans = process_data(test_filename, test_db, decoded_dataframe, test_datatype, test_username)
	# shouldn't return anything:
	assert ans == None 
	names_list = get_table_names(test_database)
	assert 'master_table' in names_list
	list_new_tables =  ['Raw', '-CleanCycle1', '-Cycle1', 'CleanSet']
    for i in list_new_tables: 
        assert get_filename_pref(test_filename)+ i in names_list
    return

def test_parse_update_master(): 
	"""Tests the parse update master function"""
	decoded_dataframe = pd.read_excel(test_filename, 1)
	ans = parse_update_master(test_filename, test_database, test_datatype, decoded dataframe, test_username)
	assert ans == None 
	master_table = dbfs.get_file_from_database('master_table', test_database)
	name = get_filename_pref(test_filename)
	assert name +'Raw' in master_table['Raw_Data_Prefix']
	assert name  + 'CleanSet' in master_table['Cleaned_Data_Prefix']
	assert name + '-CleanCycle' in master_table['Cleaned_Cycles_Prefix']
	assert name + 'ModParams-descriptors' in master_table['Descriptors_Prefix']
	return 

def test_macc_chardis(): 
	"""tests that the macc_chardis function gives the 
	right output depending on the string in the Md column 
	in a dataframe."""
	test_df= pd.DataFrame({'ColX':[0, 1, 2], 'Md': ['D', 'C', 'Something else']})
	test_row1 = test_df[0]
	test_row2 = test_df[1]
	test_row3 = test_df[2]
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
	answer = if_file_exists_in_db(test_database, test_filename)
	assert answer == True
	answer2 = if_file_exists_in_db(test_database, 'ThisFileDoesNotExist.csv')
	assert answer2 == False
	assert if_file_exists_in_db('NotaRealDB.db', test_filename) == False
	assert if_file_exists_in_db('NotaReadDB.db', 'ThisFileDoesNotExist.csv') == False
	return 

def test_get_db_filenames(): 
	"""Tests that the list of table names for one 
	specific user are returned accurately"""

	




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
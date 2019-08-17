
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
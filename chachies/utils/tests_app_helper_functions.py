from app_helper_functions import *

test_db = 'test_database.db'

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
	returned from this function from a file that
	already exists in the database 'ExampleData'"""

	df_clean, df_raw = pop_with_db('ExampleData.xlsx', test_db)

	assert df_clean is not None
	assert type(df_clean) == pd.DataFrame

	assert df_raw is not None
	assert type(df_raw) == pd.DataFrame

	assert 'Smoothed_dQ/dV' in df_clean.columns

	return 

def test_get_model_dfs(): 
	"""This tests that the model results returned make sense 
	with respect to each other. First tests types of returned 
	variables, and also checks that the number of peaks found 
	in either charge or discharge sections correspond to the
	number of unique prefixes in the model vals dictionary."""

	df_clean, df_raw = pop_with_db('ExampleData.xlsx', test_db)
	datatype = 'ARBIN' 
	cyc = 1
	lenmax = len(df_clean)
	peak_thresh = 0.7
	new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d = get_model_dfs(df_clean, datatype, cyc, lenmax, peak_thresh)

	assert type(new_df_mody) == pd.DataFrame
	assert type(model_c_vals) == dict and type(model_d_vals) == dict
	assert type(peak_heights_c) == list 
	assert type(peak_heights_d) == list

	# There should be at least a base_amplitude, base_center, base_fwhm, and base sigma for all cycles
	for key in ['base_amplitude', 'base_center', 'base_fwhm', 'base_height', 'base_sigma']:
	    assert key in model_c_vals.keys()
	    assert key in model_d_vals.keys()
	    assert type(model_c_vals[key]) == float or type(model_c_vals[key]) == int
	    assert type(model_d_vals[key]) == float or type(model_c_vals[key]) == int
	    
	# There should be one peak height in peak_heights_cd for each unique key 
	for item in [[model_d_vals, peak_heights_d], [model_c_vals, peak_heights_c]]: 
	    pref_list = []
	    for key in item[0].keys():
	        pref = key.split('_')[0]
	        pref_list.append(pref)
	        pref_set = set(pref_list)
	    assert len(pref_set) - 1 == len(item[1])
	    # minus one because of 'base' prefix
	return 

def test_generate_model(): 
	"""Tests that three new tables are generated in the database 
	in the process of generating the model. Acutal model generation
	functions are tested further outside of this wrapper."""
	filename = 'ExampleData.xlsx'
	peak_thresh = 0.7
	database = test_db
    feedback = generate_model(df_clean, filename, peak_thresh, database)
    assert type(feedback) == type(html.Div([]))
    names_list = get_table_names(database)
    filename_pref = filename.split('.')[0]
    list_new_tables =  ['-ModPoints', 'ModParams', 'ModParams-descriptors']
    for i in list_new_tables: 
        assert filename_pref + i in names_list
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
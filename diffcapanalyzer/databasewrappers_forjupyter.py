import io
import os
import pandas as pd 
from pandas import ExcelWriter
import pandas.io.sql as pd_sql
import sqlite3 as sql
import chachifuncs as ccf
import descriptors
import databasefuncs as dbfs
from app_helper_functions import generate_model

# This version takes a path to a file instead of the decoded contents (like in version 
# databasewrappers_exp). The decoded contents in the other version are needed because the 
# file is being passed through the app. Here, we are using jupyter notebooks, so we can 
# use the path to the file instead of decoded contents. 


def process_data(file_name, database_name, path, datatype, username):
	# Takes raw file 
	# sep_cycles
	# cleans cycles
	# gets descriptors - peak calcs
	# put back together - save 
	thresh1 = '0.0'
	thresh2 = '0.0'
	if not os.path.exists(database_name): 
		print('That database does not exist-creating it now.')
		dbfs.init_master_table(database_name)
	
	con = sql.connect(database_name)
	c = con.cursor()
	names_list = []
	for row in c.execute("""SELECT name FROM sqlite_master WHERE type='table'""" ):
		names_list.append(row[0])
	con.close()
	file_name3 = file_name 
	while '/' in file_name3:
		file_name3 = file_name3.split('/', maxsplit = 1)[1]
	name3 = file_name3.split('.')[0] 
	if name3 + 'Raw' in names_list: 
		print('That file name has already been uploaded into the database.')
	else:
		print('Processing that data')	
		parse_update_master(file_name, database_name, datatype, path, username)
		# this takes the info from the filename and updates the master table in the database. 
		# this also adds the raw data fram into the database
		cycle_dict = ccf.load_sep_cycles(file_name, database_name, datatype)
		clean_cycle_dict= ccf.get_clean_cycles(cycle_dict, file_name, database_name, datatype, thresh1, thresh2)
		clean_set_df = ccf.get_clean_sets(clean_cycle_dict, file_name, database_name)

		cleanset_name = name3 + 'CleanSet'
		df_clean = dbfs.get_file_from_database(cleanset_name, database_name)
		v_toappend_c = []
		v_toappend_d = []
		new_peak_thresh = 0.3 
		# just as a starter value
		feedback = generate_model(v_toappend_c, v_toappend_d, df_clean, file_name, new_peak_thresh, database_name)

		# desc_df = descriptors.get_descriptors(clean_cycle_dict, datatype, windowlength = 3, polyorder = 1)
		# dbfs.update_database_newtable(desc_df, name3 + '-descriptors', database_name)
		print('Database updated with descriptors.')

	return


def parse_update_master(file_name, database_name, datatype, path, username):
	#decoded = decoded_contents
	file_name2 = file_name
	while '/' in file_name2:
		file_name2 = file_name2.split('/', maxsplit = 1)[1]
	name = file_name2.split('.')[0]    
	if datatype == 'Arbin':
		data1 = pd.read_excel(path, 1)
		data1['datatype'] = 'Arbin'
	elif datatype == 'MACCOR':
		data1 = pd.read_csv(path, header = 12, delimiter='\t', index_col=False)
		dataheader = pd.read_fwf(path, delimiter = '\t')
		weight = float(dataheader.iloc[2][0].split('mg')[0].split('_')[1].replace('p', '.'))
		data1['Const_Weight[mg]'] = weight

		data1['MaccCharLab'] = data1.apply(lambda row: macc_chardis(row), axis = 1)
		data1['Current(A)'] = data1['Current [A]']*data1['MaccCharLab']
		data1['datatype'] = 'MACCOR'
		
		data1.rename(columns={'Cycle C': 'Cycle_Index', 'Voltage [V]': 'Voltage(V)', 'Current [A]': 'Abs_Current(A)', 'Cap. [Ah]': 'Cap(Ah)'}, inplace=True)

	else: 
		print('please put in either "Arbin" or "MACCOR" for datatype.')

	data = ccf.calc_dq_dqdv(data1, datatype)
	dbfs.update_database_newtable(data, name + 'Raw', database_name)
	update_dic ={'Dataset_Name': name,'Raw_Data_Prefix': name +'Raw',
					'Cleaned_Data_Prefix': name + 'CleanSet', 
					'Cleaned_Cycles_Prefix': name + '-CleanCycle', 'Descriptors_Prefix': name + '-descriptors'}
	dbfs.update_master_table(update_dic, database_name, username)
	return

def macc_chardis(row):
	if row['Md'] == 'D':
		return -1
	else:
		return 1

def if_file_exists_in_db(database_name, file_name):
	if os.path.exists(database_name): 
		con = sql.connect(database_name)
		c = con.cursor()
		names_list = []
		for row in c.execute("""SELECT name FROM sqlite_master WHERE type='table'""" ):
			names_list.append(row[0])
		con.close()
		while '/' in file_name:
			file_name = file_name.split('/', maxsplit = 1)[1]
		name3 = file_name.split('.')[0] 
		if name3 + 'CleanSet' in names_list: 
			ans = True
		else:
			ans = False
	else:
		ans = False
	return ans

def get_db_filenames(database_name):
	con = sql.connect(database_name)
	c = con.cursor()
	names_list = []
	raw_names = []
	cleanset_names = []
	for row in c.execute("""SELECT name FROM sqlite_master WHERE type='table'""" ):
		names_list.append(row[0])
	con.close()

	for item in names_list:
		if 'Raw' in item:
			raw_names.append(item)
		else: 
			None
	return raw_names
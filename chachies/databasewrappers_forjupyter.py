import io
import os
import pandas as pd 
from pandas import ExcelWriter
import pandas.io.sql as pd_sql
import sqlite3 as sql
import chachifuncs_exp as ccf
import descriptors
import databasefuncs as dbfs
# OVERALL Wrapper Function
################################
# This version takes a path to a file instead of the decoded contents (like in version 
# databasewrappers_exp). The decoded contents in the other version are needed because the 
# file is being passed through the app. Here, we are using jupyter notebooks, so we can 
# use the path to the file instead of decoded contents. 


def process_data(file_name, database_name, path, datatype, thresh1, thresh2):
	# Takes raw file 
	# sep_cycles
	# cleans cycles
	# gets descriptors - peak calcs
	# put back together - save 
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
		#datatype = input('What datatype do you have (either CALCE or MACCOR)')
		print('Processing that data')	
		parse_update_master(file_name, database_name, datatype, path)
		#this takes the info from the filename and updates the master table in the database. 
		# this also adds the raw data fram into the database
		cycle_dict = ccf.load_sep_cycles(file_name, database_name, datatype)
		clean_cycle_dict= ccf.get_clean_cycles(cycle_dict, file_name, database_name, datatype, thresh1, thresh2)
		clean_set_df = ccf.get_clean_sets(clean_cycle_dict, file_name, database_name)
		##################################################
		#uncomment the below to get descriptors ###########
		#####################################################
		desc_df = descriptors.get_descriptors(clean_cycle_dict, datatype, windowlength = 3, polyorder = 1)
		dbfs.update_database_newtable(desc_df, name3 + '-descriptors', database_name)
		print('Database updated with descriptors.')
		###################################################################
		#######################################################################
		# pass this clean cycle dictionary to function to get descriptors - same as what we did with get clean setss
		#for k,v in clean_cycle_dict.items():
		#	print(k,v)
		# there are definitely values in the dictionary at this point 
		#should Switch descriptors to be after we get the clean set. maybe ask user if we want descriptors
		# since it seems to be the longest step
		

	return


def parse_update_master(file_name, database_name, datatype, path):
	#decoded = decoded_contents
	file_name2 = file_name
	while '/' in file_name2:
		file_name2 = file_name2.split('/', maxsplit = 1)[1]
	name = file_name2.split('.')[0]    
	if datatype == 'CALCE':
		data1 = pd.read_excel(path, 1)
	elif datatype == 'MACCOR':
		data1 = pd.read_csv(path, header = 12, delimiter='\t', index_col=False)
		dataheader = pd.read_fwf(path, delimiter = '\t')
		weight = float(dataheader.iloc[2][0].split('mg')[0].split('_')[1].replace('p', '.'))
		data1['Const_Weight[mg]'] = weight
		#somehow set the Current column to negative when the 'Md' column has a D in it(current > 0 - charge)
		data1['MaccCharLab'] = data1.apply(lambda row: macc_chardis(row), axis = 1)
		data1['Current(A)'] = data1['Current [A]']*data1['MaccCharLab']

		data1.rename(columns={'Voltage [V]': 'Voltage(V)', 'Current [A]': 'Abs_Current(A)', 'Cap. [Ah]': 'Cap(Ah)'}, inplace=True)
		#print(data1.columns)
	else: 
		print('please put in either "CALCE" or "MACCOR" for datatype.')
	# this is the only time the raw data file is read into the program from excel
	data = ccf.calc_dq_dqdv(data1, datatype)
	dbfs.update_database_newtable(data, name + 'Raw', database_name)
	update_dic ={'Dataset_Name': name,'Raw_Data_Prefix': name +'Raw',
					'Cleaned_Data_Prefix': name + 'CleanSet', 
					'Cleaned_Cycles_Prefix': name + '-CleanCycle', 'Descriptors_Prefix': name + '-descriptors'}
	dbfs.update_master_table(update_dic, database_name)
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
		#elif 'CleanSet' in item: 
		#	cleanset_names.append(item)
		else: 
			None
	return raw_names
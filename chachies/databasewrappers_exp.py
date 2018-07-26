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



def process_data(file_name, database_name):
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
		print('Processing that data')	
		parse_update_master(file_name, database_name)
		#this takes the info from the filename and updates the master table in the database. 
		# this also adds the raw data fram into the database
		cycle_dict = ccf.load_sep_cycles(file_name, database_name)
		clean_cycle_dict= ccf.get_clean_cycles(cycle_dict, file_name, database_name)
		desc_df = descriptors.get_descriptors(clean_cycle_dict)
		dbfs.update_database_newtable(desc_df, name3 + '-descriptors', database_name)
		# pass this clean cycle dictionary to function to get descriptors - same as what we did with get clean setss
		#for k,v in clean_cycle_dict.items():
		#	print(k,v)
		# there are definitely values in the dictionary at this point 
		clean_set_df = ccf.get_clean_sets(clean_cycle_dict, file_name, database_name)

	return 


def parse_update_master(file_name, database_name):
	file_name2 = file_name
	while '/' in file_name2:
		file_name2 = file_name2.split('/', maxsplit = 1)[1]
	name = file_name2.split('.')[0]    
	data1 = pd.read_excel(file_name, 1)
	# this is the only time the raw data file is read into the program from excel
	data = ccf.calc_dq_dqdv(data1)
	dbfs.update_database_newtable(data, name + 'Raw', database_name)
	update_dic ={'Dataset_Name': name,'Raw_Data_Prefix': name +'Raw',
					'Cleaned_Data_Prefix': name + 'CleanSet', 
					'Cleaned_Cycles_Prefix': name + '-CleanCycle', 'Descriptors_Prefix': name + '-descriptors'}
	dbfs.update_master_table(update_dic, database_name)
	return
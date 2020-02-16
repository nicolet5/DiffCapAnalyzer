import ast 
import io
import os
import pandas as pd 
from pandas import ExcelWriter
import pandas.io.sql as pd_sql
import sqlite3 as sql
import scipy
import numpy as np

from diffcapanalyzer.chachifuncs import load_sep_cycles, get_clean_cycles, get_clean_sets, calc_dq_dqdv
from diffcapanalyzer.descriptors import dfsortpeakvals
from diffcapanalyzer.databasefuncs import init_master_table, update_database_newtable, update_master_table, get_file_from_database

def process_data(file_name, database_name, decoded_dataframe, 
				 datatype, username, windowlength = 9,
				 polyorder = 3):
	"""Takes raw file, separates cycles, cleans cycles, 
	gets the descriptors, saves descriptors for each cycle
	into database, puts cycles back together, and then saves
	resulting cleaned data. """
	if not os.path.exists(database_name): 
		init_master_table(database_name)
	names_list = get_table_names(database_name)
	core_file_name = get_filename_pref(file_name)
	if core_file_name + 'CleanSet' in names_list: 
		return 
	else:
		parse_update_master(core_file_name, database_name, 
							datatype, decoded_dataframe, username)
		cycle_dict = load_sep_cycles(core_file_name, 
										 database_name, 
										 datatype)
		clean_cycle_dict= get_clean_cycles(cycle_dict,
											   core_file_name, 
											   database_name, 
											   datatype,
											   windowlength, 
											   polyorder)
		clean_set_df = get_clean_sets(clean_cycle_dict,
										  core_file_name,
										  database_name)
	return


def parse_update_master(core_file_name, database_name, datatype, decoded_dataframe, username):
	"""Takes the file and calculates dq/dv from the raw data, 
	uploads that ot the database as the raw data, and 
	updates the master table with prefixes useful for accessing 
	that data related to the file uploaded."""
	# name = get_filename_pref(file_name)
	update_database_newtable(decoded_dataframe,
								  core_file_name + 'UnalteredRaw', 
								  database_name)

	data = calc_dq_dqdv(decoded_dataframe, datatype)
	update_database_newtable(data, core_file_name + 'Raw', 
								  database_name)
	update_dict ={'Dataset_Name': core_file_name,
				  'Raw_Data_Prefix': core_file_name +'Raw',
			      'Cleaned_Data_Prefix': core_file_name + 'CleanSet', 
				  'Cleaned_Cycles_Prefix': core_file_name + '-CleanCycle', 
				  'Descriptors_Prefix': core_file_name + '-descriptors',
				  'Model_Parameters_Prefix': core_file_name + 'ModParams', 
				  'Model_Points_Prefix': core_file_name + '-ModPoints', 
				  'Raw_Cycle_Prefix': core_file_name + '-Cycle', 
				  'Original_Data_Prefix': core_file_name + 'UnalteredRaw'}
	update_master_table(update_dict, database_name, username)
	return

def macc_chardis(row):
	"""Assigns an integer to distinguish rows of 
	charging cycles from those of discharging 
	cycles. -1 for discharging and +1 for charging."""
	if row['Md'] == 'D':
		return -1
	else:
		return 1

def if_file_exists_in_db(database_name, file_name):
	"""Checks if file exists in the given database
	by checking the list of table names for the 
	table name corresponding to the whole CleanSet."""
	if os.path.exists(database_name): 
		names_list = get_table_names(database_name)
		filename_pref = get_filename_pref(file_name)
		if filename_pref + 'CleanSet' in names_list: 
			ans = True
		else:
			ans = False
	else:
		ans = False
	return ans

def get_db_filenames(database_name, username):
	""" This is used to populate the dropdown menu, so users can only access their data if their 
	name is in the user column"""
	con = sql.connect(database_name)
	c = con.cursor()
	names_list = []
	for row in c.execute("""SELECT Dataset_Name, Username FROM master_table WHERE Username = '%s'""" % username):
		# this chooses the dataset_name and username from the mastertable where the username is equal to the username used
		# to sign in 
		names_list.append(row[0])
	con.close()
	exists_list = []
	for name in names_list: 
		if if_file_exists_in_db(database_name, name):
			exists_list.append(name)
	return exists_list


def my_pseudovoigt(x, cent, amp, fract, sigma): 
	"""This function is from http://cars9.uchicago.edu/software/python/lmfit/builtin_models.html"""
	sig_g = sigma/np.sqrt(2*np.log(2)) # calculate the sigma_g parameter for the gaussian distribution 
	part1 = (((1-fract)*amp)/(sig_g*np.sqrt(2*np.pi)))*np.exp((-(x-cent)**2)/(2*sig_g**2))
	part2 = ((fract*amp)/np.pi)*(sigma/((x-cent)**2+sigma**2))
	fit = part1 + part2
	return(fit)

def param_dicts_to_df(mod_params_name, database):
	"""Uses the already generated parameter dictionaries stored in the filename+ModParams 
	datatable in the database, to add in the dictionary data table with those parameter
	dictionaries formatted nicely into one table. """
	mod_params_df = get_file_from_database(mod_params_name, database)
	charge_descript = pd.DataFrame()
	discharge_descript = pd.DataFrame()
	for i in range(len(mod_params_df)):
		param_dict_charge = ast.literal_eval(mod_params_df.loc[i, ('Model_Parameters_charge')])
		param_dict_discharge = ast.literal_eval(mod_params_df.loc[i, ('Model_Parameters_discharge')])
		charge_peak_heights = ast.literal_eval(mod_params_df.loc[i, ('charge_peak_heights')])
		discharge_peak_heights = ast.literal_eval(mod_params_df.loc[i, ('discharge_peak_heights')])
		charge_keys =[]
		new_dict_charge = {}
		if param_dict_charge is not None:
			for key, value in param_dict_charge.items(): 
				if '_amplitude' in key and not 'base_' in key:
					charge_keys.append(key.split('_')[0])
			new_dict_charge.update({'c_gauss_sigma': param_dict_charge['base_sigma'], # changed from c0- c4  to base_ .. 10-10-18
							 'c_gauss_center': param_dict_charge['base_center'],
							 'c_gauss_amplitude': param_dict_charge['base_amplitude'], 
							 'c_gauss_fwhm': param_dict_charge['base_fwhm'], 
							 'c_gauss_height': param_dict_charge['base_height'], 
							 })
			new_dict_charge.update({'c_cycle_number': float(mod_params_df.loc[i, ('Cycle')])})
		peaknum = 0
		for item in charge_keys:
			peaknum = peaknum +1 
			center = param_dict_charge[item + '_center']
			amp = param_dict_charge[item + '_amplitude']
			fract = param_dict_charge[item + '_fraction']
			sigma = param_dict_charge[item + '_sigma']
			height = param_dict_charge[item + '_height']
			fwhm = param_dict_charge[item + '_fwhm']
			raw_peakheight = charge_peak_heights[peaknum-1]
			PeakArea, PeakAreaError = scipy.integrate.quad(my_pseudovoigt,
														   0.0, 
														   100, 
														   args=(center, 
														   	     amp, 
														   	     fract, 
														   	     sigma))
			new_dict_charge.update({'c_area_peak_'+str(peaknum): PeakArea, 
							 'c_center_peak_' +str(peaknum):center, 
							 'c_amp_peak_' +str(peaknum):amp,
							 'c_fract_peak_' +str(peaknum):fract, 
							 'c_sigma_peak_' +str(peaknum):sigma, 
							 'c_height_peak_' +str(peaknum):height, 
							 'c_fwhm_peak_' +str(peaknum):fwhm, 
							 'c_rawheight_peak_' + str(peaknum):raw_peakheight})      
		new_dict_df = pd.DataFrame(columns = new_dict_charge.keys())
		for key1, val1 in new_dict_charge.items():
			new_dict_df.at[0, key1] = new_dict_charge[key1]
		charge_descript = pd.concat([charge_descript, new_dict_df], sort = True)
		charge_descript = charge_descript.reset_index(drop = True)
		charge_descript2 = dfsortpeakvals(charge_descript, 'c')
		discharge_keys =[]
		if param_dict_discharge is not None:
			for key, value in param_dict_discharge.items(): 
				if '_amplitude' in key and not 'base_' in key:
					discharge_keys.append(key.split('_')[0])
			new_dict_discharge = {}
			new_dict_discharge.update({'d_gauss_sigma': param_dict_discharge['base_sigma'], # changed 10-10-18
							 'd_gauss_center': param_dict_discharge['base_center'],
							 'd_gauss_amplitude': param_dict_discharge['base_amplitude'], 
							 'd_gauss_fwhm': param_dict_discharge['base_fwhm'], 
							 'd_gauss_height': param_dict_discharge['base_height'], 
							 })
			new_dict_discharge.update({'d_cycle_number': float(mod_params_df.loc[i, ('Cycle')])})
			peaknum = 0
			for item in discharge_keys:
				peaknum = peaknum +1 
				center = param_dict_discharge[item + '_center']
				amp = param_dict_discharge[item + '_amplitude']
				fract = param_dict_discharge[item + '_fraction']
				sigma = param_dict_discharge[item + '_sigma']
				height = param_dict_discharge[item + '_height']
				fwhm = param_dict_discharge[item + '_fwhm']
				raw_peakheight = discharge_peak_heights[peaknum-1]
				PeakArea, PeakAreaError = scipy.integrate.quad(my_pseudovoigt, 0.0, 100, args=(center, amp, fract, sigma))
				new_dict_discharge.update({'d_area_peak_'+str(peaknum): PeakArea, 
								 'd_center_peak_' +str(peaknum):center, 
								 'd_amp_peak_' +str(peaknum):amp,
								 'd_fract_peak_' +str(peaknum):fract, 
								 'd_sigma_peak_' +str(peaknum):sigma, 
								 'd_height_peak_' +str(peaknum):height, 
								 'd_fwhm_peak_' +str(peaknum):fwhm, 
								 'd_rawheight_peak_' + str(peaknum):raw_peakheight})  
		else: 
			new_dict_discharge = None    
		if new_dict_discharge is not None:
			new_dict_df_d = pd.DataFrame(columns = new_dict_discharge.keys())
			for key1, val1 in new_dict_discharge.items():
				new_dict_df_d.at[0, key1] = new_dict_discharge[key1]
			discharge_descript = pd.concat([discharge_descript, new_dict_df_d], sort = True)
			discharge_descript = discharge_descript.reset_index(drop = True)
			discharge_descript2 = dfsortpeakvals(discharge_descript, 'd')
		else:
			discharge_descript2 = None
			# append the two dfs (charge and discharge) before putting them in database
		full_df_descript = pd.concat([charge_descript2, discharge_descript2], sort = True, axis = 1)
		update_database_newtable(full_df_descript, mod_params_name[:-9] +'-descriptors', database)
	return

def get_filename_pref(file_name):
	"""Splits the filename apart from the path 
	and the extension. This is used as part of 
	the identifier for individual file uploads."""
	while '/' in file_name:
		file_name = file_name.split('/', maxsplit = 1)[1]
	file_name_pref = file_name.split('.')[0] 
	return file_name_pref


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
""" This file processes all the data located in the specified directories
to change the source data directories, edit the lines where "c_list" and "k_list"
are defined.
This code was largely used to gather the descriptors necessary for the ML classificaiton 
problem, because a large number of files needed to be processed and the time to do that through 
the dash app was unrealistic. 
"""
from app_helper_functions import generate_model
import databasewrappers as dbw
import pandas as pd
import numpy as np
import os
import glob

c_database = 'classification_cdata.db'
k_database = 'classification_kdata.db'

if not os.path.exists(c_database): 
	print('That database does not exist-creating it now.')
	dbw.dbfs.init_master_table(c_database)

if not os.path.exists(k_database): 
	print('That database does not exist-creating it now.')
	dbw.dbfs.init_master_table(k_database)

# The below two lines would be where you would edit the filepaths to the folders which contain the 
# two types of data. Here we have CS2_33 battery data and K2_016 battery data from the CALCE site. 

c_list = [f for f in glob.glob('data/CS2_33/*.xlsx')]
k_list = [f for f in glob.glob('data/K2_016/*.xlsx')]
# these are lists of all raw filenames

def process_one_file(filename, database):
	while '/' in filename: 
		filename = filename.split('/', maxsplit = 1)[1]
	cleanset_name = filename.split('.')[0] + 'CleanSet'
	datatype = 'ARBIN'
	thresh1 = 0.5
	username = 'me'
	decoded = None
	dbw.process_data(filename, database, decoded, datatype, thresh1, thresh2, username)
	df_clean = dbw.dbfs.get_file_from_database(cleanset_name, database)
	v_toappend_c = []
	v_toappend_d = []
	new_peak_thresh = 0.3 
	feedback = generate_model(v_toappend_c, v_toappend_d, df_clean, filename, new_peak_thresh, database)
	# maybe split the process data function into getting descriptors as well?	
	return 

# def generate_model(v_toappend_c, v_toappend_d, df_clean, filename, peak_thresh, database):
# 	"""Generates the model for each cycle"""
# 	datatype = df_clean.loc[0,('datatype')]
# 	(cycle_ind_col, data_point_col, volt_col, curr_col, \
# 	 dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)

# 	chargeloc_dict = {}
# 	param_df = pd.DataFrame(columns = ['Cycle','Model_Parameters_charge', 'Model_Parameters_discharge'])

# 	if len(df_clean[cycle_ind_col].unique())>1:
# 		length_list = [len(df_clean[df_clean[cycle_ind_col]==cyc])\
# 		for cyc in df_clean[cycle_ind_col].unique() if cyc != 1]
# 		lenmax = max(length_list)
# 	else:
# 		length_list = 1
# 		lenmax = len(df_clean)

# 	mod_pointsdf = pd.DataFrame()
# 	cycles_no_models = []
# 	for cyc in df_clean[cycle_ind_col].unique():
# 		try: 
# 			new_df_mody, model_c_vals, model_d_vals, \
# 				peak_heights_c, peak_heights_d = get_model_dfs(df_clean, datatype, cyc,\
# 					v_toappend_c, v_toappend_d, lenmax, peak_thresh)
# 			mod_pointsdf = mod_pointsdf.append(new_df_mody)
# 			param_df = param_df.append({'Cycle': cyc,
# 										'Model_Parameters_charge': str(model_c_vals), 
# 										'Model_Parameters_discharge': str(model_d_vals), 
# 										'charge_peak_heights': str(peak_heights_c), 
# 										'discharge_peak_heights': str(peak_heights_d)}, 
# 										ignore_index = True)
# 		except Exception as e: 
# 			print('Model was not generated for Cycle ' + str(cyc))
# 			cycles_no_models.append(cyc)
# 	# want this outside of for loop to update the db with the complete df of new params 
# 	dbw.dbfs.update_database_newtable(mod_pointsdf, filename.split('.')[0]+ '-ModPoints', database)
# 	# this will replace the data table in there if it exists already 
# 	dbw.dbfs.update_database_newtable(param_df, filename.split('.')[0] + 'ModParams', database)
# 	# the below also updates the database with the new descriptors after evaluating the spit out 
# 	# dictionary and putting those parameters into a nicely formatted datatable. 
# 	dbw.param_dicts_to_df(filename.split('.')[0] + 'ModParams', database)		

# 	return #Model has been added to the database 

def get_model_dfs(df_clean, datatype, cyc, v_toappend_c, v_toappend_d, lenmax, peak_thresh):
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)
	clean_charge, clean_discharge = dbw.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==cyc], datatype)
	windowlength = 75
	polyorder = 3
	#####################################
	# length_dict = {key: len(value) for key, value in import_dictionary.items()}
 #    lenmax = max(length_dict.values())
	######################################
	# speed this up by moving the initial peak finder out of this, and just have those two things passed to it 
	i_charge, volts_i_ch, peak_heights_c = dbw.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype, lenmax, peak_thresh)
	#chargeloc_dict.update({cyc: volts_i_ch})
	V_series_c = clean_charge[volt_col]
	dQdV_series_c = clean_charge['Smoothed_dQ/dV']
	par_c, mod_c, indices_c = dbw.descriptors.fitters.model_gen(V_series_c, dQdV_series_c, 'c', i_charge, cyc, v_toappend_c, peak_thresh)
	model_c = dbw.descriptors.fitters.model_eval(V_series_c, dQdV_series_c, 'c', par_c, mod_c)			
	if model_c is not None:
		mod_y_c = mod_c.eval(params = model_c.params, x = V_series_c)
		myseries_c = pd.Series(mod_y_c)
		myseries_c = myseries_c.rename('Model')
		model_c_vals = model_c.values
		new_df_mody_c = pd.concat([myseries_c, V_series_c, dQdV_series_c, clean_charge[cycle_ind_col]], axis = 1)
	else:
		mod_y_c = None
		new_df_mody_c = None
		model_c_vals = None
	# now the discharge: 
	i_discharge, volts_i_dc, peak_heights_d= dbw.descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype, lenmax, peak_thresh)
	V_series_d = clean_discharge[volt_col]
	dQdV_series_d = clean_discharge['Smoothed_dQ/dV']
	par_d, mod_d, indices_d = dbw.descriptors.fitters.model_gen(V_series_d, dQdV_series_d, 'd', i_discharge, cyc, v_toappend_d, peak_thresh)
	model_d = dbw.descriptors.fitters.model_eval(V_series_d, dQdV_series_d, 'd', par_d, mod_d)			
	if model_d is not None:
		mod_y_d = mod_d.eval(params = model_d.params, x = V_series_d)
		myseries_d = pd.Series(mod_y_d)
		myseries_d = myseries_d.rename('Model')
		new_df_mody_d = pd.concat([-myseries_d, V_series_d, dQdV_series_d, clean_discharge[cycle_ind_col]], axis = 1)
		model_d_vals = model_d.values
	else:
		mod_y_d = None
		new_df_mody_d = None
		model_d_vals = None
	# save the model parameters in the database with the data
	if new_df_mody_c is not None or new_df_mody_d is not None: 
		new_df_mody = pd.concat([new_df_mody_c, new_df_mody_d], axis = 0)
	else: 
		new_df_mody = None
	# combine the charge and discharge
	# update model_c_vals and model_d_vals with peak heights 
	
	return new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d

### the rest: 

df_c = pd.DataFrame()
for each in c_list:
	descript_name = each.split('.')[0] + 'ModParams-descriptors'
	while '/' in descript_name:
		descript_name = descript_name.split('/', maxsplit = 1)[1]
	print(descript_name)
	df1 = dbw.dbfs.get_file_from_database(descript_name, c_database)
	if df1 is not None:

		df_c = df_c.append(df1)
df_c['CS2-1-K16-0'] = 1


df_k = pd.DataFrame()
for each in k_list:
	descript_name = each.split('.')[0] + 'ModParams-descriptors'
	while '/' in descript_name:
		descript_name = descript_name.split('/', maxsplit = 1)[1]
	print(descript_name)
	df2 = dbw.dbfs.get_file_from_database(descript_name, k_database)
	if df2 is not None:
		df_k = df_k.append(df2)
df_k['CS2-1-K16-0'] = 0

 
df_final = df_k.append(df_c)
writer3 = pd.ExcelWriter('final_descriptors.xlsx')
df_final.to_excel(writer3, 'Sheet1')
writer3.save()


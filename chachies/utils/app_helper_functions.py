import databasewrappers as dbw
import dash_html_components as html
import base64
import pandas as pd 
import ast 
import base64
import databasewrappers as dbw
import dash
import dash_auth
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_table_experiments as dt
import io
import json
from lmfit.model import load_modelresult
from lmfit.model import save_modelresult
import numpy as np
import os
import pandas as pd
import plotly 
import urllib
import urllib.parse

#### parse down these imports as you need them 

def parse_contents(contents, filename, datatype, thresh1, thresh2, database, auth):
	# this is just to be used to get a df from an uploaded file

	if contents == None:
		return html.Div(['No file has been uploaded, or the file uploaded was empty.'])
	else: 
		content_type, content_string = contents.split(',')
		decoded = base64.b64decode(content_string)
	# try: 
		cleanset_name = filename.split('.')[0] + 'CleanSet'
		#this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
			#check to see if the database exists, and if it does, check if the file exists.
		ans_p = dbw.if_file_exists_in_db(database, filename)
		if ans_p == True: 
			df_clean = dbw.dbfs.get_file_from_database(cleanset_name, database)
			new_peak_thresh = 0.7 # just as a starter value 
			feedback = generate_model(df_clean, filename, new_peak_thresh, database)
			return html.Div(['That file exists in the database: ' + str(filename.split('.')[0])])
			#df = dbw.dbfs.get_file_from_database(cleanset_name, database)
		else:

			username = auth._username
			dbw.process_data(filename, database, decoded, datatype, thresh1, thresh2, username)
			df_clean = dbw.dbfs.get_file_from_database(cleanset_name, database)
			new_peak_thresh = 0.3 # just as a starter value
			feedback = generate_model(df_clean, filename, new_peak_thresh, database)
			# maybe split the process data function into getting descriptors as well?
			#since that is the slowest step 
			return html.Div(['New file has been processed: ' + str(filename)])
			

# this part should be ran everytime something is updated, keeping the filename. whenever the dropdown menu changes
def pop_with_db(filename, database):
# *new
	cleanset_name = filename.split('.')[0] + 'CleanSet'
	rawset_name = filename.split('.')[0] + 'Raw'
	#this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
	ans = dbw.if_file_exists_in_db(database, filename)
	print(ans)
	if ans == True: 
		# then the file exists in the database and we can just read it 
		df_clean = dbw.dbfs.get_file_from_database(cleanset_name, database)
		df_raw = dbw.dbfs.get_file_from_database(rawset_name, database)
		datatype = df_clean.loc[0,('datatype')]
		(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)

	else:
		df_clean = None
		df_raw = None
		peakloc_dict = {}
	# else: # *new
	# 	df_clean = None # *new
	# 	df_raw = None # *new
	# 	peakloc_dict = {} # *new
	return df_clean, df_raw

def get_model_dfs(df_clean, datatype, cyc, lenmax, peak_thresh):
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)
	clean_charge, clean_discharge = dbw.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==cyc], datatype)
	windowlength = 75
	polyorder = 3
	# speed this up by moving the initial peak finder out of this, and just have those two things passed to it 
	i_charge, volts_i_ch, peak_heights_c = dbw.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype, lenmax, peak_thresh)

	V_series_c = clean_charge[volt_col]
	dQdV_series_c = clean_charge['Smoothed_dQ/dV']
	par_c, mod_c, indices_c = dbw.descriptors.fitters.model_gen(V_series_c, dQdV_series_c, 'c', i_charge, cyc, peak_thresh)
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
	par_d, mod_d, indices_d = dbw.descriptors.fitters.model_gen(V_series_d, dQdV_series_d, 'd', i_discharge, cyc, peak_thresh)
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

def generate_model(df_clean, filename, peak_thresh, database):
	# run this when get descriptors button is pushed, and re-run it when user puts in new voltage 
	# create model based off of initial peaks 
	# show user model, then ask if more peak locations should be used (shoulders etc)
	datatype = df_clean.loc[0,('datatype')]
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)

	chargeloc_dict = {}
	param_df = pd.DataFrame(columns = ['Cycle','Model_Parameters_charge', 'Model_Parameters_discharge'])
	if len(df_clean[cycle_ind_col].unique())>1:
		length_list = [len(df_clean[df_clean[cycle_ind_col]==cyc]) for cyc in df_clean[cycle_ind_col].unique() if cyc != 1]
		lenmax = max(length_list)
	else:
		length_list = 1
		lenmax = len(df_clean)

	mod_pointsdf = pd.DataFrame()
	for cyc in df_clean[cycle_ind_col].unique():
		new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d = get_model_dfs(df_clean, datatype, cyc, lenmax, peak_thresh)
		mod_pointsdf = mod_pointsdf.append(new_df_mody)
		param_df = param_df.append({'Cycle': cyc, 'Model_Parameters_charge': str(model_c_vals), 'Model_Parameters_discharge': str(model_d_vals), 'charge_peak_heights': str(peak_heights_c), 'discharge_peak_heights': str(peak_heights_d)}, ignore_index = True)
	
	# want this outside of for loop to update the db with the complete df of new params 
	dbw.dbfs.update_database_newtable(mod_pointsdf, filename.split('.')[0]+ '-ModPoints', database)
	# this will replace the data table in there if it exists already 
	dbw.dbfs.update_database_newtable(param_df, filename.split('.')[0] + 'ModParams', database)
	
	dbw.param_dicts_to_df(filename.split('.')[0] + 'ModParams', database)		

	return html.Div(['That model has been added to the database'])
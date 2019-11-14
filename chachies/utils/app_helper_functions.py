import databasewrappers as dbw
import dash_html_components as html

import ast 
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


def check_database_and_get_creds(database):
	"""This function both serves to initialize the database 
	if it doesn't exist yet, and to get the login credentials
	from the database.
	database: string of name of either existing database or 
			name for new database
	returns VALID_USERNAME_PASSWORD_PAIRS as a list of lists,
	if the database was new there is at least one login credential 
	created within the init_master_table function - [[Example User, password]] """
	if not os.path.exists(database): 
		print('That database does not exist-creating it now.')
		dbw.dbfs.init_master_table(database)

	# we have a previously set up file in the database with acceptable users/password pairs
	usernames = dbw.dbfs.get_file_from_database('users', database)

	VALID_USERNAME_PASSWORD_PAIRS = []
	for i in range(len(usernames)):
		VALID_USERNAME_PASSWORD_PAIRS.append(list([usernames.loc[i, ('Username')], usernames.loc[i,('Password')]]))
	
	return VALID_USERNAME_PASSWORD_PAIRS



def parse_contents(decoded, filename, datatype, database, auth, windowlength = 9, polyorder = 3):
	"""Checks if the uploaded file exists in the database yet. Will 
	process and add that file to the database if it doesn't appear in 
	the master table yet. Otherwise will return html.Div that the 
	file already exists in the database. """

	cleanset_name = dbw.get_filename_pref(filename) + 'CleanSet'
	#this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
		#check to see if the database exists, and if it does, check if the file exists.
	ans_p = dbw.if_file_exists_in_db(database, filename)
	if ans_p == True: 
		df_clean = dbw.dbfs.get_file_from_database(cleanset_name, database)
		new_peak_thresh = 0.7 
		feedback = generate_model(df_clean, filename, new_peak_thresh, database)
		return 'That file exists in the database: ' + str(dbw.get_filename_pref(filename))
	else:
		username = auth._username
		# put decoded contents into df to pass to process_data
		decoded_dataframe = decoded_to_dataframe(decoded, datatype, filename)
		dbw.process_data(filename, database, decoded_dataframe, datatype, username, windowlength, polyorder)
		df_clean = dbw.dbfs.get_file_from_database(cleanset_name, database)
		new_peak_thresh = 0.7
		feedback = generate_model(df_clean, filename, new_peak_thresh, database)
		return 'New file has been processed: ' + str(dbw.get_filename_pref(filename))

def decoded_to_dataframe(decoded, datatype, file_name): 
	"""Decodes the contents uploaded via the app. Returns 
	contents as a dataframe."""
	if datatype == 'ARBIN':
		if decoded is None:
			data1 = pd.read_excel(file_name, 1)
		else:
			data1 = pd.read_excel(io.BytesIO(decoded), 1)
		data1['datatype'] = 'ARBIN'
	elif datatype == 'MACCOR':
		data1 = pd.read_csv(io.StringIO(decoded.decode('utf-8')), header = 12, delimiter='\t', index_col=False)
		dataheader = pd.read_fwf(io.StringIO(decoded.decode('utf-8')), delimiter = '\t')
		weight = float(dataheader.iloc[2][0].split('mg')[0].split('_')[1].replace('p', '.'))
		data1['Const_Weight[mg]'] = weight
		#somehow set the Current column to negative when the 'Md' column has a D in it(current > 0 - charge)
		data1['MaccCharLab'] = data1.apply(lambda row: macc_chardis(row), axis = 1)
		data1['Current(A)'] = data1['Current [A]']*data1['MaccCharLab']
		data1['datatype'] = 'MACCOR'

		data1.rename(columns={'Cycle C': 'Cycle_Index', 'Voltage [V]': 'Voltage(V)', 'Current [A]': 'Abs_Current(A)', 'Cap. [Ah]': 'Cap(Ah)'}, inplace=True)
	else: 
		None	
	return data1

def pop_with_db(filename, database):
	"""Returns dataframes that can be used to populate the app graphs.
	Finds the already existing file in the database and returns
	the cleaned version (as a dataframe) and the raw version 
	(also as a dataframe)."""
	cleanset_name = dbw.get_filename_pref(filename) + 'CleanSet'
	rawset_name = dbw.get_filename_pref(filename) + 'Raw'
	if dbw.if_file_exists_in_db(database, filename) == True: 
		# then the file exists in the database and we can just read it 
		df_clean = dbw.dbfs.get_file_from_database(cleanset_name, database)
		df_raw = dbw.dbfs.get_file_from_database(rawset_name, database)
		datatype = df_clean.loc[0,('datatype')]
		(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)

	else:
		df_clean = None
		df_raw = None
		peakloc_dict = {}

	return df_clean, df_raw

def get_model_dfs(df_clean, datatype, cyc, lenmax, peak_thresh):
	"""This is the wrapper for the model generation and fitting for the cycles.
	Returns dictionaries for the charge cycle model parameters and discharge 
	cycle model parameters. These will each have at the least base gaussian 
	parameter values, with the keys: 'base_amplitude', 'base_center', 
	'base_fwhm', 'base_height', and 'base_sigma'. The other keys are 
	dependent on whether any peaks were found in the cycle. 
	"""
	(cycle_ind_col, data_point_col, volt_col, curr_col, \
		dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)
	clean_charge, clean_discharge = dbw.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==cyc], datatype)
	windowlength = 9
	polyorder = 3

	i_charge, volts_i_ch, peak_heights_c = dbw.descriptors.fitters.peak_finder(clean_charge, 
																			   'c', windowlength,
																			    polyorder, 
																			    datatype, 
																			    lenmax, 
																			    peak_thresh)

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
	i_discharge, volts_i_dc, peak_heights_d= dbw.descriptors.fitters.peak_finder(clean_discharge, 'd',
																			     windowlength, polyorder, 
																			     datatype, lenmax, peak_thresh)
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

	if new_df_mody_c is not None or new_df_mody_d is not None: 
		new_df_mody = pd.concat([new_df_mody_c, new_df_mody_d], axis = 0)
	else: 
		new_df_mody = None

	return new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d

def generate_model(df_clean, filename, peak_thresh, database):
	"""Wrapper for the get_model_dfs function. Takes those results
	and adds them to the database with three new tables 
	with the suffices: '-ModPoints', 'ModParams', 
	and '-descriptors'."""
	datatype = df_clean.loc[0,('datatype')]
	(cycle_ind_col, data_point_col, volt_col, curr_col, \
		dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)
	chargeloc_dict = {}
	param_df = pd.DataFrame(columns = ['Cycle','Model_Parameters_charge', 'Model_Parameters_discharge'])
	if len(df_clean[cycle_ind_col].unique())>1:
		length_list = [len(df_clean[df_clean[cycle_ind_col]==cyc])\
					 for cyc in df_clean[cycle_ind_col].unique() if cyc != 1]
		lenmax = max(length_list)
	else:
		length_list = 1
		lenmax = len(df_clean)

	mod_pointsdf = pd.DataFrame()
	cycles_no_models = []
	for cyc in df_clean[cycle_ind_col].unique():
		try: 
			new_df_mody, model_c_vals, model_d_vals, \
				peak_heights_c, peak_heights_d = get_model_dfs(df_clean, datatype, cyc, lenmax, peak_thresh)
			mod_pointsdf = mod_pointsdf.append(new_df_mody)
			param_df = param_df.append({'Cycle': cyc, 
										'Model_Parameters_charge': str(model_c_vals), 
										'Model_Parameters_discharge': str(model_d_vals), 
										'charge_peak_heights': str(peak_heights_c), 
										'discharge_peak_heights': str(peak_heights_d)}, 
										ignore_index = True)
		except Exception as e:
			print('Model was not generated for Cycle ' + str(cyc))
			cycles_no_models.append(cyc)
	# want this outside of for loop to update the db with the complete df of new params 
	dbw.dbfs.update_database_newtable(mod_pointsdf, filename.split('.')[0]+ '-ModPoints', database)
	# this will replace the data table in there if it exists already 
	dbw.dbfs.update_database_newtable(param_df, filename.split('.')[0] + 'ModParams', database)
	# the below also updates the database with the new descriptors after evaluating the spit out 
	# dictionary and putting those parameters into a nicely formatted datatable. 
	dbw.param_dicts_to_df(filename.split('.')[0] + 'ModParams', database)		
	if len(cycles_no_models) > 0: 
		return html.Div(['That model has been added to the database.' \
						+ 'No model was generated for Cycle(s) ' + str(cycles_no_models)])
	return html.Div(['That model has been added to the database'])
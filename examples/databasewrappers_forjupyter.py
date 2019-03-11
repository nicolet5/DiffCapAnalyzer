import ast
import io
import numpy as np
import os
import pandas as pd 
from pandas import ExcelWriter
import pandas.io.sql as pd_sql
import scipy
import sqlite3 as sql
import chachifuncs as ccf
import descriptors
import databasefuncs as dbfs

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
	thresh1 = 0.0
	thresh2 = 0.0
	if datatype == 'Arbin':
		datatype = 'CALCE'
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
		parse_update_master(file_name, database_name, datatype, path, username)
		# this takes the info from the filename and updates the master table in the database. 
		# this also adds the raw data fram into the database
		cycle_dict = ccf.load_sep_cycles(file_name, database_name, datatype)
		clean_cycle_dict= ccf.get_clean_cycles(cycle_dict, file_name, database_name, datatype, thresh1, thresh2)
		clean_set_df = ccf.get_clean_sets(clean_cycle_dict, file_name, database_name)

		cleanset_name = name3 + 'CleanSet'
		df_clean = dbfs.get_file_from_database(cleanset_name, database_name)
		new_peak_thresh = 0.7
		# just as a starter value
		feedback = generate_model_for_jupyter(df_clean, file_name, new_peak_thresh, database_name)

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
	if datatype == 'CALCE':
		data1 = pd.read_excel(path, 1)
		data1['datatype'] = 'CALCE'
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
		print('please use either "CALCE" or "MACCOR" for datatype.')

	data = ccf.calc_dq_dqdv(data1, datatype)
	dbfs.update_database_newtable(data, name + 'Raw', database_name)
	update_dic ={'Dataset_Name': name,'Raw_Data_Prefix': name +'Raw',
					'Cleaned_Data_Prefix': name + 'CleanSet', 
					'Cleaned_Cycles_Prefix': name + '-CleanCycle', 'Descriptors_Prefix': name + 'ModParams-descriptors'}
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

def my_pseudovoigt(x, cent, amp, fract, sigma): 
	"""This function is from http://cars9.uchicago.edu/software/python/lmfit/builtin_models.html"""
	sig_g = sigma/np.sqrt(2*np.log(2)) # calculate the sigma_g parameter for the gaussian distribution 
	part1 = (((1-fract)*amp)/(sig_g*np.sqrt(2*np.pi)))*np.exp((-(x-cent)**2)/(2*sig_g**2))
	part2 = ((fract*amp)/np.pi)*(sigma/((x-cent)**2+sigma**2))
	fit = part1 + part2
	return(fit)

def param_dicts_to_df(mod_params_name, database):
	mod_params_df = dbfs.get_file_from_database(mod_params_name, database)
	#charge_df = mod_paramsgraphit[mod_paramsgraphit['C/D'] == 'discharge']
	#charge_df = charge_df.reset_index(drop = True)
	#charge_df = mod_params_df
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
					#print(int(key.split('_')[0].split('a')[1]))
					charge_keys.append(key.split('_')[0])
			#print(charge_keys) 

			new_dict_charge.update({'c_gauss_sigma': param_dict_charge['base_sigma'], # changed from c0- c4  to base_ .. 10-10-18
							 'c_gauss_center': param_dict_charge['base_center'],
							 'c_gauss_amplitude': param_dict_charge['base_amplitude'], 
							 'c_gauss_fwhm': param_dict_charge['base_fwhm'], 
							 'c_gauss_height': param_dict_charge['base_height'], 
							 #'c_poly_coef5': param_dict_charge['c4'],
							 })
			new_dict_charge.update({'c_cycle_number': float(mod_params_df.loc[i, ('Cycle')])})
			#new_dict.update({'charge/discharge': mod_params_df.loc[i, ('C/D')], 
							 #'cycle_number': float(mod_params_df.loc[i, ('Cycle')])})
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
			#print('center' + str(center))
			PeakArea, PeakAreaError = scipy.integrate.quad(my_pseudovoigt, 0.0, 100, args=(center, amp, fract, sigma))
			#print('peak location is : ' + str(center) + ' Peak area is: ' + str(PeakArea))
			new_dict_charge.update({'c_area_peak_'+str(peaknum): PeakArea, 
							 'c_center_peak_' +str(peaknum):center, 
							 'c_amp_peak_' +str(peaknum):amp,
							 'c_fract_peak_' +str(peaknum):fract, 
							 'c_sigma_peak_' +str(peaknum):sigma, 
							 'c_height_peak_' +str(peaknum):height, 
							 'c_fwhm_peak_' +str(peaknum):fwhm, 
							 'c_rawheight_peak_' + str(peaknum):raw_peakheight})      
		#print(new_dict)
		new_dict_df = pd.DataFrame(columns = new_dict_charge.keys())
		for key1, val1 in new_dict_charge.items():
			new_dict_df.at[0, key1] = new_dict_charge[key1]
		charge_descript = pd.concat([charge_descript, new_dict_df])
		charge_descript = charge_descript.reset_index(drop = True)
		charge_descript2 = descriptors.dfsortpeakvals(charge_descript, 'c')
		################################ now the discharge

		discharge_keys =[]
		if param_dict_discharge is not None:
			for key, value in param_dict_discharge.items(): 
				if '_amplitude' in key and not 'base_' in key:
					#print(int(key.split('_')[0].split('a')[1]))
					discharge_keys.append(key.split('_')[0])
			#print(charge_keys) 
			new_dict_discharge = {}
			new_dict_discharge.update({'d_gauss_sigma': param_dict_discharge['base_sigma'], # changed 10-10-18
							 'd_gauss_center': param_dict_discharge['base_center'],
							 'd_gauss_amplitude': param_dict_discharge['base_amplitude'], 
							 'd_gauss_fwhm': param_dict_discharge['base_fwhm'], 
							 'd_gauss_height': param_dict_discharge['base_height'], 
							 #'d_poly_coef5': param_dict_discharge['c4'],
							 })
			new_dict_discharge.update({'d_cycle_number': float(mod_params_df.loc[i, ('Cycle')])})
			#new_dict.update({'charge/discharge': mod_params_df.loc[i, ('C/D')], 
								 #'cycle_number': float(mod_params_df.loc[i, ('Cycle')])})
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
				#print('center' + str(center))
				PeakArea, PeakAreaError = scipy.integrate.quad(my_pseudovoigt, 0.0, 100, args=(center, amp, fract, sigma))
				#print('peak location is : ' + str(center) + ' Peak area is: ' + str(PeakArea))
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
			#print(new_dict)
		if new_dict_discharge is not None:
			new_dict_df_d = pd.DataFrame(columns = new_dict_discharge.keys())
			for key1, val1 in new_dict_discharge.items():
				new_dict_df_d.at[0, key1] = new_dict_discharge[key1]
			discharge_descript = pd.concat([discharge_descript, new_dict_df_d])
			discharge_descript = discharge_descript.reset_index(drop = True)
			discharge_descript2 = descriptors.dfsortpeakvals(discharge_descript, 'd')
		else:
			discharge_descript2 = None
			# append the two dfs (charge and discharge) before putting them in database
		full_df_descript = pd.concat([charge_descript2, discharge_descript2], axis = 1)
		dbfs.update_database_newtable(full_df_descript, mod_params_name +'-descriptors', database)
	return

def generate_model_for_jupyter(df_clean, filename, peak_thresh, database):
	# this function is analagous to the generate_model function in the app.py file
	# run this when get descriptors button is pushed, and re-run it when user puts in new voltage 
	# create model based off of initial peaks 
	# show user model, then ask if more peak locations should be used (shoulders etc)
	datatype = df_clean.loc[0,('datatype')]
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = ccf.col_variables(datatype)

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
		new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d = get_model_dfs_for_jupyter(df_clean, datatype, cyc, lenmax, peak_thresh)
		mod_pointsdf = mod_pointsdf.append(new_df_mody)
		param_df = param_df.append({'Cycle': cyc, 'Model_Parameters_charge': str(model_c_vals), 'Model_Parameters_discharge': str(model_d_vals), 'charge_peak_heights': str(peak_heights_c), 'discharge_peak_heights': str(peak_heights_d)}, ignore_index = True)
	
	# want this outside of for loop to update the db with the complete df of new params 
	dbfs.update_database_newtable(mod_pointsdf, filename.split('.')[0]+ '-ModPoints', database)
	# this will replace the data table in there if it exists already 
	dbfs.update_database_newtable(param_df, filename.split('.')[0] + 'ModParams', database)
	
	param_dicts_to_df(filename.split('.')[0] + 'ModParams', database)		

	# print("That model has been added to the database")
	return 


def get_model_dfs_for_jupyter(df_clean, datatype, cyc, lenmax, peak_thresh):
	# this function is analagous to the get_model_dfs function in the app.py file 
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = ccf.col_variables(datatype)
	clean_charge, clean_discharge = ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==cyc], datatype)
	windowlength = 75
	polyorder = 3
	# speed this up by moving the initial peak finder out of this, and just have those two things passed to it 
	i_charge, volts_i_ch, peak_heights_c = descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype, lenmax, peak_thresh)

	V_series_c = clean_charge[volt_col]
	dQdV_series_c = clean_charge['Smoothed_dQ/dV']
	par_c, mod_c, indices_c = descriptors.fitters.model_gen(V_series_c, dQdV_series_c, 'c', i_charge, cyc, peak_thresh)
	model_c = descriptors.fitters.model_eval(V_series_c, dQdV_series_c, 'c', par_c, mod_c)			
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
	i_discharge, volts_i_dc, peak_heights_d= descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype, lenmax, peak_thresh)
	V_series_d = clean_discharge[volt_col]
	dQdV_series_d = clean_discharge['Smoothed_dQ/dV']
	par_d, mod_d, indices_d = descriptors.fitters.model_gen(V_series_d, dQdV_series_d, 'd', i_discharge, cyc, peak_thresh)
	model_d = descriptors.fitters.model_eval(V_series_d, dQdV_series_d, 'd', par_d, mod_d)			
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

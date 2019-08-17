import glob
from math import isclose
import numpy as np
import os
import pandas as pd
import requests
import scipy.io
import scipy.signal
import databasefuncs as dbfs



def load_sep_cycles(file_name, database_name, datatype):
	"""Get data from a specified file, separates out data into
	cycles and saves those cycles as .xlsx files in specified
	filepath (must be an existing folder)"""
	#df_single = pd.read_excel(file_name,1)
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = col_variables(datatype)

	while '/' in file_name:
		file_name = file_name.split('/', maxsplit = 1)[1]
	name = file_name.split('.')[0] + 'Raw'
	df_single = dbfs.get_file_from_database(name, database_name)
	gb = df_single.groupby(by=[cycle_ind_col])
	cycle_dict = dict(iter(gb))
	battname = file_name.split('.')[0]
	for i in range(1, len(cycle_dict)+1):
		cycle_dict[i]['Battery_Label'] = battname
	for i in range(1, len(cycle_dict)+1):
		dbfs.update_database_newtable(cycle_dict[i], battname+'-'+'Cycle'+ str(i), database_name)
	print('All data separated into cycles and saved in database.')
	return cycle_dict




def get_clean_cycles(cycle_dict, file_name, database_name, datatype, windowlength = 9, polyorder = 3):
	"""Imports all separated out cycles in given path and cleans them
	and saves them in the specified filepath"""

	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = col_variables(datatype)
	while '/' in file_name:
		file_name = file_name.split('/', maxsplit = 1)[1]
	name = file_name.split('.')[0]

	clean_cycle_dict = {} 

	for i in range(1, len(cycle_dict)+1):
		charge, discharge = clean_calc_sep_smooth(cycle_dict[i], datatype, windowlength, polyorder)
		clean_data = charge.append(discharge, ignore_index=True)
		clean_data = clean_data.sort_values([data_point_col], ascending = True)
		clean_data = clean_data.reset_index(drop=True)
		cyclename = name + '-CleanCycle' + str(i)
		clean_cycle_dict.update({cyclename : clean_data})
		dbfs.update_database_newtable(clean_data, cyclename, database_name)

	print('All cycles cleaned and saved in database')
	return clean_cycle_dict


def get_clean_sets(clean_cycle_dict, file_name, database_name):
	"""Imports all clean cycles of data from import path and appends
	them into complete sets of battery data, saved into save_filepath"""
	
	clean_set_df = pd.DataFrame()
	while '/' in file_name:
		file_name = file_name.split('/', maxsplit = 1)[1]
	name = file_name.split('.')[0]
	
	for k, v in clean_cycle_dict.items():
		clean_set_df = clean_set_df.append(v, ignore_index = True)
	dbfs.update_database_newtable(clean_set_df, name + 'CleanSet', database_name)
	print('All clean cycles recombined and saved in database')
	return clean_set_df

############################
# Component Functions
############################

def clean_calc_sep_smooth(dataframe, datatype, windowlength, polyorder):
	"""Takes one cycle dataframe, calculates dq/dv, cleans the data,
	separates out charge and discharge, and applies sav-golay filter.
	Returns two dataframes, one charge and one discharge.
	Windowlength and polyorder are for the sav-golay filter."""
	assert type(dataframe) == pd.DataFrame
	df = init_columns(dataframe, datatype)
	df1 = calc_dq_dqdv(df, datatype)
	cleandf2 = drop_inf_nan_dqdv(df1, datatype)

	charge, discharge = sep_char_dis(cleandf2, datatype)
	# separating into charge and discharge cycles

	if len(discharge) > windowlength:
		smooth_discharge = my_savgolay(discharge, windowlength, polyorder)
	else:
		discharge['Smoothed_dQ/dV'] = discharge['dQ/dV']
		smooth_discharge = discharge
	# this if statement is for when the datasets have less datapoints
	# than the windowlength given to the sav_golay filter.
	# without this if statement, the sav_golay filter throws an error
	# when given a dataset with too few points. This way, we simply
	# forego the smoothing function.
	if len(charge) > windowlength:
		smooth_charge = my_savgolay(charge, windowlength, polyorder)
	else:
		charge['Smoothed_dQ/dV'] = charge['dQ/dV']
		smooth_charge = charge
	# same as above, but for charging cycles.
	return smooth_charge, smooth_discharge



def init_columns(cycle_df, datatype):
	"""This function calculates the dv and the dq/dv for a dataframe."""
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = col_variables(datatype)
	assert type(cycle_df) == pd.DataFrame
	assert volt_col in cycle_df.columns
	assert dis_cap_col in cycle_df.columns
	assert char_cap_col in cycle_df.columns

	cycle_df = cycle_df.reset_index(drop=True)
	cycle_df['dV'] = None
	cycle_df['Discharge_dQ'] = None
	cycle_df['Charge_dQ'] = None
	return cycle_df

def calc_dq_dqdv(cycle_df, datatype):
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = col_variables(datatype)
	pd.options.mode.chained_assignment = None
	#to avoid the warning 
	cycle_df['roundedV'] = round(cycle_df[volt_col], 3)
	cycle_df = cycle_df.drop_duplicates(subset = ['roundedV', cycle_ind_col, charge_or_discharge])
	cycle_df = cycle_df.reset_index(drop = True)
	cycle_df['dV'] = cycle_df[volt_col].diff()

	cycle_df_charge = cycle_df[cycle_df[curr_col] > 0]
	cycle_df_charge['Charge_dQ'] = cycle_df_charge[char_cap_col].diff()
	cycle_df_charge['dQ/dV'] = cycle_df_charge['Charge_dQ']/cycle_df_charge['dV']
	cycle_df_charge = cycle_df_charge[cycle_df_charge['dQ/dV']>0]

	cycle_df_discharge = cycle_df[cycle_df[curr_col] <= 0]
	cycle_df_discharge['Discharge_dQ'] = cycle_df_discharge[dis_cap_col].diff()
	cycle_df_discharge['dQ/dV'] = cycle_df_discharge['Discharge_dQ']/cycle_df_discharge['dV']
	cycle_df_discharge = cycle_df_discharge[cycle_df_discharge['dQ/dV']<0]
	cycle_df = pd.concat((cycle_df_charge, cycle_df_discharge ))
	cycle_df = cycle_df.sort_index()
	return cycle_df

def drop_inf_nan_dqdv(cycle_df_dv, datatype):
	'''Drop rows where dv=0 (or about 0) in a dataframe that has
	already had dv calculated. Then recalculate dv and calculate dq/dv'''
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col,charge_or_discharge) = col_variables(datatype)
	assert 'dV' in cycle_df_dv.columns
	assert curr_col in cycle_df_dv.columns

	cycle_df_dv = cycle_df_dv.reset_index(drop=True)

	cycle_df_dv = cycle_df_dv.replace([np.inf, -np.inf], np.nan)
	cycle_df_dv = cycle_df_dv.dropna(subset=['dQ/dV'])

	cycle_df_dv = cycle_df_dv.reset_index(drop=True)
	return cycle_df_dv


def sep_char_dis(df_dqdv, datatype):
	'''Takes a dataframe of one cycle with calculated dq/dv and
	separates into charge and discharge differential capacity curves'''
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = col_variables(datatype)
	switch_cd_index = np.where(np.diff(np.sign(df_dqdv[curr_col])))
	#print(switch_cd_index)
	if len(switch_cd_index[0]) > 1:
		split = min(switch_cd_index[0], key=lambda x:abs(x-(len(df_dqdv)/2)))
		# this chooses the split point which is closest to the halfway point of datapoints in the dataframe
	elif len(switch_cd_index[0])>0: 
		split = int(switch_cd_index[0])
	else:
		split = 0
	firstpart = df_dqdv[:split+1] 
	secondpart = df_dqdv[split+1:]
	if firstpart['dQ/dV'].mean() < secondpart['dQ/dV'].mean():
			# then the first part has more negative values
		discharge = firstpart
		charge = secondpart
	else:
		charge = firstpart
		discharge = secondpart
	charge = charge.reset_index(drop=True)
	discharge = discharge.reset_index(drop=True)
	return charge, discharge


def my_savgolay(dataframe, windowlength, polyorder):
	"""Takes battery dataframe with a dQ/dV column and applies a
	sav_golay filter to it, returning the dataframe with a new
	column called Smoothed_dQ/dV"""
	assert not windowlength % 2 == 0
	# asserts this is an odd number - necessary to run the
	# savgol_filter function
	assert polyorder < windowlength
	# necessary to run the savgol_filter function as well.
	unfilt = pd.concat([dataframe['dQ/dV']])
	unfiltar = unfilt.values
	dataframe['Smoothed_dQ/dV'] = scipy.signal.savgol_filter(unfiltar, windowlength, polyorder)
	return dataframe

#define column names:
def col_variables(datatype):
	"""This function provides a key for column names of the two 
	most widely used battery data collection instruments, Arbin and 
	MACCOR"""
	if datatype == 'ARBIN':
		cycle_ind_col = 'Cycle_Index'
		data_point_col = 'Data_Point'
		volt_col = 'Voltage(V)'
		curr_col = 'Current(A)'
		dis_cap_col = 'Discharge_Capacity(Ah)'
		char_cap_col = 'Charge_Capacity(Ah)'
		charge_or_discharge = 'Step_Index'
		# this is just used to make sure duplicate voltages are not removed from 
		# repeats in charge and discharge 
	elif datatype == 'MACCOR':
		cycle_ind_col = 'Cycle_Index'
		data_point_col = 'Rec'
		volt_col = 'Voltage(V)'
		curr_col = 'Current(A)'
		dis_cap_col = 'Cap(Ah)'
		char_cap_col = 'Cap(Ah)'
		charge_or_discharge = 'Md'
	else: 
		print('that is not a valid')
	return(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge)
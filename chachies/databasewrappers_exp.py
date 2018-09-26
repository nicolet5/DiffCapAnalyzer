import ast 
import io
import os
import pandas as pd 
from pandas import ExcelWriter
import pandas.io.sql as pd_sql
import sqlite3 as sql
import chachifuncs_exp as ccf
import descriptors
import databasefuncs as dbfs
import scipy
import numpy as np
# OVERALL Wrapper Function
################################



def process_data(file_name, database_name, decoded_contents, datatype, thresh1, thresh2):
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
		parse_update_master(file_name, database_name, datatype, decoded_contents)
		#this takes the info from the filename and updates the master table in the database. 
		# this also adds the raw data fram into the database
		cycle_dict = ccf.load_sep_cycles(file_name, database_name, datatype)
		clean_cycle_dict= ccf.get_clean_cycles(cycle_dict, file_name, database_name, datatype, thresh1, thresh2)
		clean_set_df = ccf.get_clean_sets(clean_cycle_dict, file_name, database_name)
		##################################################
		#uncomment the below to get descriptors ###########
		#####################################################
		#desc_df = descriptors.get_descriptors(clean_cycle_dict, datatype, windowlength, polyorder)
		#dbfs.update_database_newtable(desc_df, name3 + '-descriptors', database_name)
		#print('Database updated with descriptors.')
		###################################################################
		#######################################################################
		# pass this clean cycle dictionary to function to get descriptors - same as what we did with get clean setss
		#for k,v in clean_cycle_dict.items():
		#	print(k,v)
		# there are definitely values in the dictionary at this point 
		#should Switch descriptors to be after we get the clean set. maybe ask user if we want descriptors
		# since it seems to be the longest step
		

	return


def parse_update_master(file_name, database_name, datatype, decoded_contents):
	decoded = decoded_contents
	file_name2 = file_name
	while '/' in file_name2:
		file_name2 = file_name2.split('/', maxsplit = 1)[1]
	name = file_name2.split('.')[0]    
	if datatype == 'CALCE':
		data1 = pd.read_excel(io.BytesIO(decoded), 1)
		data1['datatype'] = 'CALCE'
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
		#print(data1.columns)
	else: 
		None
		#print('please put in either "CALCE" or "MACCOR" for datatype.')
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

        charge_keys =[]
        if param_dict_charge is not None:
            for key, value in param_dict_charge.items(): 
                if '_amplitude' in key:
                    #print(int(key.split('_')[0].split('a')[1]))
                    charge_keys.append(key.split('_')[0])
            #print(charge_keys) 
            new_dict_charge = {}
            new_dict_charge.update({'c_poly_coef1': param_dict_charge['c0'],
                             'c_poly_coef2': param_dict_charge['c1'], 
                             'c_poly_coef3': param_dict_charge['c2'], 
                             'c_poly_coef4': param_dict_charge['c3'], 
                             'c_poly_coef5': param_dict_charge['c4']})
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
            #print('center' + str(center))
            PeakArea, PeakAreaError = scipy.integrate.quad(my_pseudovoigt, 0.0, 100, args=(center, amp, fract, sigma))
            #print('peak location is : ' + str(center) + ' Peak area is: ' + str(PeakArea))
            new_dict_charge.update({'c_area_peak_'+str(peaknum): PeakArea, 
                             'c_center_peak_' +str(peaknum):center, 
                             'c_amp_peak_' +str(peaknum):amp,
                             'c_fract_peak_' +str(peaknum):fract, 
                             'c_sigma_peak_' +str(peaknum):sigma, 
                             'c_height_peak_' +str(peaknum):height, 
                             'c_fwhm_peak_' +str(peaknum):fwhm})      
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
                if '_amplitude' in key:
                    #print(int(key.split('_')[0].split('a')[1]))
                    discharge_keys.append(key.split('_')[0])
            #print(charge_keys) 
            new_dict_discharge = {}
            new_dict_discharge.update({'d_poly_coef1': param_dict_discharge['c0'],
                             'd_poly_coef2': param_dict_discharge['c1'], 
                             'd_poly_coef3': param_dict_discharge['c2'], 
                             'd_poly_coef4': param_dict_discharge['c3'], 
                             'd_poly_coef5': param_dict_discharge['c4']})
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
            #print('center' + str(center))
            PeakArea, PeakAreaError = scipy.integrate.quad(my_pseudovoigt, 0.0, 100, args=(center, amp, fract, sigma))
            #print('peak location is : ' + str(center) + ' Peak area is: ' + str(PeakArea))
            new_dict_discharge.update({'d_area_peak_'+str(peaknum): PeakArea, 
                             'd_center_peak_' +str(peaknum):center, 
                             'd_amp_peak_' +str(peaknum):amp,
                             'd_fract_peak_' +str(peaknum):fract, 
                             'd_sigma_peak_' +str(peaknum):sigma, 
                             'd_height_peak_' +str(peaknum):height, 
                             'd_fwhm_peak_' +str(peaknum):fwhm})      
        #print(new_dict)
        new_dict_df_d = pd.DataFrame(columns = new_dict_discharge.keys())
        for key1, val1 in new_dict_discharge.items():
            new_dict_df_d.at[0, key1] = new_dict_discharge[key1]
        discharge_descript = pd.concat([discharge_descript, new_dict_df_d])
        discharge_descript = discharge_descript.reset_index(drop = True)
        discharge_descript2 = descriptors.dfsortpeakvals(discharge_descript, 'd')

        # append the two dfs (charge and discharge) before putting them in database
        full_df_descript = pd.concat([charge_descript2, discharge_descript2], axis = 1)
        dbfs.update_database_newtable(full_df_descript, mod_params_name +'-descriptors', database)
    return
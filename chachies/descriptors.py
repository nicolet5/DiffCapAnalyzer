import scipy.signal
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import peakutils
from lmfit import models
import chachifuncs_sepcd as ccf
import os
import glob

################################
### OVERALL Wrapper Function ###
################################

def ML_generate(import_filepath):
	"""Generates a dataframe containing charge and discharge data
	also writes descriptors to an excel spreadsheet 'describe.xlsx'

	import_filepath = filepath containing cleaned separated cycles"""

	df_ch = df_generate(import_filepath, 'c')

	df_dc = df_generate(import_filepath, 'd')

	df_final = pd.concat([df_ch, df_dc], axis=1)
	#df_final = df_final.T.drop_duplicates().T

	writer = pd.ExcelWriter('describe.xlsx')
	df_final.to_excel(writer,'Sheet1')
	writer.save()

	return df_final

############################
### Sub - Wrapper Functions
############################

#first function called by ML_generate
def df_generate(import_filepath, cd):
	"""Creates a list of pandas dataframe containing descriptors for each battery

	import_filepath = filepath containing cleaned separated cycles
	cd = 'c' for charge and 'd' for discharge

	Output:
	df_ch = list of dictionaries for each battery
	col_ch = list of numbers of columns for each battery"""
	rootdir = import_filepath
	file_list = [f for f in glob.glob(os.path.join(rootdir,'*.xlsx'))]
	#iterate through dir to get excel file
	
	list_bats = [] 
	
	for file in file_list:

		name = os.path.split(file)[1].split('.')[0]
		batname = name.split('-')[0]
		if batname not in list_bats:
			list_bats.append(batname)
		else: None
	notice = 'Successfully extracted all battery names for ' + cd
	print(notice)
	df_ch = pd_create(cd)
	name_ch = []
	for bat in list_bats:
		notice = 'Fitting battery: ' + bat + ' ' + cd
		print(notice)

		df = imp_all(import_filepath, bat, cd)
		name_ch = name_ch + [bat] * len(df.index)
		df_ch = pd.concat([df_ch, df])
	df_ch['names'] = name_ch
		
	return df_ch

#dependencies
def imp_and_combine(path, battery, cd):
	"""imports separated charge, discharge spreadsheets from a specified path
	path = path to battery cycles
	battery = battery name
	cd = either 'c' for charge or 'd' for discharge

	Output: dataframe of descriptrs"""
	
	charge_descript = imp_all(path, battery, cd)

	charge_df = pd_create(cd)
	df = pd_update(charge_df, charge_descript)


	return df

def imp_all(source, battery, cd):
	"""Generates a list of dictionaries containing the fitting parameters for a particular battery

	source = string containing directory with the excel sheets for individual cycle data
	battery = string containing excel spreadsheet of file name

	Output:
	charge_descript = list of charge dictionaries"""

	file_pref = battery + '*.xlsx'
	file_list = [f for f in glob.glob(os.path.join(source,file_pref))]
	
	#this is the shit that sorts by cycle
	cycle = []
	for file in file_list:
		cyc1 = os.path.split(file)[1].split('Clean')[0]
		cyc = os.path.split(cyc1)[1].split('-Cycle')[1]
		cycle.append(int(cyc))

	cyc_sort = sorted(cycle)
	cyc_index = []
	for cyc in cyc_sort:
		cyc_index.append(cycle.index(cyc))
	
	file_sort = []
	for indices in cyc_index:
		file_sort.append(file_list[indices])

	#this is the end of the shit that sorts by cycle
	charge_descript = pd_create(cd)
	# while excel spreadsheet with path exists
	for file_val, cyc_loop in zip(file_sort, cyc_sort):

		c = imp_one_cycle(file_val, cd, cyc_loop, battery)
		print(cyc_loop)
		if c != 'throw':
			charge_descript = pd_update(charge_descript, c)

	return charge_descript

def imp_one_cycle(file_val, cd, cyc_loop, battery):
	"""imports and fits a single charge discharge cycle of a battery

	file_val = directory containing current cycle
	cd = either 'c' for charge or 'd' for discharge
	cyc_loop = cycle number
	battery = battery name

	output:
	a list of descriptors"""
	testdf = pd.read_excel(file_val)
	#print(cyc_loop)
	charge, discharge = ccf.sep_char_dis(testdf)
	if cd == 'c':
		df_run = charge
	elif cd == 'd':
		df_run = discharge
	else:
		raise TypeError("Cycle type must be either 'c' for charge or 'd' for discharge.")
	
	if (len(charge['Voltage(V)'].index) >= 10) and (len(discharge['Voltage(V)'].index) >= 10):
		
		c = descriptor_func(df_run['Voltage(V)'], df_run['Smoothed_dQ/dV'], cd, cyc_loop, battery)
	else:
		notice = 'Cycle ' + str(cyc_loop) + ' in battery '+ battery + ' had fewer than 10 datapoints and was removed from the dataset.'
		print(notice)
		c = 'throw'
	return c

def descriptor_func(V_series,dQdV_series, cd, cyc, battery):
    """Generates dictionary of descriptors

	V_series = Pandas series of voltage data
	dQdV_series = Pandas series of differential capacity data
	cd = either 'c' for charge and 'd' for discharge.

	Output:
	dictionary with keys 'codfficients', 'peakLocation(V)', 'peakHeight(dQdV)', 'peakFWHM'"""

    sigx_bot, sigy_bot = cd_dataframe(V_series, dQdV_series, cd)
    
    i = peak_finder(V_series, dQdV_series, cd)
    
    par, mod = model_gen(V_series,dQdV_series, cd, i, cyc, battery)

    model = model_eval(V_series,dQdV_series, cd, par, mod)
    
    coefficients = []
    

    for k in np.arange(4):
    	coef = 'c' + str(k)
    	coefficients.append(model.best_values[coef])

    desc = {'coefficients': coefficients}
    if len(i) > 0:
    	sigx, sigy = cd_dataframe(V_series, dQdV_series, cd)
    	desc.update({'peakLocation(V)': sigx[i].tolist(), 'peakHeight(dQdV)': sigy[i].tolist()})
    	FWHM = []
    	for index in i:
    		center, sigma, amplitude, fraction, comb = label_gen(index)
    		FWHM.append(model.best_values[sigma])
    	desc.update({'peakFWHM': FWHM})

    return desc

############################
### Sub - descriptor_func
############################

def cd_dataframe(V_series, dQdV_series, cd):
	"""Classifies and flips differential capactity data.

	V_series = Pandas series of voltage data
	dQdV_series = Pandas series of differential capacity data
	cd = either 'c' for charge and 'd' for discharge.

	Output:
	sigx = numpy array of signal x values
	sigy = numpy array of signal y values"""

	#converts voltage data to numpy array

	sigx = pd.to_numeric(V_series).as_matrix()

	#descriminates between charge and discharge cycle
	if cd == 'c':
		sigy = pd.to_numeric(dQdV_series).as_matrix()
	elif cd == 'd':
		sigy = -pd.to_numeric(dQdV_series).as_matrix()
	
	return sigx, sigy

def peak_finder(V_series, dQdV_series, cd):   
	"""Determines the index of each peak in a dQdV curve

	V_series = Pandas series of voltage data
	dQdV_series = Pandas series of differential capacity data
	cd = either 'c' for charge and 'd' for discharge.

	Output:
	i = list of indexes for each found peak"""
	sigx, sigy = cd_dataframe(V_series, dQdV_series, cd)
	windowlength = 25
	if len(sigy) > windowlength:
		sigy_smooth = scipy.signal.savgol_filter(sigy, windowlength, 3)
	elif len(sigy) > 10:
		sigy_smooth = sigy
	i = peakutils.indexes(sigy_smooth, thres=.3/max(sigy_smooth), min_dist=9)

	return i

def label_gen(index):
    """Generates label set for individual gaussian
	index = index of peak location

	output string format: 
	'a' + index + "_" + parameter"""
    
    pref = str(int(index))
    comb = 'a' + pref + '_'
    
    cent = 'center'
    sig = 'sigma'
    amp = 'amplitude'
    fract = 'fraction'
    
    center = comb + cent
    sigma = comb + sig
    amplitude = comb + amp
    fraction = comb + fract
    
    return center, sigma, amplitude, fraction, comb
    
def model_gen(V_series, dQdV_series, cd, i, cyc, battery):
    """Develops initial model and parameters for battery data fitting.

	V_series = Pandas series of voltage data
	dQdV_series = Pandas series of differential capacity data
	cd = either 'c' for charge and 'd' for discharge.

	Output:
	par = lmfit parameters object
	mod = lmfit model object"""
    
    sigx_bot, sigy_bot = cd_dataframe(V_series, dQdV_series, cd)
    
    mod = models.PolynomialModel(4)
    par = mod.guess(sigy_bot, x=sigx_bot)
    #i = np.append(i, i+5)
    #print(i)
    if all(i) == False:
    	notice = 'Cycle ' + str(cyc) + cd + ' in battery ' + battery + ' has no peaks.'
    	print(notice)
    else:
    	for index in i:
	        
	        center, sigma, amplitude, fraction, comb = label_gen(index)
	        
	        gaus_loop = models.PseudoVoigtModel(prefix=comb)
	        par.update(gaus_loop.make_params())

	        par[center].set(sigx_bot[index], min=sigx_bot[index]-0.01, max=sigx_bot[index]+0.01)
	        par[sigma].set(0.01)
	        par[amplitude].set(.05, min=0)
	        par[fraction].set(.5, min=0, max=1)

	        mod = mod + gaus_loop
        
    return par, mod

def model_eval(V_series, dQdV_series, cd, par, mod):
	"""evaluate lmfit model generated in model_gen function

	V_series = Pandas series of voltage data
	dQdV_series = Pandas series of differential capacity data
	cd = either 'c' for charge and 'd' for discharge.
	par = lmfit parameters object
	mod = lmfit model object

	output:
	model = lmfit model object fitted to dataset"""
	sigx_bot, sigy_bot = cd_dataframe(V_series, dQdV_series, cd)

	model = mod.fit(sigy_bot, par, x=sigx_bot)

	return model

#next function to be called by imp_and_combine
def pd_create(cd):
	"""Creates a blank dataframe for a particular battery containing either charge or discharge descriptors

	charege_descript = list of dictionaries containing descriptors
	name_dat = name of battery prior to '-'
	cd = either 'c' for charge or 'd' for discharge

	Output:
	blank pandas dataframe with descriptor columns and cycle number rows"""

	if cd == 'c':
		prefix = 'ch_'
	else:
		prefix = 'dc_'
	
	names = []
	for ch in np.arange(19):
		names.append(prefix + str(int(ch)))
	
	desc = pd.DataFrame(columns = names)

	return desc

def pd_update(desc, charge_descript):
	"""adds list to the pandas DataFrame

	desc = blank dataframe from pd_create
	charge_descript = descriptor dictionaries

	Output:
	pandas dataframe for a single battery"""

	#for i in np.arange(len(desc.index)):
	#desc_ls = dict_2_list(charge_descript[i])
	desc_ls = dict_2_list(charge_descript)
	#print(desc_ls)
		
	desc_app = desc_ls + np.zeros(19-len(desc_ls)).tolist()

	#print(desc.head())
	desc_df = pd.DataFrame([desc_app], columns = desc.columns)
	desc = pd.concat([desc, desc_df], ignore_index=True)
	#print(desc.head())

	return desc

#used by pd_update
def dict_2_list(desc):
	"""Converts a dictionary of descriptors into a list for pandas assignment

	desc = dictionary containing descriptors

	Output:
	list of descriptors"""
	desc_ls = list(desc['coefficients'])
	if 'peakFWHM' in desc.keys():
		for i in np.arange(len(desc['peakFWHM'])):
			desc_ls.append(desc['peakLocation(V)'][i])
			desc_ls.append(desc['peakHeight(dQdV)'][i])
			desc_ls.append(desc['peakFWHM'][i])

	return desc_ls

#final function used by ML_generate
def df_combine(df_ch, cd):
	"""creates a dataframe containing charge descriptors for all batteries for a charge or discharge cycle

	df_ch = list of dataframes for each battery
	col_ch = list of dataframe columns

	Output: dataframe containing charge or discharge descriptors for all batteries"""
	
	df_max = pd_create(cd)

	for df in df_ch:
		df_max.append(df)

	return df_max
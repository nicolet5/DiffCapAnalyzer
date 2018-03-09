import scipy.signal
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import peakutils
from lmfit import models
import chachifuncs
import os
import glob

#peak finding algorithm

def peak_finder(V_series, dQdV_series, cd):   
	"""Determines the index of each peak in a dQdV curve V_series = Pandas series of voltage data dQdV_series = Pandas series of differential capacity data cd = either 'c' for charge and 'd' for discharge."""
	sigx, sigy = cd_dataframe(V_series, dQdV_series, cd)
	windowlength = 25
	if len(sigy) > windowlength:
		sigy_smooth = scipy.signal.savgol_filter(sigy, windowlength, 3)
	elif len(sigy) > 10:
		sigy_smooth = sigy
	i = peakutils.indexes(sigy_smooth, thres=3/max(sigy_smooth), min_dist=9)

	return i

def cd_dataframe(V_series, dQdV_series, cd):
	"""Classifies and flips differential capactity data.

V_series = Pandas series of voltage data
dQdV_series = Pandas series of differential capacity data
cd = either 'c' for charge and 'd' for discharge."""

	sigx = pd.to_numeric(V_series).as_matrix()
	if cd == 'c':
		sigy = -pd.to_numeric(dQdV_series).as_matrix()
	elif cd == 'd':
		sigy = pd.to_numeric(dQdV_series).as_matrix()

	return sigx, sigy



def model_gen(V_series, dQdV_series, cd, i):
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

    for index in i:
        
        center, sigma, amplitude, fraction, comb = label_gen(index)
        
        gaus_loop = models.PseudoVoigtModel(prefix=comb)
        par.update(gaus_loop.make_params())

        par[center].set(sigx_bot[index], vary=False)
        par[sigma].set(0.001)
        par[amplitude].set(5, min=0)
        par[fraction].set(.5, min=0, max=1)

        mod = mod + gaus_loop
        
    return par, mod

def model_eval(V_series, dQdV_series, cd, par, mod):
    sigx_bot, sigy_bot = cd_dataframe(V_series, dQdV_series, cd)
    
    model = mod.fit(sigy_bot, par, x=sigx_bot)
    #print(model.fit_report(min_correl=0.5))

    #fig = plt.figure(figsize=(10, 10), facecolor='w', edgecolor='k')
    #plt.plot(sigx_bot, sigy_bot)
    #plt.plot(sigx_bot, model.init_fit, 'k--')
    #plt.plot(sigx_bot, model.best_fit, 'r-')
    
    return model

def label_gen(index):
    """Generates label set for individual gaussian
index = index of peak location

output string format: 
'a' + index + "_" + parameters"""
    
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

def descriptor_func(V_series,dQdV_series, cd, file_val):
    """Generates dictionary of descriptors

V_series = Pandas series of voltage data
dQdV_series = Pandas series of differential capacity data
cd = either 'c' for charge and 'd' for discharge."""

    sigx_bot, sigy_bot = cd_dataframe(V_series, dQdV_series, cd)
    
    i = peak_finder(V_series, dQdV_series, cd)
    
    par, mod = model_gen(V_series,dQdV_series, cd, i)

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
    else:
    	print(file_val)

    return desc


def imp_item(direct, pref, cyc, sgf_frame, sgf_order):
	"""Function to import a set of charge, discharge pandas dataframes from a single file

	direct = string containing directory with the excel sheets for individual cycle data
	pref = text prior to the cycle number
	cyc = cycle number (must be an integer)
	sgf_frame = Savitzky-Golay filter frame width
	sgf_order =Savitzsky-Golay filter order"""
	pt = direct + pref + str(cyc)

	testdf = pd.read_excel(pt)
	#just picked a random one out of the separated out cycles

	charge, discharge = chachifuncs.sep_char_dis(testdf)


	return charge, discharge

def imp_all(source):
	"""Generates a list of dictionaries containing the fitting parameters

	source = string containing directory with the excel sheets for individual cycle data"""
	file_list = [f for f in glob.glob(os.path.join(source,'*.xlsx'))]

	name_l = os.path.split(file_list[1])[1].split('.')[0]
	name_dat = os.path.split(name_l)[1].split('-')[0]

	charge_descript = []
	discharge_descript = []
	# while excel spreadsheet with path exists
	for file_val in file_list:

		testdf = pd.read_excel(file_val)
		#just picked a random one out of the separated out cycles

		charge, discharge = chachifuncs.sep_char_dis(testdf)
		
		if (len(charge['Voltage(V)'].index) >= 10) and (len(discharge['Voltage(V)'].index) >= 10):
			c = descriptor_func(charge['Voltage(V)'], charge['Smoothed_dQ/dV'], 'c', file_val)
			d = descriptor_func(discharge['Voltage(V)'] , discharge['Smoothed_dQ/dV'], 'd', file_val)
			charge_descript.append(c)
			discharge_descript.append(d)


	return charge_descript, discharge_descript, name_dat

def pd_create(charge_descript, name_dat, cd):
	"""Creates a blank dataframe for a particular battery containing charge, discharge descriptors

	"""
	ncyc = len(charge_descript)
	if cd == 'c':
		prefix = 'ch_'
	else:
		prefix = 'dc_'
	
	ch_npeaks = []
	for ch in charge_descript:
		if 'peakFWHM' in ch.keys():
			ch_npeaks.append(len(ch['peakFWHM']))
	ch_mxpeaks = max(ch_npeaks)

	desc = pd.DataFrame()
	for ch in np.arange(ch_mxpeaks*3+4):
		names = prefix + str(int(ch))
		par = pd.DataFrame({names: np.zeros(ncyc)})
		desc = pd.concat([desc, par], axis=1)

	desc.index.names = [name_dat]

	return desc

def dict_2_list(desc):
	"""Converts a dictionary of descriptors into a list for pandas assignment

	desc = pandas dataframe containing descriptors"""
	desc_ls = list(desc['coefficients'])
	if 'peakFWHM' in desc.keys():
		for i in np.arange(len(desc['peakFWHM'])):
			desc_ls.append(desc['peakLocation(V)'][i])
			desc_ls.append(desc['peakHeight(dQdV)'][i])
			desc_ls.append(desc['peakFWHM'][i])

	return desc_ls

def pd_update(desc, charge_descript):
	"""adds list to the series
	desc = blank dataframe from pd_create
	charge_descript = list of descriptor dictionaries"""

	for index, row in desc.iterrows():
		desc_ls = dict_2_list(charge_descript[index])

		i = 0
		for it in desc_ls:
			row.iat[i] = it
			i = i + 1

	return desc

def imp_and_combine(path):
	"""imports separated charge, discharge spreadsheets from a specified path and generates a dataframe of descriptrs"""
	
	charge_descript, discharge_descript, name_dat = imp_all(path)

	charge_df = pd_create(charge_descript, name_dat, 'c')
	charge_df = pd_update(charge_df, charge_descript)

	discharge_df = pd_create(discharge_descript, name_dat, 'd')
	discharge_df = pd_update(discharge_df, discharge_descript)

	df = pd.concat([charge_df, discharge_df], axis = 1)

	return df


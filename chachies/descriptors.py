import scipy.signal
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import peakutils
from lmfit import models

#peak finding algorithm

def peak_finder(V_series, dQdV_series, cd):   
	"""Determines the index of each peak in a dQdV curve V_series = Pandas series of voltage data dQdV_series = Pandas series of differential capacity data cd = either 'c' for charge and 'd' for discharge."""
	sigx, sigy = cd_dataframe(V_series, dQdV_series, cd)

	sigy_smooth = scipy.signal.savgol_filter(sigy, 25, 3)

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

def descriptor_func(V_series,dQdV_series, cd):
    """Generates dictionary of descriptors

V_series = Pandas series of voltage data
dQdV_series = Pandas series of differential capacity data
cd = either 'c' for charge and 'd' for discharge."""
    sigx_bot, sigy_bot = cd_dataframe(V_series, dQdV_series, cd)
    
    i = peak_finder(V_series, dQdV_series, cd)
    
    par, mod = model_gen(V_series,dQdV_series, cd, i)

    model = model_eval(V_series,dQdV_series, cd, par, mod)
    
    sigx, sigy = cd_dataframe(V_series, dQdV_series, cd) 
    
    desc = {'peakLocation(V)': sigx[i], 'peakHeight(dQdV)': sigy[i]}
    
    FWHM = []
    for index in i:
        center, sigma, amplitude, fraction, comb = label_gen(index)
        FWHM.append(model.best_values[sigma])

    
    coefficients = []
    for k in np.arange(4):
        coef = 'c' + str(k)
        coefficients.append(model.best_values[coef])
        
    desc.update({'peakFWHM': FWHM, 'coefficients': coefficients})
    
    return desc
    
    
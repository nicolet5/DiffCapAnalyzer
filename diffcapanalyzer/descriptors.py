import scipy.signal
import pandas as pd
import numpy as np
import peakutils
from lmfit import models
import os
import glob

from diffcapanalyzer.chachifuncs import col_variables

def peak_finder(df_run, cd, windowlength, polyorder, datatype, lenmax, peak_thresh):
    """Determines the index of each peak in a dQdV curve
    V_series = Pandas series of voltage data
    dQdV_series = Pandas series of differential capacity data
    cd = either 'c' for charge and 'd' for discharge.
    
    Output:
    i = list of indexes for each found peak"""
    (cycle_ind_col, data_point_col, volt_col, curr_col, \
        dis_cap_col, char_cap_col, charge_or_discharge) = col_variables(datatype)
    V_series = df_run[volt_col]
    # this makes the peak finding smoothing independent of any smoothing that has already occured. 
    dQdV_series = df_run['Smoothed_dQ/dV']
    sigx, sigy = cd_dataframe(V_series, dQdV_series, cd)
    #the below is to make sure the window length ends up an odd number - even though we are basing it on the length of the df
    wl = lenmax/20
    wlint = int(round(wl))
    if wlint%2 == 0:
        windowlength_new = wlint + 1
    else: 
        windowlength_new = wlint
    if len(sigy) > windowlength_new and windowlength_new > polyorder:
        #has to be larger than 69 so that windowlength > 3 - necessary for sav golay function  
        sigy_smooth = scipy.signal.savgol_filter(sigy, windowlength_new, polyorder)
    else:
        sigy_smooth = sigy
    peak_thresh_ft = float(peak_thresh)
    i = peakutils.indexes(sigy_smooth, thres=peak_thresh_ft, min_dist=lenmax/50)
    if i is not None and len(i)>0:
        sigx_volts = list(sigx[i])
        peak_heights = list(sigy[i])
    else:
        sigx_volts = []
        peak_heights = []
    return i, sigx_volts, peak_heights

def cd_dataframe(V_series, dQdV_series, cd):
    """Classifies and flips differential capactity data.
    V_series = Pandas series of voltage data
    dQdV_series = Pandas series of differential capacity data
    cd = either 'c' for charge and 'd' for discharge.
    Output:
    sigx = numpy array of signal x values
    sigy = numpy array of signal y values"""
    sigx = pd.to_numeric(V_series).values
    # descriminates between charge and discharge cycle
    if cd == 'c':
        sigy = pd.to_numeric(dQdV_series).values
    elif cd == 'd':
        sigy = -pd.to_numeric(dQdV_series).values
    return sigx, sigy

def label_gen(index):
    """Generates label set for individual gaussian
    index = index of peak location
    output string format:
    'a' + index + "_" + parameter"""
    # generates unique parameter strings based on index of peak
    pref = str(int(index))
    comb = 'a' + pref + '_'
    cent = 'center'
    sig = 'sigma'
    amp = 'amplitude'
    fract = 'fraction'
    # creates final objects for use in model generation
    center = comb + cent
    sigma = comb + sig
    amplitude = comb + amp
    fraction = comb + fract
    return center, sigma, amplitude, fraction, comb

def model_gen(V_series, dQdV_series, cd, i, cyc, thresh):
    """Develops initial model and parameters for battery data fitting.
    V_series = Pandas series of voltage data
    dQdV_series = Pandas series of differential capacity data
    cd = either 'c' for charge and 'd' for discharge.
    i = list of peak indices found by peak finder 
    Output:
    par = lmfit parameters object
    mod = lmfit model object"""

    # generates numpy arrays for use in fitting
    sigx_bot, sigy_bot = cd_dataframe(V_series, dQdV_series, cd)
    if len(sigx_bot)>5 and sigx_bot[5]>sigx_bot[1]:
        # check if the voltage values are increasing - the right order for gaussian
        sigx_bot_new = sigx_bot
        sigy_bot_new = sigy_bot
        newi = i
    else:
        sigx_bot_new = sigx_bot[::-1] 
        # reverses the order of elements in the array
        sigy_bot_new = sigy_bot[::-1]
        newi = np.array([], dtype = int)
        for elem in i:
            # append a new index, because now everything is backwards
            newi = np.append(newi, int(len(sigx_bot_new) - elem - 1))
    if all(newi) is False or len(newi) < 1:
        base_mod = models.GaussianModel(prefix = 'base_')
        mod = base_mod
        par = mod.make_params()
    else:
        # have to convert from inputted voltages to indices of peaks within sigx_bot
        user_appended_ind = []
        rev_user_append = []
        if type(i) != list: 
            i = i.tolist()
        if type(newi) != list: 
            newi = newi.tolist()
        count = 0
        for index in newi:

            # generates unique parameter strings based on index of peak
            center, sigma, amplitude, fraction, comb = label_gen(
                index)
            # generates a pseudo voigt fitting model
            gaus_loop = models.PseudoVoigtModel(prefix=comb)
            if count == 0:
                mod = gaus_loop 
                par = mod.make_params()
                count = count + 1
            else: 
                mod = mod + gaus_loop
                par.update(gaus_loop.make_params())
                count = count + 1 
            par[center].set(sigx_bot_new[index], vary=False)
            par[sigma].set((np.max(sigx_bot_new)-np.min(sigx_bot_new))/100)
            par[amplitude].set((np.mean(sigy_bot_new))/50, min=0)
            par[fraction].set(.5, min=0, max=1)

    # then add the gaussian after the peaks
        base_mod = models.GaussianModel(prefix = 'base_')
        mod = mod + base_mod
        base_par = base_mod.make_params()
        base_par['base_amplitude'].set(np.mean(sigy_bot_new))
        # these are initial guesses for the base
        base_par['base_center'].set(np.mean(sigx_bot_new))
        base_par['base_sigma'].set((np.max(sigx_bot_new)-np.min(sigx_bot_new))/2)
        par.update(base_par)
    return par, mod, i

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
    if len(sigx_bot)>5 and sigx_bot[5]>sigx_bot[1]:
        # check if the voltage values are increasing - the right order for gaussian
        sigx_bot_new = sigx_bot
        sigy_bot_new = sigy_bot
    else:
        sigx_bot_new = sigx_bot[::-1] # reverses the order of elements in the array
        sigy_bot_new = sigy_bot[::-1]

    try: 
        model = mod.fit(sigy_bot_new, params = par, x=sigx_bot_new)
    except Exception:
        model = None
    return model

def dfsortpeakvals(mydf, cd):
    """This sorts the peak values based off of all the other values in the df, so that 
    all that belong to peak 1 are in the peak one column etc. Mydf has to be of only charge or
    discharge data. Filter for that first then feed into this function"""

    filter_col_loc=[col for col in mydf if str(col).startswith(cd + '_center')]
    filter_col_height = [col for col in mydf if str(col).startswith(cd + '_height')]
    filter_col_area = [col for col in mydf if str(col).startswith(cd + '_area')]
    filter_col_sigma = [col for col in mydf if str(col).startswith(cd + '_sigma')]
    filter_col_ampl= [col for col in mydf if str(col).startswith(cd + '_amp')]
    filter_col_fwhm = [col for col in mydf if str(col).startswith(cd + '_fwhm')]
    filter_col_fract = [col for col in mydf if str(col).startswith(cd + '_fract')]
    filter_col_actheight = [col for col in mydf if str(col).startswith(cd+'_rawheight')]
    newdf = pd.DataFrame(None)
    for col in filter_col_loc:
        newdf = pd.concat([newdf, mydf[col]])
    if len(newdf)>0:
        newdf.columns = ['allpeaks']
        sortdf = newdf.sort_values(by = 'allpeaks')
        sortdf = sortdf.reset_index(inplace = False)
        newgroupindex = np.where(np.diff(sortdf['allpeaks'])>0.01)
        listnew=newgroupindex[0].tolist()
        listnew.insert(0, 0)
        listnew.append(len(sortdf))
        groupdict = {}
        for i in range(1, len(listnew)):
            if i ==1: 
                newgroup = sortdf[listnew[i-1]:listnew[i]+1]
            else: 
                newgroup = sortdf[listnew[i-1]+1:listnew[i]+1]  
            newkey = newgroup.allpeaks.mean()
            groupdict.update({newkey: newgroup})
        count = 0
        for key in groupdict:
            count = count + 1
            mydf['sortedloc-'+cd+'-'+str(count)] = None
            mydf['sortedheight-'+cd+'-'+str(count)] = None
            mydf['sortedarea-'+cd+'-'+str(count)] = None
            mydf['sortedSIGMA-'+cd+'-'+str(count)] = None 
            mydf['sortedamplitude-'+cd+'-'+str(count)] = None 
            mydf['sortedfwhm-'+cd+'-'+str(count)] = None 
            mydf['sortedfraction-'+cd+'-'+str(count)] = None
            mydf['sortedactheight-'+cd+'-'+str(count)] = None  
            for j in range(len(filter_col_loc)):
            #iterate over the names of columns in mydf - ex[peakloc1, peakloc2, peakloc3..]
                # this is where we sort the values in the df based on if they appear in the group
                for i in range(len(mydf)):
                    #iterate over rows in the dataframe
                    if mydf.loc[i,(filter_col_loc[j])] >= min(list(groupdict[key].allpeaks)) and mydf.loc[i,(filter_col_loc[j])] <= max(list(groupdict[key].allpeaks)):
                        mydf.loc[i, ('sortedloc-'+cd+'-'+str(count))] = mydf.loc[i, (filter_col_loc[j])]
                        mydf.loc[i, ('sortedheight-'+cd+'-' + str(count))] = mydf.loc[i, (filter_col_height[j])]
                        mydf.loc[i, ('sortedarea-'+cd+'-'+str(count))] = mydf.loc[i, (filter_col_area[j])]
                        mydf.loc[i, ('sortedSIGMA-'+cd+'-'+str(count))] = mydf.loc[i, (filter_col_sigma[j])]
                        mydf.loc[i, ('sortedamplitude-'+cd+'-'+str(count))] = mydf.loc[i, (filter_col_ampl[j])]
                        mydf.loc[i, ('sortedfwhm-'+cd+'-'+str(count))] = mydf.loc[i, (filter_col_fwhm[j])] 
                        mydf.loc[i, ('sortedfraction-'+cd+'-'+str(count))] = mydf.loc[i, (filter_col_fract[j])] 
                        mydf.loc[i, ('sortedactheight-'+cd+'-'+str(count))] = mydf.loc[i, (filter_col_actheight[j])]
                    else:
                        None
    else: 
        None 
        # this will just return the original df  - nothing sorted 
    return mydf



import ast
import scipy.signal
import pandas as pd
import numpy as np
import peakutils
from lmfit import models
import os
import glob

from diffcapanalyzer.chachifuncs import col_variables, sep_char_dis
from diffcapanalyzer.databasefuncs import update_database_newtable, get_file_from_database

# Wrapper Functions

def generate_model(df_clean, filename, peak_thresh, database):
    """Wrapper for the get_model_dfs function. Takes those results
    and adds them to the database with three new tables
    with the suffices: '-ModPoints', 'ModParams',
    and '-descriptors'."""
    datatype = df_clean['datatype'].iloc[0]
    (cycle_ind_col, data_point_col, volt_col, curr_col,
     dis_cap_col, char_cap_col, charge_or_discharge) = col_variables(datatype)
    chargeloc_dict = {}
    param_df = pd.DataFrame(
        columns=[
            'Cycle',
            'Model_Parameters_charge',
            'Model_Parameters_discharge'])
    if len(df_clean[cycle_ind_col].unique()) > 1:
        length_list = [len(df_clean[df_clean[cycle_ind_col] == cyc])
                       for cyc in df_clean[cycle_ind_col].unique() if cyc != 1]
        lenmax = max(length_list)
    else:
        length_list = 1
        lenmax = len(df_clean)

    mod_pointsdf = pd.DataFrame()
    cycles_no_models = []
    for cyc in df_clean[cycle_ind_col].unique():
        try:
            new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d = get_model_dfs(
                df_clean, datatype, cyc, lenmax, peak_thresh)
            mod_pointsdf = mod_pointsdf.append(new_df_mody)
            param_df = param_df.append({'Cycle': cyc,
                                        'Model_Parameters_charge': str(model_c_vals),
                                        'Model_Parameters_discharge': str(model_d_vals),
                                        'charge_peak_heights': str(peak_heights_c),
                                        'discharge_peak_heights': str(peak_heights_d)},
                                       ignore_index=True)
        except Exception as e:
            cycles_no_models.append(cyc)
    # want this outside of for loop to update the db with the complete df of
    # new params
    update_database_newtable(
        mod_pointsdf,
        filename.split('.')[0] +
        '-ModPoints',
        database)
    # this will replace the data table in there if it exists already
    update_database_newtable(
        param_df,
        filename.split('.')[0] +
        'ModParams',
        database)
    # the below also updates the database with the new descriptors after evaluating the spit out
    # dictionary and putting those parameters into a nicely formatted
    # datatable.
    param_dicts_to_df(filename.split('.')[0] + 'ModParams', database)
    if len(cycles_no_models) > 0:
        return 'That model has been added to the database.' \
            + 'No model was generated for Cycle(s) ' + str(cycles_no_models)
    return 'That model has been added to the database'


def get_model_dfs(df_clean, datatype, cyc, lenmax, peak_thresh):
    """This is the wrapper for the model generation and fitting for the cycles.
    Returns dictionaries for the charge cycle model parameters and discharge
    cycle model parameters. These will each have at the least base gaussian
    parameter values, with the keys: 'base_amplitude', 'base_center',
    'base_fwhm', 'base_height', and 'base_sigma'. The other keys are
    dependent on whether any peaks were found in the cycle.
    """
    (cycle_ind_col, data_point_col, volt_col, curr_col,
     dis_cap_col, char_cap_col, charge_or_discharge) = col_variables(datatype)
    clean_charge, clean_discharge = sep_char_dis(
        df_clean[df_clean[cycle_ind_col] == cyc], datatype)
    windowlength = 9
    polyorder = 3

    i_charge, volts_i_ch, peak_heights_c = peak_finder(clean_charge,
                                                       'c', windowlength,
                                                       polyorder,
                                                       datatype,
                                                       lenmax,
                                                       peak_thresh)

    V_series_c = clean_charge[volt_col]
    dQdV_series_c = clean_charge['Smoothed_dQ/dV']
    par_c, mod_c, indices_c = model_gen(
        V_series_c, dQdV_series_c, 'c', i_charge, cyc, peak_thresh)
    model_c = model_eval(V_series_c, dQdV_series_c, 'c', par_c, mod_c)
    if model_c is not None:
        mod_y_c = mod_c.eval(params=model_c.params, x=V_series_c)
        myseries_c = pd.Series(mod_y_c)
        myseries_c = myseries_c.rename('Model')
        model_c_vals = model_c.values
        new_df_mody_c = pd.concat(
            [myseries_c, V_series_c, dQdV_series_c, clean_charge[cycle_ind_col]], axis=1)
    else:
        mod_y_c = None
        new_df_mody_c = None
        model_c_vals = None
    # now the discharge:
    i_discharge, volts_i_dc, peak_heights_d = peak_finder(
        clean_discharge, 'd', windowlength, polyorder, datatype, lenmax, peak_thresh)
    V_series_d = clean_discharge[volt_col]
    dQdV_series_d = clean_discharge['Smoothed_dQ/dV']
    par_d, mod_d, indices_d = model_gen(
        V_series_d, dQdV_series_d, 'd', i_discharge, cyc, peak_thresh)
    model_d = model_eval(V_series_d, dQdV_series_d, 'd', par_d, mod_d)
    if model_d is not None:
        mod_y_d = mod_d.eval(params=model_d.params, x=V_series_d)
        myseries_d = pd.Series(mod_y_d)
        myseries_d = myseries_d.rename('Model')
        new_df_mody_d = pd.concat(
            [-myseries_d, V_series_d, dQdV_series_d, clean_discharge[cycle_ind_col]], axis=1)
        model_d_vals = model_d.values
    else:
        mod_y_d = None
        new_df_mody_d = None
        model_d_vals = None

    if new_df_mody_c is not None or new_df_mody_d is not None:
        new_df_mody = pd.concat([new_df_mody_c, new_df_mody_d], axis=0)
    else:
        new_df_mody = None

    return new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d


# Component Functions

def my_pseudovoigt(x, cent, amp, fract, sigma):
    """This function is from http://cars9.uchicago.edu/software/python/lmfit/builtin_models.html"""
    sig_g = sigma / \
        np.sqrt(2 * np.log(2))  # calculate the sigma_g parameter for the gaussian distribution
    part1 = (((1 - fract) * amp) / (sig_g * np.sqrt(2 * np.pi))) * \
        np.exp((-(x - cent)**2) / (2 * sig_g**2))
    part2 = ((fract * amp) / np.pi) * (sigma / ((x - cent)**2 + sigma**2))
    fit = part1 + part2
    return(fit)


def param_dicts_to_df(mod_params_name, database):
    """Uses the already generated parameter dictionaries stored in the filename+ModParams
    datatable in the database, to add in the dictionary data table with those parameter
    dictionaries formatted nicely into one table. """
    mod_params_df = get_file_from_database(mod_params_name, database)
    charge_descript = pd.DataFrame()
    discharge_descript = pd.DataFrame()
    for i in range(len(mod_params_df)):
        param_dict_charge = ast.literal_eval(
            mod_params_df.loc[i, ('Model_Parameters_charge')])
        param_dict_discharge = ast.literal_eval(
            mod_params_df.loc[i, ('Model_Parameters_discharge')])
        charge_peak_heights = ast.literal_eval(
            mod_params_df.loc[i, ('charge_peak_heights')])
        discharge_peak_heights = ast.literal_eval(
            mod_params_df.loc[i, ('discharge_peak_heights')])
        charge_keys = []
        new_dict_charge = {}
        if param_dict_charge is not None:
            for key, value in param_dict_charge.items():
                if '_amplitude' in key and 'base_' not in key:
                    charge_keys.append(key.split('_')[0])
            new_dict_charge.update({'c_gauss_sigma': param_dict_charge['base_sigma'],  # changed from c0- c4  to base_ .. 10-10-18
                                    'c_gauss_center': param_dict_charge['base_center'],
                                    'c_gauss_amplitude': param_dict_charge['base_amplitude'],
                                    'c_gauss_fwhm': param_dict_charge['base_fwhm'],
                                    'c_gauss_height': param_dict_charge['base_height'],
                                    })
            new_dict_charge.update(
                {'c_cycle_number': float(mod_params_df.loc[i, ('Cycle')])})
        peaknum = 0
        for item in charge_keys:
            peaknum = peaknum + 1
            center = param_dict_charge[item + '_center']
            amp = param_dict_charge[item + '_amplitude']
            fract = param_dict_charge[item + '_fraction']
            sigma = param_dict_charge[item + '_sigma']
            height = param_dict_charge[item + '_height']
            fwhm = param_dict_charge[item + '_fwhm']
            raw_peakheight = charge_peak_heights[peaknum - 1]
            PeakArea, PeakAreaError = scipy.integrate.quad(my_pseudovoigt,
                                                           0.0,
                                                           100,
                                                           args=(center,
                                                                 amp,
                                                                 fract,
                                                                 sigma))
            new_dict_charge.update({'c_area_peak_' +
                                    str(peaknum): PeakArea, 'c_center_peak_' +
                                    str(peaknum): center, 'c_amp_peak_' +
                                    str(peaknum): amp, 'c_fract_peak_' +
                                    str(peaknum): fract, 'c_sigma_peak_' +
                                    str(peaknum): sigma, 'c_height_peak_' +
                                    str(peaknum): height, 'c_fwhm_peak_' +
                                    str(peaknum): fwhm, 'c_rawheight_peak_' +
                                    str(peaknum): raw_peakheight})
        new_dict_df = pd.DataFrame(columns=new_dict_charge.keys())
        for key1, val1 in new_dict_charge.items():
            new_dict_df.at[0, key1] = new_dict_charge[key1]
        charge_descript = pd.concat([charge_descript, new_dict_df], sort=True)
        charge_descript = charge_descript.reset_index(drop=True)
        charge_descript2 = dfsortpeakvals(charge_descript, 'c')
        discharge_keys = []
        if param_dict_discharge is not None:
            for key, value in param_dict_discharge.items():
                if '_amplitude' in key and 'base_' not in key:
                    discharge_keys.append(key.split('_')[0])
            new_dict_discharge = {}
            new_dict_discharge.update({'d_gauss_sigma': param_dict_discharge['base_sigma'],  # changed 10-10-18
                                       'd_gauss_center': param_dict_discharge['base_center'],
                                       'd_gauss_amplitude': param_dict_discharge['base_amplitude'],
                                       'd_gauss_fwhm': param_dict_discharge['base_fwhm'],
                                       'd_gauss_height': param_dict_discharge['base_height'],
                                       })
            new_dict_discharge.update(
                {'d_cycle_number': float(mod_params_df.loc[i, ('Cycle')])})
            peaknum = 0
            for item in discharge_keys:
                peaknum = peaknum + 1
                center = param_dict_discharge[item + '_center']
                amp = param_dict_discharge[item + '_amplitude']
                fract = param_dict_discharge[item + '_fraction']
                sigma = param_dict_discharge[item + '_sigma']
                height = param_dict_discharge[item + '_height']
                fwhm = param_dict_discharge[item + '_fwhm']
                raw_peakheight = discharge_peak_heights[peaknum - 1]
                PeakArea, PeakAreaError = scipy.integrate.quad(
                    my_pseudovoigt, 0.0, 100, args=(center, amp, fract, sigma))
                new_dict_discharge.update({'d_area_peak_' +
                                           str(peaknum): PeakArea, 'd_center_peak_' +
                                           str(peaknum): center, 'd_amp_peak_' +
                                           str(peaknum): amp, 'd_fract_peak_' +
                                           str(peaknum): fract, 'd_sigma_peak_' +
                                           str(peaknum): sigma, 'd_height_peak_' +
                                           str(peaknum): height, 'd_fwhm_peak_' +
                                           str(peaknum): fwhm, 'd_rawheight_peak_' +
                                           str(peaknum): raw_peakheight})
        else:
            new_dict_discharge = None
        if new_dict_discharge is not None:
            new_dict_df_d = pd.DataFrame(columns=new_dict_discharge.keys())
            for key1, val1 in new_dict_discharge.items():
                new_dict_df_d.at[0, key1] = new_dict_discharge[key1]
            discharge_descript = pd.concat(
                [discharge_descript, new_dict_df_d], sort=True)
            discharge_descript = discharge_descript.reset_index(drop=True)
            discharge_descript2 = dfsortpeakvals(discharge_descript, 'd')
        else:
            discharge_descript2 = None
            # append the two dfs (charge and discharge) before putting them in
            # database
        full_df_descript = pd.concat(
            [charge_descript2, discharge_descript2], sort=True, axis=1)
        update_database_newtable(
            full_df_descript, mod_params_name[:-9] + '-descriptors', database)
    return

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



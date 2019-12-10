import scipy.signal
import pandas as pd
import numpy as np
import peakutils
from lmfit import models
import chachifuncs as ccf
import os
import glob
import databasefuncs as dbfs

################################
# OVERALL Wrapper Function
################################
# Import dictionary is format of {batcleancycle-1 : df1, batcleancycle-2: df2 ... and so on }
# individual clean cycles 


# def get_descriptors(import_dictionary, datatype, windowlength, polyorder):
#     """Generates a dataframe containing charge and discharge
#     descriptors/error parameters. Also writes descriptors to an
#     excel spreadsheet 'describe.xlsx' import_filepath = filepath
#     containing cleaned separated cycles"""

#     # creates dataframe of descriptors for the charge/discharge
#     # cycles of all batteries

#     print('Generating descriptors from the data set.')
#     df_ch = process.df_generate(import_dictionary, 'c', datatype, windowlength, polyorder)
#     #ther eare duplicates coming out of this function - does cycle 1 2 times (different numbers) then cycle 2 2 times 
#     #does all cycles charge cycle first, then all discharge cycles
#     df_dc = process.df_generate(import_dictionary, 'd', datatype, windowlength, polyorder)

#     df_final = dflists_to_dfind(pd.concat([df_ch, df_dc], axis=1))

#     df_sorted = dfsortpeakvals(df_final, 'c')
#     df_sorted_final = dfsortpeakvals(df_sorted, 'd')
#     return df_sorted_final

############################
# Sub - Wrapper Functions
############################
# data processing that calls from fitting class
# def dflists_to_dfind(df):
#     """Takes the df of lists and based on max length of list in each column, 
#     puts each value into individual columns. This is the df that will be 
#     written to the database. """
#     #add if NaN in df replace with [] (an empty list) (this will be a list instead of a float)
#     df.reset_index(drop = True)

#     #print(df.to_string())
#     df_new = pd.DataFrame()
#     for column in df.columns:
#         #for row in (df.loc[df[column].isnull(), column].index):
#          #   df.at[row, column] = []
#         x = int(max(list(df[column].str.len())))
#         #print(x)
#         new_cols = []
#         #print(column)
#         for i in range(x):
#             colname = column + str(i)
#             #print(colname)
#             new_cols.append(colname)
#         #print(new_cols)
#         df_new[new_cols]= pd.DataFrame(df[column].values.tolist())
#     return(df_new)

# run peak finder first, to feed i (indices of peaks) into this function 
#     def descriptor_func(df_run, cd, cyc, battery, windowlength, polyorder, datatype, lenmax):
#         """Generates dictionary of descriptors/error parameters
#         V_series = Pandas series of voltage data
#         dQdV_series = Pandas series of differential capacity data
#         cd = either 'c' for charge and 'd' for discharge.
#         Output:
#         dictionary with keys 'coefficients', 'peakLocation(V)',
#         'peakHeight(dQdV)', 'peakSIGMA', 'errorParams"""
#         (cycle_ind_col, data_point_col, volt_col, curr_col, \
#             dis_cap_col, char_cap_col, charge_or_discharge) = ccf.col_variables(datatype)

#         V_series = df_run[volt_col]
#         dQdV_series = df_run['Smoothed_dQ/dV']
#         # make sure a single column of the data frame is passed to
#         # the function
#         assert isinstance(V_series, pd.core.series.Series)
#         assert isinstance(dQdV_series, pd.core.series.Series)

#         # appropriately reclassifies data from pandas to numpy
#         sigx_bot, sigy_bot = fitters.cd_dataframe(V_series, dQdV_series, cd)
#         peak_thresh = 0.3
#         # returns the indices of the peaks for the dataset
#         i, volts_of_i, peak_heights = fitters.peak_finder(df_run, cd, windowlength, polyorder, datatype, lenmax, peak_thresh)
#         #print('Here are the peak finder fitters - indices of peaks in dataset')
#         #print(i)

#         # THIS is where we will append whatever user inputted indices - they 
#         # will be the same for each cycle (but allowed to vary in the model gen section)
#         # generates the necessary model parameters for the fit calculation
#         par, mod, indices = fitters.model_gen(
#             V_series, dQdV_series, cd, i, cyc, thresh)

#         # returns a fitted lmfit model object from the parameters and data
#         model = fitters.model_eval(V_series, dQdV_series, cd, par, mod)
# ############################ SPLIT  here - have user evaluate model before adding coefficients into df 
#         # initiates collection of coefficients
#         coefficients = []

#         for k in np.arange(1): # this was 4 for polynomial changed 10-10-18
#             # key calculation for coefficient collection
#             #coef = 'c' + str(k)
#             coef1 = 'base_sigma'
#             coef2 = 'base_center'
#             coef3 = 'base_amplitude'
#             coef4 = 'base_fwhm'
#             coef5 = 'base_height'
#             # extracting coefficients from model object
#             coefficients.append(model.best_values[coef1])
#             coefficients.append(model.best_values[coef2])
#             coefficients.append(model.best_values[coef3])
#             coefficients.append(model.best_values[coef4])
#             coefficients.append(model.best_values[coef5])




#         # creates a dictionary of coefficients
#         desc = {'coefficients' + '-' +str(cd): list(coefficients)}
#         sig = []
#         if len(i) > 0:
#             # generates numpy array for peak calculation
#             sigx, sigy = fitters.cd_dataframe(V_series, dQdV_series, cd)

#             # determines peak location and height locations from raw data
#             desc.update({'peakLocation(V)' +'-' +str(cd): list(sigx[i].tolist(
#             )), 'peakHeight(dQdV)'+'-' +str(cd): list(sigy[i].tolist())})

#             # initiates loop to extract
#             #sig = []
#             for index in i:
#                 # determines appropriate string to call standard
#                 # deviation object from model
#                 center, sigma, amplitude, fraction, comb = fitters.label_gen(index)
#                 sig.append(model.best_values[sigma])
#         else:
#             desc.update({'peakLocation(V)' + '-' + str(cd): list([np.NaN]), 'peakHeight(dQdV)' + '-' + str(cd): list([np.NaN])})
#             #pass

#             # updates dictionary with sigma key and object
#         desc.update({'peakSIGMA'+ '-' +str(cd): list(sig)})
#         # print('Here is the desc within the descriptor_func function: ')
#         # print(desc)
#         # adds keys for the error parameters of each fit
#         desc.update({'errorParams'+'-' +str(cd): list([model.aic, model.bic, model.redchi])})

#         return desc

    ############################
    # Sub - descriptor_func
    ############################

def peak_finder(df_run, cd, windowlength, polyorder, datatype, lenmax, peak_thresh):
    """Determines the index of each peak in a dQdV curve
    V_series = Pandas series of voltage data
    dQdV_series = Pandas series of differential capacity data
    cd = either 'c' for charge and 'd' for discharge.
    
    Output:
    i = list of indexes for each found peak"""
    (cycle_ind_col, data_point_col, volt_col, curr_col, \
        dis_cap_col, char_cap_col, charge_or_discharge) = ccf.col_variables(datatype)
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
    ###############################################
    if len(sigy) > windowlength_new and windowlength_new > polyorder:
        #has to be larger than 69 so that windowlength > 3 - necessary for sav golay function  
        sigy_smooth = scipy.signal.savgol_filter(sigy, windowlength_new, polyorder)
    else:
        sigy_smooth = sigy
    # this used to be sigy_smooth in the .indexes function below -= changed it to just sigy for graphite
    # change was made on 9.12.18  . also changed min_dist=lenmax/50 to min_dist= 10
    ###################################################
    peak_thresh_ft = float(peak_thresh)
    i = peakutils.indexes(sigy_smooth, thres=peak_thresh_ft, min_dist=lenmax/50)
    ###################################################
    #i = peakutils.indexes(sigy_smooth, thres=0.7, min_dist=50) # used to be 0.25
    #i = peakutils.indexes(sigy_smooth, thres=.3 /
    #                      max(sigy_smooth), min_dist=9)
    #print(i)

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

    # converts voltage data to numpy array

    sigx = pd.to_numeric(V_series).values

    # descriminates between charge and discharge cycle
    if cd == 'c':
        sigy = pd.to_numeric(dQdV_series).values
    elif cd == 'd':
        sigy = -pd.to_numeric(dQdV_series).values
        # d should have a - on it
               # check that the ouptut for these fuctions is positive
    # (with a little wiggle room of 0.5)
    #threshold = -0.5
    #min_sigy = np.min(sigy)
    #assert min_sigy > threshold

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

    # creates a polynomial fitting object
    # prints a notice if no peaks are found
    if all(newi) is False or len(newi) < 1:
        notice = 'Cycle ' + str(cyc) + cd + \
            ' in battery ' + ' has no peaks.'
        print(notice)
        base_mod = models.GaussianModel(prefix = 'base_')
        mod = base_mod
        # changed from PolynomialModel to Gaussian on 10-10-18
        # Gaussian params are A, mew, and sigma
        # sets polynomial parameters based on a
        # guess of a polynomial fit to the data with no peaks
        #mod.set_param_hint('base_amplitude', min = 0)
        #mod.set_param_hint('base_sigma', min = 0.001)
        par = mod.make_params()
    # iterates over all peak indices
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
                #mod.set_param_hint(amplitude, min = 0.001)
                par = mod.make_params()
                #par = mod.guess(sigy_bot_new, x=sigx_bot_new)
                count = count + 1
            else: 
                mod = mod + gaus_loop
                #gaus_loop.set_param_hint(amplitude, min = 0.001)
                par.update(gaus_loop.make_params())
                count = count + 1 

            # uses unique parameter strings to generate parameters
            # with initial guesses
            # in this model, the center of the peak is locked at the
            # peak location determined from PeakUtils
            par[center].set(sigx_bot_new[index], vary=False)
                # don't allow the centers of the peaks found by peakutsils to vary 
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
        # changed from PolynomialModel to Gaussian on 10-10-18
        # Gaussian params are A, mew, and sigma
        # sets polynomial parameters based on a
        # guess of a polynomial fit to the data with no peaks
        #base_mod.set_param_hint('base_amplitude', min = 0)
        #base_mod.set_param_hint('base_sigma', min = 0.001)
        par.update(base_par)
    #mod.set_param_hint('base_height', min = 0, max = 0.01) 

    #par = mod.guess(sigy_bot_new, x=sigx_bot_new)
    #print(cyc)
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
        # set the max of the gaussian to be smaller than the smallest peak 
        #par['base_sigma'].set(min = float(par[smallest_peak]))
        # max_height = max(sigy_bot_new) - min(sigy_bot_new)*thresh + min(sigy_bot_new)
        # #par['base_height'].set(max = float(par[smallest_peak]))
        # par['base_height']
        # par['base_amplitude'].set(max = max_height*2.506*par['base_sigma'])
        # this is a problem because its setting the max not as a relationship but as a float depending 
        # what each par is at this moment (unoptimiza)
        #par['base_amplitude'].set(max = ((2*3.14159)**0.5)*float(par[smallest_peak])*par['base_sigma'])

        #par['base_amplitude'].set(max = (((2*3.14159)**0.5)*max_height*par['base_sigma']))
        model = mod.fit(sigy_bot_new, params = par, x=sigx_bot_new)
    except Exception as E:
        print(E)
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



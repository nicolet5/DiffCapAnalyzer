import scipy.signal
import pandas as pd
import numpy as np
import peakutils
from lmfit import models
import chachifuncs_exp as ccf
import os
import glob
import databasefuncs as dbfs

################################
# OVERALL Wrapper Function
################################
# Import dictionary is format of {batcleancycle-1 : df1, batcleancycle-2: df2 ... and so on }
# individual clean cycles 

def get_descriptors(import_dictionary):
    """Generates a dataframe containing charge and discharge
    descriptors/error parameters. Also writes descriptors to an
    excel spreadsheet 'describe.xlsx' import_filepath = filepath
    containing cleaned separated cycles"""
    # import filepath is path of clean, separated cycles 
    # checks that the file exists
    #assert os.path.exists(import_filepath), 'The file does not exist'

    # check that the whatever is passed to ML_generate is a string
    #assert isinstance(import_filepath, str), 'The input should be a string'

    # creates dataframe of descriptors for the charge/discharge
    # cycles of all batteries
    df_ch = process.df_generate(import_dictionary, 'c')
    #ther eare duplicates coming out of this function - does cycle 1 2 times (different numbers) then cycle 2 2 times 
    #print('this is df_ch')
    #print(df_ch.to_string())
    #does all cycles charge cycle first, then all discharge cycles
    df_dc = process.df_generate(import_dictionary, 'd')
    #print('this is df_dc')
    #print(df_dc.to_string())
    # concats charge and discharge cycles
    df_final = pd.concat([df_ch, df_dc], axis=1)
    #print('this is the df_final')
    #print(df_final.to_string())
    # drops any duplicate rows
    df_final = df_final.T.drop_duplicates().T
    #print('this is the df_final after dropping duplicates: ')
    #print(df_final.to_string())
    # saves data to database

    return df_final

############################
# Sub - Wrapper Functions
############################
# data processing that calls from fitting class


class process:

    # first function called by ML_generate
    def df_generate(import_dictionary, cd):
        """Creates a pandas dataframe for each battery's charge/
        discharge cycle in the import_filepath folder.
        import_filepath = filepath containing cleaned separated cycles
        cd = 'c' for charge and 'd' for discharge

        Output:
        df_ch = pandas dataframe for all cycles of all batteries in a
        col_ch = list of numbers of columns for each battery"""

        #assert cd == (
        #    'c' or 'd'), 'This must be charge (c) or discharge (d) data'

        # generates a list of datafiles to analyze
        # rootdir = import_filepath
        # file_list = [f for f in glob.glob(os.path.join(rootdir, '*.xlsx'))]
        # iterate through dir to get excel file

        # generates a list of unique batteries
        list_bats = []

        for k, v in import_dictionary.items():
            #clean_set_df = clean_set_df.append(v, ignore_index = True)

            # splits file paths to get battery names
            batname = k
            # this batname is "batname-cleancycle#" individual cycles
            # name = os.path.split(file)[1].split('.')[0]
            # batname = name.split('-')[0]

            # adds unique battery names to the list of batteries
            if batname not in list_bats:
                list_bats.append(batname)
            else:
                None

        # notifies user of successful import
        notice = 'Successfully extracted all battery names for ' + cd
        print(notice)

        # generates a blank dataframe of charge/discharge descriptors
        df_ch = process.pd_create(cd)
        #print('here is list_bats')
        #print(list_bats)
        # begins generating dataframe of descriptors
        name_ch = []
        for bat in list_bats:
            # bat is batnamecleancycle# - individual cycles
            # notifies user which battery is being fit
            notice = 'Fitting battery: ' + bat + ' ' + cd
            print(notice)

            # generates dataframe of descriptor fits for each battery
            df = process.imp_all(import_dictionary, bat, cd)
            # get dataframe of descriptors from all the batcleancycle#'s'
            # generates an iterative list of names for the 'name'
            # column of the final dataframe
            #print('here is the df in the df_generate function: ')
            #print(df.to_string())
            #this df has two rows 
            #print('here is the bat param in the function : ')
            #print(bat)
            name_ch = name_ch + [bat] * len(df.index)
            #print('here is the name of that battery the df was just printed for above')
            #print(name_ch)
            # concats dataframe from current battery with previous
            # batteries
            df_ch = pd.concat([df_ch, df])

        # adds name column to the dataframe
        df_ch['names'] = name_ch
        #print('here is the df_ch in the df_generate function: ')
        #print(df_ch.to_string())
        return df_ch

    def imp_all(import_dictionary, battery, cd):
        """Generates a Pandas dataframe of descriptors for a single battery

        source = string containing directory with the excel sheets
        for individual cycle data
        battery = string containing excel spreadsheet of file name
        cd = either 'c' for charge or 'd' for discharge

        Output:
        charge_descript = pandas dataframe of charge descriptors"""
        # battery is the name "batcleancycle#"
        # check that the battery label is a string
        # check that the whatever is passed to ML_generate is a string
        # check that 'c' or 'd' is passed
        #assert isinstance(source, str), 'The input should be a string'
        #assert isinstance(battery, str), 'The input should be a string'
        #assert cd == (
         #   'c' or 'd'), 'This must be charge (c) or discharge (d) data'

        # generates list of battery files for import
        #file_pref = battery + '*.xlsx'
        #file_list = [f for f in glob.glob(os.path.join(source, file_pref))]

        # sorts by cycle
        cycle = []

        # extracts cycle number from file name using known pattern
        # for file in file_list:
        #for k, v in import_dictionary:
        #    cyc = k.split('Cycle')[1]
        #    cycle.append(int(cyc))

        # sorts cycle numbers
        # cyc_sort = sorted(cycle)

        # determines order of indexes that will properly sort the data
        # cyc_index = []
        # for cyc in cyc_sort:
        #   cyc_index.append(cycle.index(cyc))

        # reindexes file list using the lists of indices from above
        # file_sort = []
        # for indices in cyc_index:
         #   file_sort.append(file_list[indices])

        # this is the end of the shit that sorts by cycle
        charge_descript = process.pd_create(cd)
        # this makes an empty dataframe to populate with the descriptors
        # iterates over the file list and the cycle number
        #for file_val, cyc_loop in zip(file_sort, cyc_sort):
        for k, v in import_dictionary.items():
            # cyc_loop is just the cycle number associated with the testdf - get from k
            # determines dictionary of descriptors from file data
            print('here is the key in imp all')
            print(k)
            cyc_loop = int(k.split('Cycle')[1])
            testdf = v
            c = process.imp_one_cycle(testdf, cd, cyc_loop, battery)
            # c is a dictionary
            print('here is c before appending: ')
            print(c)
            
            if c != 'throw':
                c['name'] = k
                print('here is c after apending: ')
                print(c)
                # generates list of dictionaries while rejecting any that
                # return the 'throw' error
                #print('here is c: ')
                #print(c)
                charge_descript = process.pd_update(charge_descript, c)
               # print('here is charge_descript: ')
                #print(charge_descript)
        print('Here is the charge_descript parameter in the imp all function:  ')
        print(charge_descript.to_string())
        return charge_descript

    def pd_create(cd):
        """Creates a blank dataframe containing either charge or
        discharge descriptors/error parameters

        cd = either 'c' for charge or 'd' for discharge

        Output:
        blank pandas dataframe with descriptor columns and cycle number rows"""

        # check that 'c' or 'd' is passed
        #assert cd == (
        #    'c' or 'd'), 'This must be charge (c) or discharge (d) data'

        # number of descriptors it generates
        n_desc = 19

        # determines prefix string based on need for a charge or
        # discharge dataframe
        if cd == 'c':
            prefix = 'ch_'
        else:
            prefix = 'dc_'

        # generates list of names for the top of the descriptors dataframe
        names = []
        for ch in np.arange(n_desc):
            names.append(prefix + str(int(ch)))

        # adds names of error parameters to the end of the descriptor list
        names = names + [prefix+'AIC', prefix+'BIC', prefix+'red_chi_squared']

        # creates pandas dataframe with necessary heading
        # print(names)
        desc = pd.DataFrame(columns=names)

        return desc

    def pd_update(desc, charge_descript):
        """adds a list of charge descriptors to a pandas dataframe

        desc = dataframe from pd_create
        charge_descript = descriptor dictionaries

        Output:
        pandas dataframe with a row of descriptors appended on"""

        # check if the inputs have the right Type
        # c is the charge_descript and desc is the empty dataframe 
        assert isinstance(
            desc, pd.core.frame.DataFrame), "This input must be a pandas dataframe"
        assert isinstance(
            charge_descript, dict), "Stop right there, only dictionaries are allowed in these parts"
        print('here is charge descript thingy: ')
        print(charge_descript)
        # converts the dictionary of descriptors into a list of descriptors
        desc_ls = process.dict_2_list(charge_descript)
        # still c but as a list 
        print('here is c but as a list: ')
        print(desc_ls)
        # print('here is the desc_ls: ')
        # print(desc_ls)
        # adds zeros to the end of each descriptor list to create
        # a list with 22 entries
        # also appends error parameters to the end of the descriptor list
        desc_app = desc_ls + \
            np.zeros(19-len(desc_ls)).tolist() + charge_descript['errorParams']
        # generates a dataframe of descriptors
        desc_df = pd.DataFrame([desc_app], columns=desc.columns)
        # combines row of a dataframe with previous dataframe
        desc = pd.concat([desc, desc_df], ignore_index=True)
        # print('here is the desc.to_string(): ')
        # print(desc.to_string())

        return desc

    # used by pd_update
    def dict_2_list(desc):
        """Converts a dictionary of descriptors into a list for
        pandas assignment

        desc = dictionary containing descriptors

        Output:
        list of descriptors"""

        # this function is kinda pointless if you don't give it
        # a dictionary
        assert isinstance(
            desc, dict), "Stop right there, only dictionaries are allowed in these parts"

        # generates an initial list from the coefficients
        desc_ls = list(desc['coefficients'])
        desc_ls.append(desc['name'])
        # determines whether or not there are peaks in the datasent
        if 'peakSIGMA' in desc.keys():
            # iterates over the number of peaks
            for i in np.arange(len(desc['peakSIGMA'])):
                # appends peak descriptors to the list in order of peak number
                desc_ls.append(desc['peakLocation(V)'][i])
                desc_ls.append(desc['peakHeight(dQdV)'][i])
                desc_ls.append(desc['peakSIGMA'][i])
        else:
            pass
        #print('here is the desc_ls with peakloc in the dict_2_list definition: ')
        #print(desc_ls)
        return desc_ls

    def imp_one_cycle(testdf, cd, cyc_loop, battery):
        """imports and fits a single charge discharge cycle of a battery

        file_val = directory containing current cycle
        cd = either 'c' for charge or 'd' for discharge
        cyc_loop = cycle number
        battery = battery name

        output: a dictionary of descriptors for a single battery"""

        # make sure this is an Excel spreadsheet by checking the file extension
        # assert file_val.split('.')[-1] == ('xlsx' or 'xls')

        # reads excel file into pandas
        # testdf = pd.read_excel(file_val)

        # extracts charge and discharge from the dataset
        charge, discharge = ccf.sep_char_dis(testdf)

        # determines if the charge, discharge indicator was inputted correctly
        # assigns daframe for fitting accordingly
        if cd == 'c':
            df_run = charge
        elif cd == 'd':
            df_run = discharge
        else:
            raise TypeError(
                "Cycle type must be either 'c' for charge or 'd' for discharge.")

        # determines if a cycle should be passed into the descriptor
        # fitting function
        if (len(charge['Voltage(V)'].index) >= 10) and (len(discharge['Voltage(V)'].index) >= 10):
            # generates a dictionary of descriptors
            c = fitters.descriptor_func(
                df_run['Voltage(V)'], df_run['Smoothed_dQ/dV'], cd, cyc_loop, battery)
        # eliminates cycle number and notifies user of cycle removal
        else:
            notice = 'Cycle ' + str(cyc_loop) + ' in battery ' + battery + \
                ' had fewer than 10 datapoints and was removed from the dataset.'
            print(notice)
            c = 'throw'
        # print('here is the c parameter in the imp_one_cycle: ')
        # print(c)
        return c


class fitters:

    def descriptor_func(V_series, dQdV_series, cd, cyc, battery):
        """Generates dictionary of descriptors/error parameters

        V_series = Pandas series of voltage data
        dQdV_series = Pandas series of differential capacity data
        cd = either 'c' for charge and 'd' for discharge.

        Output:
        dictionary with keys 'coefficients', 'peakLocation(V)',
        'peakHeight(dQdV)', 'peakSIGMA', 'errorParams"""

        # make sure a single column of the data frame is passed to
        # the function
        assert isinstance(V_series, pd.core.series.Series)
        assert isinstance(dQdV_series, pd.core.series.Series)

        # appropriately reclassifies data from pandas to numpy
        sigx_bot, sigy_bot = fitters.cd_dataframe(V_series, dQdV_series, cd)

        # returns the indices of the peaks for the dataset
        i = fitters.peak_finder(V_series, dQdV_series, cd)

        # generates the necessary model parameters for the fit calculation
        par, mod = fitters.model_gen(
            V_series, dQdV_series, cd, i, cyc, battery)

        # returns a fitted lmfit model object from the parameters and data
        model = fitters.model_eval(V_series, dQdV_series, cd, par, mod)

        # initiates collection of coefficients
        coefficients = []

        for k in np.arange(4):
            # key calculation for coefficient collection
            coef = 'c' + str(k)
            # extracting coefficients from model object
            coefficients.append(model.best_values[coef])

        # creates a dictionary of coefficients
        desc = {'coefficients': coefficients}
        sig = []
        if len(i) > 0:
            # generates numpy array for peak calculation
            sigx, sigy = fitters.cd_dataframe(V_series, dQdV_series, cd)

            # determines peak location and height locations from raw data
            desc.update({'peakLocation(V)': sigx[i].tolist(
            ), 'peakHeight(dQdV)': sigy[i].tolist()})

            # initiates loop to extract
            #sig = []
            for index in i:
                # determines appropriate string to call standard
                # deviation object from model
                center, sigma, amplitude, fraction, comb = fitters.label_gen(index)
                sig.append(model.best_values[sigma])
        else:
            pass

            # updates dictionary with sigma key and object
        desc.update({'peakSIGMA': sig})
        # print('Here is the desc within the descriptor_func function: ')
        # print(desc)
        # adds keys for the error parameters of each fit
        desc.update({'errorParams': [model.aic, model.bic, model.redchi]})

        return desc

    ############################
    # Sub - descriptor_func
    ############################

    def cd_dataframe(V_series, dQdV_series, cd):
        """Classifies and flips differential capactity data.

        V_series = Pandas series of voltage data
        dQdV_series = Pandas series of differential capacity data
        cd = either 'c' for charge and 'd' for discharge.

        Output:
        sigx = numpy array of signal x values
        sigy = numpy array of signal y values"""

        # converts voltage data to numpy array

        sigx = pd.to_numeric(V_series).as_matrix()

        # descriminates between charge and discharge cycle
        if cd == 'c':
            sigy = pd.to_numeric(dQdV_series).as_matrix()
        elif cd == 'd':
            sigy = -pd.to_numeric(dQdV_series).as_matrix()

        # check that the ouptut for these fuctions is positive
        # (with a little wiggle room of 0.5)
        threshold = -0.5
        min_sigy = np.min(sigy)
        #assert min_sigy > threshold

        return sigx, sigy

    def peak_finder(V_series, dQdV_series, cd):
        """Determines the index of each peak in a dQdV curve

        V_series = Pandas series of voltage data
        dQdV_series = Pandas series of differential capacity data
        cd = either 'c' for charge and 'd' for discharge.

        Output:
        i = list of indexes for each found peak"""

        assert len(dQdV_series) > 10

        sigx, sigy = fitters.cd_dataframe(V_series, dQdV_series, cd)

        windowlength = 25
        if len(sigy) > windowlength:
            sigy_smooth = scipy.signal.savgol_filter(sigy, windowlength, 3)
        elif len(sigy) > 10:
            sigy_smooth = sigy

        i = peakutils.indexes(sigy_smooth, thres=.3 /
                              max(sigy_smooth), min_dist=9)
        #print(i)

        return i

    def label_gen(index):
        """Generates label set for individual gaussian
        index = index of peak location

        output string format:
        'a' + index + "_" + parameter"""
        # print(index)
        #print(type(index))
        #assert isinstance(index, (float, int))

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
    
        #assert isinstance((center, sigma, amplitude, fraction, comb), str)

        return center, sigma, amplitude, fraction, comb

    def model_gen(V_series, dQdV_series, cd, i, cyc, battery):
        """Develops initial model and parameters for battery data fitting.

        V_series = Pandas series of voltage data
        dQdV_series = Pandas series of differential capacity data
        cd = either 'c' for charge and 'd' for discharge.

        Output:
        par = lmfit parameters object
        mod = lmfit model object"""

        # generates numpy arrays for use in fitting
        sigx_bot, sigy_bot = fitters.cd_dataframe(V_series, dQdV_series, cd)

        # creates a polynomial fitting object
        mod = models.PolynomialModel(4)

        # sets polynomial parameters based on a
        # guess of a polynomial fit to the data with no peaks
        par = mod.guess(sigy_bot, x=sigx_bot)

        # prints a notice if no peaks are found
        if all(i) is False:
            notice = 'Cycle ' + str(cyc) + cd + \
                ' in battery ' + battery + ' has no peaks.'
            print(notice)

        # iterates over all peak indices
        else:
            for index in i:

                # generates unique parameter strings based on index of peak
                center, sigma, amplitude, fraction, comb = fitters.label_gen(
                    index)

                # generates a pseudo voigt fitting model
                gaus_loop = models.PseudoVoigtModel(prefix=comb)
                par.update(gaus_loop.make_params())

                # uses unique parameter strings to generate parameters
                # with initial guesses
                # in this model, the center of the peak is locked at the
                # peak location determined from PeakUtils

                par[center].set(sigx_bot[index], vary=False)
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
        sigx_bot, sigy_bot = fitters.cd_dataframe(V_series, dQdV_series, cd)

        model = mod.fit(sigy_bot, par, x=sigx_bot)

        return model

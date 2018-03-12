import glob 
from math import isclose 
import numpy as np
import os 
import pandas as pd
from pandas import ExcelWriter
import requests
import scipy.io
import scipy.signal

################################
### OVERALL Wrapper Function ###
################################

def get_all_data(rootdir, path_to_raw_data_folder):
    '''Gets all raw data from the rootdir (ie 'data/') and specified folder (path_to_raw_data_folder), i.e. 'Source_Data' (which is within rootdir), and then 
    1. separates it into raw cycles and puts them in a folder (data/Separated_Cycles/)
    2. cleans those separated cycles and puts them in a folder (data/Clean_Separated_Cycles/)
    3. recombines the cleaned, separated cycles and saves those data sets in a folder (data/Clean_Whole_Sets/)
    These folders do not have to have existed previously. '''
    if not os.path.exists(rootdir):
        print('The specified rootdir does not exist.')
    if not os.path.exists(rootdir+'Separated_Cycles/'):
        os.makedirs(rootdir+'Separated_Cycles/')
    if not os.path.exists(rootdir+'Clean_Separated_Cycles/'):
        os.makedirs(rootdir + 'Clean_Separated_Cycles/')
    if not os.path.exists(rootdir + 'Clean_Whole_Sets/'):
        os.makedirs(rootdir + 'Clean_Whole_Sets/')
    load_sep_cycles(rootdir + path_to_raw_data_folder, rootdir+ 'Separated_Cycles/')
    get_clean_cycles(rootdir + 'Separated_Cycles/', rootdir +'Clean_Separated_Cycles/')
    get_clean_sets(rootdir +'Clean_Separated_Cycles/', rootdir+'Clean_Whole_Sets/')
    return 

############################
### Sub - Wrapper Functions
############################

def load_sep_cycles(getdata_filepath, savedata_filepath):
    """Get data from a specified filepath, separates out data into cycles and saves those cycles as .xlsx files in specified filepath (must be an existing folder)"""
    dfdict = get_data(getdata_filepath)
    assert type(dfdict) == dict
    assert os.path.exists(getdata_filepath) == 1
    assert os.path.exists(savedata_filepath) == 1 
    for key in dfdict:
        all_cycles_df = dfdict[key]
        cycle_dict = sep_cycles(all_cycles_df)
        battname = key 
        save_sep_cycles_xlsx(cycle_dict, battname, savedata_filepath) 
    print('All data separated into cycles and saved in folder "data/Separated_Cycles". ')
    return 

def clean_calc_sep_smooth(dataframe, windowlength, polyorder):
    """Takes one cycle dataframe, calculates dq/dv, cleans the data, separates out charge and discharge, and applies sav-golay filter. Returns two dataframes, one charge and one discharge.
    Windowlength and polyorder are for the sav-golay filter."""
    assert type(dataframe) = pd.DataFrame 
    assert 'Current(A)'and 'Voltage(V)' and 'dQ/dV' in dataframe.columns 

    df1 = calc_dv_dqdv(dataframe)
    raw_charge = df1[df1['Current(A)'] > 0]
    raw_charge = raw_charge.reset_index(drop = True)
    #this separated out the charging data and put it in 'raw_charge'. Reset the index as well. 

    raw_discharge = df1[df1['Current(A)'] < 0]
    raw_discharge = raw_discharge.reset_index(drop = True)
    #this separated out the discharging data and put it in 'raw_discharge'. Reset the index as well.

    clean_charge2 = drop_0_dv(raw_charge)
    clean_discharge2 = drop_0_dv(raw_discharge)
    #apply the drop_0_dv function to clean out the wonky data points, especially near the voltage corresponding to the end of a cycle.  

    clean_charge2 = clean_charge2.sort_values(['Voltage(V)'], ascending = True)
    clean_discharge2 = clean_discharge2.sort_values(['Voltage(V)'], ascending = False)
    #sorted the values because sometimes the data points are out of order, especially in the first cycle of a battery.  

    cleandf2 = clean_charge2.append(clean_discharge2, ignore_index = True)
    cleandf2 = cleandf2.reset_index(drop = True)
    #appends the clean charge and discharge cycles to get a full set of clean data. Reset the index as well. 

    charge, discharge = sep_char_dis(cleandf2)
    #apply the sep_char_dis function to cleandf2. This is necessary because the sep_char_dis function actually 
    #assigns the values of dq/dv to use. The discharge cycles need dq/dv to be calculated based on the 
    #discharge capacity, and the charge cycles need dq/dv to be calculated based on the charge capacity. 
    #This structure could probably be improved since we are separating out charge/discharge, then recombining, then
    #separating again, then recombining. 

    if len(discharge) > windowlength:
        smooth_discharge = my_savgolay(discharge, windowlength, polyorder)
    else:
        discharge['Smoothed_dQ/dV'] = discharge['dQ/dV']
        smooth_discharge = discharge
    #this if statement is for when the datasets have less datapoints than the windowlength given to the sav_golay filter. 
    #without this if statement, the sav_golay filter throws an error when given a dataset with too few points. This way, 
    #we simply forego the smoothing function. 
    if len(charge) > windowlength: 
        smooth_charge = my_savgolay(charge, windowlength, polyorder)
    else:
        charge['Smoothed_dQ/dV'] = charge['dQ/dV']
        smooth_charge = charge   
    #same as above, but for charging cycles. 
    return smooth_charge, smooth_discharge

def get_clean_cycles(import_filepath, save_filepath): 
    """Imports all separated out cycles in given path and cleans them and saves them in the specified filepath"""
    rootdir = import_filepath
    file_list = [f for f in glob.glob(os.path.join(rootdir,'*.xlsx'))] #iterate through dir to get excel files 
    d = {} #initiate dict for data storage
    count = 0
    for file in file_list:
        count += 1
        name = os.path.split(file)[1].split('.')[0]
        data = pd.read_excel(file)
        charge, discharge = clean_calc_sep_smooth(data, 9, 3)
        clean_data = discharge.append(charge, ignore_index = True)
        
        clean_data = clean_data.reset_index(drop = True)
       
        clean_cycle = {name : clean_data}
        d.update(clean_cycle)
       # print("adding file to dictionary" + str(count) + ' ' + str(name))
    for key in d:
        clean_cycle_df = d[key]
        cyclename = key 
        writer = ExcelWriter(save_filepath + cyclename + 'Clean'+ '.xlsx')
        clean_cycle_df.to_excel(writer)
        writer.save() 
    print('All cycles cleaned and saved in folder "data/Clean_Separated_Cycles".')
    return 

def get_clean_sets(import_filepath, save_filepath): 
    """Imports all clean cycles of data from import path and appends them into complete sets of battery data, saved into save_filepath"""
    rootdir = import_filepath
    file_list = [f for f in glob.glob(os.path.join(rootdir,'*.xlsx'))] #iterate through dir to get excel files 
    d = {} #initiate dict for data storage
    count = 0
    list_bats = [] 
    for file in file_list:
        count += 1
        name = os.path.split(file)[1].split('.')[0]
        batname = name.split('-')[0]
        if batname not in list_bats:
            list_bats.append(batname)
        else: None  
            
    set_dict = {}
    
    for i in range(len(list_bats)): 
        batID = list_bats[i] 
        setdf = pd.DataFrame()
        for file in file_list:
            name = os.path.split(file)[1].split('.')[0]
            batname = name.split('-')[0]
            if batname == batID:
                df = pd.read_excel(file)
                setdf = setdf.append(df, ignore_index=True)
            else:
                None 
        setdf = setdf.sort_values(['Voltage(V)'], ascending = True)
        setdf = setdf.reset_index(drop = True)
        newset = {batID : setdf}
        set_dict.update(newset) 
        
    for key, value in set_dict.items():
        writer = ExcelWriter(save_filepath + key + 'CleanSet'+'.xlsx')
        value.to_excel(writer)
        writer.save() 
                
    print('All clean cycles recombined and saved in folder "data/Clean_Whole_Sets".')
    return
############################
# Component Functions
############################

def get_data(filepath): 
    """Imports all data in given path"""
    assert type(filepath) == str, 'Input must be a string'
    rootdir = filepath
    file_list = [f for f in glob.glob(os.path.join(rootdir,'*.xlsx'))] #iterate through dir to get excel files 
    
    d = {} #initiate dict for data storage
    count = 0
    for file in file_list:
        count += 1
        name = os.path.split(file)[1].split('.')[0]
        data = pd.read_excel(file,1)
        new_set = {name : data}
        d.update(new_set)
    return d

#separate out dataframes into cycles
def sep_cycles(dataframe):
    """This function separates out the cycles in the battery dataframe by grouping by the 'Cycle_Index' column, and putting them in a dictionary. """
    assert type(dataframe) == pd.DataFrame, 'Input must be a dataframe' 
    gb = dataframe.groupby(by = ['Cycle_Index'])
    cycle_dict = dict(iter(gb))
    return cycle_dict

def save_sep_cycles_xlsx(cycle_dict, battname, path_to_folder):
    """This saves the separated out cycles into different excel files, beginning with the battery name. Battname and path to folder must be strings."""
    assert type(cycle_dict) == dict, 'First entry must be a dictionary'
    assert type(battname) == str, 'Second entry must be a string'
    assert type(path_to_folder) == str, 'Path to output must be a string'
    for i in range(1, len(cycle_dict)+1):
         cycle_dict[i]['Battery_Label'] = battname
    for i in range(1,len(cycle_dict)+1):
        writer = ExcelWriter(path_to_folder + battname + '-'+'Cycle' + str(i) + '.xlsx')
        cycle_dict[i].to_excel(writer)
        writer.save()
    return 


def calc_dv_dqdv(cycle_df):
    """This function calculates the dv and the dq/dv for a dataframe."""
    assert type(cycle_df) == pd.DataFrame
    assert 'Voltage(V)' in cycle_df.columns
    assert 'Discharge_Capacity(Ah)' in cycle_df.columns 
    assert 'Charge_Capacity(Ah)' in cycle_df.columns

    cycle_df = cycle_df.reset_index(drop = True)
    cycle_df['dV'] = None 
    cycle_df['Discharge_dQ'] = None
    cycle_df['Charge_dQ'] = None 
    cycle_df['Discharge_dQ/dV'] = None
    cycle_df['Charge_dQ/dV'] = None  
    for i in range(1,len(cycle_df)): 
        cycle_df.loc[i, ('dV')] = cycle_df.loc[i, ('Voltage(V)')] - cycle_df.loc[i-1, ('Voltage(V)')]  
        cycle_df.loc[i, ('Discharge_dQ')] = cycle_df.loc[i, ('Discharge_Capacity(Ah)')] - cycle_df.loc[i-1, ('Discharge_Capacity(Ah)')]
        cycle_df.loc[i, ('Charge_dQ')] = cycle_df.loc[i, ('Charge_Capacity(Ah)')] - cycle_df.loc[i-1, ('Charge_Capacity(Ah)')]
    #calculate dq/dv based off of discharge capacity - might change this later so user can choose to use charge or discharge cap. 
    cycle_df['Discharge_dQ/dV'] = cycle_df['Discharge_dQ']/cycle_df['dV']
    cycle_df['Charge_dQ/dV'] = cycle_df['Charge_dQ']/cycle_df['dV']
    return cycle_df 


def drop_0_dv(cycle_df_dv): 
    '''Drop rows where dv=0 (or about 0) in a dataframe that has already had dv calculated. Then recalculate dv and calculate dq/dv'''
    #this will clean up the data points around V = 4.2V (since they are holding it at 4.2V for a while).
    assert 'dV' in cycle_df_dv.columns
    assert 'Current(A)' in cycle_df_dv.columns 

    cycle_df_dv = cycle_df_dv.reset_index(drop = True)
   
    cycle_df_dv['dv_close_to_zero'] = None
    
    for i in range(1, len(cycle_df_dv)):
    	if isclose(cycle_df_dv.loc[i, ('Current(A)')], 0, abs_tol = 10**-3):
    		cycle_df_dv = cycle_df_dv.drop(index = i)

    cycle_df_dv = cycle_df_dv.reset_index(drop = True) 
    switch_cd_index = np.where(np.diff(np.sign(cycle_df_dv['Current(A)'])))
    for i in switch_cd_index:
        cycle_df_dv = cycle_df_dv.drop(cycle_df_dv.index[i+1])    

    cycle_df_dv = cycle_df_dv.reset_index(drop = True)

    for i in range(1, len(cycle_df_dv)):
        if isclose(cycle_df_dv.loc[i, ('dV')], 0, abs_tol = 10**-3): #was -3.5 before
            cycle_df_dv.loc[i,('dv_close_to_zero')] = False
        else:
            cycle_df_dv.loc[i,('dv_close_to_zero')]= True   
    
    
    while (False in cycle_df_dv['dv_close_to_zero'].values or cycle_df_dv['dV'].max() > 0.7 or cycle_df_dv['dV'].min() < -0.7): 
        
        cycle_df_dv = cycle_df_dv.reset_index(drop = True)
        
        for i in range(1, len(cycle_df_dv)):
            if isclose(cycle_df_dv.loc[i, ('dV')], 0, abs_tol = 10**-3): 
                cycle_df_dv = cycle_df_dv.drop(index = i)

        cycle_df_dv = cycle_df_dv.reset_index(drop = True)

        separate_dis_char = np.where(np.diff(np.sign(cycle_df_dv['Current(A)'])))
        
        for i in range(1, len(cycle_df_dv)):
            if (cycle_df_dv.loc[i,('dV')] > 0.7 or cycle_df_dv.loc[i,('dV')] < -0.7):
                cycle_df_dv = cycle_df_dv.drop(index = i)       
                
        cycle_df_dv = cycle_df_dv.reset_index(drop = True)
        
        for i in range(1, len(cycle_df_dv)): 
            cycle_df_dv.loc[i, ('dV')] = cycle_df_dv.loc[i, ('Voltage(V)')] - cycle_df_dv.loc[i-1, ('Voltage(V)')] 
            if isclose(cycle_df_dv.loc[i, ('dV')], 0, abs_tol = 10**-3):
                cycle_df_dv.loc[i,('dv_close_to_zero')] = False
            else:
                cycle_df_dv.loc[i,('dv_close_to_zero')]= True
                
        cycle_df_dv = cycle_df_dv.reset_index(drop = True)            
    
    cycle_df_dv = cycle_df_dv.reset_index(drop = True)
   
    #recalculating dv and dq's after dropping rows
    for i in range(1, len(cycle_df_dv)): 
        cycle_df_dv.loc[i, ('dV')] = cycle_df_dv.loc[i, ('Voltage(V)')] - cycle_df_dv.loc[i-1, ('Voltage(V)')]
        cycle_df_dv.loc[i, ('Discharge_dQ')] = cycle_df_dv.loc[i, ('Discharge_Capacity(Ah)')] - cycle_df_dv.loc[i-1, ('Discharge_Capacity(Ah)')]
        cycle_df_dv.loc[i, ('Charge_dQ')] = cycle_df_dv.loc[i, ('Charge_Capacity(Ah)')] - cycle_df_dv.loc[i-1, ('Charge_Capacity(Ah)')]
    #recalculate dq/dv  
    cycle_df_dv['Discharge_dQ/dV'] = cycle_df_dv['Discharge_dQ']/cycle_df_dv['dV']
    cycle_df_dv['Charge_dQ/dV'] = cycle_df_dv['Charge_dQ']/cycle_df_dv['dV']
    cycle_df_dv = cycle_df_dv.dropna(subset=['Discharge_dQ/dV'])
    cycle_df_dv = cycle_df_dv.dropna(subset=['Charge_dQ/dV'])
    cycle_df_dv = cycle_df_dv.reset_index(drop = True)
 


    cycle_df_dv = cycle_df_dv.reset_index(drop = True)
    return cycle_df_dv  

def sep_char_dis(df_dqdv):
    '''Takes a dataframe of one cycle with calculated dq/dv and separates into charge and discharge differential capacity curves'''
    assert 'Charge_dQ/dV' in df_dqdv.columns
    assert 'Discharge_dQ/dV' in df_dqdv.columns
    charge = df_dqdv[df_dqdv['Current(A)'] > 0]
    charge.is_copy = None
    charge = charge.reset_index(drop = True)
    charge['dQ/dV'] = charge['Charge_dQ/dV']

    for i in range(1, len(charge)):
        if charge.loc[i, ('dQ/dV')] == 0: 
            charge = charge.drop(index = i)
    charge = charge.reset_index(drop = True)

    discharge = df_dqdv[df_dqdv['Current(A)'] < 0] 
    discharge.is_copy = None 
    discharge['dQ/dV'] = discharge['Discharge_dQ/dV']
    discharge = discharge.reset_index(drop = True)

    for i in range(1, len(discharge)):
        if discharge.loc[i, ('dQ/dV')] == 0: 
            discharge = discharge.drop(index = i)
    discharge = discharge.reset_index(drop = True)
    
    return charge, discharge
    
def my_savgolay(dataframe, windowlength, polyorder):
    """Takes battery dataframe with a dQ/dV column and applies a sav_golay filter to it, returning the dataframe with a new column called Smoothed_dQ/dV"""
    assert not windowlength % 2 == 0
    #asserts this is an odd number - necessary to run the savgol_filter function 
    assert polyorder < windowlength 
    #necessary to run the savgol_filter function as well. 
    unfilt = pd.concat([dataframe['dQ/dV']])
    unfiltar = unfilt.values
    #converts into an array 
    dataframe['Smoothed_dQ/dV'] = scipy.signal.savgol_filter(unfiltar, windowlength, polyorder)
    #had windowlength = 21 and polyorder = 3 before
    return dataframe








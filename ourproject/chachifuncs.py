import dash_html_components as html
import glob 
from math import isclose 
import os 
import pandas as pd
from pandas import ExcelWriter
import requests
import xlrd


#####################
#Data Cleaning
#####################

def get_data(filepath): 
    """Imports all data in given path"""
    rootdir = filepath
    file_list = [f for f in glob.glob(os.path.join(rootdir,'*.xlsx'))] #iterate through dir to get xlsx files 
    d = {} #initiate dict for data storage
    count = 0
    
    for file in file_list:
        count += 1
        name = os.path.split(file)[1].split('.')[0]
        data = pd.read_excel(file,1)
        new_set = {name : data}
        d.update(new_set)
        print "adding file", (count, name)
    return d
    # There are 23 files in the CS2 directory, so we should have 23 entries in the dictionary - TEST 

def add_label_dv_cols(dictionary):
    '''This adds the battery label based off of the keys in the input dictionary, and adds an empty dV column and an empty dQ/dV column'''     
    for keys in dictionary:
        data1 = dictionary[keys]
        # add a battery label corresponding to that battery's key. 
        data1['Battery_Label'] = keys
        #create column labeled 'dV'
        data1['dV'] = None
        data1['dQ/dV'] = None 
    return

def sep_cycles(dataframe):
    """This function separates out the cycles in the battery dataframe by grouping by the 'Cycle_Index' column, and putting them in a dictionary. """
    gb = dataframe.groupby(by = ['Cycle_Index'])
    cycle_dict = dict(iter(gb))
    return cycle_dict

def save_sep_cycles_xlsx(cycle_dict, battname, path_to_folder):
    '''This saves the separated out cycles into different excel files, beginning with the battery name. Battname and path to folder must be strings.'''
    for i in range(1,len(cycle_dict)+1):
        writer = ExcelWriter(path_to_folder + battname + 'Cycle' + str(i) + '.xlsx')
        cycle_dict[i].to_excel(writer)
        writer.save()
    return 

def calc_dv_dqdv(cycle_df):
    '''This function calculates the dv and the dq/dv for a dataframe.'''
    cycle_df = cycle_df.reset_index(drop = True)
    for i in range(1,len(cycle_df)): 
        cycle_df.loc[i, ('dV')] = cycle_df.loc[i, ('Voltage(V)')] - cycle_df.loc[i-1, ('Voltage(V)')]
    #calculate dq/dv based off of discharge capacity - might change this later so user can choose to use charge or discharge cap. 
    cycle_df['dQ/dV'] = cycle_df['Discharge_Capacity(Ah)']/cycle_df['dV']
    return cycle_df

def drop_0_dv(cycle_df_dv): 
    '''Drop rows where dv=0 (or about 0) in a dataframe that has already had dv calculated. Then recalculate dv and dq/dv'''
    #this will clean up the data points around V = 4.2V (since they are holding it at 4.2V for a while).
    cycle_df_dv = cycle_df_dv.dropna(subset=['dQ/dV'])
    cycle_df_dv = cycle_df_dv.reset_index(drop = True)
    for i in range(1, len(cycle_df_dv)):
        if isclose(cycle_df_dv.loc[i, ('dV')], 0, abs_tol = 10**-3):
            cycle_df_dv = cycle_df_dv.drop(index = i)
    #reset index
    cycle_df_dv = cycle_df_dv.reset_index(drop = True)
    #recalculating dv after dropping rows
    for i in range(1, len(cycle_df_dv)): 
        cycle_df_dv.loc[i, ('dV')] = cycle_df_dv.loc[i, ('Voltage(V)')] - cycle_df_dv.loc[i-1, ('Voltage(V)')]
    #recalculate dq/dv  
    cycle_df_dv['dQ/dV'] = cycle_df_dv['Discharge_Capacity(Ah)']/cycle_df_dv['dV']
    return cycle_df_dv 

def sep_char_dis(df_dqdv):
    '''Takes a dataframe of one cycle with calculated dq/dv and separates into charge and discharge differential capacity curves'''
    charge = df_dqdv[df_dqdv['dV'] < 0] 
    charge = charge.reset_index(drop = True)
    discharge = df_dqdv[df_dqdv['dV'] >= 0] 
    discharge = discharge.reset_index(drop = True)
    return charge, discharge






#####################
#DASH Functions 
#***Beck said not to write unit tests so IM NOT GONNA 
#####################

def generate_table(data, maxrows=10):
    """Generates a table with Header and Body given a data set and number of rows to display in Dash format"""
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in data.columns])] +

        # Body
        [html.Tr([
            html.Td(data.iloc[i][col]) for col in data.columns
        ]) for i in range(min(len(data), maxrows))]
    )



import dash_html_components as html
import glob 
import os 
import pandas as pd
import requests

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



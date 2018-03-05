#Roberts Notebook converted to Function 

import glob 
import os 
import pandas as pd
import requests

def get_data(filepath): 
    """Imports all data in given path"""
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
        print(count, name)
    return d
### There are 23 files in the CS2 directory, so we should have 23 entries in the dictionary - add unit test for this, super EASY check 


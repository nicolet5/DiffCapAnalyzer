## TODO: TEST THIS

""" This file processes all the data located in the specified directories.
This code was largely used to gather the descriptors necessary for the ML classificaiton 
problem, because a large number of files needed to be processed and the time to do that through 
the dash app was unrealistic. 

All files in the specified directories must be the same type (Arbin/MACCOR)
"""
import pandas as pd
import numpy as np
import os
import glob

from diffcapanalyzer.databasewrappers import process_data
from diffcapanalyzer.databasewrappers import get_filename_pref
from diffcapanalyzer.databasefuncs import init_master_table
from diffcapanalyzer.databasefuncs import get_file_from_database
from diffcapanalyzer.descriptors import generate_model

# database = 'classification_data.db'
# directories_list = ['../data/ARBIN/CS2_33/', '../data/ARBIN/K2_016/']
	
def descriptors_for_files_in_multiple_dirs(list_of_paths_to_directories, database, datatype, 
											windowlength = 9, polyorder = 3, peak_thresh = 0.7, 
											save_to_excel = False):
	multi_dir_descriptors = pd.DataFrame()
	for path in list_of_paths_to_directories: 
		dir_descriptors = descriptors_for_all_files_in_dir(path, database, datatype, 
							windowlength = 9, polyoder = 3, peak_thresh =0.7): 
		multi_dir_descriptors = multi_dir_descriptors.append(dir_descriptors)
	if save_to_excel: 
		writer = pd.ExcelWriter('multiple_directories_descriptors.xlsx')
		multi_dir_descriptors.to_excel(writer, 'Sheet1')
		writer.save()
	return multi_dir_descriptors

def descriptors_for_all_files_in_dir(path_to_directory, database, datatype,
							 windowlength = 9, polyorder = 3, peak_thresh = 0.7, 
							 save_to_excel = False):
	path = os.path.join(path_to_directory, "*.csv")
	dict_save_name_to_df = {}
	for fname in glob.glob(path):
		save_as_name = get_filename_pref(fname)
		df = pd.read_csv(fname, index = False)
    	dict_save_name_to_df.update({save_as_name : df})
    all_descriptors_df = process_multiple_files(dict_save_name_to_df, database, datatype, windowlength, polyorder, peak_thresh)
	if save_to_excel: 
		writer = pd.ExcelWriter('directory_descriptors.xlsx')
		all_descriptors_df.to_excel(writer, 'Sheet1')
		writer.save()
    return all_descriptors_df


def process_multiple_files(dict_save_name_to_df, database, datatype, windowlength = 9, polyorder = 3, peak_thresh = 0.7, save_to_excel = False):
	"""dict_save_name_to_df example: {'CS233_1': pd.DataFrame()}"""
	all_descriptors_df = pd.DataFrame()
	for key, value in dict_save_name_to_df:
		descriptors_df = process_one_file(value, key, database, datatype, windowlength, polyorder, peak_thresh)
		descriptors_df['Name'] = key
		all_descriptors_df = all_descriptors_df.append(descriptors_df)
	if save_to_excel: 
		writer = pd.ExcelWriter('multi_file_descriptors.xlsx')
		all_descriptors_df.to_excel(writer, 'Sheet1')
		writer.save()
	return all_descriptors_df

def process_one_file(df, save_as_name, database, datatype, windowlength = 9, polyorder = 3, peak_thresh = 0.7, save_to_excel = False):
	if not os.path.exists(database): 
		init_master_table(database)
	cleanset_name = save_as_name + 'CleanSet'
    process_data(
	    save_as_name,
	    database,
	    df,
	    datatype,
	    windowlength,
	    polyorder)
	df_clean = get_file_from_database(cleanset_name, database)
	feedback = generate_model(
    	df_clean, save_as_name, peak_thresh, database)
	descriptors_df = get_file_from_database(save_as_name + '-descriptors', database)
	if save_to_excel: 
		writer = pd.ExcelWriter(save_as_name + '-descriptors.xlsx')
		descriptors_df.to_excel(writer, 'Sheet1')
		writer.save()
	return descriptors_df




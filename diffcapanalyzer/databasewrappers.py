import io
import os
import pandas as pd
from pandas import ExcelWriter
import pandas.io.sql as pd_sql
import sqlite3 as sql
import scipy
import numpy as np

from diffcapanalyzer.chachifuncs import load_sep_cycles, get_clean_cycles, get_clean_sets, calc_dq_dqdv
from diffcapanalyzer.descriptors import dfsortpeakvals
from diffcapanalyzer.databasefuncs import init_master_table, update_database_newtable, update_master_table, get_file_from_database


def process_data(file_name, database_name, decoded_dataframe,
                 datatype, windowlength=9,
                 polyorder=3):
    """Takes raw file, separates cycles, cleans cycles,
    gets the descriptors, saves descriptors for each cycle
    into database, puts cycles back together, and then saves
    resulting cleaned data. """
    if not os.path.exists(database_name):
        init_master_table(database_name)
    names_list = get_table_names(database_name)
    core_file_name = get_filename_pref(file_name)
    if core_file_name + 'CleanSet' in names_list:
        return
    else:
        parse_update_master(core_file_name, database_name,
                            datatype, decoded_dataframe)
        cycle_dict = load_sep_cycles(core_file_name,
                                     database_name,
                                     datatype)
        clean_cycle_dict = get_clean_cycles(cycle_dict,
                                            core_file_name,
                                            database_name,
                                            datatype,
                                            windowlength,
                                            polyorder)
        clean_set_df = get_clean_sets(clean_cycle_dict,
                                      core_file_name,
                                      database_name)
    return


def parse_update_master(
        core_file_name,
        database_name,
        datatype,
        decoded_dataframe):
    """Takes the file and calculates dq/dv from the raw data,
    uploads that ot the database as the raw data, and
    updates the master table with prefixes useful for accessing
    that data related to the file uploaded."""
    # name = get_filename_pref(file_name)
    update_database_newtable(decoded_dataframe,
                             core_file_name + 'UnalteredRaw',
                             database_name)

    data = calc_dq_dqdv(decoded_dataframe, datatype)
    update_database_newtable(data, core_file_name + 'Raw',
                             database_name)
    update_dict = {'Dataset_Name': core_file_name,
                   'Raw_Data_Prefix': core_file_name + 'Raw',
                   'Cleaned_Data_Prefix': core_file_name + 'CleanSet',
                   'Cleaned_Cycles_Prefix': core_file_name + '-CleanCycle',
                   'Descriptors_Prefix': core_file_name + '-descriptors',
                   'Model_Parameters_Prefix': core_file_name + 'ModParams',
                   'Model_Points_Prefix': core_file_name + '-ModPoints',
                   'Raw_Cycle_Prefix': core_file_name + '-Cycle',
                   'Original_Data_Prefix': core_file_name + 'UnalteredRaw'}
    update_master_table(update_dict, database_name)
    return


def macc_chardis(row):
    """Assigns an integer to distinguish rows of
    charging cycles from those of discharging
    cycles. -1 for discharging and +1 for charging."""
    if row['Md'] == 'D':
        return -1
    else:
        return 1


def if_file_exists_in_db(database_name, file_name):
    """Checks if file exists in the given database
    by checking the list of table names for the
    table name corresponding to the whole CleanSet."""
    if os.path.exists(database_name):
        names_list = get_table_names(database_name)
        filename_pref = get_filename_pref(file_name)
        if filename_pref + 'CleanSet' in names_list:
            ans = True
        else:
            ans = False
    else:
        ans = False
    return ans


def get_db_filenames(database_name):
    """ This is used to populate the dropdown menu, so users can only access their data if their
    name is in the user column"""
    con = sql.connect(database_name)
    c = con.cursor()
    names_list = []
    for row in c.execute(
        """SELECT Dataset_Name FROM master_table""" ):
        names_list.append(row[0])
    con.close()
    exists_list = []
    for name in names_list:
        if if_file_exists_in_db(database_name, name):
            exists_list.append(name)
    return exists_list


def get_filename_pref(file_name):
    """Splits the filename apart from the path
    and the extension. This is used as part of
    the identifier for individual file uploads."""
    while '/' in file_name:
        file_name = file_name.split('/', maxsplit=1)[1]
    file_name_pref = file_name.split('.')[0]
    return file_name_pref


def get_table_names(database):
    """Returns all the names of tables that exist in the database"""
    if os.path.exists(database):
        con = sql.connect(database)
        c = con.cursor()
        names_list = []
        for row in c.execute(
                """SELECT name FROM sqlite_master WHERE type='table'"""):
            names_list.append(row[0])
        con.close()
    return names_list

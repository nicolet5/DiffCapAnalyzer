import pandas.io.sql as pd_sql
import sqlite3 as sql

################################
# OVERALL Wrapper Function
################################

def process_data(file_name, database_name):
	# Takes raw file 
	# sep_cycles
	# cleans cycles
	# gets descriptors - peak calcs
	# put back together - save 
	if not os.path.exists(database_name): 
		print('That database does not exist-creating it now.')
		init_master_table(database_name)
	
	con = sql.connect(database_name)
	c = con.cursor()
	names_list = []
	for row in c.execute("""SELECT name FROM sqlite_master WHERE type='table'""" ):
		names_list.append(row[0])
	con.close()
	name = file_name + 'Raw'
	if name in names_list: 
		print('That file name has already been uploaded into the database.')
	else:
		print('Processing that data')	
		parse_update_master(file_name, database_name)
		#this takes the info from the filename and updates the master table in the database. 
		cycle_dict = load_sep_cycles(file_name, database_name)
		clean_cycle_dict= get_clean_cycles(cycle_dict, file_name, database_name)
		#for key in clean_cycle_dict:
    	#	print(key)
		clean_set_df = get_clean_sets(clean_cycle_dict, file_name, database_name)

	return 

	#create sql_master table - this is only ran once 
def init_master_table(database_name):
	con = sql.connect(database_name)
	c = con.cursor()
	mydf = pd.DataFrame({'Dataset_Name': ['example'], 
                     	'Raw_Data_Prefix': ['ex1'], 
                     	'Cleaned_Data_Prefix':['ex2'], 
                     	'Cleaned_Cycles_Prefix': ['ex3']})
	mydf.to_sql('master_table', con, if_exists='replace')
	#my_df is the name of the table within the database

	con.close()
	return 

def update_master_table(update_dic, database_name):
    """This updates the master table in the database based off of the information in the update dictionary"""
    if update_dic is not None:
        con = sql.connect(database_name)
        c = con.cursor()
        #add upload data filename in sql_master table
        c.execute('''INSERT INTO master_table('Dataset_Name', 'Raw_Data_Prefix','Cleaned_Data_Prefix', 'Cleaned_Cycles_Prefix') 
                     VALUES ('%s', '%s', '%s', '%s')
                  ''' % (update_dic['Dataset_Name'], update_dic['Raw_Data_Prefix'], update_dic['Cleaned_Data_Prefix'], update_dic['Cleaned_Cycles_Prefix']))
        # check if update_dic['Dataset_Name'] exists in master_table, if so, don't run the rest of the code. 
        #the above part updates the master table in the data frame
        con.commit()
        con.close()
        #display table in layout
        return 
    else:
        return [{}]

def update_database_newtable(df, upload_filename, database_name):

    #add df into sqlite database as table
    con = sql.connect(database_name)
    c = con.cursor()
    df.to_sql(upload_filename, con, if_exists="replace")
    return

def parse_update_master(file_name, database_name):
	name = file_name.split('.')[0]
	data = pd.read_excel(file_name, 1)
	update_database_newtable(data, name + 'Raw', database_name)
	update_dic ={'Dataset_Name': name,'Raw_Data_Prefix': name +'Raw',
    				'Cleaned_Data_Prefix': name + 'CleanSet', 
    				'Cleaned_Cycles_Prefix': name + '-CleanCycle'}
	update_master_table(update_dic, database_name)
	return
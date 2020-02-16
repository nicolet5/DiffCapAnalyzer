import pandas as pd
import pandas.io.sql as pd_sql
import sqlite3 as sql

def update_database_newtable(df, upload_filename, database_name):
	"""add df into sqlite database as table"""
	con = sql.connect(database_name)
	c = con.cursor()
	df.to_sql(upload_filename, con, if_exists="replace", index = False)
	return

def get_file_from_database(name, database):
	"""Pull file from database by name, returns that dataframe"""
	con = sql.connect(database)
	c = con.cursor()
	names_list = []
	for row in c.execute("""SELECT name FROM sqlite_master WHERE type='table'""" ): 
		names_list.append(row[0])
	if name in names_list: 
		df_from_database = pd.read_sql_query("SELECT * FROM '%s'" % (name),con)
		con.close()
	else:
		df_from_database = None
	return df_from_database

def update_master_table(update_dic, database_name, username):
	"""This updates the master table in the database based off of the information in the update dictionary"""
	if update_dic is not None:
		con = sql.connect(database_name)
		c = con.cursor()
		df_master = get_file_from_database('master_table', database_name)
		if update_dic['Dataset_Name'] not in df_master['Dataset_Name']: 
		#add upload data filename in sql_master table
			c.execute('''INSERT INTO master_table('Dataset_Name', 
											'Raw_Data_Prefix',
											'Cleaned_Data_Prefix', 
											'Cleaned_Cycles_Prefix', 
											'Descriptors_Prefix', 
											'Username') 
						 VALUES ('%s', '%s', '%s', '%s', '%s', '%s')
					  ''' % (update_dic['Dataset_Name'],
					  		 update_dic['Raw_Data_Prefix'], 
					  		 update_dic['Cleaned_Data_Prefix'], 
					  		 update_dic['Cleaned_Cycles_Prefix'],
					  		 update_dic['Descriptors_Prefix'], 
					  		 username))
		# check if update_dic['Dataset_Name'] exists in master_table, if so, don't run the rest of the code. 
		#the above part updates the master table in the data frame
		con.commit()
		con.close()
		#display table in layout
		return 
	else:
		return [{}]

def init_master_table(database_name):
	con = sql.connect(database_name)
	c = con.cursor()
	mydf = pd.DataFrame({'Dataset_Name': [], 
						 'Raw_Data_Prefix': [], 
						 'Cleaned_Data_Prefix':[], 
						 'Cleaned_Cycles_Prefix': [], 
						 'Descriptors_Prefix': [],
						 'Username':[]})
	mydf.to_sql('master_table', con, if_exists='replace', index = False)
	# my_df is the name of the table within the database
  	# add dummy users + passwords
	df = pd.DataFrame(data = [['Example User', 'password']],
				  columns = ['Username', 'Password'])

	# add the dataframe created above with the users and passwords to the db
	# if a table named "users" already exists, it will be replaced with this one
	df.to_sql('users', con, if_exists="replace", index = False)
	con.close()
	return 
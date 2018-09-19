#import chachifuncs_exp as ccf
import databasewrappers_exp as dbexp
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_table_experiments as dt
import pandas as pd
import io
import os
import json
import plotly 
import base64
from lmfit.model import save_modelresult
from lmfit.model import load_modelresult
#from unittest.mock import patch
##########################################
#Load Datakljkjjkj
##############################################
#eventually add everything in folder and creates a dropdowssn jfsklsjsjdsthadtl loads that data into data 
database = 'dqdvDataBase_0912APP_85.db'
if not os.path.exists(database): 
	print('That database does not exist-creating it now.')
	dbexp.dbfs.init_master_table(database)
#datatype = 'CALCE'
#for now just use some data we have 
#data = pd.read_excel('data/Clean_Whole_Sets/CS2_33_12_16_10CleanSet.xlsx')
data = dbexp.dbfs.get_file_from_database('CS2_33_10_04_10CleanSet', 'dqdvDataBase_sortedpeaks4.db')
#these are just initial values to use:
slidmax = 15
slidmax2 = 15
#charge, discharge = dbexp.ccf.sep_char_dis(data, datatype)

#df_dqdv = ccf.calc_dv_dqdv('data/CS2_33/CS2_33_10_04_10.xlsx')
#df_dqdv = ccf.calc_dv_dqdv(data)
#charge, discharge = ccf.sep_char_dis(data)



##########################################
#App Layout 
##########################################
app = dash.Dash() #initialize dash 

Introduction= dcc.Markdown('''
        # ChaChi
        ## Interface for visualizing battery cycle data
        #'''), #Add some Markdown


app.layout = html.Div([
    html.Div([
        html.H1('ChaChi Battery Cycle Visualization'),
        ]),

    html.Div([
        html.Br(),
        dcc.Dropdown(id='input-datatype', options =[{'label':'Arbin', 'value':'CALCE'},{'label':'MACCOR', 'value':'MACCOR'}],  placeholder='datatype'),
        html.H4('Input lower voltage range to exclude from the clean data: '),
        dcc.Input(id='input-voltrange1', type='text', placeholder='0' ),
        html.H4('Input upper voltage range to exclude from the clean data: '),
        dcc.Input(id ='input-voltrange2', type='text', placeholder='0.03'),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '98%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                #'margin': '10px'
            },
            multiple=False),
        ##################
        ]),
    
    html.Div(id = 'output-data-upload'),    

    html.Div(id = 'model-output'),

    html.Div(id = 'update-model-ans'), 
    
    html.Div([dcc.Dropdown(id ='available-data',
    					   options = 'options')]),
    html.Div([dcc.Input(id = 'charge-newpeak', placeholder = 'charge new peak')]),
    html.Div([dcc.Input(id = 'discharge-newpeak', placeholder = 'discharge new peak')]),
    html.Button('Update Preview of Model', id = 'update-model-button'),
    html.Button('Update Model in Database', id = 'update-model-indb-button'),
    html.Div(id = 'gen-desc-confirmation'),
    html.Div([
        html.Br(),
        dcc.Slider(
            id='cycle--slider',
            min=0,
            #min=charge['Cycle_Index'].min(),
            #max=data['Cycle_Index'].max(),
            max = slidmax,
            #value=charge['Cycle_Index'].max(),
            #value = data['Cycle_Index'].max(),
            value = slidmax2,
            step=1,
            included=True,
            marks={str(each): str(each) for each in range(slidmax)},
            #data['Cycle_Index'].unique()},
            #includes a mark for each step
            )
        ],
        style={
                'width': '98%',
                'margin': '10px'
                }
        ),

    html.Div([
        html.Br(),
        dcc.Graph(id='charge-graph'), #initialize a simple plot
        #html.Br(),
        #dcc.Graph(id='discharge-graph'),
        ],style={
            'columnCount': 1,
            'width':'98%',
            'height': '80%',
            }
        ),
    
    html.Div([
        html.Br(),
        dcc.Graph(id='model-graph'), #initialize a simple plot
        #html.Br(),
        #dcc.Graph(id='discharge-graph'),
        ],style={
            'columnCount': 1,
            'width':'98%',
            'height': '80%',
            }
        ),

    html.Div([
        html.H4('DataTable'),
        dt.DataTable(
            #rows=charge.to_dict('records'), #converts df to dict
            rows=[{}],
            #columns=sorted(charge.columns), #sorts columns
            row_selectable=True,
            filterable=True,
            selected_row_indices=[],
            id='datatable'
            ),
        html.Div(id='selected-indexes'),

        #html.H4('Discharge DataTable'),
        #dt.DataTable(
            #rows=discharge.to_dict('records'), #converts df to dict
         #   rows=[{}],
            #columns=sorted(discharge.columns), #sorts columns
         #   row_selectable=True,
        #    filterable=True,
        #    selected_row_indices=[],
        #    id='discharge-datatable'
        #    ),
        #html.Div(id='selected-indexes'),
        ],
        style={
            'width': '98%',
            #'height': '60px',
            #'lineHeight': '60px',
            'margin': '10px'
            },
        ), 
    html.Div(id='hidden-div', style={'display':'none'}) #this is so we can have a callback to run the process data function on the raw data inputted


])

##########################################
#Interactive Parts
##########################################

#@patch('databasewrappers_exp.process_data.input', create=True)

def parse_contents(contents, filename, datatype, thresh1, thresh2):
	# this is just to be used to get a df from an uploaded file
    if contents == None:
    	return html.Div(['No file has been uploaded, or the file uploaded was empty.'])
    else: 
    	content_type, content_string = contents.split(',')
    	decoded = base64.b64decode(content_string)
    #try: 
    	cleanset_name = filename.split('.')[0] + 'CleanSet'
    	#this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
    		#check to see if the database exists, and if it does, check if the file exists.
    	ans_p = dbexp.if_file_exists_in_db(database, filename)
    	if ans_p == True: 
    		df_clean = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    		v_toappend_c = []
    		v_toappend_d = []
    		feedback = generate_model(v_toappend_c, v_toappend_d, df_clean, filename)
    		return html.Div(['That file exists in the database: ' + str(filename.split('.')[0])])
    		#df = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    	else:
    		dbexp.process_data(filename, database, decoded, datatype, thresh1, thresh2)
    		df_clean = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    		v_toappend_c = []
    		v_toappend_d = []
    		feedback = generate_model(v_toappend_c, v_toappend_d, df_clean, filename)
    		# maybe split the process data function into getting descriptors as well?
    		#since that is the slowest step 
    		return html.Div(['New file has been processed: ' + str(filename)])
    		
    		#df = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    	#have to pass decoded to it so it has the contents of the file
    #except Exception as e:
    #    print('THERE WAS A PROBLEM PROCESSING THE FILE: ' + str(e))
        #df = None
     #   return html.Div([
     #       'There was an error processing this file: '+ str(filename) + str(e)
      #  ])
    #return html.Div([
    #        'Something else happened.'
    #    ])

	    #mocked_input.side_effect = ['CALCE', 'y', '4.17', '4.25']
	#try:   
    #this should take a raw file and process it, then put it in the database
########################################################################################
#########################################################################################
# this part should be ran everytime something is updated, keeping the filename. whenever the dropdown menu changes
def pop_with_db(filename, database):
    cleanset_name = filename.split('.')[0] + 'CleanSet'
    rawset_name = filename.split('.')[0] + 'Raw'
    #this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
    ans = dbexp.if_file_exists_in_db(database, filename)
    print(ans)
    if ans == True: 
    	# then the file exists in the database and we can just read it 
    	df_clean = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    	df_raw = dbexp.dbfs.get_file_from_database(rawset_name, database)
    	datatype = df_clean.loc[0,('datatype')]
    	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    	# for each cycle in the clean set, separate into charge and discharge and find peak indices for every cycle
    	#######################################comment all this out later
    	# chargeloc_dict = {}
    	# dischloc_dict = {}
    	# windowlength = 11
    	# polyorder = 1
    	# # change these to be user inputs - they are just the windowlength and polyorder for peak finding - not the overall one
    	# for each_cyc in df_clean[cycle_ind_col].unique():
    	# 	clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==each_cyc], datatype)
    	# 	i_charge, volts_i_ch = dbexp.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype)
    	# 	i_discharge, volts_i_dc = dbexp.descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype)
    	# 	#lenmax (equal to 200 here) does literally nothing as the code is written now on 9.13.18
    	# 	# this returns the peak locations as found by peakutils -plot these as vertical lines on
    	# 	chargeloc_dict.update({each_cyc: volts_i_ch})
    	# 	dischloc_dict.update({each_cyc: volts_i_dc})
    	############################################################
    else:
    	df_clean = None
    	df_raw = None
    	peakloc_dict = {}
    return df_clean, df_raw

def get_model_dfs(df_clean, datatype, cyc, v_toappend_c, v_toappend_d, max_char_ind, max_dischar_ind):
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
	clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==cyc], datatype)
	windowlength = 3
	polyorder = 1
	# speed this up by moving the initial peak finder out of this, and just have those two things passed to it 
	#i_charge, volts_i_ch = dbexp.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype)
	i_charge = max_char_ind
	i_discharge = max_dischar_ind
	#chargeloc_dict.update({cyc: volts_i_ch})
	V_series_c = clean_charge[volt_col]
	dQdV_series_c = clean_charge['Smoothed_dQ/dV']
	par_c, mod_c, indices_c = dbexp.descriptors.fitters.model_gen(V_series_c, dQdV_series_c, 'c', i_charge, cyc, v_toappend_c)
	model_c = dbexp.descriptors.fitters.model_eval(V_series_c, dQdV_series_c, 'c', par_c, mod_c)			
	if model_c is not None:
		mod_y_c = mod_c.eval(params = model_c.params, x = V_series_c)
		mod_y_c = mod_y_c.rename('Model')
		model_c_vals = model_c.values
		model_c_errors = {'aic' : model_c.aic, 'bic': model_c.bic, 'redchi':model_c.redchi}
	else:
		mod_y_c = None 
		model_c_vals = None
		model_c_errors = None

	# now the discharge: 
	#i_discharge, volts_i_dc = dbexp.descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype)
	V_series_d = clean_discharge[volt_col]
	dQdV_series_d = clean_discharge['Smoothed_dQ/dV']
	par_d, mod_d, indices_d = dbexp.descriptors.fitters.model_gen(V_series_d, dQdV_series_d, 'd', i_discharge, cyc, v_toappend_d)
	model_d = dbexp.descriptors.fitters.model_eval(V_series_d, dQdV_series_d, 'd', par_d, mod_d)			
	if model_d is not None:
		mod_y_d = mod_d.eval(params = model_d.params, x = V_series_d)
		mod_y_d = mod_y_d.rename('Model')
		model_d_vals = model_d.values
		mod_y_d = -mod_y_d # because discharge 
		model_d_errors = {'aic' : model_d.aic, 'bic': model_d.bic, 'redchi':model_d.redchi}
	else:
		mod_y_d = None
		model_d_vals = None
		model_d_errors = None
		# still not working
	# save the model parameters in the database with the data
	new_df_mody_c = pd.concat([mod_y_c, V_series_c, dQdV_series_c, clean_charge[cycle_ind_col]], axis = 1)
	new_df_mody_d = pd.concat([mod_y_d, V_series_d, dQdV_series_d, clean_discharge[cycle_ind_col]], axis = 1)
	new_df_mody = pd.concat([new_df_mody_c, new_df_mody_d], axis = 0)

	# combine the charge and discharge together
	

	return new_df_mody, model_c_vals, model_d_vals, model_c_errors, model_d_errors

def generate_model(v_toappend_c, v_toappend_d, df_clean, filename):
	# run this when get descriptors button is pushed, andfd re-run it when user puts in new voltage 
	# create model based off of initial peaks 
	# show user model, then ask if more peak locations should be used (shoulders etc)
	datatype = df_clean.loc[0,('datatype')]
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)

	chargeloc_dict = {}
	param_df = pd.DataFrame(columns = ['Cycle','Model_Parameters'])
	#ans = dbexp.if_file_exists_in_db(database, filename)
	#if ans == True:
		#return html.Div(['A model for that filename already exists in the database.'])
	#else: 
	mod_pointsdf = pd.DataFrame()
	charge_i_dict = {}
	discharge_i_dict = {} 
	# for cyc in df_clean[cycle_ind_col].unique():
	# 	# run peak finder to find inital number + locations of max number peaks  
	# 	if cyc != 1 and cyc != df_clean[cycle_ind_col].max():
	# 		# we don't want to use the first cycle since thats got some funny stuff goin on 
	# 		clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==cyc], datatype)
	# 		windowlength = 3
	# 		polyorder = 1
	# 		#print(type(clean_charge))
	# 		#print(type(clean_discharge))
	# 		#print("just before peak finder in generate model")
	# 		i_charge, volts_i_ch = dbexp.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype)
	# 		i_discharge, volts_i_dc = dbexp.descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype)
	# 		#print('got the descriptors')
	# 		if i_charge is not None: 
	# 			charge_i_dict.update({cyc: i_charge})
	# 		#	print('updated charge dict')
	# 		if i_discharge is not None:
	# 			discharge_i_dict.update({cyc:i_discharge})
	# 		#	print('updated discharge dict')
	# 		#print(charge_i_dict)d
	# 		#print(type(i_discharge))
	# 		#print(discharge_i_dict)
	# 	#max_char_cyc = 2
	# 	#max_dischar_cyc = 2
	# if len(charge_i_dict) > 0:
	# 	max_char_cyc = max(charge_i_dict, key= lambda x: len(set(charge_i_dict[x])))
	# 	max_char_ind = charge_i_dict[max_char_cyc]
	# else:
	# 	clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==2], datatype)
	# 	windowlength = 3
	# 	polyorder = 1
	# 	i_charge, volts_i_ch = dbexp.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype)
	# 	max_char_ind = i_charge
	# 	#print('got the descriptors')
	# 	#max_char_cyc = df_clean[cycle_ind_col].max()

	# if len(discharge_i_dict) > 0:
	# 	max_dischar_cyc = max(discharge_i_dict, key= lambda x: len(set(discharge_i_dict[x])))
	# 	max_dischar_ind = discharge_i_dict[max_dischar_cyc]
	# else: 
	# 	clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==2], datatype)
	# 	windowlength = 3
	# 	polyorder = 1
	# 	i_discharge, volts_i_dc = dbexp.descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype)
	# 	max_dischar_ind = i_discharge
	# use max_char_ind as the indicies for dpeaks, but allow them to vary 
	# use max_dischar_cyc as the indices for the discharge peaks, but allow them to vary 
	for cyc in df_clean[cycle_ind_col].unique():
		######################################################################9.15.18
		clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==2], datatype)
		windowlength = 3
		polyorder = 1
		i_charge, volts_i_ch = dbexp.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype)
		max_char_ind = i_charge
		i_discharge, volts_i_dc = dbexp.descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype)
		max_dischar_ind = i_discharge
		new_df_mody, model_c_vals, model_d_vals, model_c_errors, model_d_errors = get_model_dfs(df_clean, datatype, cyc, v_toappend_c, v_toappend_d, max_char_ind, max_dischar_ind)
		mod_pointsdf = mod_pointsdf.append(new_df_mody)
		param_df = param_df.append({'Cycle': cyc, 'C/D': 'charge', 'Model_Parameters': str(model_c_vals), 'Model_Error_Params': str(model_c_errors)}, ignore_index = True)
		param_df = param_df.append({'Cycle': cyc, 'C/D': 'discharge', 'Model_Parameters': str(model_d_vals), 'Model_Error_Params': str(model_d_errors)}, ignore_index = True)
	# want this outside of for loop to update the db with the complete df of new params 
	dbexp.dbfs.update_database_newtable(mod_pointsdf, filename.split('.')[0]+ '-ModPoints', database)
	# this will replace the data table in there if it exists already 
	dbexp.dbfs.update_database_newtable(param_df, filename.split('.')[0] + 'ModParams', database)
			#save_model(model, path, saveas)
			# for index in indices: hjkhj

			# 	print('sigma for '+ str(index)+': '+ str(model.values['a'+str(index)+'_sigma']))
			# 	print('fraction for '+ str(index)+': '+ str(model.values['a'+str(index)+'_fraction']))
			# 	print('center for '+ str(index)+': '+ str(model.values['a'+str(index)+'_center']))
			# 	print('amplitude for '+ str(index)+': '+ str(model.values['a'+str(index)+'_amplitude']))
			# 	print('')
			# then discharge cycle:
#return html.Div([str(model.values)])
	return html.Div(['That model has been added to the database'])



def param_dicts_to_df(mod_params_name, database):
    mod_paramsgraphit = dbexp.dbfs.get_file_from_database(mod_params_name, database)
    #charge_df = mod_paramsgraphit[mod_paramsgraphit['C/D'] == 'discharge']
    #charge_df = charge_df.reset_index(drop = True)
    charge_df = mod_paramsgraphit
    charge_descript = pd.DataFrame()
    for i in range(len(charge_df)):
        param_dict = ast.literal_eval(charge_df.loc[i, ('Model_Parameters')])

        charge_keys =[]
        for key, value in param_dict.items(): 
            if '_amplitude' in key:
                #print(int(key.split('_')[0].split('a')[1]))
                charge_keys.append(key.split('_')[0])
        print(charge_keys) 
        new_dict = {}
        new_dict.update({'poly_coef1': param_dict['c0'],
                         'poly_coef2': param_dict['c1'], 
                         'poly_coef3': param_dict['c2'], 
                         'poly_coef4': param_dict['c3'], 
                         'poly_coef5': param_dict['c4']})
        new_dict.update({'charge/discharge': mod_paramsgraphit.loc[i, ('C/D')], 
                         'cycle_number': str(mod_paramsgraphit.loc[i, ('Cycle')])})
        peaknum = 0
        for item in charge_keys:
            peaknum = peaknum +1 
            center = param_dict[item + '_center']
            amp = param_dict[item + '_amplitude']
            fract = param_dict[item + '_fraction']
            sigma = param_dict[item + '_sigma']
            height = param_dict[item + '_height']
            fwhm = param_dict[item + '_fwhm']
            #print('center' + str(center))
            PeakArea, PeakAreaError = scipy.integrate.quad(my_pseudovoigt, 0.0, 100, args=(center, amp, fract, sigma))
            #print('peak location is : ' + str(center) + ' Peak area is: ' + str(PeakArea))
            new_dict.update({'area_peak_'+str(peaknum): PeakArea, 
                             'center_peak_' +str(peaknum):center, 
                             'amp_peak_' +str(peaknum):amp,
                             'fract_peak_' +str(peaknum):fract, 
                             'sigma_peak_' +str(peaknum):sigma, 
                             'height_peak_' +str(peaknum):height, 
                             'fwhm_peak_' +str(peaknum):fwhm})      
        #print(new_dict)
        new_dict_df = pd.DataFrame(columns = new_dict.keys())
        for key1, val1 in new_dict.items():
            new_dict_df.at[0, key1] = new_dict[key1]
        charge_descript = pd.concat([charge_descript, new_dict_df])
        charge_descript = charge_descript.reset_index(drop = True)
        dbexp.dbfs.update_database_newtable(charge_descript, mod_params_name +'-descriptors', database)
    return charge_descript

##############################################################################################
#@app.callback(
#	Output('hidden-div', 'hidden'),
#	[Input('upload-data', 'contents'), 
#	 Input('upload-data', 'filename'), 
#	 Input('upload-data', 'last_modified')])

#def process_new_rawdata(contents, filename, date):
#	dbexp.process_data('data/example_files/Raw_Data_Examples/'+filename, database)
#	return None

@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename'), 
               Input('input-datatype', 'value'), 
               Input('input-voltrange1', 'value'), 
               Input('input-voltrange2', 'value')])
def update_output(contents, filename, value, thresh1, thresh2):
	#value here is the datatype, then voltagerange1, then voltagerange2
    children = parse_contents(contents, filename, value, thresh1, thresh2)
    return children

@app.callback(Output('available-data', 'options'), 
			  [Input('output-data-upload', 'children')])
def update_dropdown(children):
	options = [{'label':i[:-3], 'value':i[:-3]} for i in dbexp.get_db_filenames(database)]
	return options

@app.callback(Output('update-model-ans', 'children'), 
			  [Input('available-data', 'value'), 
			   Input('charge-newpeak', 'value'), 
			   Input('discharge-newpeak', 'value'),
			   Input('update-model-indb-button', 'n_clicks')])
def update_model_indb(filename, new_charge_vals, new_discharge_vals, n_clicks):
	if n_clicks is not None:
		int_list_c = []
		int_list_d = []
		if new_charge_vals is not None: 
			new_list_c = new_charge_vals.split(',')
			for i in new_list_c:
			    int_list_c.append(float(i))
		else: 
			None
		if new_discharge_vals is not None: 
			new_list_d = new_discharge_vals.split(',')
			for i in new_list_d:
			    int_list_d.append(float(i))
		else: 
			None
		cleanset_name = filename.split('.')[0] + 'CleanSet'
		df_clean = dbexp.dbfs.get_file_from_database(cleanset_name, database)
		feedback = generate_model(int_list_c, int_list_d, df_clean, filename)
	else:
		feedback = html.Div(['Model has not been updated yet.'])
	return feedback
	# maybe split the process data function into getting descriptors as well?
    		#since that is the slowest step 
# Make this app callback from a drop down menu selecting a filename in the database
# populate dropdown using master_table column= Dataslket_Name
# sdksl
#@app.callback(Output('model-output', 'children'), 
#			  [Input('upload-data', 'filename')])
#def get_model_feedback(filename):
#	cleanset_name = filename.split('.')[0] + 'CleanSet'
#	rawset_name = filename.split('.')[0] + 'Raw'
#    #this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
#	ans = dbexp.if_file_exists_in_db(database, filename)
#	if ans == True: 
 #		# then the file exists in the database and we can just read it 
#		df_clean = dbexp.dbfs.get_file_from_database(cleanset_name, database)
#		v_toappend_c = [3.4]
#		v_toappend_d = [3.7]
#		feedback = generate_model(v_toappend_c, v_toappend_d, df_clean, filename)
#	else: 
#		feedback = html.Div(['That did not work.'])
#	return feedback


@app.callback( #update slider 
    Output('cycle--slider', 'max'),
    [Input('available-data', 'value')])

def update_slider_max(filename):
    data, raw_data= pop_with_db(filename, database)
    #charge, discharge = dbexp.ccf.sep_char_dis(data, datatype)
    datatype = data.loc[0,('datatype')]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    slidmax = data['Cycle_Index'].max()
    return data['Cycle_Index'].max()

@app.callback(#update slider marks
	Output('cycle--slider', 'marks'), 
	[Input('available-data', 'value')])

def update_slider_marks(filename):
	data, raw_data= pop_with_db(filename, database)
	return {str(each): str(each) for each in data['Cycle_Index'].unique()}

@app.callback( #update slider 
    Output('cycle--slider', 'value'),
    [Input('available-data', 'value')])

def update_slider_value(filename):
    data, raw_data = pop_with_db(filename, database)
    #charge, discharge = dbexp.ccf.sep_char_dis(data, datatype)
    datatype = data.loc[0,('datatype')]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    slidmax2 = data['Cycle_Index'].max()
    return data['Cycle_Index'].max()



@app.callback( #decorator wrapper for table 
        Output('datatable', 'selected_row_indices'), #component_id, component_property 
        [Input('charge-graph','clickData')],
        [State('datatable','selected_row_indices')]
        )

def update_selected_row_indices(clickData, selected_row_indices):
    if clickData:
        for point in clickData['points']:
            if point['pointNumber'] in selected_row_indices:
                selected_row_indices.remove(point['pointNumber'])
            else:
                selected_row_indices.append(point['pointNumber'])
    return selected_row_indices

@app.callback( #decorator wrapper for plot
        Output('charge-graph','figure'),
        [Input('cycle--slider','value'),
         Input('available-data', 'value'), # this will be the filename of the file 
         #Input('input-datatype', 'value'),
         Input('datatable','selected_row_indices')]
         #Input('upload-data','contents')]
        )

def update_figure1(selected_step,filename, selected_row_indices):
    data, raw_data= pop_with_db(filename, database)
    datatype = data.loc[0,('datatype')]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    #stupid change
    modset_name = filename.split('.')[0] + '-ModPoints'
    df_model = dbexp.dbfs.get_file_from_database(modset_name, database)
    if df_model is not None: 
    	filt_mod = df_model[df_model[cycle_ind_col] == selected_step]

    #(charge, discharge) = dbexp.ccf.sep_char_dis(data, datatype)
    # grab datattype from file:

    filtered_data = data[data[cycle_ind_col] == selected_step]
    raw_filtered_data= raw_data[raw_data[cycle_ind_col]== selected_step]
    
    #filt_chargeloc = chargeloc_dict[selected_step] # this returns a list [] of peak indices
    #filt_disloc = dischloc_dict[selected_step]
    for i in filtered_data[cycle_ind_col].unique():
        dff = filtered_data[filtered_data[cycle_ind_col] == i]
        dff_raw = raw_filtered_data[raw_filtered_data[cycle_ind_col] == i]
        if df_model is not None:
        	dff_mod = filt_mod[filt_mod[cycle_ind_col] == i]
        fig = plotly.tools.make_subplots(
            rows=1,cols=2,
            subplot_titles=('Raw Cycle','Smoothed Cycle'),
            shared_xaxes=True)
        marker = {'color': ['#0074D9']}
                #fig.append_trace({'x': [2.0, 2.0],'y': [0, 2.0], 'type': 'line', 'name': 'Peak Position'}, 1, 2

        for i in (selected_row_indices or []):
            marker['color'][i] = '#FF851B'
        fig.append_trace({
            'x': dff[volt_col],
            'y': dff['Smoothed_dQ/dV'],
            'type': 'scatter',
            'marker': marker,
            'name': 'Smoothed Data'
            }, 1, 2)
        fig.append_trace({
            'x': dff_raw[volt_col],
            'y': dff_raw['dQ/dV'],
            'type': 'scatter',
            'marker': marker,
            'name': 'Raw Data'
            }, 1, 1)
        if df_model is not None:   
	        fig.append_trace({
	            'x':dff_mod[volt_col], 
	            'y':dff_mod['Model'] ,
	            'type': 'scatter',
	            'name': 'Model'
	            }, 1,2)
        #fig.append_trace({'x': (2.0, 2.0),'y': (0, 2.0), 'type': 'line', 'name': 'Peak Position'}, 1, 2)
        # shapes = list()
        # for vline in filt_chargeloc:
        # 	shapes.append({'type':'line',
        # 		   'x0' : vline, 
        # 		   'y0':0, 
        # 		   'x1':vline, 
        # 		   'y1': dff['dQ/dV'].max(), 
        # 		   'line': {
        # 		   	   'color':'rgb(128, 0, 128)',
        # 		   	   'width': 2, 
        # 		   	   'dash': 'dashdot'}})
        # for vline in filt_disloc:
        # 	shapes.append({'type':'line',
        # 		   'x0' : vline, 
        # 		   'y0':0, 
        # 		   'x1':vline, 
        # 		   'y1': dff['dQ/dV'].min(), 
        # 		   'line': {
        # 		   	   'color':'rgb(128, 0, 128)',
        # 		   	   'width': 2, 
        # 		   	   'dash': 'dashdot'}})
        
        fig['layout']['showlegend'] = False
        #fig['layout']['shapes'] = shapes
        fig['layout']['xaxis1'].update(title = 'Voltage (V)')
        fig['layout']['xaxis2'].update(title = 'Voltage (V)')
        fig['layout']['yaxis1'].update(title = 'dQ/dV')
        fig['layout']['yaxis2'].update(title = 'dQ/dV')
        fig['layout']['height'] = 600
        fig['layout']['margin'] = {
            'l': 40,
            'r': 10,
            't': 60,
            'b': 200
            }
        #fig['layout']['yaxis'] = {'title': 'dQ/dV'}
    return fig

@app.callback( #decorator wrapper for plot
        Output('model-graph','figure'),
        [
         Input('available-data', 'value'), # this will be the filename of the file 
         #Input('input-datatype', 'value'),
         #Input('datatable','selected_row_indices'),
         Input('charge-newpeak', 'value'), 
         Input('discharge-newpeak', 'value'), 
         Input('update-model-button', 'n_clicks')]
         #Input('upload-data','contents')]
        )

def update_figure2(filename, charge_newpeaks, discharge_newpeaks, n_clicks):
    """ This is  a function to evaluate the model on a sample plot before updating the database"""
    data, raw_data= pop_with_db(filename, database)
    datatype = data.loc[0,('datatype')]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    selected_step = round(data[cycle_ind_col].max()/2) +1 
    # select a cycle in the middle of the set
    dff_data= data[data[cycle_ind_col] == selected_step]
    dff_raw = raw_data[raw_data[cycle_ind_col]==selected_step]
    if n_clicks is not None:
    	# if the user has hit the update-model-button - remake model
        int_list_c = []
        int_list_d = []
        if charge_newpeaks is not None: 
            new_list_c = charge_newpeaks.split(',')
            for i in new_list_c:
                int_list_c.append(float(i))
        else: 
            None
        if discharge_newpeaks is not None: 
            new_list_d = discharge_newpeaks.split(',')
            for i in new_list_d:
                int_list_d.append(float(i))
        else: 
            None
        charge_i_dict = {}
        discharge_i_dict = {} 
        for cyc in data[cycle_ind_col].unique():
		# run peak finder to find inital number + locations of max number peaks  
            if cyc != 1 and cyc != data[cycle_ind_col].max():
                # we don't want to use the first or the last cycle since thats got some funny stuff goin on 
                clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(data[data[cycle_ind_col] ==cyc], datatype)
                windowlength = 3
                polyorder = 1
                i_charge, volts_i_ch = dbexp.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype)
                i_discharge, volts_i_dc = dbexp.descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype)
                #print('got the descriptors')
                if i_charge is not None: 
                    charge_i_dict.update({cyc: i_charge})
				#	print('updated charge dict')
                if i_discharge is not None:
                    discharge_i_dict.update({cyc:i_discharge})
#
        if len(charge_i_dict) > 0:
            max_char_cyc = max(charge_i_dict, key= lambda x: len(set(charge_i_dict[x])))
            max_char_ind = charge_i_dict[max_char_cyc]
        else:
          clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(data[data[cycle_ind_col] ==2], datatype)
          windowlength = 3
          polyorder = 1
          i_charge, volts_i_ch = dbexp.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype)
          max_char_ind = i_charge
			#print('got the descriptors')
			#max_char_cyc = df_clean[cycle_ind_col].max()

        if len(discharge_i_dict) > 0:
          max_dischar_cyc = max(discharge_i_dict, key= lambda x: len(set(discharge_i_dict[x])))
          max_dischar_ind = discharge_i_dict[max_dischar_cyc]
        else: 
          clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(data[data[cycle_ind_col] ==2], datatype)
          windowlength = 3
          polyorder = 1
          i_discharge, volts_i_dc = dbexp.descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype)
          max_dischar_ind = i_discharge
	# use max_char_ind as the indicies for peaks, but allow them to vary
	# use max_dischar_cyc as the indices for the diskcharge peaks, but allow them to vary 
        new_df_mody, model_c_vals, model_d_vals, model_c_errors, model_d_errors = get_model_dfs(dff_data, datatype, selected_step, int_list_c, int_list_d,  max_char_ind, max_dischar_ind)
        dff_mod = new_df_mody
    else: 
    	# if user hasn't pushed the button, populate with original model from database
        modset_name = filename.split('.')[0] + '-ModPoints'
        df_model = dbexp.dbfs.get_file_from_database(modset_name, database)
        if df_model is not None: 
        	dff_mod = df_model[df_model[cycle_ind_col] == selected_step]
        else: 
        	dff_mod = None
    #(charge, discharge) = dbexp.ccf.sep_char_dis(data, datatype)
    # grab datattype from file:dfd
    
    
    #raw_filtered_data= raw_data[raw_data[cycle_ind_col]== selected_step]
    
    #filt_chargeloc = chargeloc_dict[selected_step] # this returns a list [] of peak indices
    #filt_disloc = dischloc_dict[selected_step]
    #for i in filtered_data[cycle_ind_col].unique():
    fig = plotly.tools.make_subplots(
        rows=1,cols=2,
        subplot_titles=('Raw Cycle','Smoothed Cycle'),
        shared_xaxes=True)
    marker = {'color': ['#0074D9']}
            #fig.append_trace({'x': [2.0, 2.0],'y': [0, 2.0], 'type': 'line', 'name': 'Peak Position'}, 1, 2
    fig.append_trace({
        'x': dff_data[volt_col],
        'y': dff_data['Smoothed_dQ/dV'],
        'type': 'scatter',
        'marker': marker,
        'name': 'Smoothed Data'
        }, 1, 2)
    fig.append_trace({
        'x': dff_raw[volt_col],
        'y': dff_raw['dQ/dV'],
        'type': 'scatter',
        'marker': marker,
        'name': 'Raw Data'
        }, 1, 1)
    if dff_mod is not None:
        fig.append_trace({
            'x':dff_mod[volt_col], 
            'y':dff_mod['Model'] ,
            'type': 'scatter',
            'name': 'Model of One Cycle'
            }, 1,2)

    fig['layout']['showlegend'] = False
    #fig['layout']['shapes'] = shapes
    fig['layout']['xaxis1'].update(title = 'Voltage (V)')
    fig['layout']['xaxis2'].update(title = 'Voltage (V)')
    fig['layout']['yaxis1'].update(title = 'dQ/dV')
    fig['layout']['yaxis2'].update(title = 'dQ/dV')
    fig['layout']['height'] = 600
    fig['layout']['margin'] = {
        'l': 40,
        'r': 10,
        't': 60,
        'b': 200
        }
        #fig['layout']['yaxis'] = {'title': 'dQ/dV'}
    return fig

@app.callback( #update charge datatable
    Output('datatable', 'rows'),
    [Input('available-data', 'value'),
     #Input('upload-data', 'filename'),
     #Input('upload-data', 'last_modified')
     ])

def update_table1(filename):
    data, raw_data = pop_with_db(filename, database) 
    return data.to_dict('records')


#@app.callback(
#    Output('gen-desc-confirmation', 'children'),
#    [Input('update-model-button-button', 'n_clicks')])
#def update_output(n_clicks):
#    if n_clicks> 0:
#    	return 'Generating descriptors'
#    else:
#    	return 'Descriptors have not been generated yet.'

# #@app.callback( #decorator wrapper for plot
# #        Output('discharge-graph','figure'),
# #        [Input('cycle--slider','value'),
# #         Input('discharge-datatable','rows'),
# #         Input('discharge-datatable','selected_row_indices')]
# #        )

# @app.callback( #decorator wrapper for plot
#         Output('discharge-graph','figure'),
#         [Input('cycle--slider','value'),
#          #Input('charge-datatable','rows'),
#          Input('upload-data','contents'),
#          Input('upload-data','filename'),
#          Input('upload-data','last_modified'),
#          Input('discharge-datatable','selected_row_indices')]
#          #Input('upload-data','contents')]
#         )

# def update_figure2(selected_step,contents,filename,date,selected_row_indices):
#     data = parse_contents(contents, filename)
#     #(charge, discharge) = dbexp.ccf.sep_char_dis(data, datatype)
#     filtered_data = data[data['Cycle_Index'] == selected_step]
#     for i in filtered_data['Cycle_Index'].unique():
#         dff = filtered_data[filtered_data['Cycle_Index'] == i]
#         fig = plotly.tools.make_subplots(
#             rows=2,cols=1,
#             subplot_titles=('Smoothed dQ/dV Discharge Cycle','Cleaned dQ/dV Discharge Cycle'),
#             shared_xaxes=True)
#         marker = {'color': ['#0074D9']*len(dff)}
#         for i in (selected_row_indices or []):
#             marker['color'][i] = '#FF851B'
#         fig.append_trace({
#             'x': dff['Voltage(V)'],
#             'y': dff['Smoothed_dQ/dV'],
#             'type': 'scatter',
#             'marker': marker,
#             'name': 'Smoothed Data'
#             }, 1, 1)
#         fig.append_trace({
#             'x': dff['Voltage(V)'],
#             'y': dff['dQ/dV'],
#             'type': 'scatter',
#             'marker': marker,
#             'name': 'Raw Data'
#             }, 2, 1)
#         fig['layout']['showlegend'] = False
#         fig['layout']['height'] = 800
#         fig['layout']['margin'] = {
#             'l': 40,
#             'r': 10,
#             't': 60,
#             'b': 200
#             }
#         fig['layout']['yaxis2']
#     return fig


##########################################
#Customize CSS
##########################################
##TO DO: FORK THIS REPOSITORY (url) TO CUSTOMIZE CSS
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})


if __name__ == '__main__':
    app.run_server(debug=True)

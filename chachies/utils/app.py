import ast 
import base64
import databasewrappers as dbw
import dash
import dash_auth
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_table as dt
import io
import json
from lmfit.model import load_modelresult
from lmfit.model import save_modelresult
import numpy as np
import os
import pandas as pd
import plotly 
import urllib
import urllib.parse

from app_helper_functions import get_model_dfs
from app_helper_functions import parse_contents
from app_helper_functions import pop_with_db
from app_helper_functions import generate_model
from app_helper_functions import check_database_and_get_creds


##########################################
#Load Data
##########################################
#eventually add everything in folder and create a dropdown that loads that data sinto data 
database = 'dQdVDB_DONOTPUSH3.db'
init_db = 'init_database.db'
assert os.path.exists(init_db)	


VALID_USERNAME_PASSWORD_PAIRS = check_database_and_get_creds(database)
app = dash.Dash(__name__,
	external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css", 
							{'href': "https://codepen.io/chriddyp/pen/bWLwgP.css",
							 'rel': 'stylesheet'}]
) 

auth = dash_auth.BasicAuth(
	app,
	VALID_USERNAME_PASSWORD_PAIRS
)


##########################################
#App Layout 
##########################################


Introduction= dcc.Markdown('''
		# dQ/dV
		## Interface for visualizing battery cycle data
		#'''), 


app.layout = html.Div([
	html.Div([
		html.H1('Quantitative dQ/dV Analysis and Visualization'),
		]),

	html.Div([
		html.Br(),
		html.Div([html.H3('Choose existing data: '), 
		html.Div([html.Div([html.H6('Here are the files currently available in the database: ')],
		style={'width': '90%', 'textAlign': 'left', 'margin-left':'50px'}),
		html.Div([dcc.Dropdown(id ='available-data', options = [{'label':'options', 'value':'options'}])], style={'width': '80%', 'vertical-align':'center', 'margin-left': '50px'}),
		html.Div(id = 'gen-desc-confirmation')])], style = {'width':'43%', 'display': 'inline-block', 'vertical-align': 'top'}),

		html.Div([html.H3('Or load in your own data: '),
		html.Div([html.Div([html.H5('1. Input your datatype: ')],style={'width': '40%', 'textAlign': 'left', 'display': 'inline-block', 'margin-left':'50px'}),
				html.Div([dcc.Dropdown(id='input-datatype', 
					options =[{'label':'Arbin', 'value':'ARBIN'},{'label':'MACCOR', 'value':'MACCOR'}],  
					placeholder='datatype')], 
				style={'width': '40%', 'vertical-align':'top', 'display': 'inline-block', 
				'margin-right': '10px', 'margin-left': '10px'})],
				),

		html.Div([html.Div([html.H5('2. Upload your data: ')], style={'width': '40%', 'textAlign': 'left', 'display': 'inline-block', 'margin-left':'50px'}), 
				html.Div([dcc.Upload(
				id='upload-data',
				children=html.Div([
					'Drag and Drop or ',
					html.A('Select Files'),
					dcc.Loading(id="loading-1", children=[html.Div(id="loading-output-1")], type="default")]),
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
				multiple=False)], style= {'width': '40.2%', 'display': 'inline-block', 'margin-right': '10px', 'margin-left': '10px'}),
				html.Div(id = 'output-data-upload', style={'margin-left':'50px', 'font-size': '20px'}),
				html.Div(['Note: data will be saved in database with the original filename.'],
					style={'margin-left':'50px', 'font-style':'italic'}), 
				html.Div(['Once data is uploaded, refresh this page and select the new data from the dropdown menu to the left.'],
					style={'margin-left':'50px', 'font-style': 'italic'})],
				)], style = {'width': '55%', 'display': 'inline-block'}),
			

	]),

	html.Div([
		html.Br(),
		html.Div([html.H6('Cycle Number')], style ={'textAlign': 'left'}),
		dcc.Slider(
			id='cycle--slider',
			min=0,
			max = 15,
			value = 15,
			step=1,
			included=True,
			marks={str(each): str(each) for each in range(15)},
			),
		html.Br(),
		html.Br(),
		html.Div([html.Br()], style = {'width':'89%', 'display': 'inline-block'}),
		html.Div([dcc.RadioItems(id = 'show-model-fig1', options = [{'label': 'Show Model', 'value': 'showmodel'}, 
																	{'label': 'Hide Model', 'value': 'hidemodel'},
				], labelStyle = {'display': 'inline-block'}, value = 'showmodel')], style ={'width':'10%', 'textAlign': 'left', 'display':'inline-block'}),
		],
		style={
				'width': '98%',
				'margin': '10px',
				}
		),

	html.Div([
		html.Br(),
		dcc.Graph(id='charge-graph'), 
		],
		style={
			'columnCount': 1,
			'width':'98%',
			'height': '80%',
			}
		),
	
	html.Div([
		html.H4(['Explore Descriptors']),
	html.Div([
	html.Div(['Specify charge/discharge, locations/areas/heights, and peak number(s).'], style = {'width':'75%', 'font-style': 'italic'}),
	html.Br(), 
	dcc.RadioItems(id = 'cd-to-plot', options=[ # 'sortedloc-c-1'
			{'label': '(+) dQ/dV', 'value': 'c-'}, 
			{'label': '(-) dQ/dV', 'value': 'd-'}
		],
		value = 'c-', labelStyle={'display': 'inline-block'}),
	html.Br(),
	dcc.RadioItems(id = 'desc-to-plot', options=[
		{'label': 'Peak Locations', 'value': 'sortedloc-'}, 
		{'label': 'Peak Areas', 'value': 'sortedarea-'},
		{'label': 'Peak Height', 'value': 'sortedactheight-'},
	],
	value = 'sortedloc-', labelStyle={'display': 'inline-block'}),
	html.Br(), 
	html.Div([dcc.Checklist(id = 'desc-peaknum-to-plot', 
		options=[
			{'label': 'Peak 1', 'value': '1'}, 
			{'label': 'Peak 2', 'value': '2'},
			{'label': 'Peak 3', 'value': '3'},
			{'label': 'Peak 4', 'value': '4'},
			{'label': 'Peak 5', 'value': '5'}, 
			{'label': 'Peak 6', 'value': '6'}, 
			{'label': 'Peak 7', 'value': '7'}, 
			{'label': 'Peak 8', 'value': '8'}, 
			{'label': 'Peak 9', 'value': '9'}, 
			{'label': 'Peak 10', 'value': '10'},
		],
		value=['1'], labelStyle={'display': 'inline-block'})], style = {'width':'55%'}), 
	html.Br(),
	dcc.Checklist(id = 'show-gauss', 
	options=[
		{'label': 'Show Guassian Baseline', 'value': 'show'},
	],
	value=['show']),

	]),
	], style = {'display': 'inline-block', 'width':'49%', 'margin':'10px'}), 

	html.Div([
		html.H4(['Update Model']),
	html.Div(['New Peak Detection Threshold (default is 0.7, must be between 0 and 1): ']), 
	html.Div([dcc.Input(id = 'new-peak-threshold', placeholder = 'threshold for peak detection')]),
	html.Br(), 

	html.Div(['After updating the threshold, you can update the preview of the model'+
		' and then update the database once the model appears to be optimal.'], style={'font-style':'italic'}), 
	html.Br(), 
	html.Div(id = 'update-model-ans'),
	html.Button('Update Preview of Model', id = 'update-model-button'),
	html.Button('Update Model in Database', id = 'update-model-indb-button'),
	], style = {'display':'inline-block', 'width':'49%'}),    

	html.Div([
		html.Br(),
		dcc.Graph(id='model-graph'), 
		],style={
			'columnCount': 1,
			'width':'98%',
			'height': '80%',
			}
		),

	html.Div([
		html.A('Download Peak Descriptors CSV', download = "descriptors.csv", id = 'my-link'),
		html.H4('DataTable'),
		html.Div([dcc.RadioItems(id = 'data-table-selection', options = [{'label': 'Raw Data', 'value': 'raw_data'},
																		 {'label': 'Clean Data', 'value': 'clean_data'}, 
																		 {'label': 'Descriptors', 'value': 'descript_data'}],
																		 value = 'raw_data', labelStyle={'display': 'inline-block'},

																		 )], style = {'display': 'inline-block'}),
		dt.DataTable(
			data = [],
			selected_row_ids = [],
			filter_action = 'native',
			id='datatable'
			),
		html.Div(id='selected-indexes'),
		],
		style={
			'width': '98%',
			'margin': '10px'
			},
		), 
	html.Div(id='hidden-div', style={'display':'none'}) 
	#this is so we can have a callback to run the process data function on the raw data inputted


])

##########################################
#Interactive Parts
##########################################

@app.callback(Output('output-data-upload', 'children'),
			  [Input('upload-data', 'contents'),
			   Input('upload-data', 'filename'), 
			   Input('input-datatype', 'value')]) 

def update_output(contents, filename, value):
	#value here is the datatype, then voltagerange1, then voltagerange2
	try:
		# Windowlength and polyorder are parameters for the savitsky golay filter, could be inputs eventually
		windowlength = 9
		polyorder = 3
		if contents == None:
			return html.Div(['No file has been uploaded, or the file uploaded was empty.'])
		else: 
			content_type, content_string = contents.split(',')
			decoded = base64.b64decode(content_string)
			return html.Div([parse_contents(decoded, 
											filename, 
											value,
											database, 
											auth, 
											windowlength, 
											polyorder)])
	except Exception as e: 
		return html.Div(['There was a problem uploading that file: ' + str(e)])
	# return children

@app.callback(Output('available-data', 'options'), 
			  [Input('output-data-upload', 'children')])
def update_dropdown(children):
	username = auth._username
	options = [{'label':i, 'value':i} for i in dbw.get_db_filenames(database, username)]
	return options

@app.callback(Output('update-model-ans', 'children'), 
			  [Input('available-data', 'value'), 
			   Input('update-model-indb-button', 'n_clicks'), 
			   Input('new-peak-threshold', 'value')])
def update_model_indb(filename, n_clicks, new_peak_thresh): #new_charge_vals, new_discharge_vals,
	if n_clicks is not None:
		int_list_c = []
		int_list_d = []

		cleanset_name = filename.split('.')[0] + 'CleanSet'
		df_clean = dbw.dbfs.get_file_from_database(cleanset_name, database)
		feedback = generate_model(df_clean, filename, new_peak_thresh, database)
	else:
		feedback = html.Div(['Model has not been updated yet.'])
	return feedback


@app.callback( #update slider 
	Output('cycle--slider', 'max'),
	[Input('available-data', 'value')])

def update_slider_max(filename):
	if filename == None:
		filename = 'ExampleData'
		database_sel = init_db
	else:
		filename = filename	
		database_sel = database
	data, raw_data= pop_with_db(filename, database_sel)
	datatype = data.loc[0,('datatype')]
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)
	# slidmax = data['Cycle_Index'].max()
	return data['Cycle_Index'].max()

@app.callback(#update slider marks
	Output('cycle--slider', 'marks'), 
	[Input('available-data', 'value')])

def update_slider_marks(filename):
	if filename == None:
		filename = 'ExampleData'
		database_sel = init_db
	else:
		filename = filename	
		database_sel = database
	data, raw_data= pop_with_db(filename, database_sel)
	return {str(each): str(each) for each in data['Cycle_Index'].unique()}

@app.callback( #update slider 
	Output('cycle--slider', 'value'),
	[Input('available-data', 'value')])

def update_slider_value(filename):
	if filename == None:
		filename = 'ExampleData'
		database_sel = init_db
	else:
		filename = filename	
		database_sel = database
	data, raw_data = pop_with_db(filename, database_sel)
	datatype = data.loc[0,('datatype')]
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)

	return data['Cycle_Index'].max()



@app.callback(
		Output('datatable', 'selected_row_ids'),
		[Input('charge-graph','clickData')],
		[State('datatable','selected_row_ids')]
		)

def update_selected_row_indices(clickData, selected_row_ids):
	if clickData:
		for point in clickData['points']:
			if point['pointNumber'] in selected_row_ids:
				selected_row_ids.remove(point['pointNumber'])
			else:
				selected_row_ids.append(point['pointNumber'])
	return selected_row_ids

@app.callback( 
		Output('charge-graph','figure'),
		[Input('cycle--slider','value'),
		 Input('available-data', 'value'), 
		 Input('show-model-fig1', 'value'), 
		 Input('datatable','selected_row_ids')]
		)

def update_figure1(selected_step,filename, showmodel, selected_row_indices):
	fig = plotly.subplots.make_subplots(
	rows=1,cols=2,
	subplot_titles=('Raw Cycle','Smoothed Cycle'),
	shared_xaxes=True)
	marker = {'color': ['#0074D9']}
	if filename == None:
		filename = 'ExampleData'
		database_sel = init_db
	else:
		filename = filename	
		database_sel = database
	data, raw_data= pop_with_db(filename, database_sel)
	datatype = data.loc[0,('datatype')]
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)
	modset_name = filename.split('.')[0] + '-ModPoints'
	df_model = dbw.dbfs.get_file_from_database(modset_name, database_sel)
	if df_model is not None: 
		filt_mod = df_model[df_model[cycle_ind_col] == selected_step]

	if data is not None:
		filtered_data = data[data[cycle_ind_col] == selected_step]
	if raw_data is not None:
		raw_filtered_data= raw_data[raw_data[cycle_ind_col]== selected_step]
	
	for i in filtered_data[cycle_ind_col].unique():
		if data is not None:
			dff = filtered_data[filtered_data[cycle_ind_col] == i]
		if raw_data is not None:
			dff_raw = raw_filtered_data[raw_filtered_data[cycle_ind_col] == i]
		if df_model is not None:
			dff_mod = filt_mod[filt_mod[cycle_ind_col] == i]


		for i in (selected_row_indices or []):
			marker['color'][i] = '#FF851B'
		if data is not None:
			fig.append_trace({
				'x': dff[volt_col],
				'y': dff['Smoothed_dQ/dV'],
				'type': 'scatter',
				'marker': marker,
				'name': 'Smoothed Data'
				}, 1, 2)
		if raw_data is not None:
			fig.append_trace({
				'x': dff_raw[volt_col],
				'y': dff_raw['dQ/dV'],
				'type': 'scatter',
				'marker': marker,
				'name': 'Raw Data'
				}, 1, 1)
		if df_model is not None and showmodel == 'showmodel':   
			fig.append_trace({
				'x':dff_mod[volt_col], 
				'y':dff_mod['Model'] ,
				'type': 'scatter',
				'name': 'Model'
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
	return fig

@app.callback( 
		Output('model-graph','figure'),
		[
		 Input('available-data', 'value'), 
		 Input('new-peak-threshold', 'value'), 
		 Input('update-model-button', 'n_clicks'), 
		 Input('show-gauss', 'value'), 
		 Input('desc-to-plot', 'value'),
		 Input('cd-to-plot', 'value'), 
		 Input('desc-peaknum-to-plot', 'value')]
		)

def update_figure2(filename, peak_thresh, n_clicks, show_gauss, desc_to_plot, cd_to_plot, peaknum_to_plot):
	""" This is  a function to evaluate the model on a sample plot before updating the database"""
	if filename == None:
		filename = 'ExampleData'
		database_sel = init_db
	else:
		filename = filename	
		database_sel = database
	data, raw_data= pop_with_db(filename, database_sel)
	datatype = data.loc[0,('datatype')]
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, \
		char_cap_col, charge_or_discharge) = dbw.ccf.col_variables(datatype)
	selected_step = round(data[cycle_ind_col].max()/2) +1 
	# select a cycle in the middle of the set
	dff_data= data[data[cycle_ind_col] == selected_step]
	if len(data[cycle_ind_col].unique())>1:
		lenmax = max([len(data[data[cycle_ind_col]==cyc]) \
					   for cyc in data[cycle_ind_col].unique() if cyc != 1])
	else:
		lenmax = len(data)
	dff_raw = raw_data[raw_data[cycle_ind_col]==selected_step]
	peak_vals_df = dbw.dbfs.get_file_from_database(filename.split('.')[0] + '-descriptors',database_sel)

	fig = plotly.subplots.make_subplots(
		rows=1,cols=2,
		subplot_titles=('Descriptors','Example Data for Model Tuning (Cycle ' + str(int(selected_step)) + ')'),
		shared_xaxes=True)
	marker = {'color': ['#0074D9']}
	if peak_vals_df is not None: 
		if n_clicks is not None:
			# if the user has hit the update-model-button - remake model
			new_df_mody, model_c_vals, model_d_vals,\
				peak_heights_c, peak_heights_d = get_model_dfs(dff_data, datatype, selected_step, lenmax, peak_thresh)
			dff_mod = new_df_mody
			c_sigma = model_c_vals['base_sigma']
			c_center = model_c_vals['base_center']
			c_amplitude= model_c_vals['base_amplitude']
			c_fwhm = model_c_vals['base_fwhm']
			c_height = model_c_vals['base_height']

			d_sigma = model_d_vals['base_sigma']
			d_center = model_d_vals['base_center']
			d_amplitude= model_d_vals['base_amplitude']
			d_fwhm = model_d_vals['base_fwhm']
			d_height = model_d_vals['base_height']
		else: 
			# if user hasn't pushed the button, populate with original model from database
			modset_name = filename.split('.')[0] + '-ModPoints'
			df_model = dbw.dbfs.get_file_from_database(modset_name, database_sel)
			dff_mod = df_model[df_model[cycle_ind_col] == selected_step]

			filtpeakvals = peak_vals_df[peak_vals_df['c_cycle_number'] == selected_step]
			filtpeakvals = filtpeakvals.reset_index(drop = True)
			# grab values for the underlying gaussian in the charge: 
			c_sigma = filtpeakvals.loc[0,('c_gauss_sigma')]
			c_center = filtpeakvals.loc[0, ('c_gauss_center')]
			c_amplitude = filtpeakvals.loc[0, ('c_gauss_amplitude')]
			c_fwhm = filtpeakvals.loc[0, ('c_gauss_fwhm')]
			c_height = filtpeakvals.loc[0, ('c_gauss_height')]
			# grab values for the underlying discharge gaussian: 
			d_sigma = filtpeakvals.loc[0,('d_gauss_sigma')]
			d_center = filtpeakvals.loc[0, ('d_gauss_center')]
			d_amplitude = filtpeakvals.loc[0, ('d_gauss_amplitude')]
			d_fwhm = filtpeakvals.loc[0, ('d_gauss_fwhm')]
			d_height = filtpeakvals.loc[0, ('d_gauss_height')]
			
		fig.append_trace({
			'x': dff_data[volt_col],
			'y': dff_data['Smoothed_dQ/dV'],
			'type': 'scatter',
			'marker': marker,
			'name': 'Smoothed Data'
			}, 1, 2)
		if len(peaknum_to_plot) > 0:
			for value in peaknum_to_plot: 
				try: 
					fig.append_trace({
						'x': peak_vals_df['c_cycle_number'],
						'y': peak_vals_df[str(''.join(desc_to_plot)) + str(''.join(cd_to_plot)) + value],
						'type': 'scatter',
						'marker': marker,
						'name': value 
						}, 1, 1)
				except KeyError as e:
					print('User attempted to plot descriptors for more peaks than are in the data set.')
		   
		fig.append_trace({
			'x':dff_mod[volt_col], 
			'y':dff_mod['Model'] ,
			'type': 'scatter',
			'name': 'Model of One Cycle'
			}, 1,2)
	   # add if checkbox is selected to show polynomial baseline 
		if 'show' in show_gauss: 
			fig.append_trace({
				'x': dff_mod[volt_col],
				'y': ((c_amplitude/(c_sigma*((2*3.14159)**0.5)))*np.exp((-(dff_mod[volt_col] - c_center)**2)/(2*c_sigma**2))),
				'type': 'scatter',
				'name':'Charge Gaussian Baseline' # plot the poly
				}, 1,2)
			# add the plot of the discharge guassian:
			fig.append_trace({
				'x': dff_mod[volt_col],
				'y': -((d_amplitude/(d_sigma*((2*3.14159)**0.5)))*np.exp((-(dff_mod[volt_col] - d_center)**2)/(2*d_sigma**2))),
				'type': 'scatter',
				'name':'Discharge Gaussian Baseline' # plot the poly
				}, 1,2)

	fig['layout']['showlegend'] = True
	fig['layout']['xaxis1'].update(title = 'Cycle Number')
	fig['layout']['xaxis2'].update(title = 'Voltage (V)')
	fig['layout']['yaxis1'].update(title = 'Descriptor Value')
	fig['layout']['yaxis2'].update(title = 'dQ/dV', range = [dff_data['Smoothed_dQ/dV'].min(), dff_data['Smoothed_dQ/dV'].max()])
	fig['layout']['height'] = 600
	fig['layout']['margin'] = {
		'l': 40,
		'r': 10,
		't': 60,
		'b': 200
		}
	return fig

@app.callback(Output('my-link', 'href'),
			  [Input('available-data', 'value')])
def update_link(value):
	if value is not None: 
		peak_vals_df = dbw.dbfs.get_file_from_database(value.split('.')[0] + '-descriptors', database)
		if peak_vals_df is not None: 
			csv_string = peak_vals_df.to_csv(index = False, encoding = 'utf-8')
		else: 
			# return an empty dataframe
			csv_string = pd.DataFrame().to_csv(index = False, encoding = 'utf-8')
		csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
		return csv_string

@app.callback( 
	Output('datatable', 'data'),
	[Input('available-data', 'value'),
	 Input('data-table-selection', 'value'),
	 ])

def update_table1(filename, data_to_show):
	if filename == None:
		filename = 'ExampleData'
		database_sel = init_db
	else:
		filename = filename	
		database_sel = database
	data, raw_data = pop_with_db(filename, database_sel)
	peak_vals_df = dbw.dbfs.get_file_from_database(filename.split('.')[0] + '-descriptors',database_sel)
	if data_to_show == 'raw_data':
		return raw_data.to_dict('records')
	elif data_to_show == 'clean_data':
		return data.to_dict('records')
	elif data_to_show == 'descript_data':
		if peak_vals_df is not None: 
			return peak_vals_df.to_dict('records')
		else: 
			return pd.DataFrame().to_dict('records')
	else: 
		return data.to_dict('records')


##########################################
#Customize CSS
##########################################

# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

if __name__ == '__main__':
	#server.run(debug=True)
	app.run_server(debug=True)
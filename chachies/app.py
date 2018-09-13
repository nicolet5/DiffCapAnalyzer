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
#from unittest.mock import patch
##########################################
#Load Data
##########################################
#eventually add everything in folder and create a dropdown that loads that data into data 
database = 'dqdvDataBase_0912APP_2.db'
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
    
    html.Div([dcc.Dropdown(id ='available-data',
    					   options = 'options')]),

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
    
    html.Button('Find Descriptors', id = 'get-descript-button'),
	html.Div(id = 'gen-desc-confirmation'),

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
    try: 
    	cleanset_name = filename.split('.')[0] + 'CleanSet'
    	#this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
    		#check to see if the database exists, and if it does, check if the file exists.
    	ans = dbexp.if_file_exists_in_db(database, filename)
    	if ans == True: 
    		return html.Div(['That file exists in the database: ' + str(filename.split('.')[0])])
    		#df = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    	else:
    		dbexp.process_data(filename, database, decoded, datatype, thresh1, thresh2)
    		# maybe split the process data function into getting descriptors as well?
    		#since that is the slowest step 
    		return html.Div(['New file has been processed: ' + str(filename)])
    		
    		#df = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    	#have to pass decoded to it so it has the contents of the file

    except Exception as e:
        print('THERE WAS A PROBLEM PROCESSING THE FILE: ' + str(e))
        #df = None
        return html.Div([
            'There was an error processing this file.'+ str(filename)
        ])
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
    #this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
    ans = dbexp.if_file_exists_in_db(database, filename)
    print(ans)
    if ans == True: 
    	# then the file exists in the database and we can just read it 
    	df = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    else:
    	df = None
    return df

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
# Make this app callback from a drop down menu selecting a filename in the database
# populate dropdown using master_table column= Dataset_Name


@app.callback( #update charge datatable
    Output('datatable', 'rows'),
    [Input('available-data', 'value'),
     #Input('upload-data', 'filename'),
     #Input('upload-data', 'last_modified')
     ])

def update_table1(filename):
    data = pop_with_db(filename, database) 
    return data.to_dict('records')

@app.callback( #update slider 
    Output('cycle--slider', 'max'),
    [Input('available-data', 'value')])

def update_slider_max(filename):
    data = pop_with_db(filename, database)
    #charge, discharge = dbexp.ccf.sep_char_dis(data, datatype)
    datatype = data.loc[0,('datatype')]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    slidmax = data['Cycle_Index'].max()
    return data['Cycle_Index'].max()

@app.callback(#update slider marks
	Output('cycle--slider', 'marks'), 
	[Input('available-data', 'value')])

def update_slider_marks(filename):
	data = pop_with_db(filename, database)
	return {str(each): str(each) for each in data['Cycle_Index'].unique()}

@app.callback( #update slider 
    Output('cycle--slider', 'value'),
    [Input('available-data', 'value')])

def update_slider_value(filename):
    data = pop_with_db(filename, database)
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
    data = pop_with_db(filename, database)
    #(charge, discharge) = dbexp.ccf.sep_char_dis(data, datatype)
    # grab datattype from file:
    datatype = data.loc[0,('datatype')]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)

    filtered_data = data[data[cycle_ind_col] == selected_step]
    for i in filtered_data[cycle_ind_col].unique():
        dff = filtered_data[filtered_data[cycle_ind_col] == i]
        fig = plotly.tools.make_subplots(
            rows=1,cols=2,
            subplot_titles=('Cleaned dQ/dV Charge Cycle','Smoothed dQ/dV Charge Cycle'),
            shared_xaxes=True)
        marker = {'color': ['#0074D9']}
        for i in (selected_row_indices or []):
            marker['color'][i] = '#FF851B'
        fig.append_trace({
            'x': dff[volt_col],
            'y': dff['dQ/dV'],
            'type': 'scatter',
            'marker': marker,
            'name': 'Cleaned Data'
            }, 1, 1)
        fig.append_trace({
            'x': dff[volt_col],
            'y': dff['Smoothed_dQ/dV'],
            'type': 'scatter',
            'marker': marker,
            'name': 'Smoothed Data'
            }, 1, 2)
        fig['layout']['showlegend'] = False
        fig['layout']['height'] = 600
        fig['layout']['margin'] = {
            'l': 40,
            'r': 10,
            't': 60,
            'b': 200
            }
        fig['layout']['yaxis'] = {'title': 'dQ/dV'}
    return fig

@app.callback(
    Output('gen-desc-confirmation', 'children'),
    [Input('get-descript-button', 'n_clicks')])
def update_output(n_clicks):
    if n_clicks> 0:
    	return 'Generating descriptors'
    else:
    	return 'Descriptors have not been generated yet.'

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

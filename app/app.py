import chachifuncs as ccf
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_table_experiments as dt
import pandas as pd
import io
import json
import plotly 
import base64

##########################################
#Load Data
##########################################
#eventually add everything in folder and create a dropdown that loads that data into data 

#for now just use some data we have 
data = pd.read_excel('data/Clean_Whole_Sets/CS2_33_12_16_10CleanSet.xlsx')

charge, discharge = ccf.sep_char_dis(data)

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
        ]),
        
    
    html.Div([
        html.Br(),
        dcc.Slider(
            id='cycle--slider',
            min=0,
            #min=charge['Cycle_Index'].min(),
            max=charge['Cycle_Index'].max(),
            #value=charge['Cycle_Index'].max(),
            #max=[],
            value=charge['Cycle_Index'].max(),
            step=1,
            included=True,
            marks={str(each): str(each) for each in charge['Cycle_Index'].unique()} #includes a mark for each step
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
        html.Br(),
        dcc.Graph(id='discharge-graph'),
        ],style={
            'columnCount': 2,
            'width':'98%',
            'height': '80%',
            }
        ),
    
    html.Div([
        html.H4('Charge DataTable'),
        dt.DataTable(
            #rows=charge.to_dict('records'), #converts df to dict
            rows=[{}],
            #columns=sorted(charge.columns), #sorts columns
            row_selectable=True,
            filterable=True,
            selected_row_indices=[],
            id='charge-datatable'
            ),
        html.Div(id='selected-indexes'),

        html.H4('Discharge DataTable'),
        dt.DataTable(
            #rows=discharge.to_dict('records'), #converts df to dict
            rows=[{}],
            #columns=sorted(discharge.columns), #sorts columns
            row_selectable=True,
            filterable=True,
            selected_row_indices=[],
            id='discharge-datatable'
            ),
        html.Div(id='selected-indexes'),
        ],
        style={
            'width': '98%',
            #'height': '60px',
            #'lineHeight': '60px',
            'margin': '10px'
            },
        )

])

##########################################
#Interactive Parts
##########################################

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return df 

@app.callback( #update charge datatable
    Output('charge-datatable', 'rows'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('upload-data', 'last_modified')])

def update_table1(contents, filename, date):
    data = parse_contents(contents, filename, date) 
    charge, discharge = ccf.sep_char_dis(data)
    return charge.to_dict('records')

@app.callback( #update discharge datatable
    Output('discharge-datatable', 'rows'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('upload-data', 'last_modified')])

def update_table2(contents, filename, date):
    data = parse_contents(contents, filename, date)
    charge, discharge = ccf.sep_char_dis(data)
    return discharge.to_dict('records')

@app.callback( #update slider 
    Output('cycle--slider', 'max'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('upload-data', 'last_modified')])

def update_slider_max(contents, filename, date):
    data = parse_contents(contents, filename, date)
    charge, discharge = ccf.sep_char_dis(data)
    return charge['Cycle_Index'].max()

@app.callback( #update slider 
    Output('cycle--slider', 'value'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('upload-data', 'last_modified')])

def update_slider_value(contents,filename,date):
    data = parse_contents(contents, filename, date)
    charge, discharge = ccf.sep_char_dis(data)
    return charge['Cycle_Index'].max()

@app.callback( #decorator wrapper for table 
        Output('charge-datatable', 'selected_row_indices'), #component_id, component_property 
        [Input('charge-graph','clickData')],
        [State('charge-datatable','selected_row_indices')]
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
         #Input('charge-datatable','rows'),
         Input('upload-data','contents'),
         Input('upload-data', 'filename'),
         Input('upload-data', 'last_modified'),
         Input('charge-datatable','selected_row_indices')]
         #Input('upload-data','contents')]
        )

def update_figure1(selected_step,contents,filename,date,selected_row_indices):
    data = parse_contents(contents, filename, date)
    (charge, discharge) = ccf.sep_char_dis(data)
    filtered_data = charge[charge['Cycle_Index'] == selected_step]
    for i in filtered_data['Cycle_Index'].unique():
        dff = filtered_data[filtered_data['Cycle_Index'] == i]
        fig = plotly.tools.make_subplots(
            rows=2,cols=1,
            subplot_titles=('Smoothed dQ/dV Charge Cycle','Cleaned dQ/dV Charge Cycle'),
            shared_xaxes=True)
        marker = {'color': ['#0074D9']}
        for i in (selected_row_indices or []):
            marker['color'][i] = '#FF851B'
        fig.append_trace({
            'x': dff['Voltage(V)'],
            'y': dff['Smoothed_dQ/dV'],
            'type': 'scatter',
            'marker': marker,
            'name': 'Smoothed Data'
            }, 1, 1)
        fig.append_trace({
            'x': dff['Voltage(V)'],
            'y': dff['dQ/dV'],
            'type': 'scatter',
            'marker': marker,
            'name': 'Raw Data'
            }, 2, 1)
        fig['layout']['showlegend'] = False
        fig['layout']['height'] = 800
        fig['layout']['margin'] = {
            'l': 40,
            'r': 10,
            't': 60,
            'b': 200
            }
        fig['layout']['yaxis2']
    return fig

#@app.callback( #decorator wrapper for plot
#        Output('discharge-graph','figure'),
#        [Input('cycle--slider','value'),
#         Input('discharge-datatable','rows'),
#         Input('discharge-datatable','selected_row_indices')]
#        )

@app.callback( #decorator wrapper for plot
        Output('discharge-graph','figure'),
        [Input('cycle--slider','value'),
         #Input('charge-datatable','rows'),
         Input('upload-data','contents'),
         Input('upload-data','filename'),
         Input('upload-data','last_modified'),
         Input('discharge-datatable','selected_row_indices')]
         #Input('upload-data','contents')]
        )

def update_figure2(selected_step,contents,filename,date,selected_row_indices):
    data = parse_contents(contents, filename, date)
    (charge, discharge) = ccf.sep_char_dis(data)
    filtered_data = discharge[discharge['Cycle_Index'] == selected_step]
    for i in filtered_data['Cycle_Index'].unique():
        dff = filtered_data[filtered_data['Cycle_Index'] == i]
        fig = plotly.tools.make_subplots(
            rows=2,cols=1,
            subplot_titles=('Smoothed dQ/dV Discharge Cycle','Cleaned dQ/dV Discharge Cycle'),
            shared_xaxes=True)
        marker = {'color': ['#0074D9']*len(dff)}
        for i in (selected_row_indices or []):
            marker['color'][i] = '#FF851B'
        fig.append_trace({
            'x': dff['Voltage(V)'],
            'y': dff['Smoothed_dQ/dV'],
            'type': 'scatter',
            'marker': marker,
            'name': 'Smoothed Data'
            }, 1, 1)
        fig.append_trace({
            'x': dff['Voltage(V)'],
            'y': dff['dQ/dV'],
            'type': 'scatter',
            'marker': marker,
            'name': 'Raw Data'
            }, 2, 1)
        fig['layout']['showlegend'] = False
        fig['layout']['height'] = 800
        fig['layout']['margin'] = {
            'l': 40,
            'r': 10,
            't': 60,
            'b': 200
            }
        fig['layout']['yaxis2']
    return fig


##########################################
#Customize CSS
##########################################
##TO DO: FORK THIS REPOSITORY (url) TO CUSTOMIZE CSS
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})


if __name__ == '__main__':
    app.run_server(debug=True)

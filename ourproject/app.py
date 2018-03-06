import chachifuncs as ccf
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_html_components as html
import pandas as pd

##########################################
#Load Data
##########################################

#d = ccf.get_data('data/CS2_33/') #this is super slow 
#data = d['CS2_33_8_19_10'] #working with sample data to get structure up 

#or now just use some data we have 
data = pd.read_excel('data/CS2_33/CS2_33_10_04_10.xlsx',1)


##########################################
#App Layout 
##########################################
app = dash.Dash() #initialize 

app.layout = html.Div(children=[
    html.H1(children='''ChaChi's'''), #Header 
    
    html.Div(children='''
        Interface for visualizing battery cycle data 
    '''), #Subheader

    dcc.Dropdown( #create a dropdown menu 
        id='my-dropdown',
        options=[
            {'label': 'Data Point', 'value': 'Data_Point'},
            {'label': 'Test Time(s)', 'value': 'Test_Time(s)'},
            {'label': 'Date Time(yyyy-mm-dd hh:mm:ss', 'value': 'Date_Time'},
            {'label': 'Step Time(s)', 'value': 'Step_Time(s)'},
            {'label': 'Step Index', 'value': 'Step_Index'},
            {'label': 'Cycle Index', 'value': 'Cycle_Index'},
            {'label': 'Current (A)', 'value': 'Current(A)'},
            {'label': 'Voltage (A)', 'value': 'Voltage(A)'},
            {'label': 'Charge Capacity (Ah)', 'value': 'Charge_Capacity(Ah)'},
            {'label': 'Discharge Capacity (Ah)', 'value': 'Discharge_Capacity(Ah)'},
            {'label': 'Charge Energy (Wh)', 'value': 'Charge_Energy(Wh)'},
            {'label': 'Discharge Energy (Wh)', 'value': 'Discharge_Energy(Wh)'},
            {'label': 'dV/dt (V/s)', 'value': 'dV/dt (V/s)'},
            {'label': 'Internal Resistance (Ohm)', 'value': 'Internal_Resistance(Ohm)'}
            ],
        value='Data_Point' #initialize something to plot 
        ),

    dcc.Graph(id='my-graph'), #initialize a simple plot 

    html.H4(children='Preview Data'),
    ccf.generate_table(data)

])

##########################################
#Interactive Parts
##########################################

@app.callback(
        Output(component_id='my-graph', component_property='figure'),
        [Input(component_id='my-dropdown', component_property='value')]
        )

def update_graph(selected_dropdown_value):
    df = web.DataReader(
            selected_dropdown_value, data_source='CALCE'
            )
    return { 
            'data':[{
                'x': df.index,
                'y': df.Close
                }]
            } 

##########################################
#Customize CSS
##########################################
##TO DO: FORK THIS REPOSITORY (url) TO CUSTOMIZE CSS
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})


if __name__ == '__main__':
    app.run_server(debug=True)

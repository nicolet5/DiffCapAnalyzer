import chachifuncs as ccf
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go

##########################################
#Load Data
##########################################

#d = ccf.get_data('data/CS2_33/') #this is super slow 
#data = d['CS2_33_8_19_10'] #working with sample data to get structure up 

#or now just use some data we have 
data = pd.read_excel('../data/CS2_33/CS2_33_10_04_10.xlsx',1)

available_indicators = data.columns.unique() #load in column names 

##########################################
#App Layout 
##########################################
app = dash.Dash() #initialize 

app.layout = html.Div([
    html.H1('ChaChi'), #Header 
    
    html.H3(children='Interface for visualizing battery cycle data'), #Subheader

    html.Div([
        dcc.Dropdown( #create a dropdown menu for xaxis 
            id='xaxis-column',
            options=[{'label': i, 'value':i} for i in available_indicators],
            value=['Voltage(A)'], #initialize something to plot 
            #multi=True
        )
    ],
    #insert style preferences here
    ),

    html.Div([
        dcc.Dropdown( #create a dropdown menu for yaxis
            id='yaxis-column',
            options=[{'label': i, 'value':i} for i in available_indicators],
            value=['Current(A)'], #initialize something to plot
        )
    ]
    #insert style preferences here
    ),

    dcc.Graph(id='my-graph'), #initialize a simple plot 

    dcc.Slider(
        id='step--slider',
        min=data['Step_Time(s)'].min(),
        max=data['Step_Time(s)'].max(),
        value=data['Step_Time(s)'].max(),
        step=1000,
        #marks={str(each): str(each) for each in data['Step_Time(s)'].unique()} #includes a mark for each step
        )

    #html.H4(children='Preview Data'), #generate a table 
    #ccf.generate_table(data,5)
    #I want to have this change based on choice of data 
])

##########################################
#Interactive Parts
##########################################

@app.callback( #decorator wrapper to call input/outputs 
        Output('my-graph', 'figure'), #component_id, component_property 
        [Input('xaxis-column', 'value'),
            Input('yaxis-column', 'value'),
            Input('step--slider','value')]
        )

def update_graph(xaxis_column_name, yaxis_column_name, step_time):
    
    dff = data[data['Step_Time(s)'] == step_time]

    return { 
        'data': [go.Scatter(
            x=dff[dff['Indicator Name'] == xaxis_column_name]['Value'],
            y=dff[dff['Indicator Name'] == yaxis_column_name]['Value'],
            #text=dff[dff['Indicator Name'] == yaxis_column_name]['Voltage(A)'], #adds text to hover
            mode='markers',
            marker={
                'size': 15,
                'opacity': 0.5,
                'line': {'width': 0.5, 'color': 'white'}
                }
            )],
            #'layout': go.Layout(
            #xaxis={
            #    'title': xaxis_column_name,
            #    'type': 'linear' if xaxis_type == 'Linear' else 'log'
            #},
            #yaxis={
            #    'title': yaxis_column_name,
            #    'type': 'linear' if yaxis_type == 'Linear' else 'log'
            #},
            #margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
            #hovermode='closest'
        #)
    }


##########################################
#Customize CSS
##########################################
##TO DO: FORK THIS REPOSITORY (url) TO CUSTOMIZE CSS
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})


if __name__ == '__main__':
    app.run_server(debug=True)

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

available_indicators = [str(each) for each in data.columns.unique()] #load in column names for dropdown 

##########################################
#App Layout 
##########################################
app = dash.Dash() #initialize dash 

app.layout = html.Div([
    html.Div([
        html.H1('ChaChi'), #Header

        html.H3('Interface for visualizing battery cycle data'), #Subheader
        ]),

    html.Div([
        dcc.Dropdown(
            id='yaxis-column',
            options=[{'label': i,'value': i} for i in available_indicators],
            value='Voltage(V)'
            )],
        style={'width': '48%', 'display': 'inline-block'}),

    html.Div([
        dcc.Dropdown(
            id='xaxis-column',
            options=[{'label': i,'value': i} for i in available_indicators],
            value='Current(A)'
            )],
        style={'width': '48%', 'float': 'right', 'display': 'inline-block'}),
    
    html.Div([
         dcc.Graph( #initialize a simple plot 
             id='my-graph',
             ),

         dcc.Slider(
            id='cycle--slider',
            min=data['Cycle_Index'].min(),
            max=data['Cycle_Index'].max(),
            value=data['Cycle_Index'].max(),
            step=1,
            marks={str(each): str(each) for each in data['Cycle_Index'].unique()} #includes a mark for each step
            ),
         ]),


    html.Div([
        html.H5('Preview Data'), #generate a table 
        ccf.generate_table(data,5)
    #I want to also have this change based on choice of data 
    ],
    style={'width': '49%', 'display': 'inline-block'})
])

##########################################
#Interactive Parts
##########################################

@app.callback( #decorator wrapper to call input/outputs 
        Output('my-graph', 'figure'), #format is component_id, component_property 
        [Input('xaxis-column', 'value'),
        Input('yaxis-column', 'value'),
        Input('cycle--slider','value')]
        )

def update_figure(xaxis_column_name,yaxis_column_name,selected_step):
    filtered_data = data[data['Cycle_Index'] == selected_step]
    
    traces = []
    
    for i in filtered_data['Cycle_Index'].unique():
        data_by_cycle = filtered_data[filtered_data['Cycle_Index'] == i]
        traces.append(go.Scatter(
            x=data_by_cycle['Voltage(V)'],
            y=data_by_cycle['Current(A)'],
            mode='markers',
            name=i
        ))

    return {
            'data':traces,
            'layout': go.Layout(
                xaxis={'title': xaxis_column_name},
                yaxis={'title': yaxis_column_name},
                legend={'x':0,'y':1},
                hovermode='closest'
            )
    }

##########################################
#Customize CSS
##########################################
##TO DO: FORK THIS REPOSITORY (url) TO CUSTOMIZE CSS
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})


if __name__ == '__main__':
    app.run_server(debug=True)

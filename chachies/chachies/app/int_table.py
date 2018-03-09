import chachifuncs as ccf
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_table_experiments as dt
import pandas as pd
import plotly.graph_objs as go
import plotly

##########################################
#Load Data
##########################################

#d = ccf.get_data('data/CS2_33/') #this is super slow 
#data = d['CS2_33_8_19_10'] #working with sample data to get structure up 

#or now just use some data we have 
data = pd.read_excel('../data/CS2_33/CS2_33_10_04_10.xlsx',1)

#available_indicators = data.columns.unique() #load in column names for dropdown 

##########################################
#App Layout 
##########################################
app = dash.Dash() #initialize dash 

app.layout = html.Div([
    html.H1('ChaChi'), #Header

    html.H3('Interface for visualizing battery cycle data'), #Subheader

    dcc.Graph(id='my-graph'), #initialize a simple plot 

    dcc.Slider(
        id='cycle--slider',
        min=data['Cycle_Index'].min(),
        max=data['Cycle_Index'].max(),
        value=data['Cycle_Index'].max(),
        step=1,
        marks={str(each): str(each) for each in data['Cycle_Index'].unique()} #includes a mark for each step
        ),
    

    html.H5('Data Table'), #generate a table 
    dt.DataTable(
        rows=data.to_dict('records'), #convert df to dict
        columns=sorted(data.columns),
        row_selectable=True,
        filterable=True,
        selected_row_indices=[],
        id='datatable-cycledata'
        ),
    html.Div(id='selected-indexes')
    #ccf.generate_table(data,5)
    #I want to also have this change based on choice of data 
], className='container')

##########################################
#Interactive Parts
##########################################

@app.callback( #decorator wrapper for table
        Output('datatable-cycledata','selected_row_indices'), #component_id, component_property
        [Input('my-graph','clickData')],
        [State('datatable-cycledata','selected_row_indices')])

def update_selected_row_indices(clickData, selected_row_indices):
    if clickData:
        for point in clickData['points']:
            if point['pointNumber'] in selected_row_indices:
                selected_row_indices.remove(point['pointNumber'])
            else:
                selected_row_indices.append(point['pointNumber'])
    return selected_row_indices

@app.callback( #decorator wrapper for graph 
        Output('my-graph', 'figure'), 
        [Input('cycle--slider','value'),
        Input('datatable-cycledata', 'rows'),
        Input('datatable-cycledata', 'selected_row_indices')]
        )

def update_figure(selected_step,rows,selected_row_indices):
    filtered_data = data[data['Cycle_Index'] == selected_step]
    dff=pd.DataFrame(rows)
    #fig = []
    for i in filtered_data['Cycle_Index'].unique():
        dff = filtered_data[filtered_data['Cycle_Index'] == i]
        fig=plotly.tools.make_subplots(
            rows=2, cols=1,
            subplot_titles=('dQ/dV','Voltage/Current')),
            #shared_yaxes=True),
        marker = {'color': ['#0074D9']*len(dff)}
        for i in (selected_row_indices or []):
            marker['color'][i] = '#FF851B'
        fig.append_trace({
            'x': dff['Voltage(V)'],
            'y': dff['Current(A)'],
            'type': 'bar',
            'marker': marker
        }, 1, 1)
        fig.append_trace({
            'x': dff['Voltage(V)'],
            'y': dff['Discharge_Capacity(Ah)'],
            'type': 'bar',
            'marker': marker
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

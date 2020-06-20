import ast
import base64
import dash
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

from diffcapanalyzer.app_helper_functions import parse_contents
from diffcapanalyzer.app_helper_functions import pop_with_db
from diffcapanalyzer.chachifuncs import col_variables
from diffcapanalyzer.databasewrappers import get_db_filenames, get_filename_pref
from diffcapanalyzer.databasefuncs import get_file_from_database
from diffcapanalyzer.databasefuncs import init_master_table
from diffcapanalyzer.descriptors import generate_model
from diffcapanalyzer.descriptors import get_model_dfs



database = "data/databases/dQdV.db"
init_db = "data/databases/init_database.db"

assert os.path.exists(init_db)
if not os.path.exists(database):
    init_master_table(database)

app = dash.Dash(__name__,
                external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css",
                                      {'href': "https://codepen.io/chriddyp/pen/bWLwgP.css",
                                       'rel': 'stylesheet'}])

##########################################
# App Layout
##########################################


Introduction = dcc.Markdown('''
		# dQ/dV
		## Interface for visualizing battery cycle data
		#'''),


app.layout = html.Div([
    html.Div([
        html.H1('Differential Capacity Analyzer')
    ]),

    html.Div([
        html.Div([html.H5('Choose existing data: '),
                  html.Div([html.Div([html.H6('Here are the files currently available in the database: ')],
                                     style={'width': '90%', 'textAlign': 'left', 'margin-left': '50px'}),
                            html.Div([dcc.Dropdown(id='available-data',
                                                   options=[{'label': 'options',
                                                             'value': 'options'}])],
                                     style={'width': '80%',
                                            'vertical-align': 'center',
                                            'margin-left': '50px'}),
                            html.Div(id='gen-desc-confirmation')])], style={'width': '43%', 'display': 'inline-block', 'vertical-align': 'top'}),

        html.Div([html.H5('Or load in your own data: '),
                  html.Div([html.Div([html.H6('1. Input your datatype: ')], style={'width': '40%', 'textAlign': 'left', 'display': 'inline-block', 'margin-left': '50px'}),
                            html.Div([dcc.Dropdown(id='input-datatype',
                                                   options=[{'label': 'Arbin', 'value': 'ARBIN'}, {
                                                       'label': 'MACCOR', 'value': 'MACCOR'}],
                                                   placeholder='datatype')],
                                     style={'width': '40%', 'vertical-align': 'top', 'display': 'inline-block',
                                            'margin-right': '10px', 'margin-left': '10px'})],
                           ),

                  html.Div([html.Div([html.H6('2. Upload your data: ')], style={'width': '40%', 'textAlign': 'left', 'display': 'inline-block', 'margin-left': '50px'}),
                            html.Div([dcc.Upload(
                                id='upload-data',
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select Files')]),
                                style={
                                    'width': '98%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    # 'margin': '10px'
                                },
                                multiple=False)], style={'width': '40.2%', 'display': 'inline-block', 'margin-right': '10px', 'margin-left': '10px'}),
                            html.Div([dcc.Loading(id="loading-1",
                                                  children=[
                                                      html.Div(id='output-data-upload')],
                                                  type="default")],
                                     style={'margin-left': '50px',
                                            'font-size': '20px'}),
                            html.Div(['Note: data will be saved in database with the original filename.'],
                                     style={'margin-left': '50px', 'font-style': 'italic'}),
                            html.Div(['Once data is uploaded, select the new data from the dropdown menu to the left (refresh the page if necessary).'],
                                     style={'margin-left': '50px', 'font-style': 'italic'})],
                           )], style={'width': '55%', 'display': 'inline-block'}),


    ]),

    html.Div([
        html.Div([html.H6('Cycle Number')], style={'textAlign': 'left'}),
        dcc.Loading(id="loading-2", children=[dcc.Slider(
            id='cycle--slider',
            min=0,
            max=15,
            value=15,
            step=1,
            included=True,
            marks={str(each): str(each) for each in range(15)},
        )]),
        html.Div([html.Br()], style={
                 'width': '89%', 'display': 'inline-block'}),
        html.Br(),
        html.Div([dcc.RadioItems(id='show-model-fig1', options=[{'label': 'Show Model', 'value': 'showmodel'},
                                                                {'label': 'Hide Model',
                                                                    'value': 'hidemodel'},
                                                                ], labelStyle={'display': 'inline-block'}, value='showmodel')], style={'width': '10%', 'textAlign': 'left', 'display': 'inline-block'}),
    ],
        style={
        'width': '98%',
        'margin': '10px',
    }
    ),

    html.Div([
        dcc.Graph(id='charge-graph'),
    ],
        style={
        'columnCount': 1,
        'width': '98%',
        'height': '80%',
    }
    ),

    html.Div([
        html.Div([
            html.H4(['Explore Descriptors']),
            html.Div([
                html.Div(
                    ['Specify charge/discharge, locations/areas/heights, and peak number(s).'],
                    style={
                        'width': '75%',
                        'font-style': 'italic'}),
                dcc.RadioItems(id='cd-to-plot', options=[
                    {'label': '(+) dQ/dV', 'value': 'c-'},
                    {'label': '(-) dQ/dV', 'value': 'd-'}
                ],
                    value='c-', labelStyle={'display': 'inline-block'}),
                dcc.RadioItems(id='desc-to-plot', options=[
                    {'label': 'Peak Locations', 'value': 'sortedloc-'},
                    {'label': 'Peak Areas', 'value': 'sortedarea-'},
                    {'label': 'Peak Height', 'value': 'sortedactheight-'},
                ],
                    value='sortedloc-', labelStyle={'display': 'inline-block'}),
                html.Div([dcc.Checklist(id='desc-peaknum-to-plot',
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
                                        value=['1'], labelStyle={'display': 'inline-block'})], style={'width': '80%'}),

            ]),
            html.Br(),
            html.Br(),
        ], style={'display': 'inline-block', 'width': '49%', 'margin': '10px'}),

        html.Div([
            html.H4(['Update Model']),
            html.Div(
                ['New Peak Detection Threshold (default is 0.7, must be between 0 and 1): ']),
            html.Div([dcc.Input(id='new-peak-threshold',
                                placeholder='threshold for peak detection')]),

            html.Div(['After updating the threshold, you can update the preview of the model' +
                      ' and then update the database once the model appears to be optimal.'], style={'font-style': 'italic'}),
            html.Div(id='update-model-ans'),
            html.Button('Update Preview of Model', id='update-model-button'),
            html.Button(
                'Update Model in Database',
                id='update-model-indb-button'),
            html.Div([dcc.Checklist(id='show-gauss',
                                    options=[
                                        {'label': 'Show Guassian Baseline',
                                            'value': 'show'},
                                    ],
                                    value=['show'])]),
        ], style={'display': 'inline-block', 'width': '49%'}),

        html.Div([
            dcc.Graph(id='model-graph'),
        ], style={
            'columnCount': 1,
            'width': '98%',
            'height': '80%',
        }
        ),
    ]),

    html.Div([
        html.H4('Download Files'),
        html.A(
            'Download Peak Descriptors CSV',
            download="descriptors.csv",
            id='my-link-1'),
        html.Br(),
        html.A(
            'Download Cleaned Cycles CSV',
            download="cleaned_cycles.csv",
            id='my-link-2'),
        html.Br(),
        html.A(
            'Download Model Points CSV',
            download="model_points.csv",
            id='my-link-3'),
    ],
        style={
        'width': '98%',
        'margin': '10px'
    },
    ),
    html.Div(id='hidden-div', style={'display': 'none'})
])

##########################################
# Interactive Parts
##########################################


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename'),
               Input('input-datatype', 'value')])
def update_output(contents, filename, value):
    # value here is the datatype, then voltagerange1, then voltagerange2
    try:
        # Windowlength and polyorder are parameters for the savitsky golay
        # filter, could be inputs eventually
        windowlength = 9
        polyorder = 3
        if contents is None:
            return html.Div(
                ['No file has been uploaded, or the file uploaded was empty.'])
        else:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            return html.Div([parse_contents(decoded,
                                            filename,
                                            value,
                                            database,
                                            windowlength,
                                            polyorder)])
    except Exception as e:
        return html.Div(['There was a problem uploading that file: ' + str(e)])
    # return children

@app.callback(Output('available-data', 'options'),
              [Input('output-data-upload', 'children')])
def update_dropdown(children):
    options = [{'label': i, 'value': i} for i in get_db_filenames(database)]
    return options


@app.callback(Output('update-model-ans', 'children'),
              [Input('available-data', 'value'),
               Input('update-model-indb-button', 'n_clicks'),
               Input('new-peak-threshold', 'value')])
def update_model_indb(filename, n_clicks, new_peak_thresh):
    if n_clicks is not None:
        cleanset_name = filename.split('.')[0] + 'CleanSet'
        df_clean = get_file_from_database(cleanset_name, database)
        feedback_str = generate_model(
            df_clean, filename, new_peak_thresh, database)
        feedback = html.Div([feedback_str])
    else:
        feedback = html.Div(['Model has not been updated yet.'])
    return feedback


@app.callback(  # update slider
    Output('cycle--slider', 'max'),
    [Input('available-data', 'value')])
def update_slider_max(filename):
    if filename is None:
        filename = 'ExampleData'
        database_sel = init_db
    else:
        filename = filename
        database_sel = database
    data, raw_data = pop_with_db(filename, database_sel)
    datatype = data['datatype'].iloc[0]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col,
     char_cap_col, charge_or_discharge) = col_variables(datatype)
    return data['Cycle_Index'].max()


@app.callback(
    Output('cycle--slider', 'marks'),
    [Input('available-data', 'value')])
def update_slider_marks(filename):
    if filename is None:
        filename = 'ExampleData'
        database_sel = init_db
    else:
        filename = filename
        database_sel = database
    data, raw_data = pop_with_db(filename, database_sel)
    return {str(each): str(each) for each in data['Cycle_Index'].unique()}


@app.callback(
    Output('cycle--slider', 'value'),
    [Input('available-data', 'value')])
def update_slider_value(filename):
    if filename is None:
        filename = 'ExampleData'
        database_sel = init_db
    else:
        filename = filename
        database_sel = database
    data, raw_data = pop_with_db(filename, database_sel)
    datatype = data['datatype'].iloc[0]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col,
     char_cap_col, charge_or_discharge) = col_variables(datatype)

    return data['Cycle_Index'].min()


@app.callback(
    Output('charge-graph', 'figure'),
    [Input('cycle--slider', 'value'),
     Input('available-data', 'value'),
     Input('show-model-fig1', 'value')]
)
def update_figure1(selected_step, filename, showmodel):
    fig = plotly.subplots.make_subplots(
        rows=1, cols=2,
        subplot_titles=('Raw Cycle', 'Smoothed Cycle'),
        shared_xaxes=True)
    marker = {'color': ['#0074D9']}
    if filename is None or filename == 'options':
        filename = 'ExampleData'
        database_sel = init_db
    else:
        database_sel = database
    data, raw_data = pop_with_db(filename, database_sel)
    datatype = data['datatype'].iloc[0]
    (cycle_ind_col, data_point_col, volt_col, curr_col,
     dis_cap_col, char_cap_col, charge_or_discharge) = col_variables(datatype)
    modset_name = filename.split('.')[0] + '-ModPoints'
    df_model = get_file_from_database(modset_name, database_sel)
    if df_model is not None:
        filt_mod = df_model[df_model[cycle_ind_col] == selected_step]

    if data is not None:
        filtered_data = data[data[cycle_ind_col] == selected_step]
    if raw_data is not None:
        raw_filtered_data = raw_data[raw_data[cycle_ind_col] == selected_step]

    for i in filtered_data[cycle_ind_col].unique():
        if data is not None:
            dff = filtered_data[filtered_data[cycle_ind_col] == i]
        if raw_data is not None:
            dff_raw = raw_filtered_data[raw_filtered_data[cycle_ind_col] == i]
        if df_model is not None:
            dff_mod = filt_mod[filt_mod[cycle_ind_col] == i]

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
                'x': dff_mod[volt_col],
                'y': dff_mod['Model'],
                'type': 'scatter',
                'name': 'Model'
            }, 1, 2)

        fig['layout']['showlegend'] = False
        fig['layout']['xaxis1'].update(title='Voltage (V)')
        fig['layout']['xaxis2'].update(title='Voltage (V)')
        fig['layout']['yaxis1'].update(title='dQ/dV')
        fig['layout']['yaxis2'].update(title='dQ/dV')
        fig['layout']['height'] = 600
        fig['layout']['margin'] = {
            'l': 40,
            'r': 10,
            't': 60,
            'b': 200
        }
    return fig


@app.callback(
    Output('model-graph', 'figure'),
    [
        Input('available-data', 'value'),
        Input('new-peak-threshold', 'value'),
        Input('update-model-button', 'n_clicks'),
        Input('show-gauss', 'value'),
        Input('desc-to-plot', 'value'),
        Input('cd-to-plot', 'value'),
        Input('desc-peaknum-to-plot', 'value')]
)
def update_figure2(
        filename,
        peak_thresh,
        n_clicks,
        show_gauss,
        desc_to_plot,
        cd_to_plot,
        peaknum_to_plot):
    """ This is  a function to evaluate the model on a sample plot before updating the database"""
    if filename is None:
        filename = 'ExampleData'
        database_sel = init_db
    else:
        database_sel = database
    data, raw_data = pop_with_db(filename, database_sel)
    datatype = data['datatype'].iloc[0]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col,
     char_cap_col, charge_or_discharge) = col_variables(datatype)
    selected_step = round(data[cycle_ind_col].max() / 2) + 1
    # select a cycle in the middle of the set
    dff_data = data[data[cycle_ind_col] == selected_step]
    if len(data[cycle_ind_col].unique()) > 1:
        lenmax = max([len(data[data[cycle_ind_col] == cyc])
                      for cyc in data[cycle_ind_col].unique() if cyc != 1])
    else:
        lenmax = len(data)
    dff_raw = raw_data[raw_data[cycle_ind_col] == selected_step]
    peak_vals_df = get_file_from_database(
        filename.split('.')[0] + '-descriptors', database_sel)

    fig = plotly.subplots.make_subplots(
        rows=1, cols=2, subplot_titles=(
            'Descriptors', 'Example Data for Model Tuning (Cycle ' + str(
                int(selected_step)) + ')'), shared_xaxes=True)
    marker = {'color': ['#0074D9']}
    if peak_vals_df is not None:
        if n_clicks is not None:
            # if the user has hit the update-model-button - remake model
            new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d = get_model_dfs(
                dff_data, datatype, selected_step, lenmax, peak_thresh)
            dff_mod = new_df_mody
            c_sigma = model_c_vals['base_sigma']
            c_center = model_c_vals['base_center']
            c_amplitude = model_c_vals['base_amplitude']
            c_fwhm = model_c_vals['base_fwhm']
            c_height = model_c_vals['base_height']

            d_sigma = model_d_vals['base_sigma']
            d_center = model_d_vals['base_center']
            d_amplitude = model_d_vals['base_amplitude']
            d_fwhm = model_d_vals['base_fwhm']
            d_height = model_d_vals['base_height']
        else:
            # if user hasn't pushed the button, populate with original model
            # from database
            modset_name = filename.split('.')[0] + '-ModPoints'
            df_model = get_file_from_database(modset_name, database_sel)
            dff_mod = df_model[df_model[cycle_ind_col] == selected_step]

            filtpeakvals = peak_vals_df[peak_vals_df['c_cycle_number']
                                        == selected_step]
            filtpeakvals = filtpeakvals.reset_index(drop=True)
            # grab values for the underlying gaussian in the charge:
            try:
                c_sigma = filtpeakvals['c_gauss_sigma'].iloc[0]
                c_center = filtpeakvals['c_gauss_center'].iloc[0]
                c_amplitude = filtpeakvals['c_gauss_amplitude'].iloc[0]
                c_fwhm = filtpeakvals['c_gauss_fwhm'].iloc[0]
                c_height = filtpeakvals['c_gauss_height'].iloc[0]
            except BaseException:
                # there may not be a model
                pass
            # grab values for the underlying discharge gaussian:
            try:
                d_sigma = filtpeakvals['d_gauss_sigma'].iloc[0]
                d_center = filtpeakvals['d_gauss_center'].iloc[0]
                d_amplitude = filtpeakvals['d_gauss_amplitude'].iloc[0]
                d_fwhm = filtpeakvals['d_gauss_fwhm'].iloc[0]
                d_height = filtpeakvals['d_gauss_height'].iloc[0]
            except BaseException:
                pass

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
                    None
        fig.append_trace({
            'x': dff_mod[volt_col],
            'y': dff_mod['Model'],
            'type': 'scatter',
            'name': 'Model of One Cycle'
        }, 1, 2)
   # add if checkbox is selected to show polynomial baseline
        if 'show' in show_gauss:
            try:
                fig.append_trace({
                    'x': dff_mod[volt_col],
                    'y': ((c_amplitude / (c_sigma * ((2 * 3.14159)**0.5))) * np.exp((-(dff_mod[volt_col] - c_center)**2) / (2 * c_sigma**2))),
                    'type': 'scatter',
                    'name': 'Charge Gaussian Baseline'  # plot the poly
                }, 1, 2)
            except BaseException:
                pass
            # add the plot of the discharge guassian:
            try:
                fig.append_trace({
                    'x': dff_mod[volt_col],
                    'y': -((d_amplitude / (d_sigma * ((2 * 3.14159)**0.5))) * np.exp((-(dff_mod[volt_col] - d_center)**2) / (2 * d_sigma**2))),
                    'type': 'scatter',
                    'name': 'Discharge Gaussian Baseline'  # plot the poly
                }, 1, 2)
            except BaseException:
                pass

    fig['layout']['showlegend'] = True
    fig['layout']['xaxis1'].update(title='Cycle Number')
    fig['layout']['xaxis2'].update(title='Voltage (V)')
    fig['layout']['yaxis1'].update(title='Descriptor Value')
    fig['layout']['yaxis2'].update(
        title='dQ/dV',
        range=[
            dff_data['Smoothed_dQ/dV'].min(),
            dff_data['Smoothed_dQ/dV'].max()])
    fig['layout']['height'] = 600
    fig['layout']['margin'] = {
        'l': 40,
        'r': 10,
        't': 60,
        'b': 200
    }
    return fig

@app.callback(Output('my-link-1', 'href'),
              [Input('available-data', 'value')])
def update_link_1(value):
    if value is not None:
        peak_vals_df = get_file_from_database(
            value.split('.')[0] + '-descriptors', database)
        if peak_vals_df is not None:
            csv_string = peak_vals_df.to_csv(index=False, encoding='utf-8')
        else:
            # return an empty dataframe
            csv_string = pd.DataFrame().to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + \
            urllib.parse.quote(csv_string)
        return csv_string

@app.callback(Output('my-link-2', 'href'),
              [Input('available-data', 'value')])
def update_link_2(value):
    if value is not None:
        clean_set_df = get_file_from_database(
            value.split('.')[0] + 'CleanSet', database)
        if clean_set_df is not None:
            csv_string = clean_set_df.to_csv(index=False, encoding='utf-8')
        else:
            # return an empty dataframe
            csv_string = pd.DataFrame().to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + \
            urllib.parse.quote(csv_string)
        return csv_string


@app.callback(Output('my-link-3', 'href'),
              [Input('available-data', 'value')])
def update_link_3(value):
    if value is not None:
        mod_points_df = get_file_from_database(
            value.split('.')[0] + '-ModPoints', database)
        if mod_points_df is not None:
            csv_string = mod_points_df.to_csv(index=False, encoding='utf-8')
        else:
            # return an empty dataframe
            csv_string = pd.DataFrame().to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + \
            urllib.parse.quote(csv_string)
        return csv_string


##########################################
# Customize CSS
##########################################

# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
# app.scripts.config.serve_locally = False

if __name__ == '__main__':
    app.run_server(debug=True)

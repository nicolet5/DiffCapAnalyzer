import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html

#####################
#DASH Functions 
#####################

#WAY too hard to write unit tests for these

def generate_table(data, maxrows=10):
    """Generates a table with Header and Body given a data set and number of rows to display in Dash format"""
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in data.columns])] +

        # Body
        [html.Tr([
            html.Td(data.iloc[i][col]) for col in data.columns
        ]) for i in range(min(len(data), maxrows))]
    )


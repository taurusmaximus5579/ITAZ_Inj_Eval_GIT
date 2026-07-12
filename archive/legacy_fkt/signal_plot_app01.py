# -*- coding: utf-8 -*-
"""
Created on Sun Oct 19 10:00:06 2025

@author: larsk
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objs as go
import numpy as np

# Beispiel-Daten
T = np.linspace(0, 10, 100)
signal_dict = {
    "Gruppe A": {
        "Signal 1": np.sin(T),
        "Signal 2": np.cos(T)
    },
    "Gruppe B": {
        "Signal 3": np.sin(2*T),
        "Signal 4": np.cos(2*T)
    }
}

# Erstelle die Figur
fig = go.Figure()
for group_name, signals in signal_dict.items():
    for signal_name, values in signals.items():
        fig.add_trace(go.Scatter(
            x=T, y=values,
            mode='markers',
            name=signal_name,
            customdata=np.stack((T, values), axis=-1),
            hovertemplate='Time: %{customdata[0]:.2f}<br>Value: %{customdata[1]:.2f}<extra>%{name}</extra>'
        ))

fig.update_layout(title="Interaktive Signal-Auswahl", dragmode='lasso')

# Dash App
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='signal-plot', figure=fig),
    dash_table.DataTable(
        id='selected-data-table',
        columns=[
            {"name": "Signal", "id": "curveNumber"},
            {"name": "Time", "id": "x"},
            {"name": "Value", "id": "y"}
        ],
        data=[],
        page_size=10
    )
])

@app.callback(
    Output('selected-data-table', 'data'),
    Input('signal-plot', 'selectedData')
)
def display_selected_data(selectedData):
    if selectedData is None:
        return []
    return [
        {
            "curveNumber": fig['data'][point['curveNumber']]['name'],
            "x": point['x'],
            "y": point['y']
        }
        for point in selectedData['points']
    ]

if __name__ == '__main__':
    app.run(debug=True)
    


from IPython.display import IFrame
IFrame(src="C:/Users/larsk/OneDrive/FIRMA/ITAZ/04_Project/injector/Messungen/OSZI/Testmessung/Fkt/DeinOrdnername_SigPlot.html", width='100%', height=600)

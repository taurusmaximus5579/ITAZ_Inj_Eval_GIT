# -*- coding: utf-8 -*-
"""
Created on Sat Oct 18 23:09:28 2025

@author: larsk
"""

import os
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def plot_grouped_signals_with_time(signal_dict, T, foldername):
    os.makedirs(foldername, exist_ok=True)
    output_file = os.path.join(foldername, os.path.basename(foldername) + '_SigPlot.html')

    num_groups = len(signal_dict)
    fig = make_subplots(
        rows=num_groups,
        cols=1,
        shared_xaxes=True,
        subplot_titles=list(signal_dict.keys())
    )

    all_signal_names = set()
    for signals in signal_dict.values():
        all_signal_names.update(signals.keys())
    all_signal_names = sorted(all_signal_names)

    colors = px.colors.qualitative.Plotly
    color_map = {name: colors[i % len(colors)] for i, name in enumerate(all_signal_names)}

    for i, (group_name, signals) in enumerate(signal_dict.items(), start=1):
        for signal_name in all_signal_names:
            if signal_name in signals:
                values = signals[signal_name]
                fig.add_trace(
                    go.Scatter(
                        x=T,
                        y=values,
                        mode='lines',
                        name=signal_name,
                        legendgroup=signal_name,
                        showlegend=(i == 1),
                        line=dict(color=color_map[signal_name])
                    ),
                    row=i, col=1
                )            
    
    # Füge die Achsenbeschriftung für jeden Subplot hinzu
    fig.update_xaxes(title_text="Time", row=i, col=1)

    
    fig.update_layout(
        height=300 * num_groups,
        title_text="ITAZ GmbH - Signal Plot",
        legend=dict(groupclick="toggleitem"),
        xaxis_title="Time",        
        hovermode='x unified', # Zeigt alle Y-Werte an einer gemeinsamen X-Position
        hoversubplots='axis'  # Ermöglicht den Hover-Effekt über Subplots mit gemeinsamen Achsen        
    )

    fig.write_html(output_file)
    return output_file
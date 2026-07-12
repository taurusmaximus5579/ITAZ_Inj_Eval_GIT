import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os

def plot_signals(result, dateipfad, name, signals_to_plot=None, FigTyp=1):
    """
    Erstellt ein interaktives HTML-Plot mit mehreren Subplots.
    FigTyp = 1: Zeitachse ist die erste Spalte (Standardverhalten).
    Paired signals (raw + processed) werden mit zwei Y-Achsen angezeigt.

    Parameter:
        result (pd.DataFrame): DataFrame mit Zeitspalte und Messsignalen.
        dateipfad (str): Pfad zum Speicherort (result_folder).
        name (str): Name der HTML-Datei.
        signals_to_plot (list of str, optional): Liste der zu plottenden Signalnamen.
        FigTyp (int): Plot-Typ (1 = Standard mit raw+processed Pairing).
    """
    # Konvertiere numpy array zu DataFrame falls nötig
    if isinstance(result, np.ndarray):
        result = pd.DataFrame(result)
    
    if FigTyp == 1:
        time = result.iloc[:, 0]
        time_label = result.columns[0]
    else:
        raise ValueError("Nur FigTyp=1 wird unterstützt für diesen Plot.")

    # Signale validieren
    if signals_to_plot is None:
        exclude = [time_label]
        all_signals = [col for col in result.columns if col not in exclude]
    else:
        all_signals = [sig for sig in signals_to_plot if sig in result.columns]
    
    # Definiere Signal-Paare: (raw_name, processed_name, title)
    signal_pairs = [
        ('Nadelhub [raw]', 'Needle Lift (mm) (processed)', 'Needle Lift'),
        ('Systemdruck [raw]', 'System Pressure (abs_bar) (processed)', 'System Pressure'),
        ('Rate [raw]', 'Injection Rate (abs_bar) (processed)', 'Injection Rate'),
        ('Steuersignal [raw]', 'Injector Control Signal (A) (processed)', 'Injector Control Signal'),
    ]
    
    # Filtere nur die Paare, deren Signale existieren
    valid_pairs = [pair for pair in signal_pairs 
                   if pair[0] in all_signals and pair[1] in all_signals]
    
    # Prüfe ob Mass (mg) existiert
    has_mass = 'Mass (mg) (processed)' in all_signals
    
    num_plots = len(valid_pairs) + (1 if has_mass else 0)
    
    # Erstelle Subplots mit sekundären Y-Achsen
    fig = make_subplots(
        rows=num_plots, cols=1,
        shared_xaxes=True,
        specs=[[{"secondary_y": True}] if i < len(valid_pairs) else [{}] for i in range(num_plots)],
        vertical_spacing=0.08,
        subplot_titles=[pair[2] for pair in valid_pairs] + (['Mass (mg)'] if has_mass else [])
    )
    
    # Farben für konsistente Visualisierung
    color_raw = 'rgba(100, 150, 200, 0.8)'
    color_processed = 'rgba(200, 100, 100, 0.8)'
    
    for row_idx, (raw_name, processed_name, title) in enumerate(valid_pairs, start=1):
        # Raw Signal auf linker Y-Achse
        fig.add_trace(
            go.Scatter(
                x=time, 
                y=result[raw_name],
                mode='lines',
                name=raw_name,
                line=dict(color=color_raw, width=1.5, dash='dash'),
                showlegend=False,
                hovertemplate='<b>%{fullData.name}</b><br>Time: %{x:.6f}s<br>Value: %{y:.4f}<extra></extra>'
            ),
            row=row_idx, col=1, secondary_y=False
        )
        
        # Processed Signal auf rechter Y-Achse
        fig.add_trace(
            go.Scatter(
                x=time,
                y=result[processed_name],
                mode='lines',
                name=processed_name,
                line=dict(color=color_processed, width=2.5),
                showlegend=False,
                hovertemplate='<b>%{fullData.name}</b><br>Time: %{x:.6f}s<br>Value: %{y:.4f}<extra></extra>'
            ),
            row=row_idx, col=1, secondary_y=True
        )
        
        # Y-Achsen beschriften
        fig.update_yaxes(title_text=raw_name.replace('[raw]', ''), row=row_idx, col=1, secondary_y=False)
        fig.update_yaxes(title_text=processed_name.replace('(processed)', ''), row=row_idx, col=1, secondary_y=True)
    
    # Füge Mass-Diagramm hinzu, falls vorhanden
    if has_mass:
        mass_row = len(valid_pairs) + 1
        fig.add_trace(
            go.Scatter(
                x=time,
                y=result['Mass (mg) (processed)'],
                mode='lines',
                name='Mass (mg)',
                line=dict(color='rgba(100, 200, 100, 0.8)', width=2.5),
                showlegend=False,
                hovertemplate='<b>Mass (mg)</b><br>Time: %{x:.6f}s<br>Value: %{y:.4f}mg<extra></extra>'
            ),
            row=mass_row, col=1
        )
        fig.update_yaxes(title_text='Mass (mg)', row=mass_row, col=1)

    fig.update_xaxes(title_text=time_label, row=num_plots, col=1)

    fig.update_layout(
        height=250 * num_plots,
        title_text=f'ITAZ - Raw Data Comparison',
        showlegend=False,
        hovermode='x unified',
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
    )

    # Speichern als HTML
    os.makedirs(dateipfad, exist_ok=True)
    html_file = os.path.join(dateipfad, name)
    
    fig.write_html(html_file)
    
    print(f"✅ Raw data plot saved: {html_file}")
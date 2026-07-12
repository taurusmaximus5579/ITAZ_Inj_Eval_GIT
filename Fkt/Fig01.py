import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os

def plot_signals(result, dateipfad, name, signals_to_plot=None, FigTyp=1):
    """
    Erstellt ein Diagramm mit mehreren untereinander angeordneten Subplots.
    FigTyp = 1: Zeitachse ist die erste Spalte (Standardverhalten).
    FigTyp = 2: Zeitachse ist 'local_time', neue Linie bei counter-Wechsel (counter == 0 wird ausgelassen).

    Parameter:
        result (pd.DataFrame): DataFrame mit Zeitspalte und Messsignalen.
        dateipfad (str): Pfad zur Datei, zur Ableitung des Speicherorts.
        name (str): Name der HTML-Datei.
        signals_to_plot (list of str, optional): Liste der zu plottenden Signalnamen.
        FigTyp (int): Plot-Typ (1 = Standard, 2 = local_time mit Segmentierung).
    """
    if FigTyp == 1:
        time = result.iloc[:, 0]
        time_label = result.columns[0]
    elif FigTyp == 2:
        if 'local_time' not in result.columns or 'counter' not in result.columns:
            raise ValueError("Für FigTyp=2 müssen 'local_time' und 'counter' im DataFrame enthalten sein.")
        result = result[result['counter'] != 0].copy()
        time = result['local_time']
        time_label = 'local_time'
    else:
        raise ValueError("Ungültiger FigTyp. Verwende 1 oder 2.")

    # Signale validieren
    if signals_to_plot is None:
        exclude = [time_label, 'counter'] if FigTyp == 2 else [time_label]
        signals_to_plot = [col for col in result.columns if col not in exclude]
    else:
        signals_to_plot = [sig for sig in signals_to_plot if sig in result.columns]

    num_signals = len(signals_to_plot)

    # Matplotlib Plot
    fig, axes = plt.subplots(num_signals, 1, figsize=(10, 2.5 * num_signals), sharex=True)
    if num_signals == 1:
        axes = [axes]

    for i, label in enumerate(signals_to_plot):
        signal = result[label]
        if FigTyp == 1:
            axes[i].plot(time, signal, label=label)
        else:
            for counter_value in result['counter'].unique():
                mask = result['counter'] == counter_value
                axes[i].plot(result.loc[mask, 'local_time'], signal[mask], label=f"{label} (c={counter_value})")
        axes[i].set_ylabel(label)
        axes[i].grid(True)
        axes[i].legend(loc='upper right')

    axes[-1].set_xlabel(time_label)
    plt.tight_layout()
    plt.show()

    # Plotly Subplots
    fig_plotly = make_subplots(
        rows=num_signals, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=signals_to_plot
    )

    for i, label in enumerate(signals_to_plot):
        signal = result[label]
        if FigTyp == 1:
            fig_plotly.add_trace(
                go.Scatter(x=time, y=signal, mode='lines', name=label),
                row=i + 1, col=1
            )
        else:
            for counter_value in result['counter'].unique():
                mask = result['counter'] == counter_value
                fig_plotly.add_trace(
                    go.Scatter(
                        x=result.loc[mask, 'local_time'],
                        y=signal[mask],
                        mode='lines',
                        name=f"Inj {counter_value}",
                        legendgroup=f"inj_{counter_value}",
                        showlegend=(i == 0)
                    ),
                    row=i + 1, col=1
                )

    parent_folder = os.path.basename(os.path.dirname(dateipfad))

    fig_plotly.update_layout(
        height=300 * num_signals,
        title_text=f'ITAZ - Signal Plots ({parent_folder})',
        showlegend=True,
        hovermode='closest'
    )

    ordnerpfad = os.path.dirname(dateipfad)
    os.makedirs(ordnerpfad, exist_ok=True)
    html_file = os.path.join(ordnerpfad, name)
    fig_plotly.write_html(html_file)

    print(f"Plot gespeichert unter: {html_file}")
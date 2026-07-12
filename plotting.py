import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from Fkt.Fig01 import plot_signals
from Fkt.FigDict02 import plot_grouped_signals_with_time
from Fkt.Intpol02 import interpolate_nested_signal_dict


def plot_signals_per_file(signal_dict, t_common, output_folder):
    selected_keys = [
        'Needle Lift (mm)',
        'System Pressure (abs_bar)',
        'Injection Rate (abs_bar)',
        'Injector Control Signal (A)'
    ]

    colors = {
        'Needle Lift (mm)': 'tab:blue',
        'System Pressure (abs_bar)': 'tab:red',
        'Injection Rate (abs_bar)': 'tab:green',
        'Injector Control Signal (A)': 'tab:purple'
    }

    for fname in signal_dict['Needle Lift (mm)'].keys():
        fig, ax_main = plt.subplots(figsize=(12, 8))
        axes = [ax_main]
        ax_main.spines['left'].set_position(('axes', 0.0))

        for i in range(1, len(selected_keys)):
            ax_new = ax_main.twinx()
            ax_new.spines['left'].set_position(('axes', -0.15 * i))
            ax_new.spines['left'].set_visible(True)
            axes.append(ax_new)

        for ax, key in zip(axes, selected_keys):
            if fname in signal_dict[key]:
                ax.plot(t_common, signal_dict[key][fname], color=colors[key], label=key)
                ax.set_ylabel(key, color=colors[key], rotation=90, labelpad=20)
                ax.tick_params(axis='y', colors=colors[key])
                ax.yaxis.set_label_position('left')
                ax.yaxis.set_ticks_position('left')

        ax_main.set_xlabel('Time [s]')
        plt.title(f"Signals for {fname}")
        plt.grid(True)

        lines, labels = [], []
        for ax in axes:
            line, label = ax.get_legend_handles_labels()
            lines.extend(line)
            labels.extend(label)
        plt.legend(lines, labels, loc='upper right')

        plt.tight_layout()
        img_path = os.path.join(output_folder, f"{fname}_signals.png")
        plt.savefig(img_path, dpi=300)
        plt.close()


def create_plots(signal_dict, T, result_folder, bilder_folder, rawdata_by_file=None, raw_data_plot=False):
    plot_path = plot_grouped_signals_with_time(signal_dict, T, result_folder, rawdata_by_file=rawdata_by_file)
    print(f"📊 Diagramm gespeichert unter: {plot_path}")
    plot_signals_per_file(signal_dict, T, bilder_folder)

    if raw_data_plot and rawdata_by_file:
        # Erstelle DataFrames mit allen Signalen pro Datei (raw + processed)
        if signal_dict and 'Needle Lift (mm)' in signal_dict:
            for filename in signal_dict['Needle Lift (mm)'].keys():
                data_for_file = pd.DataFrame({'Time (s)': T})
                
                # Processed signals (umgerechnet)
                for signal_name, signals_by_file in signal_dict.items():
                    if filename in signals_by_file:
                        data_for_file[f"{signal_name} (processed)"] = signals_by_file[filename]
                
                # Raw signals (direkt aus CSV, keine Umrechnung)
                if filename in rawdata_by_file:
                    raw_data = rawdata_by_file[filename]
                    # Interpoliere raw data auf die gleiche Zeitachse wie processed data
                    T_raw = raw_data['T'] - raw_data['T'].iloc[0]
                    
                    data_for_file['Nadelhub [raw]'] = np.interp(T, T_raw, raw_data['Nadelhub'])
                    data_for_file['Systemdruck [raw]'] = np.interp(T, T_raw, raw_data['Systemdruck'])
                    data_for_file['Rate [raw]'] = np.interp(T, T_raw, raw_data['Rate'])
                    data_for_file['Steuersignal [raw]'] = np.interp(T, T_raw, raw_data['Steuersignal'])
                
                html_filename = f"{filename}_rawdata.html"
                from Fkt.Fig01 import plot_signals
                plot_signals(data_for_file, result_folder, html_filename, FigTyp=1)


def interpolate_signal_data(signal_dict, T, step_size):
    return interpolate_nested_signal_dict(signal_dict, T, step_size)

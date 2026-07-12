import os
import matplotlib.pyplot as plt
from Fkt.Fig01 import plot_signals
from Fkt.FigDict02 import plot_grouped_signals_with_time
from Fkt.Intpol02 import interpolate_nested_signal_dict
from image_utils import persist_or_cache_figure


def plot_signals_per_file(signal_dict, t_common, output_folder, image_cache=None, save_to_disk=False):
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
        persist_or_cache_figure(
            fig,
            output_path=img_path if save_to_disk else None,
            image_cache=image_cache,
            category="Messsignale",
            name=fname,
            save_to_disk=save_to_disk,
            dpi=300,
        )


def create_plots(signal_dict, T, result_folder, bilder_folder, raw_data_plot=False, image_cache=None, save_to_disk=False):
    plot_path = plot_grouped_signals_with_time(signal_dict, T, result_folder)
    print(f"📊 Diagramm erstellt für die GUI und die Ergebnisdarstellung")
    plot_signals_per_file(signal_dict, T, bilder_folder, image_cache=image_cache, save_to_disk=save_to_disk)

    if raw_data_plot:
        for filename, data in signal_dict.get('Needle Lift (mm)', {}).items():
            html_filename = os.path.join(result_folder, f"{filename}_rawdata.html")
            plot_signals(data, filename, html_filename, FigTyp=1)


def interpolate_signal_data(signal_dict, T, step_size):
    return interpolate_nested_signal_dict(signal_dict, T, step_size)

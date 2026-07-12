"""
23.11.2025 Lars Köhler
[✅] Stromsignal die Zeiten und Ströme ins Diagramm eintragen
[✅] Neue Funktion für Shot2Shot inkl. Statistik
"""

# ====== mainscript.py ======
import os
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt

# Eigene Funktionen
from Fkt.Intpol02 import interpolate_nested_signal_dict
from Fkt.FigDict02 import plot_grouped_signals_with_time
from Fkt.ICS_Eval05 import analyze_plateaus
from Fkt.InjRate03 import InjectionRate
from Fkt.Fig01 import plot_signals
from Fkt.GainFig05 import GainCurve
from Fkt.InjLift05 import analyze_and_plot_needle_lifts
from Fkt.RateDownCurve02 import RateDownCurve
from Fkt.Shot2Shot02 import Eval_Shot2Shot

def plot_signals_per_file(signal_dict, t_common, output_folder):
    """
    Erstellt für jede Messung ein Diagramm mit vier Y-Achsen auf der linken Seite,
    farblich angepasst, ohne Überlappung und mit vertikalen Labels (von rechts lesbar).
    """
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

        # Hauptachse
        axes = [ax_main]
        ax_main.spines['left'].set_position(('axes', 0.0))

        # Zusätzliche Achsen erstellen und verschieben
        for i in range(1, len(selected_keys)):
            ax_new = ax_main.twinx()
            ax_new.spines['left'].set_position(('axes', -0.15 * i))  # Abstand dynamisch
            ax_new.spines['left'].set_visible(True)
            axes.append(ax_new)

        # Daten plotten und Achsen formatieren
        for ax, key in zip(axes, selected_keys):
            if fname in signal_dict[key]:
                ax.plot(t_common, signal_dict[key][fname], color=colors[key], label=key)
                # Label vertikal drehen (von rechts lesbar)
                ax.set_ylabel(key, color=colors[key], rotation=90, labelpad=20)
                ax.tick_params(axis='y', colors=colors[key])
                ax.yaxis.set_label_position('left')
                ax.yaxis.set_ticks_position('left')

        # X-Achse und Titel
        ax_main.set_xlabel('Time [s]')
        plt.title(f"Signals for {fname}")
        plt.grid(True)

        # Legende (alle Signale)
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

        print(f"✅ Bild für {fname} gespeichert unter: {img_path}")



def run_main_analysis(cfg):
    """Hauptanalyse mit Parametern aus dem GUI"""
    plot_raw_data       = cfg["plot_raw_data"]
    export_excel        = cfg["export_excel"]
    evaluate_gain_curve = cfg["eval_gain"]
    evaluate_rate_down  = cfg["eval_rate_dn"]
    evaluate_shot2shot  = cfg["shot2shot"]

    step_size = cfg["step_size"]
    cv   = cfg["cv"]
    cp   = cfg["cp"]
    R    = cfg["R"]
    A    = cfg["A"]
    Temp = cfg["Temp"]

    boost_range = (cfg["boost_min"], cfg["boost_max"])
    hold_range  = (cfg["hold_min"], cfg["hold_max"])
    zero_range  = (cfg["zero_min"], cfg["zero_max"])
        
    pressure_factor = cfg["pressure_factor"]
    injection_factor = cfg["injection_factor"]

    selected_files = cfg["selected_files"]
    shot_log_data  = cfg.get("shot_log")  # Neu: Shot-Log aus cfg

    if not selected_files:
        print("❌ Keine Dateien ausgewählt.")
        return

    signal_dict = {
        'Needle Lift (mm)': {},
        'Needle Velocity (mm_s)': {},
        'System Pressure (abs_bar)': {},
        'Injection Rate (abs_bar)': {},
        'Injector Control Signal (A)': {},
        'Power (W)': {},
        'Energy (Ws)': {}
    }

    T_min, T_max, min_time_step = float('inf'), float('-inf'), float('inf')

    # Zeitbereich bestimmen
    for path in selected_files:
        rawdata = pd.read_csv(path, sep=';', decimal=',')
        T = rawdata['T'] - rawdata['T'].iloc[0]
        T_min = min(T_min, T.min())
        T_max = max(T_max, T.max())
        diffs = T.diff().dropna()
        if not diffs.empty:
            min_step = diffs.min()
            if min_step > 0:
                min_time_step = min(min_time_step, min_step)

    t_common = np.arange(T_min, T_max, min_time_step)
    
    # Unterordner für Ergebnisse erstellen
    ordnerpfad = os.path.dirname(selected_files[0])
    ordnername = os.path.basename(ordnerpfad)
    result_folder = os.path.join(ordnerpfad, "Results")
    os.makedirs(result_folder, exist_ok=True)

    bilder_folder = os.path.join(ordnerpfad, "Bilder")
    os.makedirs(bilder_folder, exist_ok=True)

    # Daten pro Datei verarbeiten
    for path in selected_files:
        rawdata = pd.read_csv(path, sep=';', decimal=',')
        filename = os.path.splitext(os.path.basename(path))[0]
        T = rawdata['T'] - rawdata['T'].iloc[0]

        signals = pd.DataFrame({'T': T})
        signals['Needle Lift (mm)'] = (rawdata['Nadelhub'] - rawdata[rawdata['T'] <= 0.003]['Nadelhub'].median()) * 0.2
        signals['System Pressure (abs_bar)'] = rawdata['Systemdruck'] * pressure_factor
        signals['Injection Rate (abs_bar)'] = rawdata['Rate'] * injection_factor
        signals['Injector Control Signal (A)'] = (rawdata['Steuersignal'] - rawdata[rawdata['T'] >= rawdata['T'].max() - 0.0005]['Steuersignal'].median()) * 4
        signals['Power (W)'] = signals['Injector Control Signal (A)'] * 50
        signals['Energy (Ws)'] = np.cumsum(np.gradient(signals['T']) * signals['Power (W)'])
        signals['Energy (Ws)'] -= signals['Energy (Ws)'].min()

        # Glättung
        lift_signal = signals['Needle Lift (mm)']
        window_length = int(0.0005 / min_time_step)
        if window_length % 2 == 0:
            window_length += 1
        smoothed = savgol_filter(lift_signal, window_length=window_length, polyorder=3)
        velocity = np.gradient(smoothed, min_time_step)
        signal_dict['Needle Velocity (mm_s)'][filename] = velocity

        # Interpolation
        for key in signal_dict.keys():
            if key in signals.columns:
                signal_dict[key][filename] = np.interp(t_common, signals['T'], signals[key])
        
        if plot_raw_data:
            html_filename = os.path.join(result_folder, f"{filename}_rawdata.html")
            plot_signals(signals, path, html_filename, FigTyp=1)

    # Auswertung       
    ICS_Eval_Result = analyze_plateaus(signal_dict, boost_range, hold_range, zero_range,
                                       col="Injector Control Signal (A)", T=T, ordnerpfad=ordnerpfad)

    integrated_lift, hub_times = analyze_and_plot_needle_lifts(signal_dict, T, ordnerpfad)
    signal_dict['Needle Lift Integrated (mm_s)'] = integrated_lift
    
    InjRate_Eval = InjectionRate(cv, cp, R, Temp, signal_dict, T, A, hub_times)
    signal_dict["Injection Rate (mg_ms)"] = InjRate_Eval["injrate_values"]
    signal_dict["Mass (mg)"] = InjRate_Eval["cumulative_mass_values"]   

    # Diagramm speichern
    plot_path = plot_grouped_signals_with_time(signal_dict, T, result_folder)
    print(f"📊 Diagramm gespeichert unter: {plot_path}")

    # Einzelplots
    plot_signals_per_file(signal_dict, t_common, bilder_folder)

    if evaluate_gain_curve:
        mass_info = GainCurve(signal_dict, T, min_time_step, ICS_Eval_Result, hub_times, ordnerpfad)

    if evaluate_rate_down:
        mass_info = RateDownCurve(signal_dict, T, step_size, hub_times, ordnerpfad)
        
    if evaluate_shot2shot:
        all_stats = Eval_Shot2Shot(signal_dict, T, min_time_step, ICS_Eval_Result, hub_times, ordnerpfad)

    # Excel Export
    if export_excel:
        output_file = os.path.join(result_folder, f"{ordnername}.xlsx")
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            interpolated_signals = interpolate_nested_signal_dict(signal_dict, T, step_size)
            tab_order = [
                'Needle Lift (mm)', 'Mass (mg)', 'Injector Control Signal (A)',
                'System Pressure (abs_bar)', 'Injection Rate (abs_bar)',
                'Injection Rate (mg_ms)', 'Needle Velocity (mm_s)',
                'Needle Lift Integrated (mm_s)', 'Power (W)', 'Energy (Ws)'
            ]
            for sheet_name in tab_order:
                if sheet_name in interpolated_signals:
                    interpolated_signals[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)

            # GainCurve
            if evaluate_gain_curve and isinstance(mass_info, tuple) and isinstance(mass_info[0], dict):
                df_gain = pd.DataFrame([
                    {'Filename': fname, 'ICS_ON': data.get('ICS_ON', np.nan), 'Mass (mg)': data.get('mass', np.nan), 'Needle Lift Integrated (mm_s)': data.get('NeedleLiftIntegrated', np.nan)}
                    for fname, data in mass_info[0].items()
                ])
                df_gain.to_excel(writer, sheet_name='GainCurve', index=False)

            # RateDownCurve
            if evaluate_rate_down and isinstance(mass_info, tuple) and isinstance(mass_info[0], dict):
                df_rate_down = pd.DataFrame([
                    {'Filename': fname, 'System Pressure (abs_bar)': data.get('pressure', np.nan),
                     'Mass (mg)': data.get('mass', np.nan)}
                    for fname, data in mass_info[0].items()
                ])
                df_rate_down.to_excel(writer, sheet_name='RateDownCurve', index=False)

            # Neu: Shot_Log hinzufügen
            if shot_log_data is not None:
                df_shot_log = pd.DataFrame({
                    "Shot": shot_log_data.get("shot", []),
                    "Time [µs]": shot_log_data.get("time_us", []),
                    "Acq [ms]": shot_log_data.get("acq_ms", []),
                    "Wait [ms]": shot_log_data.get("wait_ms", []),
                    "Full [ms]": shot_log_data.get("full_ms", [])
                })
                if not df_shot_log.empty:
                    df_shot_log.to_excel(writer, sheet_name="shot_log", index=False)

            # Neu: Common hinzufügen (alle cfg-Werte)            
            df_common = pd.DataFrame(list(cfg.items()), columns=["Parameter", "Value"])
            df_common.to_excel(writer, sheet_name="Common", index=False)
            
            # ===== Shot2Shot Statistik – EIN Tab mit mehreren Tabellen =====
            if evaluate_shot2shot and isinstance(all_stats, dict):
            
                sheet_name = "Shot2Shot_Stats"
            
                # Leeres Sheet erzeugen (falls nicht existiert)
                writer.book.create_sheet(sheet_name)
                sheet = writer.book[sheet_name]
            
                start_row = 0
            
                for category, stats_dict in all_stats.items():
            
                    # Überschrift schreiben
                    sheet.cell(row=start_row + 1, column=1, value=category)
                    sheet.cell(row=start_row + 1, column=1).font = sheet.cell(row=start_row + 1, column=1).font.copy(bold=True)
            
                    start_row += 2
            
                    # Tabelle bauen
                    rows = []
                    for metric_name, metric_values in stats_dict.items():
                        row = {"Metric": metric_name}
                        for key, val in metric_values.items():
                            if hasattr(val, "item"):
                                val = float(val)
                            row[key] = val
                        rows.append(row)
            
                    df_stats = pd.DataFrame(rows)
            
                    # Tabelle schreiben
                    df_stats.to_excel(writer, sheet_name=sheet_name, index=False, startrow=start_row)
            
                    # Abstand für nächste Tabelle
                    start_row += len(df_stats) + 3        
                     
           
        print(f"✅ Excel gespeichert: {output_file}")

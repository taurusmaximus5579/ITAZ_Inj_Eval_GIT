# ====== mainscript.py ======
import os
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

# Eigene Funktionen
from Fkt.Intpol02 import interpolate_nested_signal_dict
from Fkt.FigDict02 import plot_grouped_signals_with_time
from Fkt.ICS_Eval03 import analyze_plateaus
from Fkt.InjRate02 import InjectionRate
from Fkt.Fig01 import plot_signals
from Fkt.GainFig03 import GainCurve
from Fkt.InjLift03 import analyze_and_plot_needle_lifts
from Fkt.RateDownCurve01 import RateDownCurve


def run_main_analysis(cfg):
    """Hauptanalyse mit Parametern aus dem GUI"""
    plot_raw_data       = cfg["plot_raw_data"]
    export_excel        = cfg["export_excel"]
    evaluate_gain_curve = cfg["eval_gain"]
    evaluate_rate_down  = cfg["eval_rate_dn"]

    step_size = cfg["step_size"]
    cv   = cfg["cv"]
    cp   = cfg["cp"]
    R    = cfg["R"]
    A    = cfg["A"]
    Temp = cfg["Temp"]

    boost_range = (cfg["boost_min"], cfg["boost_max"])
    hold_range  = (cfg["hold_min"], cfg["hold_max"])
    zero_range  = (cfg["zero_min"], cfg["zero_max"])

    selected_files = cfg["selected_files"]

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

    # Daten pro Datei verarbeiten
    for path in selected_files:
        rawdata = pd.read_csv(path, sep=';', decimal=',')
        filename = os.path.splitext(os.path.basename(path))[0]
        T = rawdata['T'] - rawdata['T'].iloc[0]

        signals = pd.DataFrame({'T': T})
        signals['Needle Lift (mm)'] = (rawdata['Nadelhub'] - rawdata[rawdata['T'] <= 0.003]['Nadelhub'].median()) * 0.2
        signals['System Pressure (abs_bar)'] = rawdata['Systemdruck'] * 5
        signals['Injection Rate (abs_bar)'] = rawdata['Rate']
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
            html_filename = f"{filename}_rawdata.html"
            plot_signals(signals, path, html_filename, FigTyp=1)

    # Auswertung
    ordnerpfad = os.path.dirname(selected_files[0])
    ordnername = os.path.basename(ordnerpfad)

    ICS_Eval_Result = analyze_plateaus(
        signal_dict,
        boost_range=boost_range,
        hold_range=hold_range,
        zero_range=zero_range,
        col="Injector Control Signal (A)",
        T=T
    )

    InjRate_Eval = InjectionRate(cv, cp, R, Temp, signal_dict, T, A)
    signal_dict["Injection Rate (mg_ms)"] = InjRate_Eval["injrate_values"]
    signal_dict["Mass (mg)"] = InjRate_Eval["cumulative_mass_values"]

    integrated_lift, hub_times = analyze_and_plot_needle_lifts(signal_dict, T)
    signal_dict['Needle Lift Integrated (mm_s)'] = integrated_lift

    plot_path = plot_grouped_signals_with_time(signal_dict, T, ordnerpfad)
    print(f"📊 Diagramm gespeichert unter: {plot_path}")

    if evaluate_gain_curve:
        mass_info = GainCurve(signal_dict, T, min_time_step, ICS_Eval_Result, hub_times, ordnerpfad)

    if evaluate_rate_down:
        mass_info = RateDownCurve(signal_dict, T, step_size, hub_times, ordnerpfad)

   # Excel Export
    if export_excel:
        output_file = os.path.join(ordnerpfad, f"{ordnername}.xlsx")
        os.makedirs(ordnerpfad, exist_ok=True)
    
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Interpolierte Signale
            interpolated_signals = interpolate_nested_signal_dict(signal_dict, T, step_size)
    
            # Wunsch-Reihenfolge der Tabs
            tab_order = [
                'Needle Lift (mm)',
                'Mass (mg)',
                'Injector Control Signal (A)',
                'System Pressure (abs_bar)',
                'Injection Rate (abs_bar)',
                'Injection Rate (mg_ms)',
                'Needle Velocity (mm_s)',
                'Needle Lift Integrated (mm_s)',
                'Power (W)',
                'Energy (Ws)'
            ]
    
            for sheet_name in tab_order:
                if sheet_name in interpolated_signals:
                    df = interpolated_signals[sheet_name]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
            # GainCurve-Tabelle
            if evaluate_gain_curve and isinstance(mass_info, tuple) and isinstance(mass_info[0], dict):
                try:
                    df_gain = pd.DataFrame([
                        {
                            'Filename': fname,
                            'ICS_ON': data.get('ICS_ON', np.nan),
                            'Mass (mg)': data.get('mass', np.nan)
                        }
                        for fname, data in mass_info[0].items()
                    ])
                    # Nur exportieren, wenn Export aktiv ist
                    if export_excel:
                        df_gain.to_excel(writer, sheet_name='GainCurve', index=False)
                        print("📁 Tab 'GainCurve' erfolgreich zur Excel-Datei hinzugefügt.")
                    else:
                        print("✅ GainCurve-Daten berechnet (kein Export).")
                except Exception as e:
                    print(f"❌ Fehler bei der GainCurve-Berechnung: {e}")
            else:
                print("⚠️ 'mass_info[0]' ist leer oder nicht vorhanden, oder GainCurve-Auswertung ist deaktiviert.")
            
            # RateDown-Tabelle
            if evaluate_rate_down and isinstance(mass_info, tuple) and isinstance(mass_info[0], dict):
                try:
                    df_rate_down = pd.DataFrame([
                        {
                            'Filename': fname,
                            'System Pressure (abs_bar)': data.get('pressure', np.nan),
                            'Mass (mg)': data.get('mass', np.nan)
                        }
                        for fname, data in mass_info[0].items()
                    ])
                    if export_excel:
                        df_rate_down.to_excel(writer, sheet_name='RateDownCurve', index=False)
                        print("📁 Tab 'RateDownCurve' erfolgreich zur Excel-Datei hinzugefügt.")
                    else:
                        print("✅ RateDown-Daten berechnet (kein Export).")
                except Exception as e:
                    print(f"❌ Fehler bei der RateDown-Berechnung: {e}")
            else:
                print("⚠️ 'mass_info[0]' ist leer oder nicht vorhanden, oder RateDownCurve-Auswertung ist deaktiviert.")
    
        print(f"✅ Excel gespeichert: {output_file}")

"""
- [✅] Eval Hubsignal; Start; Ende; Prellen --> Start und End threshold value 0,003
- [✅] Optimierung der Integration des Lifts
- [✅] ICS Funktion wurde optimiert. Kein Speichern mehr der Einzeldiagramm. Dafür Plot in Python zur Kontrolle der Signal und Analysequalität
- [✅] Anpassunge der GainFig03 auf die zwei verschiedenen Varianten; Stromsignal ändert sich und/oder Druck wird verändert InjLift03
- [✅] Umsortieren des Exceloutput
"""
try:
    from IPython import get_ipython
    get_ipython().magic('clear')     # Konsole leeren
    get_ipython().magic('reset -f')  # Variablen zurücksetzen
except:
    pass

import os
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog
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


# Konfiguration
plot_raw_data = False
export_csv_signals = True
evaluate_gain_curve = False
evaluate_rate_down_curve = True

step_size = 0.00001 #for interpolation

#cv = 743 #Stickstoff
cv = 3115 #Helium
#cp = 1040 #Stickstoff
cp = 5194 #Helium
#R = 296.76 #Stickstoff J/(kg*K)
R = 2077 #Helium J/(kg*K)
A = 0.00018
Temp = 293.15

# GUI zur Dateiauswahl
root = tk.Tk()
root.withdraw()
selected_files = filedialog.askopenfilenames(
    title="Wähle eine oder mehrere CSV-Dateien",
    filetypes=[("CSV-Dateien", "*.csv")]
)

if not selected_files:
    print("❌ Keine Dateien ausgewählt.")
else:
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

    # Zeitbereich und Schrittweite bestimmen
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
        

        # Glättung und Ableitungen
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

        # CSV Export
        if export_csv_signals:
            output_dir = os.path.dirname(selected_files[0])
            for signal_name, data in signal_dict.items():
                df_out = pd.DataFrame({'T': t_common})
                for fname, values in data.items():
                    df_out[fname] = values
                output_path = os.path.join(output_dir, f"{signal_name.replace(' ', '_').replace('(', '').replace(')', '')}.csv")
                df_out.to_csv(output_path, index=False, sep=';', decimal=',')
                print(f"✅ CSV gespeichert: {output_path}")

        # Rohdatenplot
        if plot_raw_data:
            html_filename = f"{filename}_rawdata.html"
            plot_signals(signals, path, html_filename, FigTyp=1)

    # Auswertung
    ordnerpfad = os.path.dirname(selected_files[0])
    ordnername = os.path.basename(ordnerpfad)

    ICS_Eval_Result = analyze_plateaus(
        signal_dict,
        boost_range=(10.5, 13.5),
        hold_range=(3, 5),
        zero_range=(-0.5, 0.5),
        col="Injector Control Signal (A)",        
        T=T
    )

    InjRate_Eval = InjectionRate(cv, cp, R, Temp, signal_dict, T, A)
    signal_dict["Injection Rate (mg_ms)"] = InjRate_Eval["injrate_values"]
    signal_dict["Mass (mg)"] = InjRate_Eval["cumulative_mass_values"]

    # Integrierter Injektorhub
    integrated_lift, hub_times = analyze_and_plot_needle_lifts(signal_dict, T)
    signal_dict['Needle Lift Integrated (mm_s)'] = integrated_lift

    # Gruppierte Plots
    plot_path = plot_grouped_signals_with_time(signal_dict, T, ordnerpfad)
    print(f"📊 Diagramm gespeichert unter: {plot_path}")

    # Gain-Kurvenauswertung
    if evaluate_gain_curve:
        mass_info = GainCurve(signal_dict, T, min_time_step, ICS_Eval_Result, hub_times, ordnerpfad)
    
    # Rate-Down -Kurvenauswertung    
    if RateDownCurve:
        mass_info = RateDownCurve(signal_dict, T, step_size, hub_times, ordnerpfad)
        
    # Excel Export
    if export_csv_signals:
        
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
                'Injection Rate (mg_ms)'         
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
                    df_gain.to_excel(writer, sheet_name='GainCurve', index=False)
                    print("📁 Tab 'GainCurve' erfolgreich zur Excel-Datei hinzugefügt.")
                except Exception as e:
                    print(f"❌ Fehler beim Schreiben der GainCurve-Tabelle: {e}")
            else:
                print("⚠️ 'mass_info[0]' ist leer oder nicht vorhanden, oder GainCurve-Auswertung ist deaktiviert.")
            
            
            # RateDown-Tabelle
            if evaluate_rate_down_curve and isinstance(mass_info, tuple) and isinstance(mass_info[0], dict):
                try:
                    df_rate_down = pd.DataFrame([
                        {
                            'Filename': fname,
                            'System Pressure (abs_bar)': data.get('pressure', np.nan),
                            'Mass (mg)': data.get('mass', np.nan)                        
                        }
                        for fname, data in mass_info[0].items()
                    ])
                    df_rate_down.to_excel(writer, sheet_name='RateDownCurve', index=False)
                    print("📁 Tab 'RateDownCurve' erfolgreich zur Excel-Datei hinzugefügt.")
                except Exception as e:
                    print(f"❌ Fehler beim Schreiben der RateDownCurve-Tabelle: {e}")
            else:
                print("⚠️ 'mass_info[0]' ist leer oder nicht vorhanden, oder RateDownCurve-Auswertung ist deaktiviert.")

        print(f"✅ Excel gespeichert: {output_file}")

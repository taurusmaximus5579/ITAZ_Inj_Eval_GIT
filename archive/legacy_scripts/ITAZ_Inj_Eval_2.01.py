import pandas as pd
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog
from Fkt.Intpol02 import interpolate_nested_signal_dict  # falls du die Funktion ausgelagert hast
from Fkt.FigDict02 import plot_grouped_signals_with_time
from Fkt.ICS_Eval02 import analyze_plateaus
from Fkt.InjRate02 import InjectionRate
from Fkt.Fig01 import plot_signals
#from Fkt.GainFig02 import get_mass_average


# HTML Plots erstellen von Rohmessdaten erstellen
PlotRawData = 0

# Schrittweite für die Interpolation
InterpSigMatrix = 1
step_size = 0.00001

#Einzelsignale mit Original Abtastrate speichern
CSVSigOut = 0

#Stoffwerte
cv = 743 #Stickstoff
cp = 1040 #Stickstoff
R = 296.76 #Stickstoff J/(kg*K)
A = 2.13188E-05 #Querschnitt Blende vom Prüfstand in m²
Temp = 293.15 #Temperatur Druckkammer in K


def SigRead(pfad):
    try:
        df = pd.read_csv(pfad, sep=';', decimal=',')
        return df
    except Exception as e:
        print(f"Fehler beim Einlesen der Datei: {e}")
        return None

# GUI zur Dateiauswahl
root = tk.Tk()
root.withdraw()
dateipfade = filedialog.askopenfilenames(
    title="Wähle eine oder mehrere CSV-Dateien",
    filetypes=[("CSV-Dateien", "*.csv")]
)

if not dateipfade:
    print("❌ Keine Dateien ausgewählt.")
else:
    signal_dict = {
        'Needle Lift (mm)': {},
        'System Pressure (abs_bar)': {},
        'Injection Rate (abs_bar)': {},
        'Injector Control Signal (A)': {},
        'Power (W)': {},
        'Energy (Ws)': {}
    }

    T_min, T_max = float('inf'), float('-inf')
    min_time_step = float('inf')

    # Zeitbereich und kleinste Schrittweite ermitteln
    for dateipfad in dateipfade:
        rawdata = SigRead(dateipfad)
        if rawdata is None or 'T' not in rawdata:
            continue
        T = rawdata['T'] - rawdata['T'].iloc[0]
        T_min = min(T_min, T.min())
        T_max = max(T_max, T.max())
        time_diffs = T.diff().dropna()
        if not time_diffs.empty:
            min_step = time_diffs.min()
            if min_step > 0:
                min_time_step = min(min_time_step, min_step)     

    if min_time_step == float('inf'):
        print("❌ Konnte keine gültige Zeitachse bestimmen.")
    else:
        t_common = np.arange(T_min, T_max, min_time_step)

        for dateipfad in dateipfade:
            rawdata = SigRead(dateipfad)
            if rawdata is None:
                continue

            try:
                T = rawdata['T'] - rawdata['T'].iloc[0]
                signals = pd.DataFrame({'T': T})
                signals['Needle Lift (mm)'] = (rawdata['Nadelhub'] - rawdata[rawdata['T'] <= 0.003]['Nadelhub'].median()) * 0.2
                signals['System Pressure (abs_bar)'] = rawdata['Systemdruck'] * 5
                signals['Injection Rate (abs_bar)'] = rawdata['Rate']
                signals['Injector Control Signal (A)'] = (rawdata['Steuersignal'] - rawdata[rawdata['T'] >= rawdata['T'].max() - 0.05]['Steuersignal'].median()) * 4
                signals['Power (W)'] = signals['Injector Control Signal (A)'] * 50
                signals['Energy (Ws)'] = np.cumsum(np.gradient(signals['T']) * signals['Power (W)'])
                signals['Energy (Ws)'] -= signals['Energy (Ws)'].min()
            except KeyError as e:
                print(f"Fehlende Spalte in Datei {dateipfad}: {e}")
                continue

            for key in signal_dict.keys():
                interp_values = np.interp(t_common, signals['T'], signals[key])
                filename = os.path.splitext(os.path.basename(dateipfad))[0]
                signal_dict[key][filename] = interp_values        
        
            # Tabellen schreiben
            output_dir = os.path.dirname(dateipfade[0])
            for signal_name, data in signal_dict.items():
                df_out = pd.DataFrame({'T': t_common})
                for fname, values in data.items():
                    df_out[fname] = values
                output_path = os.path.join(output_dir, f"{signal_name.replace(' ', '_').replace('(', '').replace(')', '')}.csv")
                if CSVSigOut == 1:
                    df_out.to_csv(output_path, index=False, sep=';', decimal=',')
                    print(f"✅ Tabelle geschrieben: {output_path}")
                    
            if PlotRawData == 1:
                # HTML Plots erstellen
                # Extrahiere den übergeordneten Ordnernamen
                parent_folder = os.path.basename(os.path.dirname(dateipfad))
                # Erstelle den HTML-Dateinamen mit dem Ordnernamen
                html_filename = f"{filename}_rawdata.html"
                # Verwende den dynamischen Namen beim Speichern
                if rawdata is not None: 
                    plot_signals(rawdata, dateipfad, html_filename, FigTyp=1) 
                else: 
                    print("❌ Fehler beim Einlesen der Datei.")
   
# Extrahiere den Ordnerpfad und den letzten Ordnernamen
ordnerpfad = os.path.dirname(dateipfad)
ordnername = os.path.basename(ordnerpfad)

ICS_Eval_Result = analyze_plateaus(
    signal_dict,
    boost_range=(11, np.inf),
    hold_range=(3, 5),
    zero_range=(-0.5, 0.5),
    col="Injector Control Signal (A)", 
    ordnerpfad=ordnerpfad,
    T=T
    )

InjRate_Eval = InjectionRate(cv,cp,R,Temp,signal_dict,T, A)

# Hinzufügen der gewünschten Werte
signal_dict["Injection Rate (mg_ms)"] = InjRate_Eval["injrate_values"]
signal_dict["Mass (mg)"] = InjRate_Eval["cumulative_mass_values"]

if InterpSigMatrix == 1:    
    # Zielpfad 
    output_file = os.path.join(ordnerpfad, f"{ordnername}.xlsx")        
    interpolated_signals = interpolate_nested_signal_dict(signal_dict, T, step_size)          
    # Ordner erstellen, falls nicht vorhanden
    os.makedirs(ordnerpfad, exist_ok=True)    
    # Schreiben der Excel-Datei mit mehreren Sheets
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, df in interpolated_signals.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"Datei erfolgreich gespeichert unter: {output_file}")

plot_path = plot_grouped_signals_with_time(signal_dict, T, ordnerpfad)
print(f"Das Diagramm wurde gespeichert unter: {ordnerpfad}")

#avgMass = get_mass_average(signal_dict, T, step_size)
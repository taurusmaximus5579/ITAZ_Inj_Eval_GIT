# -*- coding: utf-8 -*-
"""
Created on Fri Oct  3 18:18:03 2025

@author: larsk
"""
import pandas as pd
import numpy as np
import os

from Fkt.Fig01 import plot_signals
from Fkt.SigRead01 import SigRead
from Fkt.Intpol01 import interpolate_signals
from Fkt.Shot2Shot01 import shot2shot

import tkinter as tk
from tkinter import filedialog

# Eingabe
IntTimeStep = 0.001 # In diesen Zeitschritten werden die Signale in die Excel geschrieben
Shot2Shot = 1 # 1 Auswertung machen; 0 keine Auswertung machen


root = tk.Tk()
root.withdraw()
dateipfad = filedialog.askopenfilename(
    title="Wähle eine CSV-Datei",
    filetypes=[("CSV-Dateien", "*.csv")]
)

if dateipfad:
    rawdata = SigRead(dateipfad)
    
    # Umrechnen der Signale
    signals = pd.DataFrame()
    signals['t in s'] = rawdata['in s'] - rawdata['in s'].iloc[0] 
    
    # Prüfen, ob 'C1' in den Spalten vorhanden ist
    if 'C1 in V' in rawdata.columns:       
       signals['lift (mm)'] = (rawdata['C1 in V'] - rawdata[rawdata['in s'] <= 0.5]['C1 in V'].median())*0.2       
    else:
       print("❌ Spalte 'C1' nicht gefunden.")
       rawdata = None
       
    # Prüfen, ob 'C2' in den Spalten vorhanden ist   
    if 'C2 in V' in rawdata.columns:       
       signals['pressure (abs_bar)'] = rawdata['C2 in V'] * 5       
    else:
       print("❌ Spalte 'C2' nicht gefunden.")
       rawdata = None
       
    # Prüfen, ob 'C4' in den Spalten vorhanden ist   
    if 'C4 in V' in rawdata.columns:            
       signals['injection rate (abs_bar)'] = rawdata['C4 in V']
    else:
       print("❌ Spalte 'C4' nicht gefunden.")
       rawdata = None
    
    # Prüfen, ob 'C3' in den Spalten vorhanden ist      
    if 'C3 in V' in rawdata.columns:       
       signals['current (A)'] = (rawdata['C3 in V'] - rawdata[rawdata['in s'] >= rawdata['in s'].max() - 0.05]['C3 in V'].median())*-10
    else:
       print("❌ Spalte 'C3' nicht gefunden.")
       rawdata = None
       
    # Berechnung der elektrischen Leistung
    signals['Power (W)'] = signals['current (A)'] * 50
    
    # Berechnung der elektrischen Energie in Ws (Joule)
    # Voraussetzung: 'Power (W)' und 't in s' sind vorhanden
    signals['Energy (Ws)'] = np.cumsum(np.gradient(signals['t in s']) * signals['Power (W)'])
    signals['Energy (Ws)'] = signals['Energy (Ws)'] - np.min(signals['Energy (Ws)'])
    
    # HTML Plots erstellen
    # Extrahiere den übergeordneten Ordnernamen
    parent_folder = os.path.basename(os.path.dirname(dateipfad))
    
    # Erstelle den HTML-Dateinamen mit dem Ordnernamen
    html_filename = f"{parent_folder}_rawdata.html"
    
    # Verwende den dynamischen Namen beim Speichern
    if rawdata is not None: 
        plot_signals(rawdata, dateipfad, html_filename, FigTyp=1) 
    else: 
        print("❌ Fehler beim Einlesen der Datei.")      
      
        
    # Interpolieren der Daten
    signals_interp = interpolate_signals(signals, IntTimeStep)
    
    # Ausgeben der Daten in Excel
    # Ursprünglicher Dateipfad
    pfad = os.path.dirname(dateipfad)
    # Übergeordneten Ordnernamen extrahieren
    ordnername = os.path.basename(pfad)
    # Neuen Dateinamen mit Ordnername erstellen
    filename = f"{ordnername}_signal_interp.xlsx"
    pfad = os.path.join(pfad, filename)
    df = pd.DataFrame(signals_interp)
    df.to_excel(pfad, index=False, engine='openpyxl')
    
    # Shot2Shot Auswertung
    if Shot2Shot == 1 :
        shot2shot(signals)
        
        # Erstelle den HTML-Dateinamen für die Signals-Plot
        html_filename_signals = f"{parent_folder}_shot2shot.html"
        # Verwende den dynamischen Namen beim Speichern
        if signals is not None:        
            plot_signals(signals, dateipfad, html_filename_signals, signals_to_plot=['lift (mm)', 'pressure (abs_bar)','injection rate (abs_bar)','current (A)','Power (W)'], FigTyp=2) 
        else:
            print("❌ Fehler beim Einlesen der Datei.")    
    
    # Erstelle den HTML-Dateinamen für die Signals-Plot
    html_filename_signals = f"{parent_folder}_signals.html"
    
    # Verwende den dynamischen Namen beim Speichern
    if signals is not None:        
        plot_signals(signals, dateipfad, html_filename_signals, signals_to_plot=['lift (mm)', 'pressure (abs_bar)','injection rate (abs_bar)','current (A)','Power (W)','counter'], FigTyp=1) 
    else:
        print("❌ Fehler beim Einlesen der Datei.")                 

else:
    print("⚠️ Keine Datei ausgewählt.")

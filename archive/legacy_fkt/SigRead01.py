# -*- coding: utf-8 -*-
"""
Created on Fri Oct  3 17:52:15 2025

@author: larsk

Tool for reading the raw data from the Rohde & Schawrz oscilloscope and for converting the measurement channels 
"""

# Fkt/SigRead.py

import pandas as pd

def SigRead(pfad):
    """
    Liest eine CSV-Datei ein und gibt die Rohdaten als DataFrame zurück.

    Parameter:
        pfad (str): Pfad zur CSV-Datei.

    Rückgabe:
        pd.DataFrame: Eingelesene Rohdaten.
    """
    try:
        df = pd.read_csv(pfad, sep=',', decimal='.')
        return df
    except Exception as e:
        print(f"Fehler beim Einlesen der Datei: {e}")
        return None
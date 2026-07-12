# -*- coding: utf-8 -*-
"""
Created on Wed Oct 29 17:05:58 2025

@author: larsk
"""


import numpy as np

def integrate_all_needle_lifts(signal_dict, T):
    T = np.asarray(T)
    dt = np.diff(T)
    needle_lifts = signal_dict.get("Needle Lift (mm)", {})
    integrated_results = {}

    for name, data in needle_lifts.items():
        data = np.asarray(data)

        if data.shape[0] != T.shape[0]:
            print(f"⚠️ Länge stimmt nicht überein bei {name}: {data.shape[0]} vs {T.shape[0]}")
            continue

        # Trapezregel: Mittelwert der benachbarten Punkte
        incremental_integral = dt * (data[:-1] + data[1:]) * 0.5
        integrated_lift = np.empty_like(data)
        integrated_lift[:-1] = np.cumsum(incremental_integral)
        integrated_lift[-1] = integrated_lift[-2]  # Letzten Wert wiederholen

        integrated_results[name] = integrated_lift

    return integrated_results
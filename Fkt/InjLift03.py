# -*- coding: utf-8 -*-
"""
Created on Wed Oct 29 17:05:58 2025

@author: larsk

InjLift03
- [✅] Eval Hubsignal; Start; Ende; Prellen
- [✅] Optimierung der Integration des Lifts
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.integrate import cumulative_trapezoid

def analyze_and_plot_needle_lifts(signal_dict, T):
    T = np.asarray(T)
    dt = np.diff(T)
    needle_lifts = signal_dict.get("Needle Lift (mm)", {})
    integrated_results = {}
    hub_times = {}

    # Parameter für Glättung und Offset
    window_size = 501  # starke Glättung
    polyorder = 3
    offset_time = 0.001  # s
    threshold = 0.003  # Fester Schwellwert in mm   

    for name, data in needle_lifts.items():
        data = np.asarray(data)

        if data.shape[0] != T.shape[0]:
            print(f"⚠️ Länge stimmt nicht überein bei {name}: {data.shape[0]} vs {T.shape[0]}")
            continue

        # --- Signal glätten ---
        #kernel = np.ones(window_size) / window_size
        #smoothed = np.convolve(data, kernel, mode='same')
        smoothed = savgol_filter(data, window_size, polyorder)

        # --- Offsetkorrektur ---
        offset_idx = np.searchsorted(T, offset_time)
        offset = np.mean(smoothed[:offset_idx])
        corrected = smoothed - offset

        # --- Startsuche erst ab 0,001s ---
        mask = T >= offset_time
        above = np.where((corrected > threshold) & mask)[0]
        if len(above) == 0:
            start_idx = end_idx = None
            start_time = end_time = None
        else:
            start_idx = above[0]
            end_idx = above[-1]
            start_time = T[start_idx]
            end_time = T[end_idx]

            # --- Verfeinerung der Endzeit
            fall_threshold =  threshold  # mm
            end_idx = None
            for i in range(start_idx, len(corrected)):
                if corrected[i] < fall_threshold:
                    end_idx = i
                    end_time = T[end_idx]
                    break

        # --- Integration ---  
        # --- Integration ---
        integrated_lift = cumulative_trapezoid(data, dx=dt, initial=0)
        
        # Ergebnisse speichern
        integrated_results[name] = integrated_lift
        hub_times[name] = {
            "start_index": start_idx,
            "start_time": start_time,
            "end_index": end_idx,
            "end_time": end_time
        }

    # Steuerung: Einzelplots aktivieren oder nicht
    show_individual_plots = True  # Auf False setzen, wenn keine Einzelplots gewünscht
    
    # --- Plot der Originaldaten + geglättete Daten (Gesamtübersicht) ---
    plt.figure(figsize=(10, 6))
    for name, data in needle_lifts.items():
        if len(data) == len(T):
            smoothed = savgol_filter(data, window_size, polyorder)
            plt.plot(T, smoothed, label=f"Geglättet - {name}", linestyle='--')
    
            if hub_times[name]["start_time"] is not None:
                plt.axvline(hub_times[name]["start_time"], color='green', linestyle='--', linewidth=1)
            if hub_times[name]["end_time"] is not None:
                plt.axvline(hub_times[name]["end_time"], color='red', linestyle='--', linewidth=1)
    
    plt.title("Needle Lift Measurements – Gesamtübersicht")
    plt.xlabel("Time (s)")
    plt.ylabel("Needle Lift (mm)")
    plt.grid(True)
    #plt.legend()
    plt.tight_layout()
    plt.show()
    
    # --- Einzelplots pro Messung ---
    if show_individual_plots:
        for name, data in needle_lifts.items():
            if len(data) == len(T):
                smoothed = savgol_filter(data, window_size, polyorder)
                
                plt.figure(figsize=(8, 5))
                plt.plot(T, data, label=f"Original - {name}", color='grey')
                plt.plot(T, smoothed, label=f"Geglättet - {name}", linestyle='--', color='blue')                
    
                if hub_times[name]["start_time"] is not None:
                    plt.axvline(hub_times[name]["start_time"], color='green', linestyle='--', linewidth=1)
                if hub_times[name]["end_time"] is not None:
                    plt.axvline(hub_times[name]["end_time"], color='red', linestyle='--', linewidth=1)
    
                plt.title(f"Needle Lift – {name}")
                plt.xlabel("Time (s)")
                plt.ylabel("Needle Lift (mm)")
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                plt.show()

    # --- Zusätzlicher Plot: Zwei Diagramme untereinander ---
    max_lift = 0.008
    fig, axes = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

    for name, data in needle_lifts.items():
        if len(data) == len(T):
            if np.max(data) > max_lift:
                continue  # Messung überspringen

            kernel = np.ones(window_size) / window_size
            smoothed = np.convolve(data, kernel, mode='same')
            offset_idx = np.searchsorted(T, offset_time)
            offset = np.mean(smoothed[:offset_idx])
            corrected = smoothed - offset

            axes[0].plot(T, data, label=f"{name}")
            axes[1].plot(T, corrected, label=f"{name}")

    axes[0].set_title(f"Unfiltered measurements (max Needle Lift ≤ {max_lift} mm)")
    axes[0].set_ylabel("Needle Lift (mm)")
    axes[0].grid(True)

    axes[1].set_title("Filtered measurements (filtered + Offset correction)")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Needle Lift (mm)")
    axes[1].grid(True)

    plt.tight_layout()
    plt.show()

    # --- Gemeinsames Histogramm für Start- und Endzeiten ---
    start_times = [v['start_time'] for v in hub_times.values() if v['start_time'] is not None]
    end_times = [v['end_time'] for v in hub_times.values() if v['end_time'] is not None]

    if start_times and end_times:
        # Gemeinsame Bins basierend auf kombinierten Zeiten
        all_times = np.array(start_times + end_times)
        bins = len(data)*2  # Anzahl der Messungen = Anzahl der Bins
        bins = np.histogram_bin_edges(all_times, bins)

        fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

        axes[0].hist(start_times, bins=bins, color='skyblue', edgecolor='black')
        axes[0].set_title('Histogram of the start times of the Needle Lifts')
        axes[0].set_ylabel('Number of measurements')
        axes[0].grid(True)

        axes[1].hist(end_times, bins=bins, color='salmon', edgecolor='black')
        axes[1].set_title('Histogram of the end times of the Needle Lifts')
        axes[1].set_xlabel('Time (s)')
        axes[1].set_ylabel('Number of measurements')
        axes[1].grid(True)

        plt.tight_layout()
        plt.show()
    else:
        print("⚠️ Nicht genügend gültige Start- oder Endzeiten für Histogramm.")

    return integrated_results, hub_times
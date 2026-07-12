# -*- coding: utf-8 -*-
"""
Created on Sun Oct 19 11:22:41 2025
@author: larsk

[✅] Keine Speicherung der Diagramme mehr. Nur Abbildung in Python
[✅] Histogramme hinzugefügt um die Qualität des Findens der Zeitpunkte und Ströme zu checken
[✅] Alle Stromsignale in ein Diagramm
[✅] Mittelwert und Standardabweichung für die markanten Punkte der Stromsignale berechnet 
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def analyze_plateaus(signal_dict, boost_range, hold_range, zero_range, col="Injector Control Signal (A)", window=20, stability=1, T=None):
    result_all = {}
    colors = ["black", "blue", "green", "red", "orange", "purple", "brown"]
    plateau_colors = {"Boost": "red", "Hold": "green", "Zero": "blue"}

    boost_medians = []
    hold_medians = []
    zero_medians = []
    ics_on_times = []
    ics_off_times = []

    plt.figure(figsize=(12, 6))

    for idx, (key, strom_raw) in enumerate(signal_dict[col].items()):
        strom = np.array(strom_raw)
        diff = np.abs(pd.Series(strom).diff().fillna(0))
        stable = diff.rolling(window, center=True).mean().fillna(1) < stability

        result = {}
        medians = {}

        for name, (minv, maxv) in zip(["Boost", "Hold", "Zero"], [boost_range, hold_range, zero_range]):
            mask = (strom >= minv) & (strom <= maxv) & stable
            werte = strom[mask]
            if len(werte) > 0:
                median = float(np.median(werte))
                mean = float(np.mean(werte))
                result[name] = {
                    "Median": round(median, 3),
                    "Mittelwert": round(mean, 3),
                    "Anzahl": int(len(werte))
                }
                medians[name] = round(median, 3)
                if name == "Boost":
                    boost_medians.append(median)
                elif name == "Hold":
                    hold_medians.append(median)
                elif name == "Zero":
                    zero_medians.append(median)

        mask_above = strom > 0.5
        if np.any(mask_above):
            first_idx = np.where(mask_above)[0][0]
            last_idx = np.where(mask_above)[0][-1]
            T_first_shifted = round(T[first_idx] - 0.00005, 8)
            T_last_shifted = round(T[last_idx] + 0.00005, 8)
            T_ICS_ON = round(T_last_shifted - T_first_shifted, 8)
            result["ICS_ON_time"] = T_first_shifted
            result["ICS_OFF_time"] = T_last_shifted
            result["ICS_ON"] = T_ICS_ON
            ics_on_times.append(T_first_shifted)
            ics_off_times.append(T_last_shifted)

            plt.axvline(x=T_first_shifted, color="blue", linestyle="--", linewidth=1, label=f"{key} ICS_ON")
            plt.axvline(x=T_last_shifted, color="red", linestyle="--", linewidth=1, label=f"{key} ICS_OFF")

        result_all[key] = result
        plt.plot(T, strom, label=f"{key}", color=colors[idx % len(colors)])

        for name, median in medians.items():
            plt.axhline(y=median, color=plateau_colors[name], linestyle="--", linewidth=1, label=f"{key} {name} Median")

    plt.title("Injector Control Signal Curves with Median and Switching Time Lines")
    plt.xlabel("Time")
    plt.ylabel("Injector Control Signal (A)")
    plt.grid(True)
    plt.tight_layout()
    #plt.legend()
    plt.show()

    # Funktion zum Plotten von Histogrammen der Medianwerte mit Textinfo
    def plot_median_histogram(data, title, color):
        if not data:
            return
        mean = np.mean(data)
        std = np.std(data)
        bins = len(data)*2  # Anzahl der Messungen = Anzahl der Bins
        plt.figure()
        plt.hist(data, bins=bins, color=color, alpha=0.7)
        plt.title(title)
        plt.xlabel('median value')
        plt.ylabel('Number of measurements')
        plt.grid(True)
        plt.text(0.95, 0.95, f"Mittelwert = {mean:.5f}\nStd = {std:.5f}",
                 transform=plt.gca().transAxes,
                 verticalalignment='top', horizontalalignment='right',
                 bbox=dict(facecolor='white', alpha=0.5))
        plt.tight_layout()
        plt.show()

    # Histogramme der Medianwerte anzeigen
    plot_median_histogram(boost_medians, "Boost Current Histogram", "red")
    plot_median_histogram(hold_medians, "Hold Current Histogram", "green")
    plot_median_histogram(zero_medians, "Zero Current Histogram", "blue")
    plot_median_histogram(ics_on_times, "ICS_ON Time Histogram", "orange")
    plot_median_histogram(ics_off_times, "ICS_OFF Time Histogram", "purple")

    # Statistische Auswertung der Mediane und Zeiten
    def print_stats(name, values):
        if values:
            mean = np.mean(values)
            std = np.std(values)
            print(f"{name}: mean value = {mean:.5f}, standard deviation = {std:.5f}")

    print("\nStatistische evaluation of all measurements:")
    print_stats("Boost Median", boost_medians)
    print_stats("Hold Median", hold_medians)
    print_stats("Zero Median", zero_medians)
    print_stats("ICS_ON Zeit", ics_on_times)
    print_stats("ICS_OFF Zeit", ics_off_times)

    return result_all
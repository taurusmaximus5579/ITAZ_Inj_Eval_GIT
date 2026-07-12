# -*- coding: utf-8 -*-
"""
Created on Sun Oct 19 11:22:41 2025
@author: larsk
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

def analyze_plateaus(signal_dict, boost_range, hold_range, zero_range, col="Injector Control Signal (A)", window=20, stability=1, ordnerpfad=None, T=None):
    result_all = {}

    for key, strom_raw in signal_dict[col].items():
        strom = np.array(strom_raw)

        # Berechnung stabiler Werte
        diff = np.abs(pd.Series(strom).diff().fillna(0))
        stable = diff.rolling(window, center=True).mean().fillna(1) < stability

        result = {}
        medians = {}
        colors = {"Boost": "red", "Hold": "green", "Zero": "blue"}

        for name, (minv, maxv) in zip(
            ["Boost", "Hold", "Zero"],
            [boost_range, hold_range, zero_range]
        ):
            mask = (strom >= minv) & (strom <= maxv) & stable
            werte = strom[mask]
            if len(werte) > 0:
                median = float(np.median(werte))
                result[name] = {
                    "Median": round(median, 5),
                    "Mittelwert": round(float(np.mean(werte)), 5),
                    "Anzahl": int(len(werte))
                }
                medians[name] = round(median, 5)

        # ICS_ON und ICS_OFF Zeiten speichern
        mask_above = strom > 0.5
        if np.any(mask_above):
            first_idx = np.where(mask_above)[0][0]
            last_idx = np.where(mask_above)[0][-1]
            T_first_shifted = round(T[first_idx] - 0.00005, 8)
            T_last_shifted = round(T[last_idx] + 0.00004, 8)
            T_ICS_ON = round(T_last_shifted - T_first_shifted, 8)
            result["ICS_ON_time"] = T_first_shifted
            result["ICS_OFF_time"] = T_last_shifted
            result["ICS_ON"] = T_ICS_ON
        result_all[key] = result
        # Plot erstellen
        plot_path = os.path.join(ordnerpfad, f"ICS_Plot_{key}.png")
        plt.figure(figsize=(10, 4))
        plt.plot(T, strom, label="Signal", color="black")

        T_above = T[mask_above]
        strom_above = strom[mask_above]

        if np.any(mask_above):
            plt.scatter(T_above, strom_above, color="green", s=20, label="ICS switched")
            plt.axvline(
                x=T_first_shifted,
                color="blue",
                linestyle="--",
                linewidth=1,
                label=f"ICS_ON: {T_first_shifted:.4f}s"
            )
            plt.axvline(
                x=T_last_shifted,
                color="red",
                linestyle="--",
                linewidth=1,
                label=f"ICS_OFF: {T_last_shifted:.4f}s"
            )
            plt.text(
                T_first_shifted,
                min(strom)-0.05,
                "ICS_ON",
                color="blue",
                rotation=90,
                verticalalignment='bottom'
            )
            plt.text(
                T_last_shifted,
                min(strom)-0.05,
                "ICS_OFF",
                color="red",
                rotation=90,
                verticalalignment='bottom'
            )
            # ICS_ON Dauer in die Legende
            plt.plot([], [], ' ', label=f"ICS_ON Dauer: {T_ICS_ON:.4f}s")

        for name, median in medians.items():
            plt.axhline(y=median, color=colors[name], linestyle="--", label=f"{name} Median: {median:.4f} A")

        plt.title(f"Injector Control Signal Curve for {key}")
        plt.xlabel("Time")
        plt.ylabel("Injector Control Signal (A)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()

    return result_all
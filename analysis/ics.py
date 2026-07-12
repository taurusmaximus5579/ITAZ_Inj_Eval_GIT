import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from image_cache_manager import get_cache
from image_utils import persist_or_cache_figure


def analyze_plateaus(signal_dict, boost_range, hold_range, zero_range,
                     col="Injector Control Signal (A)", window=20, stability=1,
                     T=None, ordnerpfad=None):
    if signal_dict is None or not isinstance(signal_dict, dict):
        raise ValueError("Fehler: signal_dict ist None oder kein Dictionary.")
    if col not in signal_dict:
        raise KeyError(f"Fehler: Spalte '{col}' nicht in signal_dict gefunden. Verfügbare Keys: {list(signal_dict.keys())}")
    if T is None or len(T) == 0:
        raise ValueError("Fehler: Zeitvektor T ist None oder leer.")
    if not (isinstance(boost_range, tuple) and isinstance(hold_range, tuple) and isinstance(zero_range, tuple)):
        raise ValueError("Fehler: boost_range, hold_range und zero_range müssen Tupel sein.")

    # Bilder werden nur im Memory gehalten, nicht auf der Festplatte gespeichert

    result_all = {}
    colors = ["black", "blue", "green", "red", "orange", "purple", "brown"]
    plateau_colors = {"Boost": "red", "Hold": "green", "Zero": "blue"}

    boost_medians, hold_medians, zero_medians = [], [], []
    ics_on_times, ics_off_times = [], []

    plt.figure(figsize=(14, 8), constrained_layout=True)

    strom_signale = signal_dict[col]
    if not isinstance(strom_signale, dict) or len(strom_signale) == 0:
        raise ValueError("Fehler: signal_dict[col] ist leer oder kein Dictionary.")

    for idx, (key, strom_raw) in enumerate(strom_signale.items()):
        strom = np.array(strom_raw)
        if len(strom) != len(T):
            print(f"Warnung: Länge von Stromsignal '{key}' ({len(strom)}) passt nicht zu T ({len(T)}).")
            continue

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
                result[name] = {"Median": round(median, 3), "Mittelwert": round(mean, 3), "Anzahl": int(len(werte))}
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

        result_all[key] = result
        plt.plot(T, strom, color=colors[idx % len(colors)], label=key)

        plt.figure(figsize=(12, 6), constrained_layout=True)
        plt.plot(T, strom, color=colors[idx % len(colors)], label=key)
        plt.title(f"Stromsignal: {key}")
        plt.xlabel("Time")
        plt.ylabel("Injector Control Signal (A)")
        plt.grid(True)

        for name, median in medians.items():
            plt.axhline(y=median, color=plateau_colors[name], linestyle="--", linewidth=1, label=f"{name}-Median = {median:.3f}A")

        if "ICS_ON_time" in result and "ICS_OFF_time" in result:
            plt.axvline(result["ICS_ON_time"], color="blue", linestyle="--", linewidth=1, label=f"ICS On = {result['ICS_ON_time']:.6f}s")
            plt.axvline(result["ICS_OFF_time"], color="red", linestyle="--", linewidth=1, label=f"ICS Off = {result['ICS_OFF_time']:.6f}s")
            plt.axvline(result["ICS_OFF_time"], color="purple", linestyle=":", linewidth=1, label=f"Duration = {result['ICS_ON']:.6f}s")

        plt.legend(fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
        fig = plt.gcf()
        persist_or_cache_figure(fig, image_cache=get_cache(), category="ICS", name=f"Signal_{idx}", save_to_disk=False)

    for val in boost_medians:
        plt.axhline(y=val, color="red", linestyle="--", linewidth=1)
    for val in hold_medians:
        plt.axhline(y=val, color="green", linestyle="--", linewidth=1)
    for val in zero_medians:
        plt.axhline(y=val, color="blue", linestyle="--", linewidth=1)
    for t_on in ics_on_times:
        plt.axvline(x=t_on, color="blue", linestyle="--", linewidth=1)
    for t_off in ics_off_times:
        plt.axvline(x=t_off, color="red", linestyle="--", linewidth=1)

    plt.title("Injector Control Signal Curves")
    plt.xlabel("Time")
    plt.ylabel("Injector Control Signal (A)")
    plt.grid(True)
    fig = plt.gcf()
    persist_or_cache_figure(fig, image_cache=get_cache(), category="ICS", name="Overview", save_to_disk=False)

    def plot_median_histogram(data, title, color, name):
        if not data:
            return
        mean = np.mean(data)
        std = np.std(data)
        bins = max(10, len(data) * 2)
        plt.figure()
        plt.hist(data, bins=bins, color=color, alpha=0.7)
        plt.title(title)
        plt.xlabel('Median value')
        plt.ylabel('Number of measurements')
        plt.grid(True)
        plt.text(0.95, 0.95, f"Mittelwert = {mean:.5f}\nStd = {std:.5f}", transform=plt.gca().transAxes, verticalalignment='top', horizontalalignment='right', bbox=dict(facecolor='white', alpha=0.5))
        plt.legend().set_visible(False)
        plt.tight_layout()
        fig = plt.gcf()
        persist_or_cache_figure(fig, image_cache=get_cache(), category="ICS", name=name, save_to_disk=False)

    plot_median_histogram(boost_medians, "Boost Current Histogram", "red", "Boost")
    plot_median_histogram(hold_medians, "Hold Current Histogram", "green", "Hold")
    plot_median_histogram(zero_medians, "Zero Current Histogram", "blue", "Zero")
    plot_median_histogram(ics_on_times, "ICS_ON Time Histogram", "orange", "ICS_ON_Histogram.png")
    plot_median_histogram(ics_off_times, "ICS_OFF Time Histogram", "purple", "ICS_OFF_Histogram.png")

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

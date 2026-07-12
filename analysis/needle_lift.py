import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.integrate import cumulative_trapezoid
from image_utils import persist_or_cache_figure


def analyze_and_plot_needle_lifts(signal_dict, T, ordnerpfad=None, image_cache=None, save_to_disk=False):
    bilder_pfad = os.path.join(ordnerpfad, "Bilder") if ordnerpfad else os.path.join(".", "Bilder")
    os.makedirs(bilder_pfad, exist_ok=True)

    T = np.asarray(T)
    dt = np.diff(T)
    needle_lifts = signal_dict.get("Needle Lift (mm)", {})
    integrated_results = {}
    hub_times = {}

    window_size = 501
    polyorder = 3
    offset_time = 0.001
    threshold = 0.003

    for name, data in needle_lifts.items():
        data = np.asarray(data)

        if data.shape[0] != T.shape[0]:
            print(f"⚠️ Länge stimmt nicht überein bei {name}: {data.shape[0]} vs {T.shape[0]}")
            continue

        smoothed = savgol_filter(data, window_size, polyorder)
        offset_idx = np.searchsorted(T, offset_time)
        offset = np.mean(smoothed[:offset_idx]) if offset_idx > 0 else 0.0
        corrected = smoothed - offset

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

            fall_threshold = threshold
            for i in range(start_idx, len(corrected)):
                if corrected[i] < fall_threshold:
                    end_idx = i
                    end_time = T[end_idx]
                    break

        integrated_lift = cumulative_trapezoid(data, dx=dt, initial=0)
        integrated_window = np.zeros_like(integrated_lift)

        if start_idx is not None and end_idx is not None:
            partial = cumulative_trapezoid(data[start_idx:end_idx+1], dx=dt[start_idx:end_idx], initial=0)
            integrated_window[start_idx:end_idx+1] = partial
            integrated_window[end_idx+1:] = partial[-1]
        else:
            integrated_window[:] = 0

        integrated_results[name] = integrated_window
        hub_times[name] = {
            "start_index": start_idx,
            "start_time": start_time,
            "end_index": end_idx,
            "end_time": end_time,
        }

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
    plt.tight_layout()
    overview_path = os.path.join(bilder_pfad, "NeedleLift_Overview.png")
    persist_or_cache_figure(plt.gcf(), output_path=overview_path if save_to_disk else None, image_cache=image_cache, category="Nadelhub", name="NeedleLift_Overview", save_to_disk=save_to_disk, dpi=150)
    print(f"✅ Übersicht gespeichert: {overview_path}")
    plt.close()

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
            single_path = os.path.join(bilder_pfad, f"NeedleLift_{name}.png")
            persist_or_cache_figure(plt.gcf(), output_path=single_path if save_to_disk else None, image_cache=image_cache, category="Nadelhub", name=f"NeedleLift_{name}", save_to_disk=save_to_disk, dpi=150)
            print(f"✅ Einzelplot gespeichert: {single_path}")
            plt.close()

    start_times = [v['start_time'] for v in hub_times.values() if v['start_time'] is not None]
    end_times = [v['end_time'] for v in hub_times.values() if v['end_time'] is not None]

    if start_times and end_times:
        all_times = np.array(start_times + end_times)
        bins = np.histogram_bin_edges(all_times, bins=len(all_times))

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
        hist_path = os.path.join(bilder_pfad, "NeedleLift_Histogram.png")
        persist_or_cache_figure(plt.gcf(), output_path=hist_path if save_to_disk else None, image_cache=image_cache, category="Ergebnisse", name="NeedleLift_Histogram", save_to_disk=save_to_disk, dpi=150)
        print(f"✅ Histogramm gespeichert: {hist_path}")
        plt.close()
    else:
        print("⚠️ Nicht genügend gültige Start- oder Endzeiten für Histogramm.")

    print(f"\n✅ Alle Diagramme gespeichert unter: {bilder_pfad}")
    return integrated_results, hub_times

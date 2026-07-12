"""
XX.XX.2025 Lars Köhler
neue Funktion
Statistische Auswertung von Shot2Shot Messungen
"""
import matplotlib.pyplot as plt
import os
import math
import numpy as np

from Fkt.build_shot_stats01 import build_shot_stats
from Fkt.plot_scatter_matrix01 import plot_scatter_matrix


# ---------------------------------------------------------
# ZENTRALE STATISTIKFUNKTION (ABSOLUT + PROZENT)
# ---------------------------------------------------------
def stats_with_percent(arr):
    arr = np.array(arr, dtype=float)
    mean = np.mean(arr)
    std = np.std(arr)

    low = mean - 3 * std
    high = mean + 3 * std

    if mean != 0:
        std_pct = 100 * std / mean
        low_pct = 100 * (low - mean) / mean     # NEGATIVES Delta
        high_pct = 100 * (high - mean) / mean   # POSITIVES Delta
    else:
        std_pct = low_pct = high_pct = 0

    return {
        "mean": mean,
        "std": std,
        "low": low,
        "high": high,
        "std_pct": std_pct,
        "low_pct": low_pct,
        "high_pct": high_pct
    }


def Eval_Shot2Shot(signal_dict, T, min_time_step, ICS_Eval_Result, hub_times, ordnerpfad,
                   use_subplots=True):

    os.makedirs(ordnerpfad, exist_ok=True)

    bilder_pfad = os.path.join(ordnerpfad, "Bilder")
    os.makedirs(bilder_pfad, exist_ok=True)

    signal_names = list(signal_dict.keys())
    n_signals = len(signal_names)

    # ---------------------------------------------------------
    # ZENTRALER STATISTIK-CONTAINER
    # ---------------------------------------------------------
    all_stats = {
        "NeedleLift": {},
        "Mass": {},
        "ICS": {},
        "NeedleLiftIntegrated": {},
        "SystemPressure": {}
    }

    # ---------------------------------------------------------
    # GESAMTPLOTS (Subplots)
    # ---------------------------------------------------------
    if use_subplots:
        cols = 2
        rows = math.ceil(n_signals / cols)
        fig, axes = plt.subplots(rows, cols, figsize=(14, 2 * rows), sharex=True)
        axes = axes.flatten()
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        axes = [ax] * n_signals

    for i, sig_name in enumerate(signal_names):
        ax = axes[i]
        messungen = signal_dict[sig_name]

        for mess_name, y in messungen.items():
            ax.plot(T, y, label=mess_name, alpha=0.6)

        ax.set_title(sig_name)
        ax.set_ylabel(sig_name)
        ax.grid(True)

    for j in range(n_signals, len(axes)):
        axes[j].set_visible(False)

    axes[-1].set_xlabel("Zeit [s]")

    fig.tight_layout()
    fig.savefig(os.path.join(bilder_pfad, "Shot2Shot_Signale.png"), dpi=150)
    plt.close(fig)

    # ---------------------------------------------------------
    # EINZELPLOTS
    # ---------------------------------------------------------
    for sig_name in signal_names:
        fig, ax = plt.subplots(figsize=(10, 6))
        messungen = signal_dict[sig_name]

        for mess_name, y in messungen.items():
            ax.plot(T, y, label=mess_name, alpha=0.6)

        ax.set_title(sig_name)
        ax.set_xlabel("Zeit [s]")
        ax.set_ylabel(sig_name)
        ax.grid(True)

        # ---------------------------------------------------------
        # NEEDLE LIFT
        # ---------------------------------------------------------
        if sig_name == "Needle Lift (mm)":
            start_times = []
            end_times = []

            for messung in hub_times.values():
                if isinstance(messung, dict):
                    start_times.append(float(messung.get("start_time", 0)))
                    end_times.append(float(messung.get("end_time", 0)))

            st = stats_with_percent(start_times)
            et = stats_with_percent(end_times)

            max_lifts = []
            max_lift_times = []

            for mess_name, y in messungen.items():
                y = np.array(y)
                idx = np.argmax(y)
                max_lifts.append(y[idx])
                max_lift_times.append(T[idx])

            ml = stats_with_percent(max_lifts)
            mlt = stats_with_percent(max_lift_times)

            # Statistik speichern
            all_stats["NeedleLift"] = {
                "StartTimes": st,
                "EndTimes": et,
                "MaxLift": ml,
                "MaxLiftTime": mlt
            }

            # Vertikale Linien
            for x in [st["mean"], st["low"], st["high"], et["mean"], et["low"], et["high"]]:
                ax.axvline(x=x,
                           color='red' if x in [st["mean"], et["mean"]] else 'orange',
                           linestyle='--', linewidth=1.5)

            for x in [mlt["mean"], mlt["low"], mlt["high"]]:
                ax.axvline(x=x,
                           color='green' if x == mlt["mean"] else 'lime',
                           linestyle='--', linewidth=1.5)

            # Tabelle
            table_data = [
                ["", "Mean", "Std", "Std [%]", "-3σ", "-3σ [%]", "+3σ", "+3σ [%]"],
                ["Start Time [s]", f"{st['mean']:.6f}", f"{st['std']:.6f}", f"{st['std_pct']:.2f}",
                 f"{st['low']:.6f}", f"{st['low_pct']:.2f}", f"{st['high']:.6f}", f"{st['high_pct']:.2f}"],
                ["End Time [s]", f"{et['mean']:.6f}", f"{et['std']:.6f}", f"{et['std_pct']:.2f}",
                 f"{et['low']:.6f}", f"{et['low_pct']:.2f}", f"{et['high']:.6f}", f"{et['high_pct']:.2f}"],
                ["Max Lift [mm]", f"{ml['mean']:.6f}", f"{ml['std']:.6f}", f"{ml['std_pct']:.2f}",
                 f"{ml['low']:.6f}", f"{ml['low_pct']:.2f}", f"{ml['high']:.6f}", f"{ml['high_pct']:.2f}"],
                ["Max Lift Time [s]", f"{mlt['mean']:.6f}", f"{mlt['std']:.6f}", f"{mlt['std_pct']:.2f}",
                 f"{mlt['low']:.6f}", f"{mlt['low_pct']:.2f}", f"{mlt['high']:.6f}", f"{mlt['high_pct']:.2f}"]
            ]

            table = ax.table(cellText=table_data, cellLoc='center',
                             loc='bottom', bbox=[0.0, -0.65, 1.0, 0.4])
            table.set_fontsize(10)
            fig.subplots_adjust(bottom=0.40)

        # ---------------------------------------------------------
        # MASS (mg)
        # ---------------------------------------------------------
        if sig_name == "Mass (mg)":

            mass_arrays = np.array([np.array(y, dtype=float) for y in messungen.values()])
            mean_vals = np.mean(mass_arrays, axis=0)
            std_vals = np.std(mass_arrays, axis=0)

            plus_3sigma = mean_vals + 3 * std_vals
            minus_3sigma = mean_vals - 3 * std_vals

            ax.plot(T, mean_vals, color="blue", linewidth=2, label="Mean")
            ax.plot(T, plus_3sigma, color="red", linestyle="--", linewidth=1.5)
            ax.plot(T, minus_3sigma, color="red", linestyle="--", linewidth=1.5)

            max_per_shot = np.max(mass_arrays, axis=1)
            ms = stats_with_percent(max_per_shot)

            # Statistik speichern
            all_stats["Mass"] = {
                "MaxMass": ms
            }

            table_data = [
                ["", "Mean [mg]", "Std", "Std [%]", "-3σ", "-3σ [%]", "+3σ", "+3σ [%]"],
                ["Max", f"{ms['mean']:.6f}", f"{ms['std']:.6f}", f"{ms['std_pct']:.2f}",
                 f"{ms['low']:.6f}", f"{ms['low_pct']:.2f}", f"{ms['high']:.6f}", f"{ms['high_pct']:.2f}"],
            ]

            table = ax.table(cellText=table_data, cellLoc='center',
                             loc='bottom', bbox=[0.0, -0.55, 1.0, 0.40])
            table.set_fontsize(10)
            fig.subplots_adjust(bottom=0.32)

        # ---------------------------------------------------------
        # ICS
        # ---------------------------------------------------------
        if sig_name == "Injector Control Signal (A)":

            on_times = []
            off_times = []
            on_durations = []
            boost_vals = []
            hold_vals = []
            zero_vals = []

            for mess_name in messungen.keys():
                if mess_name in ICS_Eval_Result:
                    res = ICS_Eval_Result[mess_name]

                    on_times.append(float(res.get("ICS_ON_time", 0)))
                    off_times.append(float(res.get("ICS_OFF_time", 0)))
                    on_durations.append(float(res.get("ICS_ON", 0)))

                    boost_vals.append(float(res["Boost"]["Median"]))
                    hold_vals.append(float(res["Hold"]["Median"]))
                    zero_vals.append(float(res["Zero"]["Median"]))

            st_on = stats_with_percent(on_times)
            st_off = stats_with_percent(off_times)
            st_dur = stats_with_percent(on_durations)
            st_boost = stats_with_percent(boost_vals)
            st_hold = stats_with_percent(hold_vals)
            st_zero = stats_with_percent(zero_vals)

            # Statistik speichern
            all_stats["ICS"] = {
                "ON_time": st_on,
                "OFF_time": st_off,
                "ON_duration": st_dur,
                "Boost": st_boost,
                "Hold": st_hold,
                "Zero": st_zero
            }

            # Linien
            for x in [st_on["mean"], st_on["low"], st_on["high"]]:
                ax.axvline(x=x, color='green' if x == st_on["mean"] else 'lime',
                           linestyle='--', linewidth=1.5)

            for x in [st_off["mean"], st_off["low"], st_off["high"]]:
                ax.axvline(x=x, color='red' if x == st_off["mean"] else 'orange',
                           linestyle='--', linewidth=1.5)

            ax.axvspan(st_on["mean"], st_off["mean"], color='yellow', alpha=0.15)

            table_data = [
                ["", "Mean", "Std", "Std [%]", "-3σ", "-3σ [%]", "+3σ", "+3σ [%]"],
                ["ICS ON time [s]", f"{st_on['mean']:.6f}", f"{st_on['std']:.6f}", f"{st_on['std_pct']:.2f}",
                 f"{st_on['low']:.6f}", f"{st_on['low_pct']:.2f}", f"{st_on['high']:.6f}", f"{st_on['high_pct']:.2f}"],
                ["ICS OFF time [s]", f"{st_off['mean']:.6f}", f"{st_off['std']:.6f}", f"{st_off['std_pct']:.2f}",
                 f"{st_off['low']:.6f}", f"{st_off['low_pct']:.2f}", f"{st_off['high']:.6f}", f"{st_off['high_pct']:.2f}"],
                ["ICS ON duration [s]", f"{st_dur['mean']:.6f}", f"{st_dur['std']:.6f}", f"{st_dur['std_pct']:.2f}",
                 f"{st_dur['low']:.6f}", f"{st_dur['low_pct']:.2f}", f"{st_dur['high']:.6f}", f"{st_dur['high_pct']:.2f}"],
                ["Boost Median [A]", f"{st_boost['mean']:.6f}", f"{st_boost['std']:.6f}", f"{st_boost['std_pct']:.2f}",
                 f"{st_boost['low']:.6f}", f"{st_boost['low_pct']:.2f}", f"{st_boost['high']:.6f}", f"{st_boost['high_pct']:.2f}"],
                ["Hold Median [A]", f"{st_hold['mean']:.6f}", f"{st_hold['std']:.6f}", f"{st_hold['std_pct']:.2f}",
                 f"{st_hold['low']:.6f}", f"{st_hold['low_pct']:.2f}", f"{st_hold['high']:.6f}", f"{st_hold['high_pct']:.2f}"],
                ["Zero Median [A]", f"{st_zero['mean']:.6f}", f"{st_zero['std']:.6f}", f"{st_zero['std_pct']:.2f}",
                 f"{st_zero['low']:.6f}", f"{st_zero['low_pct']:.2f}", f"{st_zero['high']:.6f}", f"{st_zero['high_pct']:.2f}"],
            ]

            table = ax.table(cellText=table_data, cellLoc='center',
                             loc='bottom', bbox=[0.0, -0.65, 1.0, 0.45])
            table.set_fontsize(10)
            fig.subplots_adjust(bottom=0.42)

        # ---------------------------------------------------------
        # NEEDLE LIFT INTEGRATED
        # ---------------------------------------------------------
        if sig_name == "Needle Lift Integrated (mm_s)":

            lift_int_arrays = np.array([np.array(y, dtype=float) for y in messungen.values()])
            mean_vals = np.mean(lift_int_arrays, axis=0)
            std_vals = np.std(lift_int_arrays, axis=0)

            plus_3sigma = mean_vals + 3 * std_vals
            minus_3sigma = mean_vals - 3 * std_vals

            ax.plot(T, mean_vals, color="blue", linewidth=2)
            ax.plot(T, plus_3sigma, color="red", linestyle="--", linewidth=1.5)
            ax.plot(T, minus_3sigma, color="red", linestyle="--", linewidth=1.5)

            max_per_shot = np.max(lift_int_arrays, axis=1)
            st_int = stats_with_percent(max_per_shot)

            # Statistik speichern
            all_stats["NeedleLiftIntegrated"] = {
                "MaxIntegratedLift": st_int
            }

            table_data = [
                ["", "Mean [mm_s]", "Std", "Std [%]", "-3σ", "-3σ [%]", "+3σ", "+3σ [%]"],
                ["Max", f"{st_int['mean']:.6f}", f"{st_int['std']:.6f}", f"{st_int['std_pct']:.2f}",
                 f"{st_int['low']:.6f}", f"{st_int['low_pct']:.2f}", f"{st_int['high']:.6f}", f"{st_int['high_pct']:.2f}"],
            ]

            table = ax.table(cellText=table_data, cellLoc='center',
                             loc='bottom', bbox=[0.0, -0.55, 1.0, 0.40])
            table.set_fontsize(10)
            fig.subplots_adjust(bottom=0.32)

        # ---------------------------------------------------------
        # SYSTEM PRESSURE (abs_bar)
        # ---------------------------------------------------------
        if sig_name == "System Pressure (abs_bar)":

            start_pressures = []
            end_pressures = []
            min_pressures = []
            min_times = []
            delta_pressures = []

            for mess_name, y in messungen.items():
                if mess_name in hub_times:
                    ht = hub_times[mess_name]

                    idx_start = int(ht.get("start_index", 0))
                    idx_end = int(ht.get("end_index", len(y) - 1))

                    p_start = float(y[idx_start])
                    p_end = float(y[idx_end])

                    segment = y[idx_start:idx_end+1]
                    idx_min_local = np.argmin(segment)
                    p_min = float(segment[idx_min_local])
                    idx_min = idx_start + idx_min_local
                    t_min = T[idx_min]

                    p_delta = p_start - p_min

                    start_pressures.append(p_start)
                    end_pressures.append(p_end)
                    min_pressures.append(p_min)
                    min_times.append(t_min)
                    delta_pressures.append(p_delta)

                    ax.axvline(T[idx_start], color="green", linestyle="--", linewidth=1.5)
                    ax.axvline(T[idx_end], color="red", linestyle="--", linewidth=1.5)
                    ax.axvline(t_min, color="blue", linestyle="--", linewidth=1.5)

            st_start = stats_with_percent(start_pressures)
            st_end = stats_with_percent(end_pressures)
            st_minp = stats_with_percent(min_pressures)
            st_mint = stats_with_percent(min_times)
            st_delta = stats_with_percent(delta_pressures)

            # Statistik speichern
            all_stats["SystemPressure"] = {
                "p_start": st_start,
                "p_end": st_end,
                "p_min": st_minp,
                "t_min": st_mint,
                "delta_p": st_delta
            }

            table_data = [
                ["", "Mean", "Std", "Std [%]", "-3σ", "-3σ [%]", "+3σ", "+3σ [%]"],
                ["p(start) [bar]", f"{st_start['mean']:.6f}", f"{st_start['std']:.6f}", f"{st_start['std_pct']:.2f}",
                 f"{st_start['low']:.6f}", f"{st_start['low_pct']:.2f}", f"{st_start['high']:.6f}", f"{st_start['high_pct']:.2f}"],
                ["p(end) [bar]", f"{st_end['mean']:.6f}", f"{st_end['std']:.6f}", f"{st_end['std_pct']:.2f}",
                 f"{st_end['low']:.6f}", f"{st_end['low_pct']:.2f}", f"{st_end['high']:.6f}", f"{st_end['high_pct']:.2f}"],
                ["p(min) [bar]", f"{st_minp['mean']:.6f}", f"{st_minp['std']:.6f}", f"{st_minp['std_pct']:.2f}",
                 f"{st_minp['low']:.6f}", f"{st_minp['low_pct']:.2f}", f"{st_minp['high']:.6f}", f"{st_minp['high_pct']:.2f}"],
                ["t(min) [s]", f"{st_mint['mean']:.6f}", f"{st_mint['std']:.6f}", f"{st_mint['std_pct']:.2f}",
                 f"{st_mint['low']:.6f}", f"{st_mint['low_pct']:.2f}", f"{st_mint['high']:.6f}", f"{st_mint['high_pct']:.2f}"],
                ["Δp(start-min) [bar]", f"{st_delta['mean']:.6f}", f"{st_delta['std']:.6f}", f"{st_delta['std_pct']:.2f}",
                 f"{st_delta['low']:.6f}", f"{st_delta['low_pct']:.2f}", f"{st_delta['high']:.6f}", f"{st_delta['high_pct']:.2f}"],
            ]

            table = ax.table(cellText=table_data, cellLoc='center',
                             loc='bottom', bbox=[0.0, -1.30, 1.0, 0.70])
            table.set_fontsize(10)
            fig.subplots_adjust(bottom=0.55)

        # ---------------------------------------------------------
        # PNG SPEICHERN
        # ---------------------------------------------------------
        dateiname = f"{sig_name}.png"
        fig.savefig(os.path.join(bilder_pfad, dateiname), dpi=150)
        plt.close(fig)

    # ---------------------------------------------------------
    # SCATTERPLOT – nur einmal am Ende
    # ---------------------------------------------------------
    df_stats = build_shot_stats(signal_dict, T, hub_times, ICS_Eval_Result)

    scatter_path = os.path.join(ordnerpfad, "Bilder", "Shot_Feature_ScatterMatrix.png")

    plot_scatter_matrix(df_stats, scatter_path)

    # ---------------------------------------------------------
    # SHOT-FEATURE-TABELLE (Variante 1: Präfix-Spalten)
    # ---------------------------------------------------------
    shot_feature_table = {}
    
    # Alle Messnamen extrahieren
    all_measurements = list(next(iter(signal_dict.values())).keys())
    
    for mess_name in all_measurements:
        row = {}
    
        # -----------------------------------------------------
        # NEEDLE LIFT
        # -----------------------------------------------------
        if mess_name in hub_times and "Needle Lift (mm)" in signal_dict:
            ht = hub_times[mess_name]
            row["NeedleLift_StartTime"] = ht.get("start_time", 0)
            row["NeedleLift_EndTime"] = ht.get("end_time", 0)
    
            # MaxLift + MaxLiftTime
            y = np.array(signal_dict["Needle Lift (mm)"][mess_name])
            idx = np.argmax(y)
            row["NeedleLift_MaxLift"] = float(y[idx])
            row["NeedleLift_MaxLiftTime"] = float(T[idx])
        else:
            row["NeedleLift_StartTime"] = None
            row["NeedleLift_EndTime"] = None
            row["NeedleLift_MaxLift"] = None
            row["NeedleLift_MaxLiftTime"] = None
    
        # -----------------------------------------------------
        # MASS
        # -----------------------------------------------------
        if "Mass (mg)" in signal_dict:
            y = np.array(signal_dict["Mass (mg)"][mess_name])
            row["Mass_Max"] = float(np.max(y))
        else:
            row["Mass_Max"] = None
    
        # -----------------------------------------------------
        # ICS
        # -----------------------------------------------------
        if mess_name in ICS_Eval_Result:
            ics = ICS_Eval_Result[mess_name]
            row["ICS_ON_time"] = float(ics.get("ICS_ON_time", 0))
            row["ICS_OFF_time"] = float(ics.get("ICS_OFF_time", 0))
            row["ICS_ON_duration"] = float(ics.get("ICS_ON", 0))
            row["ICS_BoostMedian"] = float(ics["Boost"]["Median"])
            row["ICS_HoldMedian"] = float(ics["Hold"]["Median"])
            row["ICS_ZeroMedian"] = float(ics["Zero"]["Median"])
        else:
            row["ICS_ON_time"] = None
            row["ICS_OFF_time"] = None
            row["ICS_ON_duration"] = None
            row["ICS_BoostMedian"] = None
            row["ICS_HoldMedian"] = None
            row["ICS_ZeroMedian"] = None
    
        # -----------------------------------------------------
        # SYSTEM PRESSURE
        # -----------------------------------------------------
        if mess_name in hub_times and "System Pressure (abs_bar)" in signal_dict:
            y = np.array(signal_dict["System Pressure (abs_bar)"][mess_name])
            ht = hub_times[mess_name]
    
            idx_start = int(ht.get("start_index", 0))
            idx_end = int(ht.get("end_index", len(y)-1))
    
            p_start = float(y[idx_start])
            p_end = float(y[idx_end])
    
            segment = y[idx_start:idx_end+1]
            idx_min_local = np.argmin(segment)
            p_min = float(segment[idx_min_local])
            idx_min = idx_start + idx_min_local
    
            row["SysPressure_p_start"] = p_start
            row["SysPressure_p_end"] = p_end
            row["SysPressure_p_min"] = p_min
            row["SysPressure_t_min"] = float(T[idx_min])
            row["SysPressure_delta_p"] = p_start - p_min
        else:
            row["SysPressure_p_start"] = None
            row["SysPressure_p_end"] = None
            row["SysPressure_p_min"] = None
            row["SysPressure_t_min"] = None
            row["SysPressure_delta_p"] = None
    
        # -----------------------------------------------------
        # Zeile speichern
        # -----------------------------------------------------
        shot_feature_table[mess_name] = row
    
    # In all_stats speichern
    all_stats["ShotFeatureTable"] = shot_feature_table
     

    # Statistik-Dict zurückgeben
    return all_stats

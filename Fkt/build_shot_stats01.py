# -*- coding: utf-8 -*-
"""
Created on Sun Feb 15 18:56:46 2026

@author: larsk
"""

def build_shot_stats(signal_dict, T, hub_times, ICS_Eval_Result):
    import numpy as np
    import pandas as pd

    # Shot-Namen aus einem beliebigen Signal holen
    any_signal = next(iter(signal_dict.values()))
    shot_names = list(any_signal.keys())

    rows = []

    # Hilfsfunktion: Maximalwert eines Signals pro Shot
    def get_max(sig_name):
        if sig_name not in signal_dict:
            return {sn: np.nan for sn in shot_names}
        return {sn: float(np.max(signal_dict[sig_name][sn])) for sn in shot_names}

    # Drucksignal prüfen
    has_pressure = "System Pressure (abs_bar)" in signal_dict

    # Vorbereiten der Max-Werte
    needle_max = get_max("Needle Lift (mm)")
    needle_int_max = get_max("Needle Lift Integrated (mm_s)")
    mass_max = get_max("Mass (mg)")

    for sn in shot_names:
        row = {"Shot": sn}

        # Max-Werte
        row["Needle_Max_mm"] = needle_max[sn]
        row["Needle_Int_Max_mm_s"] = needle_int_max[sn]
        row["Mass_Max_mg"] = mass_max[sn]

        # ICS-Daten
        ics = ICS_Eval_Result.get(sn, {})
        ics_on_dur = float(ics.get("ICS_ON", np.nan))
        row["ICS_ON_dur_s"] = ics_on_dur

        row["ICS_Boost_Median_A"] = float(ics.get("Boost", {}).get("Median", np.nan))
        row["ICS_Hold_Median_A"]  = float(ics.get("Hold", {}).get("Median", np.nan))
        # ---------------------------------------------------------
        # 🔥 Druckauswertung: jetzt über start_lift → end_lift
        # ---------------------------------------------------------
        if has_pressure:
            p = np.array(signal_dict["System Pressure (abs_bar)"][sn], dtype=float)
            t = np.array(T, dtype=float)

            # Hub-Zeiten aus hub_times
            ht = hub_times.get(sn, {})
            lift_start = float(ht.get("start_time", np.nan))
            lift_end   = float(ht.get("end_time",   np.nan))

            # Druck zu Hub-Start
            if np.isnan(lift_start):
                p_start = np.nan
            else:
                idx_start = np.argmin(np.abs(t - lift_start))
                p_start = float(p[idx_start])

            # Minimum im Hub-Fenster
            if np.isnan(lift_start) or np.isnan(lift_end):
                p_min = np.nan
                t_min = np.nan
            else:
                mask = (t >= lift_start) & (t <= lift_end)

                if np.any(mask):
                    p_segment = p[mask]
                    t_segment = t[mask]

                    min_idx = np.argmin(p_segment)
                    p_min = float(p_segment[min_idx])
                    t_min = float(t_segment[min_idx])
                else:
                    p_min = np.nan
                    t_min = np.nan

            # Druckabfall
            if np.isnan(p_start) or np.isnan(p_min):
                dp = np.nan
            else:
                dp = p_start - p_min

            # Werte in Row schreiben
            row["Pressure_at_Lift_Start_bar"] = p_start
            row["Pressure_Min_bar"] = p_min
            row["Pressure_Drop_bar"] = dp
            row["Pressure_Min_Time_s"] = t_min

        rows.append(row)

    df = pd.DataFrame(rows)
    df.set_index("Shot", inplace=True)
    return df

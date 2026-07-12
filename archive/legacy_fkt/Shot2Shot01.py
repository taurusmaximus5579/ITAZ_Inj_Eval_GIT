# -*- coding: utf-8 -*-
"""
Created on Sun Oct 12 15:29:31 2025

@author: larsk
"""

import pandas as pd
import numpy as np

def shot2shot(signals: pd.DataFrame, threshold: float = 1.0, time_shift: float = 0.002, pause_between_peaks: float = 0.01, debug: bool = False) -> pd.DataFrame:
    """
    Fügt dem DataFrame eine Spalte 'counter' hinzu, die jedes Mal um 1 erhöht wird,
    wenn 'current (A)' sprunghaft ansteigt. Nach jedem Sprung wird eine Pause von
    'pause_between_peaks' Sekunden eingelegt, bevor weitere Sprünge verarbeitet werden.
    Zusätzlich wird eine lokale Zeitachse 'local_time' erzeugt, die bei jedem Sprung wieder bei 0 beginnt.

    Parameters:
    - signals: DataFrame mit 't in s' und 'current (A)'
    - threshold: Schwelle für Stromsprung
    - time_shift: Zeitverschiebung in Sekunden (z.B. 0.005)
    - pause_between_peaks: Zeitpause nach jedem Sprung in Sekunden
    - debug: Wenn True, werden Zwischenergebnisse ausgegeben

    Returns:
    - DataFrame mit 'counter' und 'local_time'
    """

    current_diff = signals['current (A)'].diff()
    jump_indices = current_diff[current_diff > threshold].index

    signals['counter'] = 0
    counter = 0
    times = signals['t in s'].values

    next_allowed_jump_time = -np.inf  # Initial unendlich früh

    for idx in jump_indices:
        jump_time = signals.loc[idx, 't in s']

        # Sprung ignorieren, wenn innerhalb der Sperrzeit
        if jump_time < next_allowed_jump_time:
            if debug:
                print(f"Überspringe Sprung bei {jump_time:.4f}s (Pause bis {next_allowed_jump_time:.4f}s)")
            continue

        target_time = jump_time - time_shift
        prior_idx = np.searchsorted(times, target_time, side='left')

        if prior_idx < len(times):
            actual_idx = signals.index[prior_idx]

            # Nur setzen, wenn dort noch kein Zähler steht
            if signals.at[actual_idx, 'counter'] == 0:
                counter += 1
                signals.at[actual_idx, 'counter'] = counter

                if debug:
                    print(f"Sprung bei {jump_time:.4f}s → Zähler {counter} gesetzt bei {signals.loc[actual_idx, 't in s']:.4f}s")

                # Sperrzeit aktualisieren
                next_allowed_jump_time = jump_time + pause_between_peaks

    # Zähler auffüllen
    signals['counter'] = (
        signals['counter']
        .replace(0, pd.NA)
        .ffill()
        .fillna(0)
        .infer_objects(copy=False)
        .astype(int)
    )

    # Lokale Zeitachse berechnen
    signals['local_time'] = 0.0
    for counter_value, group in signals.groupby('counter'):
        t_start = group['t in s'].iloc[0]
        signals.loc[group.index, 'local_time'] = group['t in s'] - t_start

    return signals

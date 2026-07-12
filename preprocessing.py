import os
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


def build_signal_dict(rawdata_by_file, config, min_time_step=None):
    signal_dict = {
        'Needle Lift (mm)': {},
        'Needle Velocity (mm_s)': {},
        'System Pressure (abs_bar)': {},
        'Injection Rate (abs_bar)': {},
        'Injector Control Signal (A)': {},
        'Power (W)': {},
        'Energy (Ws)': {},
    }

    if not rawdata_by_file:
        return signal_dict

    T_min, T_max = float('inf'), float('-inf')
    min_step = float('inf')

    for rawdata in rawdata_by_file.values():
        T = rawdata['T'] - rawdata['T'].iloc[0]
        T_min = min(T_min, T.min())
        T_max = max(T_max, T.max())
        diffs = T.diff().dropna()
        if not diffs.empty:
            step = diffs.min()
            if step > 0:
                min_step = min(min_step, step)

    if min_time_step is None:
        min_time_step = min_step if np.isfinite(min_step) else 1e-6

    t_common = np.arange(T_min, T_max, min_time_step)

    for filename, rawdata in rawdata_by_file.items():
        T = rawdata['T'] - rawdata['T'].iloc[0]
        signals = pd.DataFrame({'T': T})
        signals['Needle Lift (mm)'] = (rawdata['Nadelhub'] - rawdata[rawdata['T'] <= 0.003]['Nadelhub'].median()) * 0.2
        signals['System Pressure (abs_bar)'] = rawdata['Systemdruck'] * config.pressure_factor
        signals['Injection Rate (abs_bar)'] = rawdata['Rate'] * config.injection_factor
        signals['Injector Control Signal (A)'] = (rawdata['Steuersignal'] - rawdata[rawdata['T'] >= rawdata['T'].max() - 0.0005]['Steuersignal'].median()) * 4
        signals['Power (W)'] = signals['Injector Control Signal (A)'] * 50
        signals['Energy (Ws)'] = np.cumsum(np.gradient(signals['T']) * signals['Power (W)'])
        signals['Energy (Ws)'] -= signals['Energy (Ws)'].min()

        lift_signal = signals['Needle Lift (mm)']
        window_length = int(0.0005 / min_time_step)
        if window_length % 2 == 0:
            window_length += 1
        smoothed = savgol_filter(lift_signal, window_length=window_length, polyorder=3)
        velocity = np.gradient(smoothed, min_time_step)
        signal_dict['Needle Velocity (mm_s)'][filename] = velocity

        for key in signal_dict.keys():
            if key in signals.columns:
                signal_dict[key][filename] = np.interp(t_common, signals['T'], signals[key])

    return signal_dict, t_common

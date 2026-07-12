# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 21:48:50 2025

@author: larsk
"""

import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

def interpolate_signals(signals: pd.DataFrame, step_size: float) -> pd.DataFrame:
    """
    Interpoliert alle Spalten eines DataFrames auf eine gleichmäßige Zeitbasis.

    Parameters:
    - signals: pd.DataFrame mit einer Zeitspalte namens 't in s' und weiteren Messwerten
    - step_size: gewünschte Schrittweite in Sekunden (z. B. 0.0001)

    Returns:
    - pd.DataFrame mit interpolierten Werten auf neuer Zeitbasis
    """
    if "t in s" not in signals.columns:
        raise ValueError("Die Zeitspalte 't in s' fehlt im DataFrame.")

    t_original = signals["t in s"].values
    t_new = np.arange(t_original.min(), t_original.max(), step_size)

    interpolated_data = {"t in s": t_new}
    for column in signals.columns:
        if column != "t in s":
            f_interp = interp1d(t_original, signals[column].values, kind='linear', fill_value="extrapolate")
            interpolated_data[column] = f_interp(t_new)

    return pd.DataFrame(interpolated_data)

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def interpolate_nested_signal_dict(signal_dict: dict[str, dict[str, np.ndarray]], T: np.ndarray, step_size: float) -> dict[str, pd.DataFrame]:
    """
    Interpoliert verschachtelte Signalstruktur auf eine gleichmäßige Zeitbasis.

    Parameters:
    - signal_dict: Dictionary mit Signalnamen als Schlüssel und weiteren Dictionaries mit Messungen.
    - T: Gemeinsame Zeitachse (1D-numpy-array)
    - step_size: Schrittweite für die neue Zeitachse

    Returns:
    - Dictionary mit Signalnamen als Schlüssel und interpolierten DataFrames als Werte
    """
    t_new = np.arange(T.min(), T.max(), step_size)
    interpolated_dict = {}

    for signal_name, measurements in signal_dict.items():
        interpolated_data = {"T": t_new}
        for meas_name, values in measurements.items():
            f_interp = interp1d(T, values, kind='linear', fill_value="extrapolate")
            interpolated_data[meas_name] = f_interp(t_new)

        interpolated_dict[signal_name] = pd.DataFrame(interpolated_data)

    return interpolated_dict
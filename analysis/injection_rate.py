import numpy as np


def InjectionRate(cv, cp, R, Temp, signal_dict, T, A, hub_times):
    result_all = {}

    Kappa = cp / cv
    Psi = (2 / (Kappa + 1)) ** (1 / (Kappa - 1)) * (Kappa / (Kappa + 1)) ** 0.5
    pvk = (2 / (Kappa + 1)) ** (Kappa / (Kappa - 1))

    T = np.array(T)
    if len(T) < 2:
        raise ValueError("Zeitvektor T muss mindestens zwei Werte enthalten.")
    dt = T[1] - T[0]
    duration = 0.0025
    num_samples = int(duration / dt)

    signal_data = signal_dict.get("Injection Rate (abs_bar)", {})
    p2_values = {}
    rho_values = {}
    p2_p1_values = {}
    psi_values = {}
    injrate_values = {}

    for key, array in signal_data.items():
        array = np.array(array)
        if array.ndim == 1 and len(array) >= num_samples:
            p2 = np.mean(array[:num_samples])
            p2_values[key] = p2
            with np.errstate(divide='ignore', invalid='ignore'):
                p2_p1 = np.where(array != 0, p2 / array, np.nan)
                p2_p1_rounded = np.round(p2_p1, 2)
                p2_p1_capped = np.where(p2_p1_rounded > 1, 1.0, p2_p1_rounded)
            p2_p1_values[key] = p2_p1_capped
        else:
            print(f"⚠️ Eintrag '{key}' ist ungültig oder zu kurz (ndim={array.ndim}, len={len(array)})")

    for key, array in signal_data.items():
        array = np.array(array)
        if array.ndim == 1:
            rho = (array * 1e5) / (R * Temp)
            rho_values[key] = rho
        else:
            print(f"⚠️ Eintrag '{key}' ist ungültig (ndim={array.ndim})")

    for key, p2_p1_array in p2_p1_values.items():
        with np.errstate(invalid='ignore'):
            psi_array = np.where(
                p2_p1_array < pvk,
                Psi,
                np.sqrt(Kappa / (Kappa - 1) * (np.power(p2_p1_array, 2 / Kappa) - np.power(p2_p1_array, (Kappa + 1) / Kappa)))
            )
        psi_values[key] = psi_array

    for key in signal_data:
        p_array = np.array(signal_data[key])
        rho_array = rho_values.get(key)
        psi_array = psi_values.get(key)

        if rho_array is not None and psi_array is not None:
            with np.errstate(invalid='ignore'):
                injrate = A * np.sqrt(2 * rho_array * p_array * 1e5) * psi_array * 1000
            injrate_values[key] = injrate
        else:
            print(f"⚠️ Keine gültigen Werte für rho oder psi bei '{key}'")

    injrate_windowed = {}
    offset_before = int(0.0005 / dt)
    offset_after = int(0.0005 / dt)

    for key, injrate_array in injrate_values.items():
        inj = np.zeros_like(injrate_array)
        if key in hub_times:
            start_i = max(0, int(hub_times[key]["start_index"]) - offset_before)
            end_i = min(len(injrate_array), int(hub_times[key]["end_index"]) + offset_after)
            inj[start_i:end_i] = injrate_array[start_i:end_i]
        injrate_windowed[key] = inj

    cumulative_mass_values = {}
    for key, injrate_array in injrate_windowed.items():
        dt_ms = dt * 1000
        mass_per_step = injrate_array * dt_ms
        cumulative_mass_values[key] = np.cumsum(mass_per_step)

    result_all["Kappa"] = Kappa
    result_all["Psi"] = Psi
    result_all["pvk"] = pvk
    result_all["p2_values"] = p2_values
    result_all["rho_values"] = rho_values
    result_all["p2_p1_values"] = p2_p1_values
    result_all["psi_values"] = psi_values
    result_all["injrate_values"] = injrate_windowed
    result_all["cumulative_mass_values"] = cumulative_mass_values
    return result_all

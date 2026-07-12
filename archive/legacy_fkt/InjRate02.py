import numpy as np

def InjectionRate(cv, cp, R, Temp, signal_dict, T, A):
    result_all = {}

    # Thermodynamische Konstanten
    Kappa = cp / cv
    Psi = (2 / (Kappa + 1)) ** (1 / (Kappa - 1)) * (Kappa / (Kappa + 1)) ** 0.5
    pvk = (2 / (Kappa + 1)) ** (Kappa / (Kappa - 1))

    # Zeitauflösung und Anzahl der Samples
    T = np.array(T)
    if len(T) < 2:
        raise ValueError("Zeitvektor T muss mindestens zwei Werte enthalten.")
    dt = T[1] - T[0]
    duration = 0.0025
    num_samples = int(duration / dt)

    # Nur das relevante Signal extrahieren
    signal_data = signal_dict.get("Injection Rate (abs_bar)", {})
    p2_values = {}
    rho_values = {}
    p2_p1_values = {}
    psi_values = {}
    injrate_values = {}

    # Berechnung von p2, p2/p1
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

    # Berechnung von rho
    for key, array in signal_data.items():
        array = np.array(array)
        if array.ndim == 1:
            rho = (array * 1e5) / (R * Temp)  # Umrechnung von bar in Pa
            rho_values[key] = rho
        else:
            print(f"⚠️ Eintrag '{key}' ist ungültig (ndim={array.ndim})")

    # Berechnung von psi
    for key, p2_p1_array in p2_p1_values.items():
        with np.errstate(invalid='ignore'):
            psi_array = np.where(
                p2_p1_array < pvk,
                Psi,
                np.sqrt(Kappa / (Kappa - 1) * (np.power(p2_p1_array, 2 / Kappa) - np.power(p2_p1_array, (Kappa + 1) / Kappa)))
            )
        psi_values[key] = psi_array

    # Berechnung der InjRate
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

    
    # Berechnung der kumulierten Menge
        cumulative_mass_values = {}
        for key, injrate_array in injrate_values.items():
            # Masse pro Zeitschritt: InjRate * dt
            dt_ms = dt * 1000  # dt in Millisekunden
            mass_per_step = injrate_array * dt_ms  # [mg/s] * [ms] = [mg]
            # Kumulative Summe
            cumulative_mass = np.cumsum(mass_per_step)
            cumulative_mass_values[key] = cumulative_mass


    # Ergebnisse speichern
    result_all["Kappa"] = Kappa
    result_all["Psi"] = Psi
    result_all["pvk"] = pvk
    result_all["p2_values"] = p2_values
    result_all["rho_values"] = rho_values
    result_all["p2_p1_values"] = p2_p1_values
    result_all["psi_values"] = psi_values
    result_all["injrate_values"] = injrate_values
    result_all["cumulative_mass_values"] = cumulative_mass_values

    return result_all
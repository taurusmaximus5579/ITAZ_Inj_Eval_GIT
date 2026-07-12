# -*- coding: utf-8 -*-
"""
Created on Wed Nov 12 21:25:56 2025

@author: larsk
"""
import numpy as np
import matplotlib.pyplot as plt
import os

def RateDownCurve(signal_dict, T, step_size, hub_times, ordnerpfad=None, regression_type="linear", auto_select=False):
    try:
        mass_dict = signal_dict["Mass (mg)"]
    except KeyError:
        print("Fehler: Schlüssel 'Mass (mg)' nicht im signal_dict gefunden.")
        return None, None    

    try:
        pressure_dict = signal_dict["System Pressure (abs_bar)"]
    except KeyError:
        print("Fehler: Schlüssel 'System Pressure (abs_bar)' nicht im signal_dict gefunden.")
        return None, None    

    mass_info = {}
    for name, data in mass_dict.items():
        end_time = hub_times.get(name, {}).get("end_time", None)
        pressure_data = pressure_dict.get(name, None)

        if end_time is None or pressure_data is None:
            print(f"Warnung: Fehlende Daten für '{name}' (end_time oder Systemdruck). Wird übersprungen.")
            mass_info[name] = {"mass": None, "pressure": None}
            continue

        end_index = int(end_time / step_size)
        if end_index >= len(data):
            print(f"Warnung: 'end_time' ({end_time}s) liegt außerhalb der Datenlänge für '{name}'. Wird übersprungen.")
            mass_info[name] = {"mass": None, "pressure": np.mean(pressure_data)}
        else:
            mass_info[name] = {
                "mass": float(data[end_index]),
                "pressure": float(np.mean(pressure_data))  # mittlerer Systemdruck
            }

    x_vals, y_vals = [], []
    for name, info in mass_info.items():
        mass = info["mass"]
        pressure = info["pressure"]
        if mass is not None and pressure is not None:
            x_vals.append(float(pressure))
            y_vals.append(float(mass))

    if len(x_vals) < 2:
        print("Nicht genügend Daten für Regression.")
        return mass_info, None

    x = np.array(x_vals)
    y = np.array(y_vals)

    def fit_regression(x, y, method):
        if method == "linear":
            coeffs = np.polyfit(x, y, 1)
            y_pred = coeffs[0] * x + coeffs[1]
        elif method == "poly2":
            coeffs = np.polyfit(x, y, 2)
            y_pred = coeffs[0] * x**2 + coeffs[1] * x + coeffs[2]
        elif method == "log":
            x_log = np.log(x)
            coeffs = np.polyfit(x_log, y, 1)
            y_pred = coeffs[0] * x_log + coeffs[1]
        elif method == "exp":
            y_log = np.log(y)
            coeffs = np.polyfit(x, y_log, 1)
            y_pred = np.exp(coeffs[1]) * np.exp(coeffs[0] * x)
        else:
            raise ValueError(f"Unbekannte Methode: {method}")
        return y_pred, coeffs

    def compute_r2(y_true, y_pred):
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot)

    if auto_select:
        methods = ["linear", "poly2", "log", "exp"]
        best_r2 = -np.inf
        for method in methods:
            try:
                y_pred, coeffs = fit_regression(x, y, method)
                r2 = compute_r2(y, y_pred)
                if r2 > best_r2:
                    best_r2 = r2
                    best_method = method
                    best_pred = y_pred
                    best_coeffs = coeffs
            except Exception:
                continue
        regression_type = best_method
        y_pred = best_pred
        coeffs = best_coeffs
        r2 = best_r2
    else:
        y_pred, coeffs = fit_regression(x, y, regression_type)
        r2 = compute_r2(y, y_pred)

    if regression_type == "linear":
        equation = f"y = {coeffs[0]:.2f}x + {coeffs[1]:.2f}"
    elif regression_type == "poly2":
        equation = f"y = {coeffs[0]:.2f}x² + {coeffs[1]:.2f}x + {coeffs[2]:.2f}"
    elif regression_type == "log":
        equation = f"y = {coeffs[0]:.2f}ln(x) + {coeffs[1]:.2f}"
    elif regression_type == "exp":
        equation = f"y = {np.exp(coeffs[1]):.2f} · exp({coeffs[0]:.2f}x)"
    else:
        equation = "Unbekannte Regression"

    regression_info = {
        "Typ": regression_type,
        "Koeffizienten": coeffs,
        "R²": r2
    }

    ordnername = os.path.basename(os.path.normpath(ordnerpfad)) if ordnerpfad else "Unbekannter_Ordner"

    # Matplotlib-Plot
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, label='Messwerte')
    plt.plot(x, y_pred, label=f'{regression_type}-Regression', color='orange')
    plt.title(f"Rate Down Curve: Systemdruck vs. Injection Mass ({ordnername})")
    plt.xlabel("System Pressure (abs_bar)")
    plt.ylabel("Mass (mg)")
    plt.grid(True)
    plt.xlim(left=0)
    plt.ylim(bottom=0)

    plt.legend(loc='upper left')

    x_pos = x.max() - 0.05 * (x.max() - x.min())
    y_pos = y.min() + 0.5 * (y.max() - y.min())

    plt.text(
        x_pos, y_pos,
        f"{equation}\nR² = {r2:.4f}",
        fontsize=10,
        ha='right',
        va='center',
        bbox=dict(facecolor='white', edgecolor='gray')
    )

    plt.tight_layout()
    plt.show()

    return mass_info, regression_info


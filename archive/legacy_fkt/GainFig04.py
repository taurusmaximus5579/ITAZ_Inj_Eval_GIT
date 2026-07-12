
# -*- coding: utf-8 -*-
"""
23.11.2025 Lars Köhler
[✅] Speichern der Diagramme im Unterordner "Bilder" und HTML zusätzlich in "Results"
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import plotly.graph_objects as go

def GainCurve(signal_dict, T, step_size, ICS_Eval_Result, hub_times, ordnerpfad=None,
              regression_type="linear", auto_select=False):
    try:
        mass_dict = signal_dict["Mass (mg)"]
    except KeyError:
        print("Fehler: Schlüssel 'Mass (mg)' nicht im signal_dict gefunden.")
        return None, None    

    mass_info = {}
    for name, data in mass_dict.items():
        end_time = hub_times.get(name, {}).get("end_time", None)
        ics_on_value = ICS_Eval_Result.get(name, {}).get("ICS_ON", None)

        if end_time is None or ics_on_value is None:
            print(f"Warnung: Fehlende Daten für '{name}' (end_time oder ICS_ON). Wird übersprungen.")
            mass_info[name] = {"mass": None, "ICS_ON": None}
            continue

        end_index = int(end_time / step_size)
        if end_index >= len(data):
            print(f"Warnung: 'end_time' ({end_time}s) liegt außerhalb der Datenlänge für '{name}'. Wird übersprungen.")
            mass_info[name] = {"mass": None, "ICS_ON": ics_on_value}
        else:
            mass_info[name] = {"mass": float(data[end_index]), "ICS_ON": ics_on_value}

    x_vals, y_vals = [], []
    for name, info in mass_info.items():
        mass = info["mass"]
        ics_on = info["ICS_ON"]
        if mass is not None and ics_on is not None:
            x_vals.append(float(ics_on))
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

    # Unterordner "Bilder" erstellen
    bilder_pfad = os.path.join(ordnerpfad if ordnerpfad else ".", "Bilder")
    os.makedirs(bilder_pfad, exist_ok=True)

    # Unterordner "Results" erstellen
    results_pfad = os.path.join(ordnerpfad if ordnerpfad else ".", "Results")
    os.makedirs(results_pfad, exist_ok=True)

    # Berechne Achsenlimits für Zentrierung
    x_min, x_max = x.min(), x.max()
    y_min, y_max = y.min(), y.max()
    x_range = x_max - x_min
    y_range = y_max - y_min
    x_center = (x_max + x_min) / 2
    y_center = (y_max + y_min) / 2

    # PNG speichern mit zentrierten Achsen
    plt.figure(figsize=(12, 6))
    plt.scatter(x, y, label='Measured Values')
    plt.plot(x, y_pred, label=f'{regression_type}-Regression', color='orange')
    plt.title(f"Gain Curve: ICS_ON vs. Injection Mass ({ordnername})")
    plt.xlabel("ICS_ON (s)")
    plt.ylabel("Mass (mg)")
    plt.grid(True)
    plt.xlim(x_center - 0.6 * x_range, x_center + 0.6 * x_range)
    plt.ylim(y_center - 0.6 * y_range, y_center + 0.6 * y_range)
    plt.legend(loc='upper left')
    plt.text(x.max() * 0.95, y.min() + 0.5 * (y.max() - y.min()),
             f"{equation}\nR² = {r2:.4f}",
             fontsize=14, ha='right', va='center',
             bbox=dict(facecolor='white', edgecolor='gray'))
    plt.tight_layout()
    png_path = os.path.join(bilder_pfad, "GainCurve.png")
    plt.savefig(png_path)
    plt.close()

    # HTML Plot mit Plotly und zentrierten Achsen
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name='Measured Values'))
    fig.add_trace(go.Scatter(x=x, y=y_pred, mode='lines', name=f'{regression_type}-Regression'))
    fig.update_layout(title=f"Gain Curve: ICS_ON vs. Injection Mass ({ordnername})",
                      xaxis_title="ICS_ON (s)", yaxis_title="Mass (mg)")
    fig.update_xaxes(range=[x_center - 0.6 * x_range, x_center + 0.6 * x_range])
    fig.update_yaxes(range=[y_center - 0.6 * y_range, y_center + 0.6 * y_range])

    # Speichern als HTML im Results-Ordner
    html_path = os.path.join(results_pfad, "GainCurve.html")
    fig.write_html(html_path)

    print(f"Plots gespeichert unter:\nPNG: {png_path}\nHTML: {html_path}")

    return mass_info, regression_info

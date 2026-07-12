import os
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from image_utils import persist_or_cache_figure


def GainCurve(signal_dict, T, step_size, ICS_Eval_Result, hub_times, ordnerpfad=None,
              regression_type="linear", auto_select=False, image_cache=None, save_to_disk=False):
    try:
        mass_dict = signal_dict["Mass (mg)"]
    except KeyError:
        print("Fehler: Schlüssel 'Mass (mg)' nicht im signal_dict gefunden.")
        return None, None

    needle_lift_dict = signal_dict.get("Needle Lift Integrated (mm_s)", {})

    mass_info = {}
    for name, data in mass_dict.items():
        end_time = hub_times.get(name, {}).get("end_time", None)
        ics_on_value = ICS_Eval_Result.get(name, {}).get("ICS_ON", None)
        needle_data = needle_lift_dict.get(name, None)

        if end_time is None or ics_on_value is None:
            mass_info[name] = {"mass": None, "ICS_ON": None, "NeedleLiftIntegrated": None}
            continue

        end_index = int(end_time / step_size)
        if end_index >= len(data):
            mass_info[name] = {"mass": None, "ICS_ON": ics_on_value, "NeedleLiftIntegrated": None}
        else:
            needle_value = float(needle_data[end_index]) if needle_data is not None and end_index < len(needle_data) else None
            mass_info[name] = {"mass": float(data[end_index]), "ICS_ON": ics_on_value, "NeedleLiftIntegrated": needle_value}

    x_vals, y_vals = [], []
    for info in mass_info.values():
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

    regression_info = {"Typ": regression_type, "Koeffizienten": coeffs, "R²": r2}

    ordnername = os.path.basename(os.path.normpath(ordnerpfad)) if ordnerpfad else "Unbekannter_Ordner"
    bilder_pfad = os.path.join(ordnerpfad if ordnerpfad else ".", "Bilder")
    os.makedirs(bilder_pfad, exist_ok=True)
    results_pfad = os.path.join(ordnerpfad if ordnerpfad else ".", "Results")
    os.makedirs(results_pfad, exist_ok=True)

    needle_vals = [info["NeedleLiftIntegrated"] for info in mass_info.values() if info["NeedleLiftIntegrated"] is not None]
    ics_vals = [info["ICS_ON"] for info in mass_info.values() if info["NeedleLiftIntegrated"] is not None]

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.scatter(x, y, label='Mass (mg)', color='blue')
    ax1.plot(x, y_pred, label=f'{regression_type}-Regression', color='orange')
    ax1.set_xlabel("ICS_ON (s)")
    ax1.set_ylabel("Mass (mg)", color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    ax2 = ax1.twinx()
    if needle_vals:
        ax2.scatter(ics_vals, needle_vals, label='Needle Lift Integrated (mm·s)', color='green', marker='x')
    ax2.set_ylabel("Needle Lift Integrated (mm·s)", color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    plt.title(f"Gain Curve ({ordnername})")
    ax1.grid(True)
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    plt.tight_layout()
    png_path = os.path.join(bilder_pfad, "GainCurve.png")
    persist_or_cache_figure(plt.gcf(), output_path=png_path if save_to_disk else None, image_cache=image_cache, category="Ergebnisse", name="GainCurve", save_to_disk=save_to_disk, dpi=150)
    plt.close()

    fig_html = go.Figure()
    fig_html.add_trace(go.Scatter(x=x, y=y, mode='markers', name='Mass (mg)', marker=dict(color='blue')))
    fig_html.add_trace(go.Scatter(x=x, y=y_pred, mode='lines', name=f'{regression_type}-Regression', line=dict(color='orange')))
    if needle_vals:
        fig_html.add_trace(go.Scatter(x=ics_vals, y=needle_vals, mode='markers', name='Needle Lift Integrated (mm·s)', marker=dict(color='green'), yaxis='y2'))

    fig_html.update_layout(
        title=f"Gain Curve: ICS_ON vs Mass & Needle Lift ({ordnername})",
        xaxis=dict(title="ICS_ON (s)"),
        yaxis=dict(title=dict(text="Mass (mg)", font=dict(color='blue')), tickfont=dict(color='blue')),
        yaxis2=dict(title=dict(text="Needle Lift Integrated (mm·s)", font=dict(color='green')), tickfont=dict(color='green'), overlaying='y', side='right'),
        legend=dict(x=0.01, y=0.99)
    )

    html_path = os.path.join(results_pfad, "GainCurve_with_NeedleLift.html")
    fig_html.write_html(html_path)

    print(f"Plots gespeichert unter:\nPNG: {png_path}\nHTML: {html_path}")
    return mass_info, regression_info


import numpy as np
import plotly.graph_objects as go
import os

def GainCurve(signal_dict, T, step_size, ICS_Eval_Result, ordnerpfad=None):
    """
    Berechnet den Mittelwert der Masse in den letzten 5ms für jede Messung,
    führt eine lineare Regression durch und erstellt ein Diagramm.

    Parameters:
    - signal_dict: Dictionary mit Schlüssel "Mass (mg)", der ein weiteres Dictionary mit Arrays enthält.
    - step_size: Zeit zwischen zwei Samples in Sekunden (z. B. 1e-5 für 100 kHz).
    - ICS_Eval_Result: Dictionary mit ICS_ON-Werten pro Messung (verschachtelt).
    - ordnerpfad: Optionaler Pfad zum Speichern des Diagramms (PNG).

    Returns:
    - avg_mass: Dictionary mit Mittelwerten pro Messung.
    - regression_info: Dictionary mit Steigung, Achsenabschnitt und R²-Wert.
    """
    try:
        mass_dict = signal_dict["Mass (mg)"]
    except KeyError:
        print("Fehler: Schlüssel 'Mass (mg)' nicht im signal_dict gefunden.")
        return None, None

    sampling_rate = 1 / step_size
    samples_5ms = int(sampling_rate * 0.005)

    avg_mass = {}

    for name, data in mass_dict.items():
        if len(data) < samples_5ms:
            print(f"Warnung: '{name}' ist kürzer als 5ms. Wird übersprungen.")
            avg_mass[name] = None
        else:
            avg_mass[name] = float(np.mean(data[-samples_5ms:]))

    # Filtere gültige Werte für Regression
    x_vals = []
    y_vals = []
    for name, mass in avg_mass.items():
        if mass is not None and name in ICS_Eval_Result:
            ics_on_value = ICS_Eval_Result[name].get('ICS_ON', None)
            if ics_on_value is not None:
                x_vals.append(float(ics_on_value))
                y_vals.append(float(mass))

    if len(x_vals) < 2:
        print("Nicht genügend Daten für Regression.")
        return avg_mass, None

    # NumPy-Regression
    x = np.array(x_vals)
    y = np.array(y_vals)
    slope, intercept = np.polyfit(x, y, 1)

    # Vorhersage und R²
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot)

    regression_info = {
        "Steigung": slope,
        "Achsenabschnitt": intercept,
        "R²": r2
    }

    ordnername = os.path.basename(os.path.normpath(ordnerpfad)) if ordnerpfad else "Unbekannter_Ordner"

    # Plot erstellen
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name='Messwerte'))
    fig.add_trace(go.Scatter(x=x, y=y_pred, mode='lines', name='Regression'))

    # Annotation mit Gleichung und R²
    equation = f"y = {slope:.2f}x + {intercept:.2f}<br>R² = {r2:.4f}"
    fig.add_annotation(x=x.mean(), y=y.max(),
                       text=equation,
                       showarrow=False,
                       font=dict(size=12),
                       bgcolor="white")

    
    fig.update_layout(
        title=f"Gain Curve: ICS_ON vs. Injection Mass ({ordnername})",
        xaxis_title="ICS_ON (s)",
        yaxis_title="Mass (mg)",
        template="simple_white",        
        font=dict(size=11),
        width=1000,
        height=600
    )

    # Speichern, falls Pfad angegeben        
    dateiname = f"GainCurve_{ordnername}.png"

    if ordnerpfad:
        # Stelle sicher, dass der Pfad ein Verzeichnis ist
        if not os.path.isdir(ordnerpfad):
            print(f"Warnung: '{ordnerpfad}' ist kein Verzeichnis. Datei wird trotzdem dort gespeichert.")
        
        # Kombiniere Ordnerpfad und Dateiname
        dateipfad = os.path.join(ordnerpfad, dateiname)
        fig.write_image(dateipfad)
        print(f"Diagramm gespeichert unter: {dateipfad}")
    else:
        fig.show()


    return avg_mass, regression_info

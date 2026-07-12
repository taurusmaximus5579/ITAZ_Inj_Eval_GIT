"""
XX.XX.2025 Lars Köhler
[✅] Tabs bei den Bildern eingeführt
[✅ ] Auswahl unterschiedlicher Sensoren
    - System Pressure
        o 10 bar Sensor                 Faktor V -> 1 bar = 1
        o 50 bar Sensor                 Faktor V -> 1 bar = 5 (Standard)
        o 200 bar Sensor                Faktor V -> 1 bar = 20
        o 350 bar Sensor                Faktor V -> 35
        o 1000 bar Sensor               Faktor V -> 100
    - Injection Rate
        o 10 bar Sensor                 Faktor V -> 1 bar = 1 (Standard)
        o 50 bar Sensor                 Faktor V -> 5
        o 200 bar Sensor                Faktor V -> 20
        o 350 bar Sensor                Faktor V -> 35
        o 1000 bar Sensor               Faktor V -> 100

[✅] Fkt Shot2Shot
[✅] Einige Sachen auslesen und in Datei und Gui, Dia schreiben
    - Shot to Shot oder Gain
    - Zeit (bei Gain den Zeitabstand zwischen den Messungen)
    - Druck
    - Messung
[✅] Werte in den Diagrammen beim Stromsignal schreiben
[✅] In der Gainauswertung Nadelhubintegral
[✅] Optimierung InjRate03 -> Rate und Masse nur solange Nadel offen ist -> Entfernen von Rauschen in der Massenauswertung
[ ] Entpivotisiertes Diagramm für Statistikauswertung
[ ] Auswahlfeld zur Bilder generieren
[✅] Komplette Umstrukturierung des Skripts und Go2Git
"""

import tkinter as tk
from tkinter import filedialog, ttk
import sys
import os
import re
from PIL import Image, ImageTk  # Pillow installieren: pip install pillow
from ITAZ_Inj_Eval_208 import run_main_analysis  # deine Hauptanalysefunktion
import csv
from types import SimpleNamespace


class TextRedirector:
    def __init__(self, text_widget, tag="stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, msg):
        if str(msg).strip() != "":
            self.text_widget.insert("end", str(msg) + "\n", self.tag)
            self.text_widget.see("end")
            self.text_widget.update_idletasks()

    def flush(self):
        pass


class InjectionGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Injection Analysis GUI")
        # Fensterpositionierung: Breite x Höhe + OffsetX + OffsetY
        self.geometry("1500x900+100+50")

        self.selected_files = []
        self.shot_log = None  # Struct (SimpleNamespace) aus shot_log.csv
        self.image_tabs = {"Messsignale": [], "Strom": [], "Nadelhub": [], "Ergebnisse": []}
        self.frames = {}

        self._build_ui()

        # Stdout/Stderr in Log-Text umleiten
        sys.stdout = TextRedirector(self.log, "stdout")
        sys.stderr = TextRedirector(self.log, "stderr")

        self.log.tag_configure("stdout", foreground="black")
        self.log.tag_configure("stderr", foreground="red")

        # Resize-Event: Logo dynamisch mitskalieren
        self.bind("<Configure>", self.on_resize)

    def _build_ui(self):
        main_pane = ttk.PanedWindow(self, orient="horizontal")
        main_pane.pack(fill="both", expand=True)

        # Linke Seite
        left_frame = ttk.Frame(main_pane)
        self._build_left_ui(left_frame)

        # Rechte Seite
        right_container = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=3)
        main_pane.add(right_container, weight=2)

        # Logo oben
        logo_frame = ttk.Frame(right_container)
        logo_frame.pack(fill="x", side="top", pady=10)

        logo_path = os.path.join(os.path.dirname(__file__), "Fkt", "Injektor.png")
        if os.path.exists(logo_path):
            self.logo_original = Image.open(logo_path)
            self.logo_tk = ImageTk.PhotoImage(self.logo_original)
            self.logo_label = tk.Label(logo_frame, image=self.logo_tk)
            self.logo_label.pack(anchor="ne", padx=20, pady=10)
        else:
            print("⚠️ Logo-Datei nicht gefunden:", logo_path)

        # Notebook für Bilder + Shot_Log
        self.notebook = ttk.Notebook(right_container)
        self.notebook.pack(fill="both", expand=True, side="top", padx=6, pady=6)

        # Tabs hinzufügen inkl. Shot_Log
        for tab_name in ["Messsignale", "Strom", "Nadelhub", "Ergebnisse", "Shot_Log"]:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_name)
            self.frames[tab_name] = frame

        # Bild-Tabs initialisieren (Bedienelemente) – Shot_Log separat
        for tab_name in ["Messsignale", "Strom", "Nadelhub", "Ergebnisse"]:
            self._setup_tab(tab_name)

        # Shot_Log-Tab aufbauen
        self._build_shot_log_tab()

    def _build_left_ui(self, parent):
        # Datei-Auswahl
        file_frame = ttk.LabelFrame(parent, text="CSV-Dateien")
        file_frame.pack(fill="x", padx=10, pady=8)
        ttk.Button(file_frame, text="CSV auswählen…", command=self.select_files).pack(side="left", padx=6, pady=6)
        self.file_count_lbl = ttk.Label(file_frame, text="0 Dateien ausgewählt")
        self.file_count_lbl.pack(side="left", padx=6)
        ttk.Button(file_frame, text="Liste leeren", command=self.clear_files).pack(side="right", padx=6)

        # Parameter
        params = ttk.LabelFrame(parent, text="Parameter")
        params.pack(fill="x", padx=10, pady=8)

        self.gas_options = {
            "Helium": {"cv": 3115, "cp": 5194, "R": 2077},
            "Stickstoff": {"cv": 743, "cp": 1040, "R": 296.76},
            "Methan": {"cv": 2220, "cp": 2850, "R": 518.24},
            "Wasserstoff": {"cv": 10290, "cp": 14300, "R": 4124.11},
        }
        self.selected_gas = tk.StringVar(value="Helium")
        gas_dropdown = ttk.Combobox(
            params,
            textvariable=self.selected_gas,
            values=list(self.gas_options.keys()),
            state="readonly",
        )
        gas_dropdown.pack(fill="x", padx=6, pady=(6, 2))
        gas_dropdown.bind("<<ComboboxSelected>>", self.set_gas_defaults)

        self.cv = tk.StringVar(value=f"{self.gas_options['Helium']['cv']:.0f}")
        self.cp = tk.StringVar(value=f"{self.gas_options['Helium']['cp']:.0f}")
        self.R = tk.StringVar(value=f"{self.gas_options['Helium']['R']:.2f}")

        grid = ttk.Frame(params)
        grid.pack(fill="x", padx=6, pady=6)

        def mk_row(r, lbl, var, unit=""):
            ttk.Label(grid, text=lbl).grid(row=r, column=0, sticky="w")
            ttk.Entry(grid, textvariable=var, width=14).grid(row=r, column=1, sticky="w", padx=6)
            ttk.Label(grid, text=unit).grid(row=r, column=2, sticky="w")

        mk_row(0, "cv", self.cv)
        mk_row(1, "cp", self.cp)
        mk_row(2, "R", self.R, "J/(kg*K)")

        # Prüfkammer
        chamber = ttk.LabelFrame(parent, text="Prüfkammer")
        chamber.pack(fill="x", padx=10, pady=8)
        self.A = tk.StringVar(value=f"{0.00018:.5f}")
        self.Temp = tk.StringVar(value=f"{293.15:.2f}")

        cgrid = ttk.Frame(chamber)
        cgrid.pack(fill="x", padx=6, pady=6)
        ttk.Label(cgrid, text="A").grid(row=0, column=0, sticky="w")
        ttk.Entry(cgrid, textvariable=self.A, width=14).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(cgrid, text="m²").grid(row=0, column=2, sticky="w")

        ttk.Label(cgrid, text="Temp").grid(row=1, column=0, sticky="w")
        ttk.Entry(cgrid, textvariable=self.Temp, width=14).grid(row=1, column=1, sticky="w", padx=6)
        ttk.Label(cgrid, text="K").grid(row=1, column=2, sticky="w")

        # Export
        export = ttk.LabelFrame(parent, text="Export")
        export.pack(fill="x", padx=10, pady=8)
        self.step_size = tk.StringVar(value=f"{0.00001:.5f}")
        egrid = ttk.Frame(export)
        egrid.pack(fill="x", padx=6, pady=6)
        ttk.Label(egrid, text="Interpolation step").grid(row=0, column=0, sticky="w")
        ttk.Entry(egrid, textvariable=self.step_size, width=14).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(egrid, text="s").grid(row=0, column=2, sticky="w")

        # ICS Auswertungsbereiche
        ranges = ttk.LabelFrame(parent, text="ICS Auswertungsbereiche")
        ranges.pack(fill="x", padx=10, pady=8)
        self.boost_min = tk.StringVar(value=f"{10.5:.1f}")
        self.boost_max = tk.StringVar(value=f"{13.5:.1f}")
        self.hold_min = tk.StringVar(value=f"{3.0:.1f}")
        self.hold_max = tk.StringVar(value=f"{5.0:.1f}")
        self.zero_min = tk.StringVar(value=f"{-0.5:.1f}")
        self.zero_max = tk.StringVar(value=f"{0.5:.1f}")

        rgrid = ttk.Frame(ranges)
        rgrid.pack(fill="x", padx=6, pady=6)

        def mk_pair(r, lbl, vmin, vmax):
            ttk.Label(rgrid, text=lbl).grid(row=r, column=0, sticky="w")
            ttk.Entry(rgrid, textvariable=vmin, width=10).grid(row=r, column=1, sticky="w", padx=6)
            ttk.Entry(rgrid, textvariable=vmax, width=10).grid(row=r, column=2, sticky="w", padx=6)

        mk_pair(0, "Boost (min/max)", self.boost_min, self.boost_max)
        mk_pair(1, "Hold (min/max)", self.hold_min, self.hold_max)
        mk_pair(2, "Zero (min/max)", self.zero_min, self.zero_max)

        # Optionen
        opts = ttk.LabelFrame(parent, text="Optionen")
        opts.pack(fill="x", padx=10, pady=8)
        self.plot_raw_data = tk.BooleanVar(value=False)
        self.export_excel = tk.BooleanVar(value=True)
        self.eval_gain = tk.BooleanVar(value=False)
        self.eval_rate_dn = tk.BooleanVar(value=False)
        self.shot2shot = tk.BooleanVar(value=False)  # ✅ NEU: Shot2Shot Checkbox
        
        ttk.Checkbutton(opts, text="Rohdaten plotten", variable=self.plot_raw_data).pack(side="left", padx=6)
        ttk.Checkbutton(opts, text="Excel exportieren", variable=self.export_excel).pack(side="left", padx=6)
        ttk.Checkbutton(opts, text="Gain-Kurve auswerten", variable=self.eval_gain).pack(side="left", padx=6)
        ttk.Checkbutton(opts, text="Rate-Down-Kurve auswerten", variable=self.eval_rate_dn).pack(side="left", padx=6)
        ttk.Checkbutton(opts, text="Shot2Shot", variable=self.shot2shot).pack(side="left", padx=6)  # ✅ NEU

        # Aktionen
        actions = ttk.LabelFrame(parent, text="Aktionen")
        actions.pack(fill="x", padx=10, pady=8)
        ttk.Button(actions, text="Analyse starten", command=self.run_analysis).pack(side="left", padx=6, pady=6)
        self.progress = ttk.Progressbar(actions, mode="determinate", length=250)
        self.progress.pack(side="left", padx=12)
        self.status_lbl = ttk.Label(actions, text="Bereit.")
        self.status_lbl.pack(side="left", padx=12)

        # Sensor Auswahl
        sensor_frame = ttk.LabelFrame(parent, text="Sensor Auswahl")
        sensor_frame.pack(fill="x", padx=10, pady=8)

        # System Pressure Dropdown
        ttk.Label(sensor_frame, text="System Pressure").pack(anchor="w", padx=6)
        self.sensor_options = {
            "System Pressure": {
                "10 bar": 1,
                "50 bar": 5,
                "200 bar": 20,
                "350 bar": 35,
                "1000 bar": 100,
            },
            "Injection Rate": {
                "10 bar": 1,
                "50 bar": 5,
                "200 bar": 20,
                "350 bar": 35,
                "1000 bar": 100,
            },
        }

        self.selected_pressure_sensor = tk.StringVar(value="50 bar")  # Standard
        pressure_dropdown = ttk.Combobox(
            sensor_frame,
            textvariable=self.selected_pressure_sensor,
            values=list(self.sensor_options["System Pressure"].keys()),
            state="readonly",
        )
        pressure_dropdown.pack(fill="x", padx=6, pady=(2, 6))

        # Injection Rate Dropdown
        ttk.Label(sensor_frame, text="Injection Rate").pack(anchor="w", padx=6)
        self.selected_injection_sensor = tk.StringVar(value="10 bar")  # Standard
        injection_dropdown = ttk.Combobox(
            sensor_frame,
            textvariable=self.selected_injection_sensor,
            values=list(self.sensor_options["Injection Rate"].keys()),
            state="readonly",
        )
        injection_dropdown.pack(fill="x", padx=6, pady=(2, 6))

        # Log
        logf = ttk.LabelFrame(parent, text="Log")
        logf.pack(fill="both", expand=True, padx=10, pady=8)
        self.log = tk.Text(logf, height=18)
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

    def set_gas_defaults(self, event=None):
        gas = self.selected_gas.get()
        defaults = self.gas_options[gas]
        self.cv.set(f"{defaults['cv']:.0f}")
        self.cp.set(f"{defaults['cp']:.0f}")
        self.R.set(f"{defaults['R']:.2f}")

    def get_config(self):
        return {
            "gas": self.selected_gas.get(),
            "cv": float(self.cv.get()),
            "cp": float(self.cp.get()),
            "R": float(self.R.get()),
            "A": float(self.A.get()),
            "Temp": float(self.Temp.get()),
            "step_size": float(self.step_size.get()),
            "boost_min": float(self.boost_min.get()),
            "boost_max": float(self.boost_max.get()),
            "hold_min": float(self.hold_min.get()),
            "hold_max": float(self.hold_max.get()),
            "zero_min": float(self.zero_min.get()),
            "zero_max": float(self.zero_max.get()),
            "plot_raw_data": self.plot_raw_data.get(),
            "export_excel": self.export_excel.get(),
            "eval_gain": self.eval_gain.get(),
            "eval_rate_dn": self.eval_rate_dn.get(),
            "shot2shot": self.shot2shot.get(),  # ✅ NEU: Wert in Konfiguration übernehmen
            "selected_files": self.selected_files,
            # Neue Sensor-Parameter
            "pressure_sensor": self.selected_pressure_sensor.get(),
            "pressure_factor": self.sensor_options["System Pressure"][self.selected_pressure_sensor.get()],
            "injection_sensor": self.selected_injection_sensor.get(),
            "injection_factor": self.sensor_options["Injection Rate"][self.selected_injection_sensor.get()],
            # shot_log für Hauptanalyse bereitstellen (als dict oder None)
            "shot_log": (vars(self.shot_log) if self.shot_log is not None else None),
        }

    def read_shot_log(self, path):
        """
        Liest shot_log.csv robust ein:
          - erkennt das Trennzeichen automatisch (Sniffer, Fallback: ; , \t)
          - normalisiert Header-Namen
          - konvertiert Datentypen (shot=int, Zeiten=float)
          - speichert als Struct (SimpleNamespace) in self.shot_log
        Erwartete Spalten (Case-insensitive, Whitespace egal):
          shot, time_us, acq_ms, wait_ms, full_ms
        """
        def normalize(s):
            return (s or "").strip().lower().replace(" ", "").replace("\u200b", "").replace("\u00A0", "")

        header_alias = {
            "shot": "shot",
            "shots": "shot",
            "time_us": "time_us",
            "timeus": "time_us",
            "acq_ms": "acq_ms",
            "acqms": "acq_ms",
            "wait_ms": "wait_ms",
            "waitms": "wait_ms",
            "full_ms": "full_ms",
            "fullms": "full_ms",
        }
        required = {"shot", "time_us", "acq_ms", "wait_ms", "full_ms"}

        if not os.path.exists(path):
            self.log_msg(f"ℹ️ shot_log.csv nicht gefunden: {path}")
            return

        try:
            # Trennzeichen erkennen
            with open(path, "r", encoding="utf-8", newline="") as f:
                sample = f.read(2048)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
                    delimiter = dialect.delimiter
                except Exception:
                    delimiter = ";"  # Fallback (typisch DE)

            # Datei lesen
            with open(path, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)

            if not rows:
                self.log_msg("⚠️ shot_log.csv ist leer.")
                return

            raw_header = rows[0]
            norm_header = [normalize(h) for h in raw_header]

            index_map = {}
            for i, nh in enumerate(norm_header):
                if nh in header_alias:
                    canonical = header_alias[nh]
                    if canonical not in index_map:
                        index_map[canonical] = i

            missing = sorted(list(required - set(index_map.keys())))
            if missing:
                self.log_msg(f"⚠️ shot_log.csv fehlt Spalten: {missing}. Trennzeichen='{delimiter}'. Datei wird ignoriert.")
                return

            shots, time_us, acq_ms, wait_ms, full_ms = [], [], [], [], []

            for line_no, row in enumerate(rows[1:], start=2):
                if not isinstance(row, (list, tuple)) or len(row) < len(raw_header):
                    self.log_msg(f"⚠️ Zeile {line_no} übersprungen (unerwartetes Format).")
                    continue

                def get_val(name):
                    idx = index_map[name]
                    val = row[idx].strip()
                    val = val.replace(",", ".")  # Dezimal-Kommas -> Punkt
                    return val

                try:
                    shots.append(int(get_val("shot")))
                    time_us.append(float(get_val("time_us")))
                    acq_ms.append(float(get_val("acq_ms")))
                    wait_ms.append(float(get_val("wait_ms")))
                    full_ms.append(float(get_val("full_ms")))
                except Exception as e:
                    self.log_msg(f"⚠️ Zeile {line_no} in shot_log.csv konnte nicht geparst werden: {e}")

            if len(shots) == 0:
                self.log_msg("⚠️ shot_log.csv enthält keine gültigen Daten.")
                return

            self.shot_log = SimpleNamespace(
                shot=shots,
                time_us=time_us,
                acq_ms=acq_ms,
                wait_ms=wait_ms,
                full_ms=full_ms,
                delimiter_used=delimiter,
            )

            self.log_msg(f"✅ shot_log.csv eingelesen ({len(shots)} Einträge, Trennzeichen='{delimiter}').")

            # Tabelle aktualisieren, falls UI steht
            if hasattr(self, "refresh_shot_log_table"):
                self.refresh_shot_log_table()

        except Exception as e:
            self.log_msg(f"❌ Fehler beim Lesen von shot_log.csv: {e}")

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Wähle eine oder mehrere CSV-Dateien",
            filetypes=[("CSV-Dateien", "*.csv")]
        )
        if files:
            pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}_\d+_\d+_.*_(He|N2|CH4|H2)_\d+bar\.csv$")
            valid_files = []
            detected_gas = None
            gain_found = False
            rate_down_found = False

            shot_log_selected_path = None

            for f in files:
                fname = os.path.basename(f)
                if fname.lower() == "shot_log.csv":
                    shot_log_selected_path = f
                    continue

                match = pattern.search(fname)
                if match:
                    valid_files.append(f)
                    if detected_gas is None:
                        detected_gas = match.group(1)
                    if "Gain" in fname:
                        gain_found = True
                    if "Rate-Down" in fname or "RateDown" in fname:
                        rate_down_found = True

            self.selected_files = valid_files

            # Gas auto-detektion
            if detected_gas:
                gas_map = {"He": "Helium", "N2": "Stickstoff", "CH4": "Methan", "H2": "Wasserstoff"}
                self.selected_gas.set(gas_map[detected_gas])
                self.set_gas_defaults()

            self.eval_gain.set(gain_found)
            self.eval_rate_dn.set(rate_down_found)

            # shot_log.csv laden, falls vorhanden
            self.shot_log = None  # zurücksetzen vor neuem Laden
            if shot_log_selected_path is not None:
                self.read_shot_log(shot_log_selected_path)
            else:
                if self.selected_files:
                    base_dir = os.path.dirname(self.selected_files[0])
                    candidate = os.path.join(base_dir, "shot_log.csv")
                    if os.path.exists(candidate):
                        self.read_shot_log(candidate)
                    else:
                        self.log_msg(f"ℹ️ Keine shot_log.csv im Ordner gefunden: {base_dir}")
                else:
                    self.log_msg("ℹ️ Es wurden keine gültigen Messdateien ausgewählt.")

            # Tabelle aktualisieren (falls keine Daten gelesen wurden -> leeren)
            self.refresh_shot_log_table()

        else:
            self.selected_files = []
            self.shot_log = None
            self.refresh_shot_log_table()

        self.file_count_lbl.config(text=f"{len(self.selected_files)} Dateien ausgewählt")

    def clear_files(self):
        self.selected_files = []
        self.shot_log = None
        self.file_count_lbl.config(text="0 Dateien ausgewählt")
        self.refresh_shot_log_table()

    def log_msg(self, msg):
        self.log.insert("end", str(msg) + "\n")
        self.log.see("end")
        self.update_idletasks()

    def set_status(self, msg):
        self.status_lbl.config(text=msg)
        self.update_idletasks()

    def run_analysis(self):
        if not self.selected_files:
            self.log_msg("⚠️ Keine Dateien ausgewählt.")
            self.set_status("Warte auf Dateien…")
            return

        try:
            step = float(self.step_size.get())
            if step <= 0:
                raise ValueError("Interpolation step muss > 0 sein.")
        except Exception as e:
            self.log_msg(f"❌ Ungültiger Interpolation step: {e}")
            self.set_status("Fehlerhafte Eingabe.")
            return

        self.progress.configure(value=0, maximum=100)
        self.log_msg("Analyse gestartet…")
        self.set_status("Analyse läuft…")

        try:
            cfg = self.get_config()
            self.progress.configure(value=10)
            self.update_idletasks()

            # Hauptanalyse
            run_main_analysis(cfg)

            self.progress.configure(value=100)
            self.log_msg("✅ Analyse beendet.")
            self.set_status("Fertig.")

            # Bilder neu laden
            self.load_images()

            # Shot_Log ggf. aktualisieren (falls Analyse neue shot_log-Daten generiert hätte)
            self.refresh_shot_log_table()

        except Exception as e:
            self.log_msg(f"❌ Fehler während der Analyse: {e}")
            self.set_status("Fehler.")

    # ---------- Bilder laden und Tabs befüllen ----------
    def load_images(self):
        # Bildlisten leeren
        self.image_tabs = {
            "Strom": [],
            "Nadelhub": [],
            "Ergebnisse": [],
            "Messsignale": [],
        }
        self.current_index = {
            "Strom": 0,
            "Nadelhub": 0,
            "Ergebnisse": 0,
            "Messsignale": 0,
        }

        if not self.selected_files:
            return

        base_dir = os.path.dirname(self.selected_files[0])
        png_files = []
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if f.lower().endswith(".png"):
                    png_files.append(os.path.join(root, f))

        # Zuordnen nach Dateinamen
        for path in png_files:
            fname = os.path.basename(path)
            current_keywords = ["Stromsignal", "Zero", "Boost", "Hold", "ICS"]
            if any(keyword in fname for keyword in current_keywords):
                self.image_tabs["Strom"].append(path)
            elif "NeedleLift" in fname:
                self.image_tabs["Nadelhub"].append(path)
            elif "signals" in fname.lower():
                self.image_tabs["Messsignale"].append(path)
            else:
                self.image_tabs["Ergebnisse"].append(path)

        # Nur die Bild-Tabs befüllen
        for tab_name in ["Messsignale", "Strom", "Nadelhub", "Ergebnisse"]:
            self._setup_tab(tab_name)

    def _setup_tab(self, tab_name):
        frame = self.frames[tab_name]
        for widget in frame.winfo_children():
            widget.destroy()

        # Bild-Label
        img_label = tk.Label(frame)
        img_label.pack(fill="both", expand=True, padx=6, pady=6)

        # Navigation
        nav_frame = ttk.Frame(frame)
        nav_frame.pack(pady=6)
        ttk.Button(nav_frame, text="◀ Zurück", command=lambda: self.show_image(tab_name, -1)).pack(side="left", padx=4)
        ttk.Button(nav_frame, text="▶ Weiter", command=lambda: self.show_image(tab_name, 1)).pack(side="left", padx=4)

        # Speichern für Zugriff
        frame.img_label = img_label

        # Erstes Bild anzeigen
        self.show_image(tab_name, 0)

    def show_image(self, tab_name, step):
        paths = self.image_tabs.get(tab_name, [])
        if not paths:
            self.frames[tab_name].img_label.config(text="Keine Bilder gefunden.", image="")
            return

        # Index aktualisieren
        if step != 0:
            self.current_index[tab_name] = (self.current_index[tab_name] + step) % len(paths)

        img_path = paths[self.current_index[tab_name]]

        try:
            img = Image.open(img_path)
        except Exception as e:
            self.frames[tab_name].img_label.config(text=f"Bild kann nicht geöffnet werden: {e}", image="")
            return

        # Größe anpassen
        frame_width = self.frames[tab_name].img_label.winfo_width()
        frame_height = self.frames[tab_name].img_label.winfo_height()
        if frame_width < 100 or frame_height < 100:
            frame_width, frame_height = 600, 450

        img.thumbnail((frame_width, frame_height), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)

        self.frames[tab_name].img_label.config(image=tk_img, text="")
        self.frames[tab_name].img_label.image = tk_img

    def _populate_tab(self, tab_name, paths):
        frame = self.frames[tab_name]
        if not paths:
            tk.Label(frame, text="Keine Bilder gefunden.").pack()
            return

        for img_path in paths:
            img = Image.open(img_path)
            img.thumbnail((400, 300), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)

            lbl = tk.Label(frame, image=tk_img)
            lbl.image = tk_img
            lbl.pack(padx=4, pady=4)

    # ---------- Shot_Log Tab (Treeview) ----------
    def _build_shot_log_tab(self):
        """Erzeugt im Tab 'Shot_Log' eine Treeview mit Scrollbars + Infoleiste."""
        frame = self.frames["Shot_Log"]
        for w in frame.winfo_children():
            w.destroy()

        top_bar = ttk.Frame(frame)
        top_bar.pack(fill="x", padx=6, pady=(6, 2))
        self.shot_log_info = ttk.Label(top_bar, text="Keine shot_log-Daten geladen.")
        self.shot_log_info.pack(side="left")

        container = ttk.Frame(frame)
        container.pack(fill="both", expand=True, padx=6, pady=6)

        # Treeview + Scrollbars
        columns = ("shot", "time_us", "acq_ms", "wait_ms", "full_ms")
        self.shot_log_tree = ttk.Treeview(container, columns=columns, show="headings")

        headings = {
            "shot": "Shot",
            "time_us": "Time [µs]",
            "acq_ms": "Acq [ms]",
            "wait_ms": "Wait [ms]",
            "full_ms": "Full [ms]",
        }
        widths = {"shot": 80, "time_us": 120, "acq_ms": 100, "wait_ms": 100, "full_ms": 100}

        for col in columns:
            self.shot_log_tree.heading(col, text=headings[col],
                                       command=lambda c=col: self._sort_shot_log_by(c, False))
            self.shot_log_tree.column(col, width=widths[col], anchor="center")

        vsb = ttk.Scrollbar(container, orient="vertical", command=self.shot_log_tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.shot_log_tree.xview)
        self.shot_log_tree.configure(yscroll=vsb.set, xscroll=hsb.set)

        self.shot_log_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # Erste Befüllung (falls shot_log bereits vorhanden)
        self.refresh_shot_log_table()

    def refresh_shot_log_table(self):
        """Befüllt/aktualisiert die Treeview aus self.shot_log."""
        if not hasattr(self, "shot_log_tree"):
            return

        # Vorherige Einträge löschen
        for item in self.shot_log_tree.get_children():
            self.shot_log_tree.delete(item)

        if self.shot_log is None:
            if hasattr(self, "shot_log_info"):
                self.shot_log_info.config(text="Keine shot_log-Daten geladen.")
            return

        shots = getattr(self.shot_log, "shot", [])
        time_us = getattr(self.shot_log, "time_us", [])
        acq_ms = getattr(self.shot_log, "acq_ms", [])
        wait_ms = getattr(self.shot_log, "wait_ms", [])
        full_ms = getattr(self.shot_log, "full_ms", [])

        n = min(len(shots), len(time_us), len(acq_ms), len(wait_ms), len(full_ms))

        for i in range(n):
            self.shot_log_tree.insert(
                "", "end",
                values=(
                    shots[i],
                    f"{time_us[i]:.3f}",
                    f"{acq_ms[i]:.3f}",
                    f"{wait_ms[i]:.3f}",
                    f"{full_ms[i]:.3f}",
                ),
            )

        d = getattr(self.shot_log, "delimiter_used", "?")
        if hasattr(self, "shot_log_info"):
            self.shot_log_info.config(text=f"{n} Zeilen geladen (Trennzeichen: '{d}').")

    def _sort_shot_log_by(self, col, reverse):
        """Sortiert die Treeview-Spalte col. reverse=False -> aufsteigend."""
        items = [(self.shot_log_tree.item(k, "values"), k) for k in self.shot_log_tree.get_children("")]
        col_index = {"shot": 0, "time_us": 1, "acq_ms": 2, "wait_ms": 3, "full_ms": 4}[col]

        def try_num(s: str):
            try:
                return float(s)
            except Exception:
                try:
                    return int(s)
                except Exception:
                    return s

        items.sort(key=lambda t: try_num(t[0][col_index]), reverse=reverse)

        for i, (_, k) in enumerate(items):
            self.shot_log_tree.move(k, "", i)

        # Nächster Klick -> invertierte Sortierung
        self.shot_log_tree.heading(col, command=lambda c=col: self._sort_shot_log_by(c, not reverse))

    def update_logo(self):
        if hasattr(self, "logo_original"):
            new_width = max(120, int(self.winfo_width() * 0.25))
            aspect_ratio = self.logo_original.height / self.logo_original.width
            new_height = int(new_width * aspect_ratio)

            resized = self.logo_original.resize((new_width, new_height), Image.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(resized)
            self.logo_label.config(image=self.logo_tk)

    def on_resize(self, event):
        self.update_logo()


if __name__ == "__main__":
    app = InjectionGUI()
    app.mainloop()

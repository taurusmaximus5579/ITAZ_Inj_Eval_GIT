"""
23.11.2025 Lars Köhler
[✅] Dateiauswahl optimiert. Er nimmt nur Dateien, welche einem bestimmten Mudter entsprechen
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}_\d+_\d+_.*_(He|N2|CH4|H2)_\d+bar\.csv$")
[✅] Aus dem Dateinamen werden Gas und Art der Auswertung voreingestellt.     
"""

import tkinter as tk
from tkinter import filedialog, ttk
import sys
import os
import re
from PIL import Image, ImageTk  # Pillow installieren: pip install pillow
from ITAZ_Inj_Eval_207 import run_main_analysis  # deine Hauptanalysefunktion


class TextRedirector:
    def __init__(self, text_widget, tag="stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, msg):
        if msg.strip() != "":
            self.text_widget.insert("end", msg + "\n", self.tag)
            self.text_widget.see("end")
            self.text_widget.update_idletasks()

    def flush(self):
        pass


class InjectionGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Injection Analysis GUI")
        self.geometry("1280x760")  # Startgröße
        self.selected_files = []
        self.image_paths = []
        self.current_image_index = 0
        self._build_ui()

        # stdout/stderr ins Log umleiten
        sys.stdout = TextRedirector(self.log, "stdout")
        sys.stderr = TextRedirector(self.log, "stderr")

        # Farben für stdout/stderr
        self.log.tag_configure("stdout", foreground="black")
        self.log.tag_configure("stderr", foreground="red")

        # Event für dynamisches Resize
        self.bind("<Configure>", self.on_resize)

    def _build_ui(self):
        main_pane = ttk.PanedWindow(self, orient="horizontal")
        main_pane.pack(fill="both", expand=True)

        # Linke Seite
        left_frame = ttk.Frame(main_pane)
        self._build_left_ui(left_frame)

        # Rechte Seite: Container für Logo und Bilder
        right_container = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=3)
        main_pane.add(right_container, weight=2)

        # Logo-Frame oben
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

        # Bild-Frame unten
        image_frame = ttk.LabelFrame(right_container, text="Bilder")
        image_frame.pack(fill="both", expand=True, side="top", padx=6, pady=6)

        self.image_label = tk.Label(image_frame)
        self.image_label.pack(fill="both", expand=True, padx=6, pady=6)

        nav_frame = ttk.Frame(image_frame)
        nav_frame.pack(pady=6)
        ttk.Button(nav_frame, text="◀ Zurück", command=self.prev_image).pack(side="left", padx=4)
        ttk.Button(nav_frame, text="▶ Weiter", command=self.next_image).pack(side="left", padx=4)

        self.image_label.config(text="Bilder werden nach Analyse angezeigt.")

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
            "Helium":      {"cv": 3115,  "cp": 5194,  "R": 2077},
            "Stickstoff":  {"cv": 743,   "cp": 1040,  "R": 296.76},
            "Methan":      {"cv": 2220,  "cp": 2850,  "R": 518.24},
            "Wasserstoff": {"cv": 10290, "cp": 14300, "R": 4124.11},
        }
        self.selected_gas = tk.StringVar(value="Helium")
        gas_dropdown = ttk.Combobox(params, textvariable=self.selected_gas,
                                    values=list(self.gas_options.keys()), state="readonly")
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

        ttk.Checkbutton(opts, text="Rohdaten plotten", variable=self.plot_raw_data).pack(side="left", padx=6)
        ttk.Checkbutton(opts, text="Excel exportieren", variable=self.export_excel).pack(side="left", padx=6)
        ttk.Checkbutton(opts, text="Gain-Kurve auswerten", variable=self.eval_gain).pack(side="left", padx=6)
        ttk.Checkbutton(opts, text="Rate-Down-Kurve auswerten", variable=self.eval_rate_dn).pack(side="left", padx=6)

        # Aktionen
        actions = ttk.LabelFrame(parent, text="Aktionen")
        actions.pack(fill="x", padx=10, pady=8)
        ttk.Button(actions, text="Analyse starten", command=self.run_analysis).pack(side="left", padx=6, pady=6)
        self.progress = ttk.Progressbar(actions, mode="determinate", length=250)
        self.progress.pack(side="left", padx=12)
        self.status_lbl = ttk.Label(actions, text="Bereit.")
        self.status_lbl.pack(side="left", padx=12)

        # Log
        logf = ttk.LabelFrame(parent, text="Log")
        logf.pack(fill="both", expand=True, padx=10, pady=8)
        self.log = tk.Text(logf, height=18)
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

    # Gas Defaults
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
            "selected_files": self.selected_files,
        }

    def select_files(self):
        files = filedialog.askopenfilenames(title="Wähle eine oder mehrere CSV-Dateien",
                                            filetypes=[("CSV-Dateien", "*.csv")])
        if files:
            pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}_\d+_\d+_.*_(He|N2|CH4|H2)_\d+bar\.csv$")
            valid_files = []
            detected_gas = None
            gain_found = False
            rate_down_found = False

            for f in files:
                fname = os.path.basename(f)
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

            if detected_gas:
                gas_map = {"He": "Helium", "N2": "Stickstoff", "CH4": "Methan", "H2": "Wasserstoff"}
                self.selected_gas.set(gas_map[detected_gas])
                self.set_gas_defaults()

            self.eval_gain.set(gain_found)
            self.eval_rate_dn.set(rate_down_found)
        else:
            self.selected_files = []

        self.file_count_lbl.config(text=f"{len(self.selected_files)} Dateien ausgewählt")

    def clear_files(self):
        self.selected_files = []
        self.file_count_lbl.config(text="0 Dateien ausgewählt")

    def log_msg(self, msg):
        self.log.insert("end", msg + "\n")
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

            run_main_analysis(cfg)

            self.progress.configure(value=100)
            self.log_msg("✅ Analyse beendet.")
            self.set_status("Fertig.")

            # Nach Analyse Bilder laden
            self.load_images()
            self.after(100, lambda: self.show_image(self.current_image_index))  # Initiales Anpassen
        except Exception as e:
            self.log_msg(f"❌ Fehler während der Analyse: {e}")
            self.set_status("Fehler.")

    # ---------- Bildanzeige ----------
    def load_images(self):
        if not self.selected_files:
            self.image_label.config(text="Keine Analyse-Dateien vorhanden.")
            return

        base_dir = os.path.dirname(self.selected_files[0])
        png_files = []
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if f.lower().endswith(".png"):
                    png_files.append(os.path.join(root, f))

        self.image_paths = sorted(png_files)

        if self.image_paths:
            self.current_image_index = 0
            self.show_image(self.current_image_index)
        else:
            self.image_label.config(text="Keine PNG-Dateien gefunden.")

    def show_image(self, index):
        if not self.image_paths:
            return

        img_path = self.image_paths[index]
        img = Image.open(img_path)

        frame_width = self.image_label.winfo_width()
        frame_height = self.image_label.winfo_height()

        if frame_width < 100 or frame_height < 100:
            frame_width, frame_height = 600, 450

        img.thumbnail((frame_width, frame_height), Image.LANCZOS)

        self.tk_img = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.tk_img, text="")

    def next_image(self):
        if self.image_paths:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
            self.show_image(self.current_image_index)

    def prev_image(self):
        if self.image_paths:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_paths)
            self.show_image(self.current_image_index)

    # ---------- Dynamisches Logo ----------
    def update_logo(self):
        if hasattr(self, "logo_original"):
            new_width = max(120, int(self.winfo_width() * 0.25))  # 8% der Fensterbreite
            aspect_ratio = self.logo_original.height / self.logo_original.width
            new_height = int(new_width * aspect_ratio)

            resized = self.logo_original.resize((new_width, new_height), Image.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(resized)
            self.logo_label.config(image=self.logo_tk)

    def on_resize(self, event):
        self.update_logo()
        if self.image_paths:
            self.show_image(self.current_image_index)


if __name__ == "__main__":
    app = InjectionGUI()
    app.mainloop()

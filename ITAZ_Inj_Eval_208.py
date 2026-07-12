"""
23.11.2025 Lars Köhler
[✅] Stromsignal die Zeiten und Ströme ins Diagramm eintragen
[✅] Neue Funktion für Shot2Shot inkl. Statistik
"""

from pipeline import run_analysis_pipeline


def run_main_analysis(cfg):
    return run_analysis_pipeline(cfg)


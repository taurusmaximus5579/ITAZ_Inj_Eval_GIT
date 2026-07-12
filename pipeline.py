import os
import numpy as np
from config import validate_config
from io_utils import discover_input_files, load_measurement_files, read_shot_log
from preprocessing import build_signal_dict
from analysis.ics import analyze_plateaus
from analysis.needle_lift import analyze_and_plot_needle_lifts
from analysis.injection_rate import InjectionRate
from analysis.gain import GainCurve
from analysis.rate_down import RateDownCurve
from analysis.shot2shot import Eval_Shot2Shot
from plotting import create_plots, plot_signals_per_file
from export import export_results
from image_cache_manager import clear_cache as clear_image_cache


def run_analysis_pipeline(cfg):
    clear_image_cache()  # Neuer Cache für diese Analyse
    config = validate_config(cfg)
    selected_files = discover_input_files(config.selected_files)
    if not selected_files:
        print("❌ Keine Dateien ausgewählt.")
        return

    rawdata_by_file = load_measurement_files(selected_files)
    signal_dict, t_common = build_signal_dict(rawdata_by_file, config)

    ordnerpfad = os.path.dirname(selected_files[0])
    ordnername = os.path.basename(ordnerpfad)
    result_folder = os.path.join(ordnerpfad, "Results")
    os.makedirs(result_folder, exist_ok=True)

    if config.shot_log is None:
        shot_log_path = os.path.join(ordnerpfad, "shot_log.csv")
        config.shot_log = read_shot_log(shot_log_path)

    T = np.array(next(iter(rawdata_by_file.values()))['T'] - next(iter(rawdata_by_file.values()))['T'].iloc[0])

    ics_result = analyze_plateaus(
        signal_dict,
        (config.boost_min, config.boost_max),
        (config.hold_min, config.hold_max),
        (config.zero_min, config.zero_max),
        col="Injector Control Signal (A)",
        T=T,
        ordnerpfad=ordnerpfad,
    )

    integrated_lift, hub_times = analyze_and_plot_needle_lifts(signal_dict, T, ordnerpfad)
    signal_dict['Needle Lift Integrated (mm_s)'] = integrated_lift

    inj_rate_eval = InjectionRate(config.cv, config.cp, config.R, config.Temp, signal_dict, T, config.A, hub_times)
    signal_dict["Injection Rate (mg_ms)"] = inj_rate_eval["injrate_values"]
    signal_dict["Mass (mg)"] = inj_rate_eval["cumulative_mass_values"]

    create_plots(signal_dict, T, result_folder, rawdata_by_file=rawdata_by_file, raw_data_plot=config.plot_raw_data)
    
    # Generate individual signal plots per file and cache them
    plot_signals_per_file(signal_dict, T, result_folder)

    mass_info = None
    all_stats = None
    if config.eval_gain:
        mass_info = GainCurve(signal_dict, T, config.step_size, ics_result, hub_times, ordnerpfad)
    if config.eval_rate_dn:
        mass_info = RateDownCurve(signal_dict, T, config.step_size, hub_times, ordnerpfad)
    if config.shot2shot:
        all_stats = Eval_Shot2Shot(signal_dict, T, config.step_size, ics_result, hub_times, ordnerpfad)

    if config.export_excel:
        export_results(
            signal_dict,
            config,
            ics_result,
            hub_times,
            result_folder,
            ordnername,
            T=T,
            evaluate_gain_curve=config.eval_gain,
            evaluate_rate_down=config.eval_rate_dn,
            evaluate_shot2shot=config.shot2shot,
            mass_info=mass_info,
            all_stats=all_stats,
        )

    return signal_dict

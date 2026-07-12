import os
import numpy as np
import pandas as pd


def export_results(signal_dict, config, ics_result, hub_times, result_folder, ordnername, evaluate_gain_curve=False, evaluate_rate_down=False, evaluate_shot2shot=False, mass_info=None, all_stats=None):
    output_file = os.path.join(result_folder, f"{ordnername}.xlsx")
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        interpolated_signals = signal_dict
        tab_order = [
            'Needle Lift (mm)', 'Mass (mg)', 'Injector Control Signal (A)',
            'System Pressure (abs_bar)', 'Injection Rate (abs_bar)',
            'Injection Rate (mg_ms)', 'Needle Velocity (mm_s)',
            'Needle Lift Integrated (mm_s)', 'Power (W)', 'Energy (Ws)'
        ]
        for sheet_name in tab_order:
            if sheet_name in interpolated_signals:
                df = pd.DataFrame(interpolated_signals[sheet_name])
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        if evaluate_gain_curve and isinstance(mass_info, tuple) and isinstance(mass_info[0], dict):
            df_gain = pd.DataFrame([
                {'Filename': fname, 'ICS_ON': data.get('ICS_ON', np.nan), 'Mass (mg)': data.get('mass', np.nan), 'Needle Lift Integrated (mm_s)': data.get('NeedleLiftIntegrated', np.nan)}
                for fname, data in mass_info[0].items()
            ])
            df_gain.to_excel(writer, sheet_name='GainCurve', index=False)

        if evaluate_rate_down and isinstance(mass_info, tuple) and isinstance(mass_info[0], dict):
            df_rate_down = pd.DataFrame([
                {'Filename': fname, 'System Pressure (abs_bar)': data.get('pressure', np.nan), 'Mass (mg)': data.get('mass', np.nan)}
                for fname, data in mass_info[0].items()
            ])
            df_rate_down.to_excel(writer, sheet_name='RateDownCurve', index=False)

        if config.shot_log is not None:
            df_shot_log = pd.DataFrame({
                "Shot": config.shot_log.get("shot", []),
                "Time [µs]": config.shot_log.get("time_us", []),
                "Acq [ms]": config.shot_log.get("acq_ms", []),
                "Wait [ms]": config.shot_log.get("wait_ms", []),
                "Full [ms]": config.shot_log.get("full_ms", []),
            })
            if not df_shot_log.empty:
                df_shot_log.to_excel(writer, sheet_name="shot_log", index=False)

        df_common = pd.DataFrame(list(config.to_dict().items()), columns=["Parameter", "Value"])
        df_common.to_excel(writer, sheet_name="Common", index=False)

        if evaluate_shot2shot and isinstance(all_stats, dict):
            sheet_name = "Shot2Shot_Stats"
            writer.book.create_sheet(sheet_name)
            sheet = writer.book[sheet_name]
            start_row = 0
            for category, stats_dict in all_stats.items():
                sheet.cell(row=start_row + 1, column=1, value=category)
                sheet.cell(row=start_row + 1, column=1).font = sheet.cell(row=start_row + 1, column=1).font.copy(bold=True)
                start_row += 2
                rows = []
                for metric_name, metric_values in stats_dict.items():
                    row = {"Metric": metric_name}
                    for key, val in metric_values.items():
                        if hasattr(val, "item"):
                            val = float(val)
                        row[key] = val
                    rows.append(row)
                df_stats = pd.DataFrame(rows)
                df_stats.to_excel(writer, sheet_name=sheet_name, index=False, startrow=start_row)
                start_row += len(df_stats) + 3

    print(f"✅ Excel gespeichert: {output_file}")

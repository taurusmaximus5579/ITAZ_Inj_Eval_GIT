import csv
import os
import re
from typing import Dict, List, Optional, Any
import pandas as pd
from types import SimpleNamespace


def discover_input_files(files: List[str]) -> List[str]:
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}_\d+_\d+_.*_(He|N2|CH4|H2)_\d+(?:\.\d+)?bar\.csv$")
    valid_files = []
    for path in files:
        fname = os.path.basename(path)
        if pattern.search(fname):
            valid_files.append(path)
    return valid_files


def load_measurement_files(paths: List[str]) -> Dict[str, pd.DataFrame]:
    data = {}
    for path in paths:
        filename = os.path.splitext(os.path.basename(path))[0]
        rawdata = pd.read_csv(path, sep=';', decimal=',')
        data[filename] = rawdata
    return data


def read_shot_log(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None

    def normalize(s: str) -> str:
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

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            sample = f.read(2048)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters="; ,\t")
                delimiter = dialect.delimiter
            except Exception:
                delimiter = ";"

        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)

        if not rows:
            return None

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
            return None

        shots, time_us, acq_ms, wait_ms, full_ms = [], [], [], [], []
        for row in rows[1:]:
            if not isinstance(row, (list, tuple)) or len(row) < len(raw_header):
                continue

            def get_val(name: str) -> str:
                idx = index_map[name]
                val = row[idx].strip().replace(",", ".")
                return val

            try:
                shots.append(int(get_val("shot")))
                time_us.append(float(get_val("time_us")))
                acq_ms.append(float(get_val("acq_ms")))
                wait_ms.append(float(get_val("wait_ms")))
                full_ms.append(float(get_val("full_ms")))
            except Exception:
                continue

        if not shots:
            return None

        return {
            "shot": shots,
            "time_us": time_us,
            "acq_ms": acq_ms,
            "wait_ms": wait_ms,
            "full_ms": full_ms,
            "delimiter_used": delimiter,
        }
    except Exception:
        return None

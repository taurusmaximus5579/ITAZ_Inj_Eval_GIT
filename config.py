import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AnalysisConfig:
    selected_files: List[str] = field(default_factory=list)
    plot_raw_data: bool = False
    export_excel: bool = True
    eval_gain: bool = False
    eval_rate_dn: bool = False
    shot2shot: bool = False

    gas: str = "Helium"
    cv: float = 3115.0
    cp: float = 5194.0
    R: float = 2077.0
    A: float = 0.00018
    Temp: float = 293.15
    step_size: float = 0.00001

    boost_min: float = 10.5
    boost_max: float = 13.5
    hold_min: float = 3.0
    hold_max: float = 5.0
    zero_min: float = -0.5
    zero_max: float = 0.5

    pressure_sensor: str = "50 bar"
    pressure_factor: float = 5.0
    injection_sensor: str = "10 bar"
    injection_factor: float = 1.0

    shot_log: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gas": self.gas,
            "cv": self.cv,
            "cp": self.cp,
            "R": self.R,
            "A": self.A,
            "Temp": self.Temp,
            "step_size": self.step_size,
            "boost_min": self.boost_min,
            "boost_max": self.boost_max,
            "hold_min": self.hold_min,
            "hold_max": self.hold_max,
            "zero_min": self.zero_min,
            "zero_max": self.zero_max,
            "plot_raw_data": self.plot_raw_data,
            "export_excel": self.export_excel,
            "eval_gain": self.eval_gain,
            "eval_rate_dn": self.eval_rate_dn,
            "shot2shot": self.shot2shot,
            "selected_files": self.selected_files,
            "pressure_sensor": self.pressure_sensor,
            "pressure_factor": self.pressure_factor,
            "injection_sensor": self.injection_sensor,
            "injection_factor": self.injection_factor,
            "shot_log": self.shot_log,
        }


def validate_config(cfg: Dict[str, Any]) -> AnalysisConfig:
    if not isinstance(cfg, dict):
        raise ValueError("cfg must be a dict")

    config = AnalysisConfig()
    config.selected_files = list(cfg.get("selected_files", []))
    config.plot_raw_data = bool(cfg.get("plot_raw_data", False))
    config.export_excel = bool(cfg.get("export_excel", True))
    config.eval_gain = bool(cfg.get("eval_gain", False))
    config.eval_rate_dn = bool(cfg.get("eval_rate_dn", False))
    config.shot2shot = bool(cfg.get("shot2shot", False))

    config.gas = cfg.get("gas", "Helium")
    config.cv = float(cfg.get("cv", 3115.0))
    config.cp = float(cfg.get("cp", 5194.0))
    config.R = float(cfg.get("R", 2077.0))
    config.A = float(cfg.get("A", 0.00018))
    config.Temp = float(cfg.get("Temp", 293.15))
    config.step_size = float(cfg.get("step_size", 0.00001))

    config.boost_min = float(cfg.get("boost_min", 10.5))
    config.boost_max = float(cfg.get("boost_max", 13.5))
    config.hold_min = float(cfg.get("hold_min", 3.0))
    config.hold_max = float(cfg.get("hold_max", 5.0))
    config.zero_min = float(cfg.get("zero_min", -0.5))
    config.zero_max = float(cfg.get("zero_max", 0.5))

    config.pressure_sensor = cfg.get("pressure_sensor", "50 bar")
    config.pressure_factor = float(cfg.get("pressure_factor", 5.0))
    config.injection_sensor = cfg.get("injection_sensor", "10 bar")
    config.injection_factor = float(cfg.get("injection_factor", 1.0))

    config.shot_log = cfg.get("shot_log")
    return config

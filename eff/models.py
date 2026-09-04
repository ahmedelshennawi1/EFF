"""Asset data model and CSV row parsing.

Every measured field is Optional. Missing data is a first-class state: it is
excluded from scoring and reported as reduced confidence, never treated as zero.
"""

from dataclasses import dataclass, field, fields
from typing import Optional

# Ordinal scales used by the condition / obsolescence / compliance indicators.
VIBRATION_ZONES = {"a": 0.0, "b": 25.0, "c": 60.0, "d": 95.0}
OIL_STATES = {"normal": 0.0, "caution": 40.0, "alert": 75.0, "critical": 95.0}
THERMO_STATES = {"normal": 0.0, "caution": 40.0, "alert": 80.0, "critical": 95.0}
INSULATION_STATES = {"good": 0.0, "caution": 45.0, "poor": 85.0, "fail": 100.0}
OEM_SUPPORT = {"supported": 0.0, "limited": 45.0, "discontinued": 80.0, "unsupported": 100.0}
EMISSIONS = {"compliant": 0.0, "marginal": 40.0, "non_compliant": 90.0}


def _f(raw: Optional[str]) -> Optional[float]:
    """Parse a CSV cell as float. Blank, '-' and 'n/a' all mean 'not measured'."""
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "")
    if s == "" or s in {"-", "n/a", "na", "N/A", "NA", "?"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _i(raw: Optional[str]) -> Optional[int]:
    v = _f(raw)
    return None if v is None else int(v)


def _s(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip().lower().replace(" ", "_").replace("-", "_")
    return s or None


@dataclass
class Asset:
    # --- identity -------------------------------------------------------
    asset_id: str = ""
    name: str = ""
    asset_class: str = "production_machine"
    site: str = ""
    manufacturer: str = ""
    model: str = ""

    # --- life -----------------------------------------------------------
    commissioned_year: Optional[int] = None
    run_hours: Optional[float] = None
    design_life_hours: Optional[float] = None
    design_life_years: Optional[float] = None
    annual_run_hours: Optional[float] = None

    # --- reliability ----------------------------------------------------
    annual_downtime_hours: Optional[float] = None
    unplanned_failures_12m: Optional[float] = None

    # --- efficiency -----------------------------------------------------
    specific_consumption: Optional[float] = None
    baseline_specific_consumption: Optional[float] = None
    consumption_unit: str = ""
    load_factor: Optional[float] = None

    # --- capacity -------------------------------------------------------
    rated_output: Optional[float] = None
    actual_output: Optional[float] = None
    output_unit: str = ""

    # --- duty matching: what job is this machine actually assigned to? ----
    duty_task: str = ""
    duty_power_required: Optional[float] = None
    energy_source: Optional[str] = None
    power_factor: Optional[float] = None

    # --- cost -----------------------------------------------------------
    annual_maint_cost: Optional[float] = None
    cumulative_maint_cost: Optional[float] = None
    replacement_value: Optional[float] = None
    salvage_value: Optional[float] = None
    currency: str = "EGP"

    # --- condition ------------------------------------------------------
    vibration_zone: Optional[str] = None
    oil_analysis: Optional[str] = None
    thermography: Optional[str] = None
    insulation: Optional[str] = None

    # --- supportability & compliance ------------------------------------
    oem_support: Optional[str] = None
    spare_lead_days: Optional[float] = None
    safety_findings: Optional[float] = None
    emissions_status: Optional[str] = None

    # --- economics inputs -----------------------------------------------
    annual_output_total: Optional[float] = None
    energy_price: Optional[float] = None
    downtime_cost_per_hour: Optional[float] = None
    new_unit_capital: Optional[float] = None
    new_unit_life_years: Optional[float] = None
    new_unit_specific_consumption: Optional[float] = None

    notes: str = ""

    @property
    def label(self) -> str:
        return f"{self.asset_id} · {self.name}" if self.name else self.asset_id

    @classmethod
    def from_row(cls, row: dict) -> "Asset":
        """Build an Asset from a CSV row, ignoring unknown columns."""
        g = {k.strip().lower(): v for k, v in row.items() if k}

        text = {"asset_id", "name", "site", "manufacturer", "model",
                "consumption_unit", "output_unit", "currency", "notes", "duty_task"}
        enums = {"asset_class", "vibration_zone", "oil_analysis", "thermography",
                 "insulation", "oem_support", "emissions_status", "energy_source"}
        ints = {"commissioned_year"}

        kwargs = {}
        for fl in fields(cls):
            if fl.name not in g:
                continue
            raw = g[fl.name]
            if fl.name in text:
                kwargs[fl.name] = (str(raw).strip() if raw is not None else "")
            elif fl.name in enums:
                v = _s(raw)
                if v is not None:
                    kwargs[fl.name] = v
            elif fl.name in ints:
                kwargs[fl.name] = _i(raw)
            else:
                kwargs[fl.name] = _f(raw)

        return cls(**kwargs)

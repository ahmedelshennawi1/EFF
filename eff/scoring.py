"""Indicator scoring.

Every indicator returns a score in 0..100 where 0 = as-new and 100 = fully
consumed, or None when the underlying data was not measured. Curves are declared
as breakpoint tables so the thresholds stay readable and match docs/CRITERIA.md.
"""

from datetime import date
from typing import List, Optional, Tuple

from .models import (
    Asset, VIBRATION_ZONES, OIL_STATES, THERMO_STATES,
    INSULATION_STATES, OEM_SUPPORT, EMISSIONS,
)
from .profiles import design_life_for, low_load_threshold, part_load_curve

Curve = List[Tuple[float, float]]


def interp(x: Optional[float], curve: Curve) -> Optional[float]:
    """Piecewise-linear lookup, clamped outside the breakpoints."""
    if x is None:
        return None
    if x <= curve[0][0]:
        return curve[0][1]
    if x >= curve[-1][0]:
        return curve[-1][1]
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return curve[-1][1]


AGE_CURVE: Curve = [(0.0, 0), (0.5, 10), (0.8, 30), (1.0, 55), (1.3, 80), (2.0, 100)]
UNAVAIL_CURVE: Curve = [(0.0, 0), (0.03, 15), (0.05, 30), (0.10, 60), (0.20, 90), (0.30, 100)]
FAILRATE_CURVE: Curve = [(0.0, 0), (0.5, 20), (1.0, 40), (2.0, 70), (4.0, 92), (6.0, 100)]
EFFICIENCY_CURVE: Curve = [(0.0, 0), (0.03, 10), (0.05, 25), (0.10, 50), (0.15, 70),
                           (0.25, 90), (0.40, 100)]
DERATE_CURVE: Curve = [(0.0, 0), (0.05, 10), (0.10, 30), (0.20, 60), (0.30, 85), (0.45, 100)]
ANNUAL_COST_CURVE: Curve = [(0.0, 0), (0.03, 10), (0.05, 25), (0.08, 50), (0.12, 75), (0.20, 100)]
CUMUL_COST_CURVE: Curve = [(0.0, 0), (0.30, 15), (0.50, 40), (0.75, 70), (1.00, 90), (1.50, 100)]
LEADTIME_CURVE: Curve = [(7.0, 0), (30.0, 20), (60.0, 45), (120.0, 75), (240.0, 100)]
SAFETY_CURVE: Curve = [(0.0, 0), (1.0, 60), (2.0, 85), (3.0, 100)]


def life_ratio(a: Asset) -> Optional[float]:
    """Fraction of design life consumed — worst of the hours and calendar views."""
    defaults = design_life_for(a.asset_class)
    ratios = []

    dlh = a.design_life_hours or defaults["hours"]
    if a.run_hours is not None and dlh:
        ratios.append(a.run_hours / dlh)

    dly = a.design_life_years or defaults["years"]
    if a.commissioned_year is not None and dly:
        ratios.append((date.today().year - a.commissioned_year) / dly)

    return max(ratios) if ratios else None


def score_age(a: Asset) -> Optional[float]:
    return interp(life_ratio(a), AGE_CURVE)


def score_reliability(a: Asset) -> Optional[float]:
    parts, weights = [], []

    if a.annual_downtime_hours is not None and a.annual_run_hours:
        total = a.annual_run_hours + a.annual_downtime_hours
        if total > 0:
            parts.append(interp(a.annual_downtime_hours / total, UNAVAIL_CURVE))
            weights.append(0.55)

    if a.unplanned_failures_12m is not None and a.annual_run_hours:
        per_1000 = a.unplanned_failures_12m / (a.annual_run_hours / 1000.0)
        parts.append(interp(per_1000, FAILRATE_CURVE))
        weights.append(0.45)

    if not parts:
        return None
    return sum(p * w for p, w in zip(parts, weights)) / sum(weights)


def corrected_baseline(a: Asset) -> Optional[float]:
    """Baseline specific consumption adjusted to the load actually measured.

    Machines are least efficient per unit of output when lightly loaded, so one
    measured at 30% load must be judged against a 30%-load baseline, not its
    nameplate figure. Comparing an uncorrected reading to a nameplate baseline is
    the single most damaging false positive this framework can produce.

    Curves live in the machinery library. Classes without one are left
    uncorrected rather than borrowing a curve that does not describe them.
    """
    if not a.baseline_specific_consumption:
        return None
    curve = part_load_curve(a.asset_class)
    if curve is None or a.load_factor is None:
        return a.baseline_specific_consumption
    return a.baseline_specific_consumption * interp(a.load_factor, curve)


def efficiency_degradation(a: Asset) -> Optional[float]:
    """Fractional rise in specific consumption vs. a load-corrected baseline."""
    base = corrected_baseline(a)
    if a.specific_consumption is None or not base:
        return None
    return (a.specific_consumption - base) / base


def score_efficiency(a: Asset) -> Optional[float]:
    return interp(efficiency_degradation(a), EFFICIENCY_CURVE)


def chronically_underloaded(a: Asset) -> bool:
    """Running well below rated load: a dispatch/sizing fault, not a worn asset.

    Sustained low load on a diesel also causes wet stacking, which degrades
    consumption and fouls the engine — the machine is being damaged by how it is
    used, and replacing it would repeat the problem with a new one.
    """
    threshold = low_load_threshold(a.asset_class)
    return (threshold is not None
            and a.load_factor is not None
            and a.load_factor < threshold)


def score_capacity(a: Asset) -> Optional[float]:
    if a.actual_output is None or not a.rated_output:
        return None
    return interp(1.0 - (a.actual_output / a.rated_output), DERATE_CURVE)


def score_maint_cost(a: Asset) -> Optional[float]:
    if not a.replacement_value:
        return None
    parts, weights = [], []

    if a.annual_maint_cost is not None:
        parts.append(interp(a.annual_maint_cost / a.replacement_value, ANNUAL_COST_CURVE))
        weights.append(0.55)

    if a.cumulative_maint_cost is not None:
        parts.append(interp(a.cumulative_maint_cost / a.replacement_value, CUMUL_COST_CURVE))
        weights.append(0.45)

    if not parts:
        return None
    return sum(p * w for p, w in zip(parts, weights)) / sum(weights)


def score_condition(a: Asset) -> Optional[float]:
    """0.6 * worst + 0.4 * mean, so one critical finding is not averaged away."""
    checks = [
        (a.vibration_zone, VIBRATION_ZONES),
        (a.oil_analysis, OIL_STATES),
        (a.thermography, THERMO_STATES),
        (a.insulation, INSULATION_STATES),
    ]
    vals = [scale[v] for v, scale in checks if v is not None and v in scale]
    if not vals:
        return None
    return 0.6 * max(vals) + 0.4 * (sum(vals) / len(vals))


def score_obsolescence(a: Asset) -> Optional[float]:
    parts, weights = [], []

    if a.oem_support is not None and a.oem_support in OEM_SUPPORT:
        parts.append(OEM_SUPPORT[a.oem_support])
        weights.append(0.60)

    if a.spare_lead_days is not None:
        parts.append(interp(a.spare_lead_days, LEADTIME_CURVE))
        weights.append(0.40)

    if not parts:
        return None
    return sum(p * w for p, w in zip(parts, weights)) / sum(weights)


def score_compliance(a: Asset) -> Optional[float]:
    """Worst-of. Safety is not tradeable against the other indicators."""
    vals = []
    if a.safety_findings is not None:
        vals.append(interp(a.safety_findings, SAFETY_CURVE))
    if a.emissions_status is not None and a.emissions_status in EMISSIONS:
        vals.append(EMISSIONS[a.emissions_status])
    return max(vals) if vals else None


SCORERS = {
    "AGE": score_age,
    "RELIABILITY": score_reliability,
    "EFFICIENCY": score_efficiency,
    "CAPACITY": score_capacity,
    "MAINT_COST": score_maint_cost,
    "CONDITION": score_condition,
    "OBSOLESCENCE": score_obsolescence,
    "COMPLIANCE": score_compliance,
}


def score_all(a: Asset) -> dict:
    """Run every indicator. Values are float or None (not measured)."""
    return {name: fn(a) for name, fn in SCORERS.items()}

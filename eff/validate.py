"""Input consistency checks.

`annual_output_total` is the quietest high-stakes field in the whole record. It
does not affect the fitness score at all, so a wrong value produces no visible
symptom — but it multiplies straight into the energy penalty, which is usually
the largest single term in the replacement economics. A tenfold unit slip there
moves the recommendation without moving anything a reader would notice.

So it is checked against what the equipment's own rate and run-hours imply.
"""

from typing import List, Optional, Tuple

from .models import Asset

# Rate units that are not per-hour, and the factor converting them to per-hour.
RATE_FACTORS = {"/min": 60.0, "/minute": 60.0, "/sec": 3600.0, "/s": 3600.0}

OUTPUT_TOLERANCE = 0.15

# Same-family unit scales, so a boiler rated in kg/h reconciles with steam totals
# in tons, and a fan rated in m3/h with totals in 1000m3 — industry-standard
# pairings, not data errors. Families are separate: kg never converts to m3.
_UNIT_SCALE = {
    "kg": ("mass", 1.0), "ton": ("mass", 1000.0), "t": ("mass", 1000.0),
    "tonne": ("mass", 1000.0),
    "m3": ("vol", 1.0), "1000m3": ("vol", 1000.0),
}


def _unit_token(s: str) -> str:
    """'kg/h' -> 'kg'; 'ton_steam' -> 'ton'; 'M3' -> 'm3'."""
    return s.strip().lower().split("/")[0].split("_")[0].strip()


def _scale_between(rate_unit: str, denom: str) -> float:
    """Factor converting the rate's unit into the denominator's unit, or 1.0."""
    a = _UNIT_SCALE.get(_unit_token(rate_unit))
    b = _UNIT_SCALE.get(denom.strip().lower().split("_")[0])
    if a and b and a[0] == b[0]:
        return a[1] / b[1]
    return 1.0


def _rate_to_hourly(a: Asset) -> Tuple[Optional[float], float]:
    """The asset's output rate, converted to 'per hour', and the factor used."""
    unit = (a.output_unit or "").strip().lower()
    factor = 1.0
    for suffix, f in RATE_FACTORS.items():
        if unit.endswith(suffix):
            factor = f
            break

    # When a load factor is recorded, the machine's *sustained* output is the
    # rated figure at that load — not what it can do flat out.
    if a.load_factor is not None and a.rated_output is not None:
        return a.rated_output * a.load_factor, factor
    if a.actual_output is not None:
        return a.actual_output, factor
    return a.rated_output, factor


def implied_annual_output(a: Asset) -> Optional[float]:
    """Annual output implied by the run-hours and the rate, or None if unknowable."""
    if not a.annual_run_hours:
        return None

    # If specific consumption is stated per hour (e.g. vehicles at L/h), then the
    # denominator of the efficiency figure IS run-hours, and annual output must
    # equal them. Nothing to derive from an output rate.
    denominator = (a.consumption_unit or "").split("/")[-1].strip().lower()
    if denominator in {"h", "hr", "hour", "hours"}:
        return a.annual_run_hours

    rate, factor = _rate_to_hourly(a)
    if rate is None:
        return None
    return (rate * factor * a.annual_run_hours
            * _scale_between(a.output_unit or "", denominator))


def check_output(a: Asset, tolerance: float = OUTPUT_TOLERANCE) -> Optional[str]:
    """Flag a declared annual output that its own rate and run-hours contradict."""
    if not a.annual_output_total:
        return None
    implied = implied_annual_output(a)
    if not implied:
        return None

    ratio = a.annual_output_total / implied
    if abs(ratio - 1.0) <= tolerance:
        return None

    # Name the likely slip in the direction the reader has to correct it.
    hint = ""
    for factor, cause in ((60.0, "a per-minute rate"), (3600.0, "a per-second rate"),
                          (1000.0, "a thousands")):
        if abs(ratio - factor) / factor < 0.10:
            hint = f" — declared is ~{factor:,.0f}x too large, as if {cause} slipped in"
            break
        if abs(ratio - 1.0 / factor) * factor < 0.10:
            hint = f" — declared is ~{factor:,.0f}x too small, as if {cause} slipped in"
            break

    return (f"annual_output_total ({a.annual_output_total:,.0f}) disagrees with the "
            f"{implied:,.0f} implied by the output rate and run-hours"
            f"{hint or f' ({ratio:.2f}x)'}. This scales the energy penalty in the "
            f"economics directly, but affects no indicator score — so a wrong value "
            f"here moves the money with no visible symptom.")


def utilisation(a: Asset) -> Optional[float]:
    """Share of the calendar year the asset actually ran."""
    if not a.annual_run_hours:
        return None
    return a.annual_run_hours / 8760.0


def advisories(a: Asset) -> List[str]:
    """Non-blocking findings about the data or how the asset is being used."""
    from .scoring import chronically_underloaded

    notes: List[str] = []

    out = check_output(a)
    if out:
        notes.append(out)

    if chronically_underloaded(a):
        notes.append(
            f"running at {a.load_factor:.0%} of rated load — chronically under-loaded. "
            f"Low-load operation raises fuel per kWh and causes wet stacking, so poor "
            f"efficiency here is a sizing and dispatch fault, not a worn machine. "
            f"Right-size or re-dispatch before replacing.")

    # Any class with a part-load curve needs a load factor for its efficiency
    # reading to mean anything at all.
    from .profiles import part_load_curve
    if (a.specific_consumption is not None and a.baseline_specific_consumption
            and a.load_factor is None
            and part_load_curve(a.asset_class) is not None):
        notes.append(
            "efficiency measured without a load factor, so the baseline could not be "
            "load-corrected. The reading is only meaningful if it was taken at rated load.")

    return notes

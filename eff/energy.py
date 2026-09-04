"""Energy burn — the daily cost of running worse than necessary.

Energy is working capital that burns every day the machine runs, which makes
annual percentages the wrong presentation. This module decomposes each asset's
excess consumption into two separately-owned problems and prices both per day:

    sec_actual     what the machine burns per unit of output (measured)
    sec_expected   what a HEALTHY machine of this rating burns at the same load
    sec_ideal      what a healthy, RIGHT-SIZED machine burns at target load

    wear burn        = (sec_actual − sec_expected) × output × price
    allocation burn  = (sec_expected − sec_ideal)  × output × price

Wear burn belongs to maintenance: the machine has degraded against its own
corrected baseline. Allocation burn belongs to operations: the machine is the
wrong size for its duty, so even in perfect condition it burns more than the
job requires. The two sum to the total gap against the ideal, with no double
counting — they partition it.

When no baseline exists, the class benchmark range from the machinery library
is used instead and the result is marked indicative: good enough to rank the
fleet's burners, not good enough to sign a purchase order.
"""

from dataclasses import dataclass
from typing import List, Optional

from .models import Asset
from .profiles import library
from .scoring import interp

DAYS = 365.0

# Below this power factor, Egyptian industrial tariffs apply reactive-power
# surcharges; flag exposure without attempting to model a specific tariff.
PF_FLAG = 0.90


@dataclass
class EnergyBurn:
    available: bool = False
    basis: str = ""              # "baseline" | "benchmark" | ""
    reason: str = ""
    currency: str = "EGP"

    sec_actual: Optional[float] = None
    sec_expected: Optional[float] = None
    sec_ideal: Optional[float] = None
    unit: str = ""

    wear_per_day: float = 0.0
    allocation_per_day: float = 0.0

    @property
    def total_per_day(self) -> float:
        return self.wear_per_day + self.allocation_per_day

    @property
    def total_per_year(self) -> float:
        return self.total_per_day * DAYS

    @property
    def indicative(self) -> bool:
        return self.basis == "benchmark"


def assess(a: Asset) -> EnergyBurn:
    lib = library()
    b = EnergyBurn(currency=a.currency or "EGP",
                   unit=a.consumption_unit or lib.klass(a.asset_class).get("unit", ""))

    if a.specific_consumption is None:
        b.reason = "specific consumption not measured"
        return b
    if not a.annual_output_total or not a.energy_price:
        b.reason = "annual output or energy price missing, so the burn cannot be priced"
        return b

    b.sec_actual = a.specific_consumption
    curve = lib.part_load_curve(a.asset_class)

    baseline = a.baseline_specific_consumption
    if baseline:
        b.basis = "baseline"
    else:
        bench = lib.benchmark_for(a.asset_class)
        if not bench:
            b.reason = ("no baseline and no class benchmark — the reading cannot "
                        "be judged against anything")
            return b
        # The top of the benchmark range is the conservative comparator: a
        # machine worse than the worst typical performer is burning money
        # under any assumption. Marked indicative either way.
        baseline = bench["high"]
        b.basis = "benchmark"

    if curve is not None and a.load_factor is not None:
        b.sec_expected = baseline * interp(a.load_factor, curve)
        b.sec_ideal = baseline * interp(lib.target_load, curve)
    else:
        b.sec_expected = baseline
        b.sec_ideal = baseline

    per_unit_to_day = a.annual_output_total * a.energy_price / DAYS
    b.wear_per_day = max(0.0, b.sec_actual - b.sec_expected) * per_unit_to_day
    b.allocation_per_day = max(0.0, b.sec_expected - b.sec_ideal) * per_unit_to_day

    b.available = True
    return b


def advisories(a: Asset, b: EnergyBurn) -> List[str]:
    notes: List[str] = []
    cur = a.currency or "EGP"

    if b.available and b.total_per_day >= 1.0:
        parts = []
        if b.wear_per_day >= 1.0:
            parts.append(f"{cur} {b.wear_per_day:,.0f}/day from degradation "
                         f"(a maintenance problem)")
        if b.allocation_per_day >= 1.0:
            parts.append(f"{cur} {b.allocation_per_day:,.0f}/day from running the wrong "
                         f"size machine for the duty (an operations problem)")
        tag = " — benchmark-based, indicative" if b.indicative else ""
        notes.append(f"burning {cur} {b.total_per_day:,.0f} per day above what the work "
                     f"requires: " + "; ".join(parts) + tag + ".")

    if a.power_factor is not None and a.power_factor < PF_FLAG:
        notes.append(
            f"power factor {a.power_factor:.2f} is below {PF_FLAG:.2f} — Egyptian "
            f"industrial tariffs surcharge reactive power at this level, and correction "
            f"capacitors are usually the fastest-payback item on the whole site.")

    return notes

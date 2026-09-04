"""Duty matching — is this the right size machine for the job it is doing?

This asks a different question from the fitness score, and mixing the two would
corrupt both. A 500 hp tractor pulling a pesticide sprayer is not worn out; it is
*misallocated*. Score it on condition and it comes back healthy, and the waste —
which can run to six figures a year in fuel — never appears anywhere.

So duty match is a separate finding with its own verdict and its own money.
The remedy is usually reassignment or re-sizing, not replacement, and it is often
the cheapest saving available on the whole site.

The comparison holds the *work* constant. Both the existing machine and a
right-sized one deliver the same duty power, so the useful-work term cancels and
what remains is purely the part-load penalty each one pays:

    excess_per_hour = duty_power x specific_consumption x (penalty(actual) - penalty(target))
"""

from dataclasses import dataclass
from typing import Optional

from .models import Asset
from .profiles import library
from .scoring import interp

# Bands on duty_power / rated_output.
SEVERELY_OVERSIZED = 0.35
OVERSIZED = 0.55
WELL_MATCHED_MAX = 1.00


@dataclass
class DutyMatch:
    available: bool = False
    reason: str = ""

    task: str = ""
    duty_power: Optional[float] = None
    rated_power: Optional[float] = None
    ratio: Optional[float] = None

    verdict: str = ""            # severely_oversized | oversized | matched | undersized
    recommended_rating: Optional[float] = None

    penalty_actual: Optional[float] = None
    penalty_target: Optional[float] = None
    excess_per_hour: Optional[float] = None      # in consumption units (L, kWh, m3)
    annual_excess_cost: Optional[float] = None
    currency: str = "EGP"

    @property
    def is_mismatched(self) -> bool:
        return self.available and self.verdict in ("severely_oversized", "oversized", "undersized")


def _verdict_for(ratio: float) -> str:
    if ratio < SEVERELY_OVERSIZED:
        return "severely_oversized"
    if ratio < OVERSIZED:
        return "oversized"
    if ratio <= WELL_MATCHED_MAX:
        return "matched"
    return "undersized"


def assess(a: Asset) -> DutyMatch:
    """Compare the power a task needs against the machine assigned to it."""
    lib = library()
    d = DutyMatch(currency=a.currency or "EGP", task=a.duty_task or "")

    if not lib.duty_matched(a.asset_class):
        d.reason = (f"duty matching does not apply to "
                    f"{lib.label(a.asset_class)} in this library")
        return d
    if not a.rated_output:
        d.reason = "no rated output for the machine"
        return d
    if not a.duty_power_required:
        d.reason = "the task's power requirement (duty_power_required) is not recorded"
        return d

    d.duty_power = a.duty_power_required
    d.rated_power = a.rated_output
    d.ratio = a.duty_power_required / a.rated_output
    d.verdict = _verdict_for(d.ratio)

    target = lib.target_load
    d.recommended_rating = a.duty_power_required / target

    curve = lib.part_load_curve(a.asset_class)
    if curve is None:
        d.available = True
        d.reason = ("no part-load curve for this class, so the size mismatch is "
                    "reported without a fuel cost")
        return d

    d.penalty_actual = interp(min(d.ratio, 1.0), curve)
    d.penalty_target = interp(target, curve)

    # An undersized machine is not paying a part-load penalty — it is being
    # overworked, which shows up as accelerated wear, not as excess fuel.
    if d.ratio > 1.0:
        d.available = True
        return d

    base = a.baseline_specific_consumption
    if base is None:
        d.available = True
        d.reason = "no baseline specific consumption, so the excess cannot be priced"
        return d

    d.excess_per_hour = max(
        0.0, d.duty_power * base * (d.penalty_actual - d.penalty_target))

    if a.annual_run_hours and a.energy_price:
        d.annual_excess_cost = d.excess_per_hour * a.annual_run_hours * a.energy_price

    d.available = True
    return d


def describe(d: DutyMatch, lib=None) -> str:
    """A one-line finding suitable for a report."""
    if not d.available:
        return ""
    if d.verdict == "matched":
        return (f"sized appropriately for its task "
                f"({d.ratio:.0%} of rated output)")

    if d.verdict == "undersized":
        return (f"the task needs {d.ratio:.0%} of this machine's rated output — it is being "
                f"overworked, which accelerates wear and shortens life. A larger unit, or "
                f"splitting the duty, is the fix.")

    head = ("severely oversized" if d.verdict == "severely_oversized" else "oversized")
    msg = (f"{head} for its task: the job needs {d.duty_power:,.0f} of "
           f"{d.rated_power:,.0f} rated ({d.ratio:.0%}). "
           f"A unit rated around {d.recommended_rating:,.0f} would carry it at "
           f"{lib.target_load if lib else 0.80:.0%} load.")
    if d.annual_excess_cost:
        msg += (f" Running oversized costs about {d.currency} "
                f"{d.annual_excess_cost:,.0f} per year in extra fuel or power alone.")
    msg += (" The remedy is reassignment or re-sizing, not replacement — "
            "the machine itself may be perfectly sound.")
    return msg

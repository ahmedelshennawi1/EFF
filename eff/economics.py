"""Replacement-timing economics.

The score says how worn a machine is. This says whether replacing it pays.
Decision rule: replace when the marginal cost of keeping the asset one more
year exceeds the equivalent annual cost of a new one.

See docs/CRITERIA.md section 6.
"""

from dataclasses import dataclass
from typing import Optional

from .models import Asset
from .scoring import life_ratio


def crf(rate: float, years: float) -> float:
    """Capital recovery factor — spreads a capital sum over n years at rate r."""
    if years <= 0:
        return 0.0
    if rate == 0:
        return 1.0 / years
    f = (1.0 + rate) ** years
    return rate * f / (f - 1.0)


@dataclass
class Economics:
    available: bool = False
    reason: str = ""
    currency: str = "EGP"
    rate: float = 0.0

    eac_new: Optional[float] = None
    marginal_keep: Optional[float] = None

    maintenance_term: Optional[float] = None
    energy_penalty: Optional[float] = None
    downtime_term: Optional[float] = None
    salvage_decay_term: Optional[float] = None
    capital_tied_term: Optional[float] = None

    excess_downtime_hours: Optional[float] = None
    materiality: float = 0.15

    @property
    def replace_favoured(self) -> bool:
        """True only when replacing wins by a margin worth acting on.

        These inputs are estimates, not invoices. A result inside the noise
        band is a tie, and a tie should not move a capital decision.
        """
        if not self.available:
            return False
        return self.marginal_keep > self.eac_new * (1.0 + self.materiality)

    @property
    def annual_saving(self) -> Optional[float]:
        """Positive means replacing saves this much per year."""
        if not self.available:
            return None
        return self.marginal_keep - self.eac_new


def assess(a: Asset, rate: float, salvage_decay: float = 0.08,
           benchmark_unavailability: float = 0.02,
           materiality: float = 0.15) -> Economics:
    """Compare keeping the asset one more year against buying its replacement.

    Both sides are stated on a **differential** basis: costs that are incurred
    either way cancel and are excluded. Concretely, the energy a new unit would
    itself consume is not charged to either side — only the *excess* the old
    unit burns above it appears, in the keep term. Charging full energy to the
    new unit while charging only the excess to the old one would compare two
    different bases and always favour keeping.

    `salvage_decay` is the fraction of current resale value lost per year of
    continued use — the cost of not selling the asset now.
    """
    e = Economics(currency=a.currency or "EGP", rate=rate, materiality=materiality)

    if not a.new_unit_capital:
        e.reason = "no replacement quote (new_unit_capital)"
        return e

    life = a.new_unit_life_years
    if not life:
        e.reason = "no expected life for the replacement (new_unit_life_years)"
        return e

    # --- cost of the new unit, annualised over its whole life ---------------
    # Capital recovery only. The new unit's maintenance is assumed covered by
    # warranty in its early years, and its energy cancels on the differential
    # basis above. Both simplifications are conservative *against* replacing.
    e.eac_new = a.new_unit_capital * crf(rate, life)

    # --- cost of keeping the existing unit one more year --------------------
    e.maintenance_term = a.annual_maint_cost or 0.0

    # Extra energy the old unit burns versus a new one, over a year of output.
    e.energy_penalty = 0.0
    baseline_new = a.new_unit_specific_consumption
    if baseline_new is None:
        baseline_new = a.baseline_specific_consumption
    if (a.annual_output_total and a.energy_price
            and a.specific_consumption is not None and baseline_new is not None):
        delta = a.specific_consumption - baseline_new
        e.energy_penalty = max(0.0, a.annual_output_total * delta * a.energy_price)

    # Only downtime *above* what a well-run new unit would itself incur is a
    # cost of keeping. Charging the full figure would assume a replacement
    # never fails, which silently biases every asset towards replacement.
    e.downtime_term = 0.0
    e.excess_downtime_hours = 0.0
    if a.annual_downtime_hours and a.downtime_cost_per_hour:
        allowance = (a.annual_run_hours or 0.0) * benchmark_unavailability
        e.excess_downtime_hours = max(0.0, a.annual_downtime_hours - allowance)
        e.downtime_term = e.excess_downtime_hours * a.downtime_cost_per_hour

    salvage = a.salvage_value or 0.0
    e.salvage_decay_term = salvage * salvage_decay
    e.capital_tied_term = salvage * rate

    e.marginal_keep = (e.maintenance_term + e.energy_penalty + e.downtime_term
                       + e.salvage_decay_term + e.capital_tied_term)
    e.available = True
    return e


def remaining_life_years(a: Asset) -> Optional[float]:
    """Rough remaining life from design-life consumption, floored at zero."""
    r = life_ratio(a)
    if r is None:
        return None
    from .profiles import design_life_for
    years = a.design_life_years or design_life_for(a.asset_class)["years"]
    return max(0.0, (1.0 - r) * years)

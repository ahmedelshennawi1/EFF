"""CO2 from wasted energy.

The environmental number must come out of the same arithmetic as the money, or
it is decoration. Every unit of excess consumption the burn ledger already
computes is converted here to CO2e using the fuel's emission factor — so the
tonnes and the pounds are two readings of one measurement, and neither can move
without the other.

Physical excess is recovered from the burn's own terms:

    excess_units = (sec_actual - sec_ideal) x annual_output_total

whose unit is the NUMERATOR of the consumption unit (L, m3, kWh), matched to the
asset's energy_source to pick a factor.
"""

from dataclasses import dataclass
from typing import Optional

from .energy import DAYS, EnergyBurn
from .models import Asset

# kg CO2e per unit burned. Combustion factors are well-established; the grid
# factor is Egypt-specific and moves as the generation mix changes, so it lives
# here as one named constant rather than scattered through the code.
FACTORS = {
    "diesel":      ("l",   2.68),   # kg CO2e per litre
    "petrol":      ("l",   2.31),
    "lpg":         ("l",   1.51),
    "natural_gas": ("m3",  1.93),   # kg CO2e per m3
    "electricity": ("kwh", 0.46),   # Egypt grid average — refresh as the mix shifts
    "solar":       ("kwh", 0.0),
    "biomass":     ("kg",  0.0),    # biogenic carbon, counted as neutral
}

# A car driven ~15,000 km/yr at ~180 g/km — used only to make tonnes legible.
KG_PER_CAR_YEAR = 2700.0
# A mature tree absorbs roughly this much per year.
KG_PER_TREE_YEAR = 22.0


def _numerator(consumption_unit: str) -> str:
    return (consumption_unit or "").split("/")[0].strip().lower()


@dataclass
class Emissions:
    available: bool = False
    reason: str = ""
    source: str = ""
    factor: float = 0.0
    excess_units_per_year: float = 0.0
    unit: str = ""
    kg_per_year: float = 0.0

    @property
    def tonnes_per_year(self) -> float:
        return self.kg_per_year / 1000.0

    @property
    def cars_equivalent(self) -> float:
        return self.kg_per_year / KG_PER_CAR_YEAR

    @property
    def trees_equivalent(self) -> float:
        return self.kg_per_year / KG_PER_TREE_YEAR


def assess(a: Asset, burn: EnergyBurn) -> Emissions:
    """CO2e attributable to the excess consumption the burn ledger found."""
    e = Emissions()

    if not (burn and burn.available):
        e.reason = "no energy burn computed for this asset"
        return e
    if not a.energy_source:
        e.reason = "energy_source not recorded, so no emission factor applies"
        return e

    spec = FACTORS.get(a.energy_source)
    if spec is None:
        e.reason = f"no emission factor for energy source '{a.energy_source}'"
        return e

    expected_unit, factor = spec
    num = _numerator(a.consumption_unit)
    # kW/TR integrates to kWh over run hours, so a kW numerator is energy here.
    if num == "kw":
        num = "kwh"
    if num != expected_unit:
        e.reason = (f"consumption is measured in '{num}' but {a.energy_source} is "
                    f"factored per '{expected_unit}' — units do not match")
        return e

    if burn.sec_actual is None or burn.sec_ideal is None or not a.annual_output_total:
        e.reason = "not enough of the burn terms survive to recover physical excess"
        return e

    e.source = a.energy_source
    e.factor = factor
    e.unit = expected_unit
    e.excess_units_per_year = max(0.0, burn.sec_actual - burn.sec_ideal) * a.annual_output_total
    e.kg_per_year = e.excess_units_per_year * factor
    e.available = True
    return e


def describe(e: Emissions) -> str:
    if not e.available or e.kg_per_year < 1:
        return ""
    return (f"wasted energy here emits {e.tonnes_per_year:,.1f} tonnes CO2e a year — "
            f"about {e.trees_equivalent:,.0f} trees' worth of annual absorption. "
            f"Cutting the waste cuts both the bill and the emissions, by construction.")

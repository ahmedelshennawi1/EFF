"""Weighted roll-up, banding, hard overrides and data confidence."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .economics import Economics, assess as assess_economics
from .models import Asset
from .duty import DutyMatch, assess as assess_duty, describe as describe_duty
from .emissions import Emissions, assess as assess_emissions
from .energy import EnergyBurn, advisories as energy_advisories, assess as assess_energy
from .profiles import library, weights_for
from .scoring import score_all
from .validate import advisories as data_advisories, utilisation

BANDS = ["KEEP", "MONITOR", "PLAN_REPLACEMENT", "RETIRE_NOW"]

BAND_THRESHOLDS = [(25.0, "KEEP"), (45.0, "MONITOR"), (65.0, "PLAN_REPLACEMENT")]

CONFIDENCE_DECISION_GRADE = 85.0
CONFIDENCE_FLOOR = 60.0


def band_for_score(score: float) -> str:
    for limit, name in BAND_THRESHOLDS:
        if score < limit:
            return name
    return "RETIRE_NOW"


def _at_least(current: str, minimum: str) -> str:
    return current if BANDS.index(current) >= BANDS.index(minimum) else minimum


@dataclass
class Assessment:
    asset: Asset
    scores: Dict[str, Optional[float]] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=dict)
    fitness: float = 0.0
    confidence: float = 0.0
    band: str = "KEEP"
    raw_band: str = "KEEP"
    overrides: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    advisories: List[str] = field(default_factory=list)
    utilisation: Optional[float] = None
    economics: Optional[Economics] = None
    duty: Optional[DutyMatch] = None
    energy: Optional[EnergyBurn] = None
    emissions: Optional[Emissions] = None
    unknown_class: bool = False

    @property
    def decision_grade(self) -> bool:
        return self.confidence >= CONFIDENCE_FLOOR

    @property
    def drivers(self) -> List[tuple]:
        """Indicators contributing most to the score, worst first."""
        contrib = [
            (name, s, self.weights[name] * s / 100.0)
            for name, s in self.scores.items()
            if s is not None and self.weights.get(name)
        ]
        contrib.sort(key=lambda t: t[2], reverse=True)
        return contrib[:3]


def _apply_overrides(a: Asset, band: str, econ: Optional[Economics]) -> tuple:
    notes: List[str] = []

    if a.safety_findings is not None and a.safety_findings >= 1:
        band = _at_least(band, "RETIRE_NOW")
        notes.append(f"{int(a.safety_findings)} open critical safety finding(s) — "
                     "remediate before any return to service")

    if a.insulation == "fail":
        band = _at_least(band, "RETIRE_NOW")
        notes.append("insulation test failed")

    if (a.cumulative_maint_cost is not None and a.replacement_value
            and a.cumulative_maint_cost > a.replacement_value):
        band = _at_least(band, "RETIRE_NOW")
        notes.append("cumulative maintenance spend has exceeded replacement value")

    if a.emissions_status == "non_compliant":
        band = _at_least(band, "PLAN_REPLACEMENT")
        notes.append("emissions non-compliant")

    if a.vibration_zone == "d":
        band = _at_least(band, "PLAN_REPLACEMENT")
        notes.append("vibration in ISO zone D")

    if (a.oem_support == "unsupported" and a.spare_lead_days is not None
            and a.spare_lead_days > 120):
        band = _at_least(band, "PLAN_REPLACEMENT")
        notes.append("no OEM support and spare lead time over 120 days")

    # The economic test tells you to *budget*, never to stop running a machine
    # that is physically sound — so it escalates at most to PLAN_REPLACEMENT.
    # Reaching RETIRE_NOW requires condition, safety or score evidence.
    if econ is not None and econ.replace_favoured:
        target = BANDS[min(BANDS.index(band) + 1, BANDS.index("PLAN_REPLACEMENT"))]
        if BANDS.index(target) > BANDS.index(band):
            notes.append(
                f"economic test favours replacement by "
                f"{econ.currency} {econ.annual_saving:,.0f}/year — escalated one band")
            band = target

    return band, notes


def assess(a: Asset, rate: float = 0.22, salvage_decay: float = 0.08,
           benchmark_unavailability: float = 0.02,
           materiality: float = 0.15) -> Assessment:
    """Score one asset end to end."""
    scores = score_all(a)
    weights = weights_for(a.asset_class)

    measured = {k: v for k, v in scores.items() if v is not None}
    total_weight = sum(weights.values())
    covered_weight = sum(weights[k] for k in measured)

    result = Assessment(asset=a, scores=scores, weights=weights)
    result.missing = sorted(k for k, v in scores.items() if v is None and weights.get(k))
    result.confidence = 100.0 * covered_weight / total_weight if total_weight else 0.0

    # Redistribute the weight of unmeasured indicators across the measured ones
    # rather than scoring them zero, which would flatter a data-poor asset.
    if covered_weight > 0:
        result.fitness = sum(weights[k] * v for k, v in measured.items()) / covered_weight
    else:
        result.fitness = 0.0

    result.advisories = data_advisories(a)
    result.utilisation = utilisation(a)

    lib = library()
    result.unknown_class = not lib.is_known(a.asset_class)
    if result.unknown_class:
        result.advisories.insert(0, (
            f"equipment class '{a.asset_class}' is not in the machinery library, so "
            f"generic weights were used. Add it to data/profiles.json to score it properly."))

    # Duty matching is a separate finding, deliberately kept out of the fitness
    # score: a misallocated machine is not a worn machine, and folding the two
    # together would hide both.
    result.duty = assess_duty(a)
    if result.duty.is_mismatched:
        result.advisories.append(describe_duty(result.duty, lib))

    # Energy as working capital: what this asset burns per day above what the
    # work requires, split into a maintenance problem and an operations problem.
    result.energy = assess_energy(a)
    result.advisories.extend(energy_advisories(a, result.energy))

    # The same excess, read as carbon. Tied to the burn so the two cannot diverge.
    result.emissions = assess_emissions(a, result.energy)

    result.raw_band = band_for_score(result.fitness)
    result.economics = assess_economics(
        a, rate=rate, salvage_decay=salvage_decay,
        benchmark_unavailability=benchmark_unavailability, materiality=materiality)
    result.band, result.overrides = _apply_overrides(a, result.raw_band, result.economics)
    return result

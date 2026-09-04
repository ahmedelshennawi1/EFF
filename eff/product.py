"""Product carbon intensity, benchmarked against a REGIONAL optimum.

The machine modules answer "is this asset fit?". This answers a different
question the market is starting to ask: *what does one tonne of our product cost
in carbon, and how far is that from the best achievable in this region?*

Region matters, and that is the whole point. A farm in the New Valley lifts
irrigation water 65 m; a Delta farm lifts it 12 m. Judging both against one
national number would punish the desert farm for its geology and flatter the
Delta farm for its luck. So every climate-driven input has its ideal scaled by
the region before the gap is computed:

    ideal_here = ideal_delta x region_factor
    gap        = actual - ideal_here        (floored at zero)

Water is converted to carbon through the energy that lifts it — rho*g*H over
pump efficiency — which is why water-table depth is a regional input and not a
national constant.

Every reference figure in data/products.json is a planning estimate. Results
rank sites honestly against each other; they are NOT a certified product carbon
footprint, and the output says so.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

PRODUCTS_PATH = Path(__file__).resolve().parent.parent / "data" / "products.json"

_CFG: Optional[dict] = None


def config(path: Path = PRODUCTS_PATH) -> dict:
    global _CFG
    if _CFG is None:
        with open(path, encoding="utf-8") as fh:
            _CFG = json.load(fh)
    return _CFG


class ProductError(ValueError):
    """Unusable product, region, or input."""


@dataclass
class InputLine:
    key: str
    actual: float
    ideal_here: float
    unit_label: str = ""
    kg_actual: float = 0.0
    kg_ideal: float = 0.0
    region_factor: float = 1.0
    higher_is_better: bool = False
    src: str = "est"

    @property
    def sourced(self) -> bool:
        return self.src != "est"

    @property
    def gap_kg(self) -> float:
        """Avoidable carbon on this line. Never negative — beating the ideal is
        credited by a lower total, not by offsetting another line's waste."""
        return max(0.0, self.kg_actual - self.kg_ideal)

    @property
    def over_ideal(self) -> Optional[float]:
        if self.ideal_here <= 0:
            return None
        if self.higher_is_better:
            return (self.ideal_here - self.actual) / self.ideal_here
        return (self.actual - self.ideal_here) / self.ideal_here


@dataclass
class Footprint:
    product: str = ""
    label_en: str = ""
    label_ar: str = ""
    region: str = ""
    region_label: str = ""
    unit: str = "tonne"
    lines: List[InputLine] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    @property
    def kg_actual(self) -> float:
        return sum(l.kg_actual for l in self.lines)

    @property
    def kg_ideal(self) -> float:
        return sum(l.kg_ideal for l in self.lines)

    @property
    def gap_kg(self) -> float:
        return sum(l.gap_kg for l in self.lines)

    @property
    def index(self) -> float:
        """0-100, where 100 means at or better than the regional optimum.

        Scaled so that running at twice the regional ideal scores 0 — a scale
        an operator can be ranked on without one bad line collapsing it.
        """
        if self.kg_ideal <= 0:
            return 0.0
        ratio = self.kg_actual / self.kg_ideal
        return max(0.0, min(100.0, 100.0 * (2.0 - ratio)))

    published_range: Optional[List[float]] = None
    range_src: str = ""
    scope_note: str = ""

    @property
    def worst(self) -> List[InputLine]:
        return sorted([l for l in self.lines if l.gap_kg > 0],
                      key=lambda l: -l.gap_kg)[:3]

    @property
    def sourced_share(self) -> float:
        """Share of the computed carbon that rests on a cited value rather than
        an eff estimate. The honest counterpart to data confidence on machines."""
        if self.kg_actual <= 0:
            return 0.0
        return sum(l.kg_actual for l in self.lines if l.sourced) / self.kg_actual

    @property
    def within_published_range(self) -> Optional[bool]:
        """Does the computed total land inside the published LCA literature range?
        A screening model that falls outside it is wrong until proven otherwise."""
        if not self.published_range or self.kg_actual <= 0:
            return None
        lo, hi = self.published_range
        return lo <= self.kg_actual <= hi


def _resolve_ef(cfg: dict, spec: dict, region: dict) -> Optional[float]:
    """kg CO2e per unit of this input, for this region."""
    if spec.get("kind") == "water":
        # Water carries no carbon itself — the pump does.
        kwh_per_m3 = cfg["pump_kwh_per_m3_per_m"] * region["water_lift_m"]
        return kwh_per_m3 * cfg["emission_factors"]["electricity_kwh"]
    ef = spec.get("ef")
    if ef:
        factor = cfg["emission_factors"].get(ef)
        if factor is None:
            raise ProductError(f"unknown emission factor '{ef}'")
        return factor
    return None


def assess(product: str,
           region: str,
           actuals: Dict[str, float],
           cfg: Optional[dict] = None) -> Footprint:
    """Compute a product's carbon intensity against its regional optimum."""
    c = cfg or config()

    if product not in c["products"]:
        raise ProductError(f"unknown product '{product}'. Known: {', '.join(c['products'])}")
    if region not in c["regions"]:
        raise ProductError(f"unknown region '{region}'. Known: {', '.join(c['regions'])}")

    p = c["products"][product]
    r = c["regions"][region]

    fp = Footprint(product=product, label_en=p.get("label_en", product),
                   label_ar=p.get("label_ar", ""), region=region,
                   region_label=r.get("label_en", region), unit=p.get("unit", "tonne"),
                   published_range=p.get("published_range_kg_per_t"),
                   range_src=p.get("range_src", ""),
                   scope_note=p.get("_scope_note", ""))

    unknown = set(actuals) - set(p["inputs"])
    if unknown:
        raise ProductError(f"inputs not defined for {product}: {', '.join(sorted(unknown))}")

    for key, spec in p["inputs"].items():
        if key not in actuals:
            fp.missing.append(key)
            continue

        climate = spec.get("climate")
        factor = r.get(f"{climate}_factor", 1.0) if climate else 1.0
        ideal_here = spec["ideal"] * factor

        # A nested product (feed inside broiler meat) carries its own footprint
        # per tonne. Use its REALISTIC footprint, not its ideal: a broiler farm
        # buys feed as it comes, and its own lever is the conversion ratio.
        # Improving the feed itself is a separate assessment of the mill.
        nested = spec.get("ef_product")
        if nested:
            ef = assess(nested, region, typical(nested, c), c).kg_actual
        else:
            ef = _resolve_ef(c, spec, r)

        if ef is None:
            fp.missing.append(key)
            continue

        line = InputLine(key=key, actual=actuals[key], ideal_here=ideal_here,
                         region_factor=factor, src=spec.get("src", "est"),
                         higher_is_better=bool(spec.get("higher_is_better")))
        line.kg_actual = actuals[key] * ef
        line.kg_ideal = ideal_here * ef
        fp.lines.append(line)

    return fp


def typical(product: str, cfg: Optional[dict] = None) -> Dict[str, float]:
    """The unoptimised reference profile — useful for demonstrating the gap."""
    c = cfg or config()
    if product not in c["products"]:
        raise ProductError(f"unknown product '{product}'")
    return {k: v["typical"] for k, v in c["products"][product]["inputs"].items()}


def render(fp: Footprint) -> str:
    w = 24
    out = ["", f"  {fp.label_en} — 1 {fp.unit} · {fp.region_label}",
           "  " + "-" * 80,
           f"  {'INPUT':<{w}} {'ACTUAL':>10} {'IDEAL HERE':>12} {'kg CO2e':>10} {'GAP kg':>9}  SRC"]
    for l in fp.lines:
        flag = "*" if l.region_factor != 1.0 else " "
        out.append(f"  {l.key:<{w}} {l.actual:>10,.1f} {l.ideal_here:>11,.1f}{flag} "
                   f"{l.kg_actual:>10,.1f} {l.gap_kg:>9,.1f}  {l.src}")
    out.append("  " + "-" * 74)
    out.append(f"  {'TOTAL':<{w}} {'':>10} {'':>12} {fp.kg_actual:>10,.1f} {fp.gap_kg:>9,.1f}")
    out.append("")
    out.append(f"  regional optimum: {fp.kg_ideal:,.1f} kg CO2e per {fp.unit}")
    out.append(f"  avoidable       : {fp.gap_kg:,.1f} kg ({fp.gap_kg / fp.kg_actual:.0%} of actual)"
               if fp.kg_actual else "  avoidable       : n/a")
    out.append(f"  intensity index : {fp.index:.0f} / 100   (100 = at or better than optimum)")
    if fp.worst:
        out.append("  biggest gaps    : " + ", ".join(f"{l.key} ({l.gap_kg:,.0f} kg)"
                                                       for l in fp.worst))
    if fp.missing:
        out.append(f"  not supplied    : {', '.join(fp.missing)}")

    out.append(f"  sourced         : {fp.sourced_share:.0%} of the carbon rests on cited "
               f"references; the rest on eff estimates")
    if fp.within_published_range is not None:
        lo, hi = fp.published_range
        verdict = "inside" if fp.within_published_range else "OUTSIDE"
        out.append(f"  literature check: {fp.kg_actual:,.0f} kg is {verdict} the published "
                   f"range {lo:,.0f}-{hi:,.0f} kg/{fp.unit}")
        if not fp.within_published_range and fp.scope_note:
            import textwrap
            for ln in textwrap.wrap("scope gap: " + fp.scope_note, 72):
                out.append(f"                    {ln}")
    out.append("")
    out.append("  * regionally adjusted ideal.  src 'est' = eff planning estimate, not yet sourced.")
    out.append("    Screening footprint for ranking sites — NOT a declarable product carbon")
    out.append("    footprint, which needs ISO 14067 work with verified primary data.")
    out.append("")
    return "\n".join(out)

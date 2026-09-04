"""Pricing criteria — every fee is computed, never looked up.

A price table cannot quote a client you have not met, and two similar clients
quoted from memory get different numbers. So the fee is derived the same way the
product derives a verdict: named factors, explicit arithmetic, an itemised
result that can be defended line by line.

    days  = setup + assets x per_asset + sites x per_site + analysis + reporting
    days x= data_readiness x urgency x diversity x language
    fee   = days x day_rate, then discounts, then rounding

A separate value check compares the fee against the fleet's annual energy spend.
That is a sanity band, not a pricing rule: it flags a quote that is too low to
respect the work or too high to survive a CFO, and never silently changes it.

All factors live in data/pricing.json — repricing the business is a data edit.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PRICING_PATH = Path(__file__).resolve().parent.parent / "data" / "pricing.json"

_CFG: Optional[dict] = None


def config(path: Path = PRICING_PATH) -> dict:
    global _CFG
    if _CFG is None:
        with open(path, encoding="utf-8") as fh:
            _CFG = json.load(fh)
    return _CFG


class PricingError(ValueError):
    """The pricing inputs or criteria file are unusable."""


@dataclass
class Quote:
    tier: str = "baseline"
    currency: str = "EGP"
    assets: int = 0
    sites: int = 1

    effort_lines: List[Tuple[str, float]] = field(default_factory=list)
    base_days: float = 0.0
    modifier_lines: List[Tuple[str, float]] = field(default_factory=list)
    total_days: float = 0.0

    gross_fee: float = 0.0
    discount_lines: List[Tuple[str, float]] = field(default_factory=list)
    fee: float = 0.0

    retainer_per_year: float = 0.0
    addon_lines: List[Tuple[str, float]] = field(default_factory=list)
    addons_total: float = 0.0

    value_note: str = ""
    value_ok: Optional[bool] = None

    @property
    def total_first_year(self) -> float:
        return self.fee + self.addons_total

    @property
    def effective_day_rate(self) -> float:
        return self.fee / self.total_days if self.total_days else 0.0


def _round_to(value: float, step: float) -> float:
    if step <= 0:
        return value
    return round(value / step) * step


def quote(assets: int,
          sites: int = 1,
          tier: str = "baseline",
          data_readiness: str = "good",
          urgency: str = "standard",
          distinct_classes: int = 0,
          extra_language: bool = False,
          founding_client: bool = False,
          retainer_committed: bool = False,
          annual_energy_spend: Optional[float] = None,
          addons: Optional[Dict[str, int]] = None,
          cfg: Optional[dict] = None) -> Quote:
    """Compute an itemised fee from the criteria."""
    c = cfg or config()
    if assets < 0 or sites < 1:
        raise PricingError("assets must be >= 0 and sites >= 1")
    if tier not in c["tiers"]:
        raise PricingError(f"unknown tier '{tier}'. Known: {', '.join(c['tiers'])}")

    tier_cfg = c["tiers"][tier]
    cap = tier_cfg.get("max_assets")
    if cap and assets > cap:
        raise PricingError(
            f"tier '{tier}' covers up to {cap} assets; {assets} requested — quote 'baseline'")

    q = Quote(tier=tier, currency=c.get("currency", "EGP"), assets=assets, sites=sites)
    e = c["effort"]

    # --- effort, bottom up ------------------------------------------------
    q.effort_lines = [
        ("setup & configuration", e["setup_days"]),
        (f"per-asset review ({assets} x {e['per_asset_days']})", assets * e["per_asset_days"]),
        (f"site coordination ({sites} x {e['per_site_days']})", sites * e["per_site_days"]),
        ("analysis", e["analysis_days"]),
        ("reporting", e["reporting_days"]),
    ]
    if tier_cfg.get("includes_presentation"):
        q.effort_lines.append(("executive presentation", e["presentation_days"]))
    q.base_days = sum(d for _, d in q.effort_lines)

    # --- modifiers --------------------------------------------------------
    m = c["modifiers"]
    readiness = m["data_readiness"].get(data_readiness)
    if readiness is None:
        raise PricingError(f"unknown data_readiness '{data_readiness}'")
    urgency_f = m["urgency"].get(urgency)
    if urgency_f is None:
        raise PricingError(f"unknown urgency '{urgency}'")

    if readiness != 1.0:
        q.modifier_lines.append((f"data readiness: {data_readiness}", readiness))
    if urgency_f != 1.0:
        q.modifier_lines.append((f"urgency: {urgency}", urgency_f))
    if distinct_classes > m["diversity"]["threshold_classes"]:
        q.modifier_lines.append(
            (f"equipment diversity ({distinct_classes} classes)", m["diversity"]["factor"]))
    if extra_language:
        q.modifier_lines.append(("additional language", m["multi_language"]["factor"]))

    q.total_days = q.base_days
    for _, f in q.modifier_lines:
        q.total_days *= f

    # --- money ------------------------------------------------------------
    q.gross_fee = q.total_days * c["day_rate"]

    d = c["discounts"]
    running = q.gross_fee
    if founding_client:
        amount = running * d["founding_client"]
        q.discount_lines.append(("Founding Client Programme", -amount))
        running -= amount
    else:
        if sites >= 3:
            amount = running * d["sites_3plus"]
            q.discount_lines.append((f"multi-site ({sites} sites)", -amount))
            running -= amount
        if retainer_committed:
            amount = running * d["retainer_committed"]
            q.discount_lines.append(("monitoring retainer committed", -amount))
            running -= amount

    q.fee = _round_to(running, c.get("rounding", 500))

    # --- retainer ---------------------------------------------------------
    r = c["retainer"]
    # Priced off the UNDISCOUNTED baseline, so a free pilot does not make the
    # retainer free too.
    q.retainer_per_year = max(
        _round_to(q.gross_fee * r["share_of_baseline_per_year"], c.get("rounding", 500)),
        r["minimum_per_year"])

    # --- add-ons ----------------------------------------------------------
    for name, qty in (addons or {}).items():
        unit = c["addons"].get(name)
        if unit is None:
            raise PricingError(f"unknown add-on '{name}'. Known: {', '.join(c['addons'])}")
        line = unit * qty
        q.addon_lines.append((f"{name.replace('_', ' ')} x{qty}", line))
        q.addons_total += line

    # --- value sanity band ------------------------------------------------
    if annual_energy_spend and annual_energy_spend > 0 and q.fee > 0:
        v = c["value_check"]
        share = q.fee / annual_energy_spend
        lo, hi = v["min_share_of_energy_spend"], v["max_share_of_energy_spend"]
        q.value_ok = lo <= share <= hi
        if share < lo:
            q.value_note = (f"fee is {share:.2%} of annual energy spend — below the {lo:.0%} "
                            f"floor; the engagement is underpriced for the value at stake")
        elif share > hi:
            q.value_note = (f"fee is {share:.2%} of annual energy spend — above the {hi:.0%} "
                            f"ceiling; expect resistance, consider narrowing scope")
        else:
            q.value_note = (f"fee is {share:.2%} of annual energy spend — inside the "
                            f"{lo:.0%}-{hi:.0%} band")

    return q


def render(q: Quote) -> str:
    """Itemised quote, defensible line by line."""
    cur = q.currency
    w = 46
    out = [""]
    out.append(f"  QUOTE — {q.tier.replace('_', ' ')} · {q.assets} assets · {q.sites} site(s)")
    out.append("  " + "-" * (w + 20))

    out.append("  Effort")
    for name, days in q.effort_lines:
        out.append(f"    {name:<{w}} {days:>6.2f} d")
    out.append(f"    {'base effort':<{w}} {q.base_days:>6.2f} d")

    if q.modifier_lines:
        out.append("\n  Modifiers")
        for name, f in q.modifier_lines:
            out.append(f"    {name:<{w}} x{f:>5.2f}")
    out.append(f"    {'total effort':<{w}} {q.total_days:>6.2f} d")

    out.append("\n  Fee")
    out.append(f"    {'effort x day rate':<{w}} {cur} {q.gross_fee:>10,.0f}")
    for name, amount in q.discount_lines:
        out.append(f"    {name:<{w}} {cur} {amount:>10,.0f}")
    out.append(f"    {'FEE':<{w}} {cur} {q.fee:>10,.0f}")

    if q.addon_lines:
        out.append("\n  Add-ons")
        for name, amount in q.addon_lines:
            out.append(f"    {name:<{w}} {cur} {amount:>10,.0f}")
        out.append(f"    {'first-year total':<{w}} {cur} {q.total_first_year:>10,.0f}")

    out.append(f"\n    {'monitoring retainer, per year':<{w}} {cur} {q.retainer_per_year:>10,.0f}")

    if q.fee > 0:
        out.append(f"\n    effective day rate: {cur} {q.effective_day_rate:,.0f}")
    if q.value_note:
        flag = "" if q.value_ok else "  (!)"
        out.append(f"    value check: {q.value_note}{flag}")
    out.append("")
    return "\n".join(out)

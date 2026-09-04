"""Console and HTML reporting."""

import html
from datetime import date
from typing import List

from .profiles import INDICATORS
from .verdict import Assessment, CONFIDENCE_DECISION_GRADE, CONFIDENCE_FLOOR

INSUFFICIENT = "INSUFFICIENT_DATA"

BAND_LABEL = {
    "KEEP": "Keep",
    "MONITOR": "Monitor",
    "PLAN_REPLACEMENT": "Plan replacement",
    "RETIRE_NOW": "Retire now",
    INSUFFICIENT: "Insufficient data",
}

BAND_COLOUR = {
    "KEEP": "#14958A",
    "MONITOR": "#D9A441",
    "PLAN_REPLACEMENT": "#C9705F",
    "RETIRE_NOW": "#8C2F22",
    INSUFFICIENT: "#5F6C70",
}

BAND_ORDER = ["RETIRE_NOW", "PLAN_REPLACEMENT", INSUFFICIENT, "MONITOR", "KEEP"]


def display_band(r: Assessment) -> str:
    """What the reader is shown.

    A verdict built on a quarter of the evidence must not be presented as
    "Keep" — the reader will act on the word, not on the confidence figure
    printed beside it. Below the confidence floor the honest output is that
    the question cannot be answered yet.
    """
    return r.band if r.decision_grade else INSUFFICIENT


def sort_key(r: Assessment):
    return (BAND_ORDER.index(display_band(r)), -r.fitness)


def _money(v, currency="EGP"):
    if v is None:
        return "—"
    return f"{currency} {v:,.0f}"


def _wrap(text, width, indent):
    import textwrap
    return ("\n" + indent).join(textwrap.wrap(text, width))


# --------------------------------------------------------------------------
# Console
# --------------------------------------------------------------------------

def print_summary(results: List[Assessment]) -> None:
    results = sorted(results, key=sort_key)

    width = max([len(r.asset.label) for r in results] + [10])
    print()
    print(f"{'ASSET'.ljust(width)}  {'SCORE':>5}  {'VERDICT':<17} {'CONF':>5}  "
          f"{'BURN/DAY':>9}  DRIVER")
    print("-" * (width + 63))

    for r in results:
        driver = r.drivers[0][0] if r.drivers else "no data"
        flag = "" if r.decision_grade else "  (!)"
        e = r.energy
        if e and e.available and e.total_per_day >= 1:
            burn = f"{e.total_per_day:8,.0f}" + ("~" if e.indicative else " ")
        else:
            burn = f"{'—':>9}"
        print(f"{r.asset.label.ljust(width)}  {r.fitness:5.1f}  "
              f"{BAND_LABEL[display_band(r)]:<17} {r.confidence:4.0f}%  {burn}  {driver}{flag}")

    print()
    counts = {b: sum(1 for r in results if display_band(r) == b) for b in BAND_ORDER}
    print("  " + " · ".join(f"{BAND_LABEL[b]}: {counts[b]}"
                            for b in BAND_ORDER if counts[b] or b != INSUFFICIENT))

    burns = [r.energy for r in results if r.energy and r.energy.available]
    total_day = sum(e.total_per_day for e in burns)
    if total_day >= 1:
        cur = results[0].asset.currency or "EGP"
        wear = sum(e.wear_per_day for e in burns)
        alloc = sum(e.allocation_per_day for e in burns)
        approx = " (~ = benchmark-based)" if any(e.indicative for e in burns) else ""
        print(f"\n  ENERGY BURN: {cur} {total_day:,.0f}/day above requirement "
              f"= {cur} {total_day * 365:,.0f}/year{approx}")
        print(f"    degradation (maintenance): {cur} {wear:,.0f}/day · "
              f"misallocation (operations): {cur} {alloc:,.0f}/day")

        co2 = sum(r.emissions.tonnes_per_year for r in results
                  if r.emissions and r.emissions.available)
        if co2 >= 0.1:
            trees = sum(r.emissions.trees_equivalent for r in results
                        if r.emissions and r.emissions.available)
            print(f"    carbon in that waste: {co2:,.1f} t CO2e/year "
                  f"(~{trees:,.0f} trees' annual absorption)")

    low = [r for r in results if not r.decision_grade]
    if low:
        print(f"\n  (!) {len(low)} asset(s) below {CONFIDENCE_FLOOR:.0f}% data confidence — "
              "not decision-grade until the missing readings are collected.")
    print()


def print_detail(r: Assessment) -> None:
    a = r.asset
    cur = a.currency or "EGP"
    print()
    print("=" * 68)
    print(f"  {a.label}")
    print(f"  {a.manufacturer} {a.model} · {a.asset_class.replace('_', ' ')} · {a.site}".rstrip(" ·"))
    print("=" * 68)
    print(f"  Fitness score   {r.fitness:.1f} / 100")
    if r.decision_grade:
        print(f"  Verdict         {BAND_LABEL[r.band]}"
              + (f"   (scored {BAND_LABEL[r.raw_band]}, raised by override)"
                 if r.band != r.raw_band else ""))
    else:
        print(f"  Verdict         {BAND_LABEL[INSUFFICIENT]}"
              f"   (indicative only: {BAND_LABEL[r.band]})")
    print(f"  Data confidence {r.confidence:.0f}%"
          + ("" if r.confidence >= CONFIDENCE_DECISION_GRADE else
             "  — directional only" if r.decision_grade else "  — NOT decision-grade"))

    print("\n  Indicators")
    for name in INDICATORS:
        s = r.scores.get(name)
        w = r.weights.get(name, 0)
        if s is None:
            print(f"    {name:<14} {'not measured':>12}   (weight {w:.0f})")
        else:
            bar = "#" * int(round(s / 5)) + "." * (20 - int(round(s / 5)))
            print(f"    {name:<14} {s:8.1f}   {bar}  (weight {w:.0f})")

    if r.missing:
        print(f"\n  Not measured: {', '.join(r.missing)}")

    if r.utilisation is not None:
        print(f"\n  Utilisation     {r.utilisation:.0%} of the calendar year"
              f"  ({a.annual_run_hours:,.0f} h)")
        if a.load_factor is not None:
            print(f"  Load factor     {a.load_factor:.0%} of rated output")

    e = r.energy
    if e and e.available and e.total_per_day >= 1:
        tag = "  (benchmark-based, indicative)" if e.indicative else ""
        print(f"\n  Energy burn     {cur} {e.total_per_day:,.0f}/day "
              f"= {cur} {e.total_per_year:,.0f}/year{tag}")
        print(f"    degradation vs healthy machine     {cur} {e.wear_per_day:>9,.0f}/day")
        print(f"    wrong size for the duty            {cur} {e.allocation_per_day:>9,.0f}/day")

    if r.overrides:
        print("\n  Overrides")
        for note in r.overrides:
            print(f"    - {note}")

    if r.advisories:
        print("\n  Advisories")
        for note in r.advisories:
            print(f"    - {_wrap(note, 62, '      ')}")

    e = r.economics
    if e and e.available:
        print("\n  Economics  (discount rate "
              f"{e.rate * 100:.0f}%)")
        print(f"    Equivalent annual cost, new unit   {_money(e.eac_new, cur):>18}")
        print(f"    Cost of keeping one more year      {_money(e.marginal_keep, cur):>18}")
        print(f"      maintenance                      {_money(e.maintenance_term, cur):>18}")
        print(f"      excess energy vs new             {_money(e.energy_penalty, cur):>18}")
        print(f"      downtime                         {_money(e.downtime_term, cur):>18}")
        print(f"      salvage value lost               {_money(e.salvage_decay_term, cur):>18}")
        print(f"      capital tied up                  {_money(e.capital_tied_term, cur):>18}")
        verdict = ("replacing saves" if e.replace_favoured else "keeping saves")
        print(f"    -> {verdict} {_money(abs(e.annual_saving), cur)} per year")
    elif e:
        print(f"\n  Economics       not computed — {e.reason}")
    print()


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------

_CSS = """
:root{--teal-d:#0E6E66;--teal:#14958A;--charcoal:#23292C;--mist:#E8EEEC;
--paper:#FAFBFA;--brass:#B8934A;--line:#D5DEDB;--muted:#5F6C70;}
*{box-sizing:border-box;}
body{margin:0;background:var(--paper);color:var(--charcoal);
font-family:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;line-height:1.55;}
.wrap{max-width:1080px;margin:0 auto;padding:40px 28px 72px;}
header{border-bottom:3px solid var(--teal-d);padding-bottom:20px;margin-bottom:32px;}
h1{margin:0 0 4px;font-size:26px;letter-spacing:-.01em;color:var(--teal-d);}
.sub{color:var(--muted);font-size:14px;}
h2{font-size:17px;margin:40px 0 14px;color:var(--teal-d);
border-bottom:1px solid var(--line);padding-bottom:6px;}
.cards{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0 8px;}
.card{flex:1 1 150px;background:#fff;border:1px solid var(--line);
border-radius:6px;padding:14px 16px;}
.card .n{font-size:28px;font-weight:600;line-height:1.1;}
.card .l{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;}
.tablewrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:14px;background:#fff;}
th{background:var(--mist);text-align:left;padding:9px 11px;font-weight:600;
font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--teal-d);
white-space:nowrap;}
td{padding:9px 11px;border-top:1px solid var(--line);vertical-align:top;}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
.pill{display:inline-block;padding:2px 9px;border-radius:99px;color:#fff;
font-size:12px;font-weight:600;white-space:nowrap;}
.bar{height:7px;background:var(--mist);border-radius:99px;overflow:hidden;min-width:80px;}
.bar i{display:block;height:100%;}
.asset{background:#fff;border:1px solid var(--line);border-radius:6px;
padding:18px 20px;margin-bottom:16px;}
.asset h3{margin:0 0 2px;font-size:16px;}
.asset .meta{color:var(--muted);font-size:13px;margin-bottom:14px;}
.ind{display:grid;grid-template-columns:130px 46px 1fr 62px;gap:8px;
align-items:center;font-size:13px;padding:3px 0;}
.ind .w{color:var(--muted);font-size:11px;text-align:right;}
.ind .na{color:var(--muted);font-style:italic;font-size:12px;}
.flag{background:#FDF3E3;border-left:3px solid var(--brass);padding:9px 13px;
margin:12px 0;font-size:13px;border-radius:0 4px 4px 0;}
.flag.adv{background:var(--mist);border-left-color:var(--teal);}
.ctx{color:var(--muted);font-size:12px;margin:-8px 0 12px;}
.econ{margin-top:14px;font-size:13px;}
.econ td{border:0;padding:2px 0;}
.econ td.num{padding-left:20px;}
.econ .tot{border-top:1px solid var(--line);font-weight:600;}
footer{margin-top:56px;padding-top:16px;border-top:1px solid var(--line);
color:var(--muted);font-size:12px;}
@media print{body{background:#fff;}.asset{break-inside:avoid;}}
"""


def _bar(score, colour):
    return (f'<div class="bar"><i style="width:{max(2, min(100, score)):.0f}%;'
            f'background:{colour}"></i></div>')


def _asset_block(r: Assessment) -> str:
    a = r.asset
    cur = a.currency or "EGP"
    shown = display_band(r)
    colour = BAND_COLOUR[shown]
    e = r.economics

    meta = " · ".join(x for x in [
        f"{a.manufacturer} {a.model}".strip(),
        a.asset_class.replace("_", " "),
        a.site,
    ] if x)

    rows = []
    for name in INDICATORS:
        s = r.scores.get(name)
        w = r.weights.get(name, 0)
        if s is None:
            rows.append(f'<div class="ind"><span>{name}</span>'
                        f'<span class="na">n/m</span><span class="na">not measured</span>'
                        f'<span class="w">wt {w:.0f}</span></div>')
        else:
            c = "#14958A" if s < 25 else "#D9A441" if s < 45 else "#C9705F" if s < 65 else "#8C2F22"
            rows.append(f'<div class="ind"><span>{name}</span>'
                        f'<span class="num">{s:.0f}</span>{_bar(s, c)}'
                        f'<span class="w">wt {w:.0f}</span></div>')

    flags = ""
    if not r.decision_grade:
        flags += (f'<div class="flag"><b>Not decision-grade.</b> Only {r.confidence:.0f}% of the '
                  f'scoring weight is backed by measurements, so no verdict is issued. '
                  f'On the evidence available this asset would score '
                  f'{r.fitness:.0f} ({BAND_LABEL[r.band]}), but that is indicative only. '
                  f'Collect: {html.escape(", ".join(r.missing))}.</div>')
    for note in r.overrides:
        flags += f'<div class="flag"><b>Override —</b> {html.escape(note)}.</div>'
    for note in r.advisories:
        flags += f'<div class="flag adv"><b>Advisory —</b> {html.escape(note)}</div>'

    context = []
    if r.utilisation is not None:
        context.append(f"utilisation {r.utilisation:.0%} of the year "
                       f"({a.annual_run_hours:,.0f} h)")
    if a.load_factor is not None:
        context.append(f"load factor {a.load_factor:.0%} of rated")
    context_html = (f'<div class="ctx">{" · ".join(context)}</div>' if context else "")

    econ_html = ""
    if e and e.available:
        saving = e.annual_saving
        line = (f'Replacing saves <b>{_money(abs(saving), cur)}</b> per year'
                if e.replace_favoured
                else f'Keeping saves <b>{_money(abs(saving), cur)}</b> per year')
        econ_html = f"""
        <table class="econ">
          <tr><td>Equivalent annual cost of a new unit</td>
              <td class="num">{_money(e.eac_new, cur)}</td></tr>
          <tr><td>Maintenance, next year</td>
              <td class="num">{_money(e.maintenance_term, cur)}</td></tr>
          <tr><td>Excess energy vs. a new unit</td>
              <td class="num">{_money(e.energy_penalty, cur)}</td></tr>
          <tr><td>Downtime cost</td>
              <td class="num">{_money(e.downtime_term, cur)}</td></tr>
          <tr><td>Salvage value lost by keeping</td>
              <td class="num">{_money(e.salvage_decay_term, cur)}</td></tr>
          <tr><td>Capital tied up in the asset</td>
              <td class="num">{_money(e.capital_tied_term, cur)}</td></tr>
          <tr class="tot"><td>Cost of keeping one more year</td>
              <td class="num">{_money(e.marginal_keep, cur)}</td></tr>
          <tr><td colspan="2" style="padding-top:8px">{line}</td></tr>
        </table>"""

    return f"""
    <div class="asset">
      <h3>{html.escape(a.label)}
        <span class="pill" style="background:{colour};float:right">
          {BAND_LABEL[shown]}{"" if shown == INSUFFICIENT else f" · {r.fitness:.0f}"}</span></h3>
      <div class="meta">{html.escape(meta)} — data confidence {r.confidence:.0f}%</div>
      {context_html}
      {"".join(rows)}
      {flags}
      {econ_html}
    </div>"""


def render_html(results: List[Assessment], cfg: dict) -> str:
    results = sorted(results, key=sort_key)
    counts = {b: sum(1 for r in results if display_band(r) == b) for b in BAND_ORDER}
    low = sum(1 for r in results if not r.decision_grade)
    org = cfg.get("organisation") or ""

    burns = [r.energy for r in results if r.energy and r.energy.available]
    burn_day = sum(e.total_per_day for e in burns)
    burn_wear = sum(e.wear_per_day for e in burns)
    burn_alloc = sum(e.allocation_per_day for e in burns)
    cur0 = results[0].asset.currency if results else "EGP"

    cards = "".join(
        f'<div class="card"><div class="n" style="color:{BAND_COLOUR[b]}">{counts[b]}</div>'
        f'<div class="l">{BAND_LABEL[b]}</div></div>'
        for b in BAND_ORDER if counts[b] or b != INSUFFICIENT
    )
    cards += (f'<div class="card"><div class="n">{len(results)}</div>'
              f'<div class="l">Assets assessed</div></div>')
    if burn_day >= 1:
        cards += (f'<div class="card"><div class="n" style="color:var(--brass)">'
                  f'{burn_day:,.0f}</div>'
                  f'<div class="l">{html.escape(cur0)} burned per day above requirement</div></div>')

    def _burn_cell(r):
        e = r.energy
        if not (e and e.available and e.total_per_day >= 1):
            return "—"
        return f"{e.total_per_day:,.0f}" + ("&nbsp;~" if e.indicative else "")

    rows = "".join(
        f'<tr><td>{html.escape(r.asset.label)}</td>'
        f'<td>{html.escape(r.asset.asset_class.replace("_", " "))}</td>'
        f'<td>{html.escape(r.asset.site)}</td>'
        f'<td class="num">{r.fitness:.1f}</td>'
        f'<td><span class="pill" style="background:{BAND_COLOUR[display_band(r)]}">'
        f'{BAND_LABEL[display_band(r)]}</span></td>'
        f'<td class="num">{r.confidence:.0f}%</td>'
        f'<td class="num">{_burn_cell(r)}</td>'
        f'<td>{html.escape(r.drivers[0][0]) if r.drivers else "—"}</td></tr>'
        for r in results
    )

    burn_note = ""
    if burn_day >= 1:
        approx = (" Figures marked ~ are benchmark-based and indicative."
                  if any(e.indicative for e in burns) else "")
        burn_note = (f'<div class="flag"><b>The fleet burns {html.escape(cur0)} '
                     f'{burn_day:,.0f} per day above what its work requires</b> — '
                     f'{html.escape(cur0)} {burn_wear:,.0f}/day from degradation '
                     f'(maintenance) and {html.escape(cur0)} {burn_alloc:,.0f}/day from '
                     f'machines mismatched to their duty (operations). '
                     f'That is {html.escape(cur0)} {burn_day * 365:,.0f} per year, paid '
                     f'whether or not anything breaks.{approx}</div>')

    warn = ""
    if low:
        warn = (f'<div class="flag"><b>{low} of {len(results)} assets are below '
                f'{CONFIDENCE_FLOOR:.0f}% data confidence and carry no verdict.</b> '
                f'The first deliverable for those assets is a measurement plan, '
                f'not a replacement decision.</div>')

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Equipment Fitness Assessment{" — " + html.escape(org) if org else ""}</title>
<style>{_CSS}</style></head><body><div class="wrap">
<header>
  <h1>Equipment Fitness Assessment</h1>
  <div class="sub">{html.escape(org) + " · " if org else ""}{date.today():%d %B %Y}
   · EFF v1.0 · discount rate {cfg.get('discount_rate', 0) * 100:.0f}%
   {" · assessor " + html.escape(cfg["assessor"]) if cfg.get("assessor") else ""}</div>
</header>

<div class="cards">{cards}</div>
{burn_note}
{warn}

<h2>Fleet summary</h2>
<div class="tablewrap"><table>
<thead><tr><th>Asset</th><th>Class</th><th>Site</th><th>Score</th>
<th>Verdict</th><th>Confidence</th><th>Burn/day</th><th>Main driver</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Asset detail</h2>
{"".join(_asset_block(r) for r in results)}

<footer>
Scores run 0 (as-new) to 100 (fully consumed) across eight weighted indicators.
Indicators that were not measured are excluded and their weight redistributed —
the resulting coverage is reported as data confidence. Verdicts below 60%
confidence are not decision-grade. Criteria, thresholds and the economic test
are documented in <b>docs/CRITERIA.md</b>.
</footer>
</div></body></html>"""

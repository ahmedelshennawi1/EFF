# EFF — Equipment Fitness Framework

A scored, auditable answer to one question:

> **Should this machine stay in service, be watched, be budgeted for replacement, or be retired now?**

Most operations answer this from age and gut feel. EFF scores eight weighted indicators —
life consumption, reliability, efficiency degradation, capacity derating, maintenance cost
burden, physical condition, supportability and safety — applies hard overrides, runs a
replacement-timing economic test, and reports how much of the verdict is actually backed by
measurements.

Pure Python, standard library only. No dependencies to install.

## Quick start

```bash
python cli.py
```

```
ASSET                                      SCORE  VERDICT            CONF  DRIVER
---------------------------------------------------------------------------------
CMP-02 · Screw compressor - packaging       59.4  Retire now         100%  EFFICIENCY
GEN-02 · Prime genset - hatchery            62.5  Plan replacement   100%  EFFICIENCY
MIL-07 · Hammer mill - feed line A          61.2  Plan replacement    85%  RELIABILITY
VEH-12 · Forklift - dispatch yard           53.5  Plan replacement   100%  MAINT_COST
PMP-04 · Irrigation pump - farm 3           47.6  Plan replacement   100%  EFFICIENCY
GEN-03 · Standby genset - cold store        15.4  Insufficient data   15%  AGE  (!)
CHL-01 · Chiller - process cooling          26.2  Monitor            100%  EFFICIENCY
GEN-01 · Standby genset - main feed plant    6.0  Keep               100%  EFFICIENCY
```

Other commands:

```bash
python cli.py --detail
```

```bash
python cli.py --asset GEN-02
```

```bash
python cli.py --html out/assessment.html
```

```bash
python cli.py --data data/client-fleet.csv --rate 0.25
```

```bash
python tests/test_eff.py
```

## What it produces

Per asset: a **fitness score** (0 = as-new, 100 = fully consumed), a **verdict band**, the
**indicators driving it**, any **overrides** that fired, a **data-confidence** percentage, and
an **economic test** stating in currency whether replacing pays this year.

```
  GEN-02 · Prime genset - hatchery
  Cummins C250 D5 · diesel generator · Belqas Hatchery
====================================================================
  Fitness score   62.5 / 100
  Verdict         Plan replacement
  Data confidence 100%

  Indicators
    AGE                60.0   ############........  (weight 10)
    RELIABILITY        50.9   ##########..........  (weight 20)
    EFFICIENCY         77.3   ###############.....  (weight 25)
    ...

  Economics  (discount rate 22%)
    Equivalent annual cost, new unit          EGP 470,824
    Cost of keeping one more year           EGP 1,514,312
    -> replacing saves EGP 1,043,488 per year
```

The HTML report carries the AHMED ELSHENNAWI palette and prints cleanly to PDF for client
delivery.

## Output is measured three ways, and they are not interchangeable

| Field | What it is | Feeds |
|---|---|---|
| `rated_output` / `actual_output` | a **rate** — 400 kW, 12 t/h | CAPACITY derating |
| `load_factor` | fraction of rated output actually drawn | EFFICIENCY baseline correction |
| `annual_output_total` | a **volume** — 780,000 kWh, 911,200 m³ | the economics |

Output is also the denominator of every specific-consumption figure, which is what makes
EFFICIENCY work at all.

**Load factor changes the answer.** An engine burns more fuel per kWh when lightly loaded, so
the baseline is corrected to the load actually measured before degradation is computed. In the
sample fleet a 60 kW genset reads 0.361 L/kWh against a 0.268 nameplate baseline — 34.7%
degradation, a near-worst score, an apparent scrap candidate. It runs at 22% load, so its
corrected baseline is 0.376 and real degradation is **−4%**. The machine is fine; the sizing is
wrong. It is flagged as a dispatch fault, because replacing it would buy a new machine that
wet-stacks exactly the same way.

**`annual_output_total` is validated, because nothing else would catch it.** It affects no
indicator score, so a wrong value has no visible symptom — but it multiplies straight into the
energy penalty, usually the largest term in the replacement economics. A tenfold unit slip moves
the money while every score on the page stays identical. It is cross-checked against the rate
and run-hours the asset itself reports, and a disagreement past 15% raises an advisory naming
the likely slip and its direction. Correct rows stay silent — there is a test asserting the
whole sample fleet triggers nothing, because an advisory that fires on good data becomes noise
people learn to ignore.

**Utilisation** (`annual_run_hours / 8760`) is reported as context, not scored. A machine
running 3% of the year is a different capital question from one running 80% at the same score.

## Three design decisions worth knowing

**Missing data is never scored as zero.** An unmeasured indicator is excluded and its weight is
redistributed across the ones that were measured. Zero-filling would flatter exactly the assets
nobody has looked at. Below 60% confidence no verdict is issued at all — the report says
*Insufficient data* rather than *Keep*, because a reader acts on the word, not on the
percentage printed next to it.

**The economics are differential.** Costs incurred either way cancel from both sides. Only the
*excess* fuel the old unit burns above a new one is charged to keeping, and only the downtime
above what a well-run new unit would itself have suffered. Charging full downtime to the old
asset assumes replacements never fail — that one assumption alone is enough to make an entire
fleet look due for replacement.

**Economics can recommend budgeting, never retirement.** A failing economic test escalates the
verdict by one band and stops at `PLAN_REPLACEMENT`. Reaching `RETIRE_NOW` requires condition,
safety or score evidence. A spreadsheet result should not take a physically sound machine out
of service.

## Layout

```
EFF/
├── cli.py                      command line
├── config.json                 discount rate, materiality, benchmarks
├── data/assets.csv             the fleet — one row per asset
├── docs/
│   ├── CRITERIA.md             the framework: indicators, curves, weights, overrides
│   └── DATA-COLLECTION.md      what to measure, with what, how often
├── eff/
│   ├── models.py               Asset record and CSV parsing
│   ├── profiles.py             per-class weights and default design lives
│   ├── scoring.py              the eight indicators
│   ├── economics.py            EAC and replacement timing
│   ├── verdict.py              roll-up, banding, overrides, confidence
│   └── report.py               console and HTML output
└── tests/test_eff.py           25 tests, no framework needed
```

## Assessing a real fleet

1. Copy `data/assets.csv`, keep the header row, replace the sample rows.
2. Fill what you have. **Leave unknowns blank** — blanks are handled honestly, guesses are not.
3. Set `discount_rate` in `config.json` to the organisation's real cost of capital. It is
   printed on every report, so it has to be a deliberate choice.
4. Run it. Expect a first pass to be mostly *Insufficient data* — that output is the
   measurement plan, and it is usually the most valuable thing in the first engagement.

See `docs/DATA-COLLECTION.md` for the field-by-field guide and a suggested rollout.

## Status

Version 1.0. Thresholds are engineering rules of thumb, not yet calibrated against a fleet
dataset with known outcomes — see `docs/CRITERIA.md` §9 for the current limitations, including
redundancy handling and standby assets, which the model does not yet address.

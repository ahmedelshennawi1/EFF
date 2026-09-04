# Equipment Fitness Framework (EFF) — Assessment Criteria

**Version 1.0** · Owner: Ahmed Elshennawi · Status: working draft

---

## 1. Purpose

Answer one question with evidence instead of opinion:

> **Should this machine stay in service, be watched, be budgeted for replacement, or be retired now?**

Most operations answer this from age and gut feel. Age is the weakest single predictor of
whether a machine should go. A 14-year-old generator running at baseline fuel consumption
with zero unplanned stops should stay. A 5-year-old one burning 18% over baseline with a
6-week spare-parts lead time should not.

EFF replaces that judgement with a scored, auditable, repeatable assessment.

## 2. Decision output

Every asset receives:

| Output | Meaning |
|---|---|
| **Fitness score** (0–100) | 0 = as-new, 100 = fully consumed. Higher is worse. |
| **Verdict band** | `KEEP` · `MONITOR` · `PLAN_REPLACEMENT` · `RETIRE_NOW` |
| **Economic test** | Marginal cost of one more year vs. equivalent annual cost of a new unit |
| **Data confidence** | % of the scoring weight backed by real measurements |
| **Drivers** | The 2–3 indicators pushing the score, so the verdict is arguable |

Band thresholds:

| Score | Band | Action |
|---|---|---|
| 0–24 | `KEEP` | Normal PM cycle. Re-assess annually. |
| 25–44 | `MONITOR` | Re-assess every 6 months. Start trending the weak indicator. |
| 45–64 | `PLAN_REPLACEMENT` | Enter capital budget for 12–24 months. Begin sourcing. |
| 65–100 | `RETIRE_NOW` | Remove from critical duty this cycle. Standby duty only if safe. |

## 3. The eight indicators

Each indicator is scored 0–100 on a piecewise-linear curve, then weighted by equipment class.
Missing data does not score zero — it is **excluded**, its weight is redistributed, and the
loss is reported as reduced data confidence.

### 3.1 Age / life consumption — `AGE`

The only purely passive indicator. Present so that assets with no other data still get a
floor estimate, not because age decides anything on its own.

```
life_ratio = max( run_hours / design_life_hours ,
                  (current_year - commissioned_year) / design_life_years )
```

Run-hours dominate when available. A genset at 40,000 hours on a 30,000-hour major-overhaul
interval is past life regardless of its calendar age.

| life_ratio | 0.0 | 0.5 | 0.8 | 1.0 | 1.3 | 2.0 |
|---|---|---|---|---|---|---|
| score | 0 | 10 | 30 | 55 | 80 | 100 |

**How to measure:** hour meter reading, commissioning certificate, OEM manual for design life.

### 3.2 Reliability — `RELIABILITY`

Two components, combined 55/45.

```
unavailability   = annual_downtime_hours / (annual_run_hours + annual_downtime_hours)
failure_density  = unplanned_failures_12m / (annual_run_hours / 1000)
```

| unavailability | 0 | 0.03 | 0.05 | 0.10 | 0.20 | 0.30 |
|---|---|---|---|---|---|---|
| score | 0 | 15 | 30 | 60 | 90 | 100 |

| failures / 1000 h | 0 | 0.5 | 1.0 | 2.0 | 4.0 | 6.0 |
|---|---|---|---|---|---|---|
| score | 0 | 20 | 40 | 70 | 92 | 100 |

**How to measure:** work-order history. Count only *unplanned* corrective orders that stopped
production. Planned PM downtime is excluded — it is not a wear signal.

### 3.3 Efficiency degradation — `EFFICIENCY`

The single most valuable indicator, and the one almost nobody in the field tracks. It is also
the one that converts directly into money.

```
degradation = (specific_consumption_now - specific_consumption_baseline)
              / specific_consumption_baseline
```

| Equipment | Specific consumption unit | Baseline source |
|---|---|---|
| Diesel generator | L fuel / kWh generated | OEM curve at the measured load factor |
| Electric motor driven machine | kWh / tonne (or / unit) output | Commissioning test or best-recorded 12-month figure |
| Pump | kWh / m³ at rated head | Pump curve + measured head |
| Compressor | kWh / m³ free air delivered | OEM data sheet |
| Chiller | kW / TR (or COP) | OEM at matched ambient & load |

| degradation | 0.00 | 0.03 | 0.05 | 0.10 | 0.15 | 0.25 | 0.40 |
|---|---|---|---|---|---|---|---|
| score | 0 | 10 | 25 | 50 | 70 | 90 | 100 |

#### Load correction — compare like with like

Specific consumption moves with load factor. An engine is least efficient per unit of output
when lightly loaded, so a genset measured at 25% load will always look degraded against its
nameplate figure even when it is mechanically perfect. **The baseline is therefore corrected to
the load actually measured** before degradation is computed:

```
corrected_baseline = baseline × part_load_penalty(load_factor)
```

| load_factor | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | 0.75 | 1.00 |
|---|---|---|---|---|---|---|---|
| penalty multiplier | 2.00 | 1.45 | 1.22 | 1.12 | 1.06 | 0.99 | 1.00 |

These are planning approximations. Where an OEM part-load curve exists, use it instead. The
curve is currently defined for **diesel generators only** — other classes are left uncorrected
rather than borrowing a curve that does not describe them. Pumps, compressors and chillers have
real part-load behaviour of their own and need their own curves before this applies to them.

Worked example from the sample fleet: a 60 kW genset serving an admin block reads 0.361 L/kWh
against a 0.268 baseline. Uncorrected that is 34.7% degradation — a near-worst efficiency score
and an apparent scrap candidate. It runs at 22% load, so its corrected baseline is 0.376, and
the true degradation is **negative**. The machine is fine. The sizing is wrong.

`load_factor` must therefore be recorded with every efficiency reading. When it is absent on a
generator, the report says so rather than silently assuming rated-load conditions.

**Wet stacking.** Sustained operation below 30% load fouls a diesel engine and degrades its
consumption over time. Under-loaded gensets are flagged as a **sizing and dispatch fault, not a
worn asset** — replacing one repeats the mistake with a new machine, and the replacement will
degrade the same way.

### 3.4 Capacity derating — `CAPACITY`

```
derate = 1 - (sustained_actual_output / rated_output)
```

| derate | 0.00 | 0.05 | 0.10 | 0.20 | 0.30 | 0.45 |
|---|---|---|---|---|---|---|
| score | 0 | 10 | 30 | 60 | 85 | 100 |

**How to measure:** for gensets, a load bank test to rated kW held for 2 hours — not the
nameplate, and not what the site load happens to draw. For production machines, best sustained
throughput over a full shift with in-spec output quality.

### 3.5 Maintenance cost burden — `MAINT_COST`

Two ratios against **current replacement value** (what an equivalent new unit costs today —
not book value, not original purchase price). Combined 55/45.

```
annual_ratio     = annual_maintenance_cost     / replacement_value
cumulative_ratio = cumulative_maintenance_cost / replacement_value
```

| annual_ratio | 0 | 0.03 | 0.05 | 0.08 | 0.12 | 0.20 |
|---|---|---|---|---|---|---|
| score | 0 | 10 | 25 | 50 | 75 | 100 |

| cumulative_ratio | 0 | 0.30 | 0.50 | 0.75 | 1.00 | 1.50 |
|---|---|---|---|---|---|---|
| score | 0 | 15 | 40 | 70 | 90 | 100 |

Include parts, contracted labour, in-house labour hours at loaded rate, and consumables
attributable to failure. Exclude routine fuel and lubricants (those belong to EFFICIENCY).

### 3.6 Physical condition — `CONDITION`

Composite of the condition-monitoring evidence that exists. Score = `0.6 × worst + 0.4 × mean`,
so one critical finding cannot be averaged away by three clean ones.

| Check | Scale | Score |
|---|---|---|
| Vibration (ISO 20816 / 10816 zone) | A / B / C / D | 0 / 25 / 60 / 95 |
| Oil analysis | normal / caution / alert / critical | 0 / 40 / 75 / 95 |
| Thermography | normal / caution / alert / critical | 0 / 40 / 80 / 95 |
| Insulation resistance & PI (IEEE 43) | good / caution / poor / fail | 0 / 45 / 85 / 100 |

**How to measure:** handheld vibration meter at bearing housings under steady load; oil sample
from mid-sump while hot; thermal camera on panels, bearings and couplings at full load;
megger + polarization index on generator and motor windings.

### 3.7 Obsolescence & supportability — `OBSOLESCENCE`

A machine you cannot get parts for is finished, whatever its condition. Combined 60/40.

| OEM support status | Score |
|---|---|
| Supported | 0 |
| Limited / last-time-buy announced | 45 |
| Discontinued, parts still available | 80 |
| Unsupported, no parts channel | 100 |

| Spare lead time (days) | 7 | 30 | 60 | 120 | 240 |
|---|---|---|---|---|---|
| score | 0 | 20 | 45 | 75 | 100 |

**Local relevance:** for imported equipment in Egypt, lead time should include customs
clearance and FX availability, not just OEM ship date. This is often the dominant term.

### 3.8 Safety & compliance — `COMPLIANCE`

Worst-of, not averaged. Safety is not tradeable against efficiency.

| Open critical safety findings | 0 | 1 | 2 | 3+ |
|---|---|---|---|---|
| score | 0 | 60 | 85 | 100 |

| Emissions status | compliant / marginal / non-compliant |
|---|---|
| score | 0 / 40 / 90 |

## 4. Weighting by equipment class

Weights reflect which failure mode actually costs money for that class.

| Indicator | Diesel generator | Production machine | Pump | Compressor | Chiller | Vehicle / mobile |
|---|---|---|---|---|---|---|
| AGE | 10 | 10 | 10 | 10 | 10 | 15 |
| RELIABILITY | 20 | 25 | 18 | 18 | 18 | 20 |
| EFFICIENCY | 25 | 15 | 22 | 25 | 25 | 15 |
| CAPACITY | 10 | 15 | 12 | 12 | 12 | 8 |
| MAINT_COST | 15 | 18 | 15 | 15 | 15 | 22 |
| CONDITION | 10 | 10 | 15 | 12 | 12 | 10 |
| OBSOLESCENCE | 5 | 5 | 5 | 5 | 5 | 5 |
| COMPLIANCE | 5 | 2 | 3 | 3 | 3 | 5 |

Gensets weight EFFICIENCY heaviest because fuel is 60–80% of their lifecycle cost.
Production machines weight RELIABILITY heaviest because their downtime stops a line.
Vehicles weight MAINT_COST heaviest because that is where their consumption actually shows.

## 5. Hard overrides

Applied after scoring. These bypass the weighted result — a machine can be unsafe or
unsupportable while scoring well everywhere else.

| Trigger | Forced minimum band |
|---|---|
| 1+ open **critical** safety finding | `RETIRE_NOW` (or immediate remediation before return to service) |
| Emissions non-compliant | `PLAN_REPLACEMENT` |
| Vibration zone **D** | `PLAN_REPLACEMENT` |
| Insulation test **fail** | `RETIRE_NOW` |
| Cumulative maintenance cost > 100% of replacement value | `RETIRE_NOW` |
| OEM support = unsupported **and** lead time > 120 days | `PLAN_REPLACEMENT` |
| Economic test fails (§6) | Escalate one band, **capped at `PLAN_REPLACEMENT`** |

Overrides are **floors, not assignments** — they can raise a band, never lower one.

The economic cap is deliberate. Economics tells you to *budget for a replacement*; it never
tells you to stop running a machine that is physically sound. Reaching `RETIRE_NOW` requires
condition, safety or score evidence, not a spreadsheet result.

## 6. The economic test

The score says *how worn*. The economics say *whether replacing pays*. Both must agree before
capital is committed.

Both sides are stated on a **differential** basis: any cost incurred either way cancels out and
is excluded from both. In particular the energy a *new* unit would itself burn is charged to
neither side — only the **excess** the old unit burns above it appears, in the keep term.
Charging full energy to the new unit while charging only the excess to the old one would
compare two different bases and would always favour keeping.

**Equivalent annual cost of a new unit** — its capital, annualised over its whole life:

```
CRF(r, n) = r(1+r)^n / ((1+r)^n − 1)

EAC_new = capital_cost × CRF(r, n)
```

The new unit's maintenance is taken as covered by warranty in its early years, and its residual
value at end of life discounts to near nothing at Egyptian rates (2% of capital at 22% over 20
years). Both simplifications are deliberately conservative **against** replacing.

**Marginal cost of keeping the existing unit one more year:**

```
marginal_keep = expected_maintenance_next_year
              + energy_penalty          # extra fuel/power vs. a new unit
              + excess_downtime_cost    # downtime a new unit would NOT have had
              + (salvage_now − salvage_next_year)   # value lost by not selling now
              + r × salvage_now                     # capital tied up in the old asset
```

where

```
energy_penalty       = annual_output × (specific_consumption_now − specific_consumption_new)
                       × energy_price          # floored at zero

excess_downtime_cost = max(0, annual_downtime_hours − benchmark × annual_run_hours)
                       × downtime_cost_per_hour
```

**A new machine also fails sometimes.** `benchmark` is the unavailability a well-run new unit
would itself incur — 2% by default. Charging the old asset's *entire* downtime to the keep side
would assume a replacement never breaks, and that single assumption is enough to make almost
every asset in a fleet look like it should be replaced. Only downtime above the benchmark is a
genuine cost of keeping.

**Decision rule:** replace when

```
marginal_keep > EAC_new × (1 + materiality)
```

with `materiality` defaulting to 15%. These inputs are estimates, not invoices — a result inside
the noise band is a tie, and a tie should not move a capital decision. Without this threshold the
test fires on a one-pound difference.

This is the classic replacement-timing rule, and it is the number that convinces a CFO. It is
also why EFFICIENCY matters so much: the energy penalty term compounds every single run-hour,
while maintenance cost only appears when something breaks.

**Discount rate.** Use the organisation's real cost of capital. In Egypt this is high and
volatile — set it explicitly in `config.json` and state it on every report. A framework that
hides its discount rate is not auditable.

## 7. Data confidence

Every report states what share of the scoring weight was backed by actual data:

| Confidence | Meaning |
|---|---|
| ≥ 85% | Verdict is decision-grade. |
| 60–84% | Verdict is directional. Name the missing indicators before acting. |
| < 60% | **No verdict is issued.** The output is a data-collection plan. |

Below the floor, reports show the band as **Insufficient data**, not as `KEEP`. This matters more
than it looks: a reader acts on the word, not on the confidence figure printed beside it, and an
asset with no readings would otherwise be presented as healthy precisely *because* nobody has
measured it. The underlying score is still shown, clearly marked indicative.

This is deliberately prominent. For most first-time clients the honest finding is *"you cannot
answer this question yet, and here is exactly what you must start measuring."* That gap is the
product.

## 7a. Output measurement and its validation

Output is measured in three distinct places, and they are not interchangeable:

| Field | What it is | Feeds |
|---|---|---|
| `rated_output` | Nameplate rate — kW, t/h, m³/h | CAPACITY |
| `actual_output` | Sustained achievable rate today | CAPACITY |
| `load_factor` | Fraction of rated output actually drawn | EFFICIENCY baseline correction |
| `annual_output_total` | **Volume** produced over the year — kWh, tonnes, m³ | Economics only |
| — | Output is also the denominator of every specific-consumption figure | EFFICIENCY |

`annual_output_total` is the quietest high-stakes field in the record. It affects **no indicator
score**, so a wrong value produces no visible symptom — but it multiplies straight into the
energy penalty, which is usually the largest term in the replacement economics. A tenfold unit
slip there changes the recommendation while every score on the page stays identical.

It is therefore cross-checked against what the asset's own rate and run-hours imply:

```
implied = rated_output × load_factor × annual_run_hours     (when load_factor is known)
        = actual_output × annual_run_hours                  (otherwise)
        = annual_run_hours                                  (when consumption is stated per hour)
```

with per-minute and per-second output units converted first. A disagreement beyond 15% is
reported as an advisory naming the likely slip and its direction. Correct data must stay silent
— an advisory that fires on good rows becomes noise people learn to ignore, so the check is
tested against the full sample fleet for false positives.

**Utilisation** — `annual_run_hours / 8760` — is reported alongside every asset. It is context,
not a scored indicator: a machine running 3% of the year is a different capital question from
one running 80%, even at an identical fitness score.

## 7b. Energy burn — the daily cost of running worse than necessary

Energy is working capital that burns every day the machine runs, so annual percentages are the
wrong presentation for a decision-maker. For every asset with a priced, measured consumption,
three levels are computed:

```
sec_actual     what the machine burns per unit of output (measured)
sec_expected   what a HEALTHY machine of this rating burns at the same load
sec_ideal      what a healthy, RIGHT-SIZED machine burns at target load (80%)

wear burn        = (sec_actual − sec_expected) × annual output × energy price
allocation burn  = (sec_expected − sec_ideal)  × annual output × energy price
```

Both floored at zero, both reported **per day**. The two terms partition the total gap against
the ideal exactly — no double counting — and each names its owner:

| Term | Cause | Owner | Remedy |
|---|---|---|---|
| Wear burn | The machine has degraded against its own load-corrected baseline | Maintenance | Overhaul / recommission / replace |
| Allocation burn | The machine is the wrong size for its duty | Operations | Reassign / re-dispatch / right-size |

**Benchmark fallback.** When no baseline exists, the class benchmark range in the machinery
library is used (top of range, the conservative comparator) and every resulting figure is
marked *indicative*: good enough to rank the fleet's burners and justify metering, not good
enough to sign a purchase order. Classes where a benchmark is meaningless without more context
(pumps without head, dryers without material) have none, and say so rather than guessing.

**Power factor.** Below 0.90 the asset is flagged: Egyptian industrial tariffs surcharge
reactive power, and correction capacitors are usually the fastest-payback item on a site.

## 7c. Standards alignment

EFF is a lightweight framework, not a certified audit — but its concepts map onto the standards
an international reviewer will ask about, and the mapping is explicit:

| EFF element | Aligns with |
|---|---|
| Retire/keep decision framework, asset value focus | ISO 55000 asset management principles |
| Efficiency tracking, baselines, burn reporting | ISO 50001 EnPI / energy-baseline concepts |
| Reliability data definitions (unplanned failures, downtime) | ISO 14224 taxonomy (simplified) |
| Vibration zones | ISO 20816 / 10816 |
| Insulation resistance & PI | IEEE 43 |
| Failure density, unavailability | SMRP best-practice metrics (simplified MTBF / availability) |
| Monitoring retainer's saving verification | IPMVP Option C-style whole-facility comparison (planned) |
| Self-service data tiers | Mirrors ASHRAE Level 1 → Level 2 audit progression |

The words "aligns with" are chosen deliberately: EFF borrows the definitions and thresholds of
these standards where they fit an SME context, and does not claim conformity assessment.

## 8. Assessment cadence

| Band | Re-assess |
|---|---|
| KEEP | Annually |
| MONITOR | Every 6 months |
| PLAN_REPLACEMENT | Quarterly until replaced |
| RETIRE_NOW | On action |

Efficiency readings should be taken **monthly** regardless of band — the trend is worth more
than any single reading, and it is what turns this from an audit into a monitoring service.

## 9. Known limitations

- Thresholds are engineering rules of thumb, not derived from a fleet dataset. They should be
  recalibrated once 50+ assessed assets with known outcomes exist.
- Efficiency scoring is only as good as the baseline correction for load and ambient
  conditions. Uncorrected baselines produce false positives.
- The framework assesses assets individually. It does not yet handle redundancy — an N+1
  genset set can tolerate a worse unit than a single-point-of-failure one.
- Standby assets (low run-hours, high consequence) are under-served by run-hour-based scoring.
  Their real risk is start reliability, which is not yet an indicator.

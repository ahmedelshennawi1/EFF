# Data collection guide

What to measure, how, and how often — so that an assessment reaches decision-grade confidence.

Every column below maps to a field in `data/assets.csv`. Blank cells are safe: a missing value
is excluded from scoring and reduces reported confidence. It is never treated as zero, so
leaving a cell empty is always better than guessing a number.

---

## Tier 1 — start here (gets most fleets to ~60% confidence)

These need no instruments beyond a clipboard and the existing work-order system.

| Field | Source | Frequency |
|---|---|---|
| `commissioned_year` | Asset register, commissioning certificate | Once |
| `run_hours` | Hour meter | Monthly |
| `annual_run_hours` | Hour meter delta over 12 months | Monthly |
| `annual_downtime_hours` | Work orders — **unplanned stops only** | Per event |
| `unplanned_failures_12m` | Count of corrective work orders that stopped production | Per event |
| `annual_maint_cost` | Parts + contracted labour + in-house hours at loaded rate | Monthly |
| `cumulative_maint_cost` | Running total since commissioning | Monthly |
| `replacement_value` | Current quote for an equivalent new unit | Annually |
| `oem_support`, `spare_lead_days` | Supplier — include customs and FX time, not just ship date | Annually |
| `safety_findings` | Open critical HSE findings against the asset | Per event |

**If an asset has no hour meter, fit one.** It is the cheapest instrument in this entire guide
and it unlocks three separate indicators.

## Tier 2 — the efficiency layer (this is where the money is)

Specific consumption is the indicator almost nobody tracks and the one that converts directly
into money. It needs a meter on the input and a count of the output.

| Field | How |
|---|---|
| `specific_consumption` | Input consumed ÷ output produced, over a measured period |
| `baseline_specific_consumption` | OEM figure at the **measured load factor**, or the best 12-month figure on record |
| `consumption_unit` | See the table below |
| `energy_price` | Current diesel price per litre, or industrial tariff per kWh |
| `annual_output_total` | Total output over the year, in the denominator unit above |

| Equipment | Unit | Input meter | Output count |
|---|---|---|---|
| Diesel generator | L/kWh | Fuel flow meter, or tank dips against a log | Genset kWh meter |
| Electric machine | kWh/tonne | Sub-meter on the panel | Production log |
| Pump | kWh/m³ | Sub-meter | Flow meter or run-hours × rated flow |
| Compressor | kWh/m³ | Sub-meter | FAD from the OEM curve × loaded hours |
| Chiller | kW/TR | Sub-meter | BTU meter, or design TR × load % |
| Vehicle | L/h | Fuel issue log | Hour meter |

**Always record `load_factor` with an efficiency reading.** Specific consumption moves with
load. A genset at 25% load burns far more fuel per kWh than the same genset at 75%, whatever
its condition. The tool corrects the baseline for this automatically on diesel generators — but
only if you give it the load factor. Without it, a perfectly healthy lightly-loaded machine
reads as a scrap candidate, which is the most damaging false positive this framework can
produce.

Measure it as the actual output drawn divided by rated output, at the same time as the
consumption reading:

```
load_factor = average kW drawn / rated kW          (generators)
```

If a genset sits below 30% load, the finding is a **sizing problem, not a wear problem** —
replacing it buys a new machine that will wet-stack the same way. Right-size or re-dispatch.

### The two output figures are different things

| Field | Unit | Example |
|---|---|---|
| `rated_output` / `actual_output` | a **rate** | 400 kW, 12 t/h, 320 m³/h |
| `annual_output_total` | a **volume** over the year | 780,000 kWh, 911,200 m³ |

`annual_output_total` must be in the denominator unit of `specific_consumption`. If consumption
is L/kWh, the total is kWh. If it is kWh/m³, the total is m³. If consumption is stated per hour
(L/h on vehicles), the total is simply `annual_run_hours`.

Get this wrong and no score changes — but the money in the economics moves, potentially by
orders of magnitude. The tool cross-checks it against your rate and run-hours and raises an
advisory if the two disagree by more than 15%.

**Take readings monthly.** The trend is worth more than any single reading, and monthly
readings are what turn a one-off audit into a monitoring retainer.

## Tier 3 — condition monitoring

| Field | Instrument | Frequency | Scale |
|---|---|---|---|
| `vibration_zone` | Handheld vibration meter at bearing housings, steady load | Quarterly | ISO 20816 zone `a` / `b` / `c` / `d` |
| `oil_analysis` | Lab sample, drawn mid-sump while hot | 2× per year | `normal` / `caution` / `alert` / `critical` |
| `thermography` | Thermal camera on panels, bearings, couplings at full load | 2× per year | `normal` / `caution` / `alert` / `critical` |
| `insulation` | Megger + polarization index, IEEE 43 | Annually | `good` / `caution` / `poor` / `fail` |

Insulation testing applies to generators and motors. Leave it blank for anything else rather
than recording a pass it never had.

## Tier 4 — the economic inputs

Needed only for the replacement-timing test. Without `new_unit_capital` and
`new_unit_life_years` the score still works; the economics are simply reported as not computed.

| Field | Notes |
|---|---|
| `new_unit_capital` | Landed cost of the replacement — include shipping, customs, installation |
| `new_unit_life_years` | Expected service life of the replacement |
| `new_unit_specific_consumption` | The new unit's rated efficiency — sets the energy-penalty baseline |
| `salvage_value` | Realistic resale today, not book value |
| `downtime_cost_per_hour` | Lost contribution margin per hour, not revenue |

`downtime_cost_per_hour` is the input clients get most wrong and the one the result is most
sensitive to. Use lost **contribution margin** — revenue minus the variable costs you avoid
while stopped. Using full revenue can overstate the case for replacement several times over.

## Enumerated values

The parser lowercases input and converts spaces and hyphens to underscores, so `Non Compliant`,
`non-compliant` and `non_compliant` are all read the same way. Anything it does not recognise is
treated as missing rather than guessed.

| Field | Accepted values |
|---|---|
| `asset_class` | `diesel_generator`, `production_machine`, `pump`, `compressor`, `chiller`, `vehicle` |
| `vibration_zone` | `a`, `b`, `c`, `d` |
| `oil_analysis`, `thermography` | `normal`, `caution`, `alert`, `critical` |
| `insulation` | `good`, `caution`, `poor`, `fail` |
| `oem_support` | `supported`, `limited`, `discontinued`, `unsupported` |
| `emissions_status` | `compliant`, `marginal`, `non_compliant` |

An unrecognised `asset_class` falls back to `production_machine` weights.

## Suggested rollout

1. **Week 1** — asset register, Tier 1 fields. Run the assessment. Expect most assets to come
   back *Insufficient data*; that report is the sales case for step 2.
2. **Month 1–2** — fit hour meters and fuel/energy sub-meters on the highest-value assets.
   Start monthly efficiency readings.
3. **Month 3** — first condition-monitoring round.
4. **Month 6** — re-assess. Confidence should now be decision-grade, and the efficiency trend
   has enough points to be meaningful.

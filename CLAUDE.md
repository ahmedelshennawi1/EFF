# eff — Equipment Fitness Framework

A scored, auditable answer to "should this machine stay in service?" plus a daily
energy-burn ledger. Being built as a **SaaS-style assessment service for Egyptian
industry** — self-service data collection, no site visits.

## Ownership — do not get this wrong

eff is an **independent venture in formation**, owned by the user (Ahmed Elshennawi).
It is NOT part of the Ahmed Elshennawi feasibility-studies practice and NOT owned by
Dakahlia Group. Never draft anything implying the Group owns or monetises the
methodology. A *personal* partnership offer to Eng. Khaled Al-Anani (user's cousin;
CEO Dakahlia Poultry, Deputy Chairman Dakahlia Group) may come later — kept strictly
separate from any Group document.

## Architecture

```
eff/            engine (pure Python, stdlib only — keep it that way)
  models.py     Asset dataclass + CSV parsing; blanks = "not measured", never 0
  profiles.py   loads data/profiles.json (archetypes → classes → sectors) + validation
  scoring.py    8 indicators, piecewise-linear curves, load-corrected baselines
  economics.py  EAC vs marginal-keep, differential basis, 15% materiality
  duty.py       right-size-for-the-task analysis (oversized tractor case)
  energy.py     daily burn ledger: wear burn vs allocation burn (they partition exactly)
  emissions.py  CO2e from the SAME excess quantities as the burn — never an independent
                estimate; refuses when fuel factor and consumption unit disagree
  verdict.py    weighted roll-up, bands, hard overrides, data confidence
  validate.py   input cross-checks (output vs rate×hours), advisories
  report.py     console + branded HTML report
cli.py          entry point; also --sectors/--sector/--check-library
data/
  profiles.json machinery library — 47 classes, 11 sectors, curves, benchmarks.
                CLIENT-EXTENSIBLE: edit JSON, never hardcode classes in Python.
  assets.csv    build artifact — Google Sheets is the master (see Data flow)
  market.json   Egypt market model inputs (from Gemini research)
tools/
  sheet2csv.py  converts Drive-connector markdown dump → assets.csv
  market_model.py  revenue/priority model per sector
tests/test_eff.py  46 tests, no framework: python tests/test_eff.py
docs/           CRITERIA.md (methodology), DATA-COLLECTION.md, market/
offer/          bilingual client-facing HTML (offer, Dakahlia brief, DataKit form)
brand/          EFF-Brand-Guide.html — the brand system
demo/           EFF-Dashboard.html — demo dashboard for proposals
```

## Commands

```bash
python cli.py                          # fleet summary + burn ledger
python cli.py --detail                 # every asset in full
python cli.py --asset GEN-02           # one asset
python cli.py --html out/report.html   # branded client report
python cli.py --sector poultry         # sector machinery checklist
python cli.py --check-library          # validate profiles.json after edits
python tests/test_eff.py               # run all tests (must stay green)
python tools/market_model.py           # market sizing
```

Windows note: Arabic output needs `chcp 65001` + `$env:PYTHONIOENCODING="utf-8"`.
No LibreOffice/poppler on this machine; use Office COM or skip Office formats.

## Data flow

Google Sheets is the master register (user's Excel is unlicensed; never depend on it).
Sync: read the sheet via the Drive connector → save dump → 
`python tools/sheet2csv.py <dump.md> data/assets.csv` → run cli.
Sheets: "EFF Asset Register" (demo, id `1jqpb7…qfbtzs`), "Dakahlia Group — EFF Asset
Register" (pilot, id `1KXGzh…RtKkvmw`). DataKit CSV exports append to the sheet via
File→Import. Never add CSV columns without adding the field to `models.Asset` first.

## Non-negotiable honesty rules (they ARE the product)

- Missing data is excluded and reported as reduced confidence — never scored as 0.
- Below 60% confidence: NO verdict shown; display "Insufficient data", never "Keep".
- Benchmark-based figures are always marked indicative (`~`).
- Economics escalate at most to PLAN_REPLACEMENT; RETIRE needs physical/safety evidence.
- Overrides are floors, never demotions.
- Demo numbers are always labeled as demonstration data, never implied to be a client's.
- Market stats: keep `EST:` prefixes; never quote 2024 prices as current.

## Brand (see brand/EFF-Brand-Guide.html)

- Wordmark **"eff" lowercase always**; in Arabic text stays Latin («منصة eff»), never «إي إف إف».
- Dark-first. Ink `#0F1416`, Surface `#171E21`, accent **Ember `#F0692F`** (light: `#D4551E`).
- Verdict ramp keep `#2FA98C` / monitor `#D9A441` / plan `#C4574D` / retire `#8C2F22`.
- **Collision rule**: ember = interactive/brand/KPI + burn data only; verdict colors = data
  only; an element is never both. Monitor pills take dark text, not white.
- Retire on dark surface is <3:1 contrast — legal only because every status mark carries a
  text label and a table view exists. Keep it that way.
- Type: Rubik (one family, both scripts), IBM Plex Mono for data, Western digits, tabular-nums.
- The older teal documents in offer/ predate the brand and await restyling approval.

## Arabic terminology — use what Egyptian plants actually say

Not literary Arabic. معمل تفريخ (not المفرخ) · دفاية عنابر · ماكينة تفريخ/حضّانة (the
*incubator*, a different machine from a brooder — never merge them) · مروحة شفط ·
ألواح تبريد · مطحنة مطارق · ماكينة بيليت · أسانسير · سكرو · بويلر · تشيلر ·
موتور · ترانس · بلوَر · فاكيوم · إكسترودر · فرن دوّار · ونش · لودر. `data/profiles.json`
`label_ar` is the source of truth; `test_datakit_matches_the_machinery_library` fails if
the DataKit's inlined copy drifts from it in classes, labels, or sector lists.

## Pricing is COMPUTED, never looked up

`eff/pricing.py` + `data/pricing.json` + `python cli.py --quote ...`. A price table cannot
quote a client you have not met and gives two similar clients different numbers, so the fee is
derived: effort (setup + assets x 0.03d + sites x 0.25d + analysis + reporting) x modifiers
(data readiness / urgency / diversity / language) x day rate, minus itemised discounts.
Retainer = 40% of the **pre-discount** value (a free pilot must not make the retainer free).
A value check flags any fee outside 1-3% of the client's annual energy spend — it flags, it
never silently changes the number. Client-facing version: `offer/EFF-Pricing.html`.
**Any worked example in a document must be produced by running the CLI, not typed by hand.**

## Product carbon intensity, regionally benchmarked

`eff/product.py` + `data/products.json` + `python cli.py --product potatoes --region new_valley`.
Answers "what does one tonne of our product cost in carbon, and how far from the best
achievable HERE?" — the regional part is the point: New Valley lifts water 65 m vs the Delta's
12 m, so its irrigation ideal is scaled up and it is not punished for geology. Water becomes
carbon through pump energy (rho*g*H / eta), which is why water-table depth is regional.
Climate-tagged inputs scale by region; untagged ones (freight, packaging) do not. Gaps are
floored at zero so beating one ideal never offsets waste elsewhere. ALL reference values are
uncalibrated planning estimates — output says so, and it is not a certified PCF (that needs
ISO 14067 / GHG Protocol work with verified primary data).

**Every reference value carries a `src` key** naming its source; `est` means an eff estimate,
not yet sourced, and `sourced_share` reports how much of a result rests on cited values.
**Each product declares `published_range_kg_per_t` and the model is ASSERTED against it in
tests** — a screening model landing outside published LCA literature is wrong until proven
otherwise. This caught a real bug: feed carbon originally counted only milling electricity and
ignored the embedded carbon of the maize and soy, which is 60-80% of poultry emissions.
When a product legitimately reads low because of scope (broiler: no manure N2O, chicks,
bedding), it declares `_scope_note` and the output prints it — **never tune a number to hit a
range; state the scope gap.**

Standards frame: ISO 14067:2018 (PCF), GHG Protocol Product Standard, PAS 2050, ISO 14064
(organisation level, for credits), Mekonnen & Hoekstra 2011 (water footprint). The model
follows their structure; it does not claim conformity.

## EU claims — get these right

**CBAM does NOT cover food or agriculture.** It covers cement, iron/steel, aluminium,
fertilizers, electricity, hydrogen; the 2028 expansion is steel/aluminium downstream goods.
Never imply it applies to poultry. The real EU lever for a food exporter is buyers' own
supply-chain emissions disclosure obligations. Carbon credits ARE real in Egypt: a regulated
voluntary market on the Egyptian Exchange under the FRA since August 2024 — but monetising
requires certification and independent verification, so never promise revenue, only the
measurement baseline certification needs.

## AI positioning

"AI monitors. Engineering criteria decide." The engine contains **no machine learning** — the
scoring is deterministic. Describe AI as the monitoring/analysis layer (tracking readings,
flagging drift, catching data contradictions), never as the decision layer. Every verdict
traces to a published threshold (ISO 20816, IEEE 43, OEM curves). If ML is ever added, this
wording must be revisited.

## No fabricated examples in client documents

The user's rule (2026-08-29): **"We don't put examples."** No invented case studies, demo
fleets, or illustrative figures in anything a client sees. The old 13-asset demo fleet, the
500 hp tractor case, EGP 3,715/day, 328.7 t CO2 — all removed from the proposal and deck and
must not come back. Client documents argue from METHOD; the numbers arrive from the client's
own pilot. Where a figure would normally sit, the deck shows a deliberately empty dashed box
("these boxes are empty on purpose; in 14 days they hold your figures").

The sample fleet in `data/assets.csv` stays — it is for testing the engine, never for showing
a client.

## Engagement shape: five-machine proof of concept

The Dakahlia pilot is NOT a fleet assessment. It is **five major, easy-to-survey machines**,
~2 hours of client time total, D+0 / D+7 / D+14, free under the Founding Client Programme,
with no obligation to widen scope. The pilot's own output is the demonstration — that is the
whole point, and it replaces every borrowed example.

## Client numbers — never assert them

Do NOT put a figure for the client's own profitability, margin, or savings into any document.
Show the arithmetic across a RANGE and let them supply the real number (the deck's profit slide
shows 5/8/12% scenarios and says outright these are "points on a scale, not an estimate of the
Group's profitability"). Same for the service price: **the Dakahlia pilot is free** (brief +
deck pilot mode), so the fee must never appear in their submission — the deck carries
`data-mode="pilot"` vs `"commercial"` and `verify_pdf.py` asserts 48,000 is absent.

## PDF build (`tools\build_submission.ps1` → `out\EFF-Submission-Dakahlia.pdf`)

Headless Edge is the only HTML→PDF path here (no LibreOffice/poppler). Three traps, all hit:
- **`Start-Process -Wait` is mandatory.** Calling the exe with `&` returns before the PDF is
  flushed: no file, no error.
- **`[regex]::Replace` has NO static count overload.** A trailing `1` is silently read as
  `RegexOptions.IgnoreCase` and the replace goes GLOBAL — which rewrote the stylesheet's
  `#deck[data-lang="ar"]` selector and blanked the entire English half. Switch language by
  matching the root opening tag and rewriting attributes inside it only.
- **Print CSS must beat `.slide.on` (0,2,0).** A bare `.slide{animation:none}` (0,1,0) loses,
  the entry animation's `opacity:0` with `fill-mode:both` survives, and the ACTIVE slide prints
  blank. Always `.slide, .slide.on{animation:none!important; opacity:1!important}`.
Verify with `scratchpad/pagesize.py` (any page under ~400 stream bytes is blank) before sending.

## Published-page gotcha: downloads

The artifact viewer blocks page-initiated downloads — an `<a download>` with a blob URL is
INERT for viewers (it works only when the HTML is opened as a local file). Any page offering
a file must declare `capabilities: {downloads: true}` and call
`await claude.use('downloads')` → `save({filename, data})`. `.csv` is in the extended
extension set and can fail with `extension_not_enabled`; fall back to `.csv.txt` and tell
the viewer to rename. Keep the blob path too, for the local-file case where no `claude`
global exists. The DataKit does all of this — copy its `exportCsv` pattern.

## Bilingual document pattern (hard-won)

AR default + RTL, toggle to EN. Language rules need specificity **(0,3,0)** —
`.page[data-doc-lang="ar"] .en-only{display:none}` — or element-typed display rules
(e.g. `.step .what span{display:block}`) leak the hidden language. Always verify with
the leak-count script in both directions before publishing. Arabic labels can't fit
narrow chart segments — move to a legend below ~34rem.

## Pricing basis (offer/EFF-Offer-AR.html)

Self-service: EGP 13,000/day blended × explicit effort. Baseline 38k/48k/69k by fleet
size; retainer 42k–130k/yr; site visits an add-on (18k/day), not the default. If the
day rate changes, EVERY fee table regenerates from it.

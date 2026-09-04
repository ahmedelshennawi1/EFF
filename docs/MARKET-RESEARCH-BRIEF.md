# Market Research Brief — Equipment Fitness Framework (EFF), Egypt

**Instructions for the research assistant (Gemini):** You are researching the Egyptian market
for an equipment-assessment consulting service. Follow this brief exactly. Where a hard figure
does not exist, give your best estimate, **label it `EST`**, and state the basis. Every hard
figure needs a source and a year. Prefer figures from 2022 or later; flag anything older.

---

## 1. Context (read, don't research)

EFF is a paid assessment service for industrial operations in Egypt. It scores machinery
(0–100) on eight indicators, tells the client which machines to keep / monitor / replace /
retire, and prices the energy each machine burns above requirement in **EGP per day**. It is
self-service (the client fills a data sheet; no site visits), priced roughly EGP 38,000–69,000
per baseline assessment and EGP 42,000–130,000/year for monitoring.

**The ideal client:** owns 15+ substantial machines (generators, boilers, mills, chillers,
compressors, tractors), pays a large monthly energy bill, has no asset-performance software
(too small for GE/IBM platforms), and makes replace/keep decisions by gut feel today.

**The purpose of this research:** rank the sectors below by how many such clients exist in
Egypt, where they are, and how painful their energy costs are — so marketing effort goes to
the richest segments first.

## 2. Sector keys (use these exact keys in all output)

| key | Sector |
| --- | --- |
| `poultry` | Poultry & livestock production (farms, hatcheries) |
| `feed_milling` | Animal feed mills |
| `agriculture` | Field-crop agriculture (large farms, land-reclamation companies) |
| `food_processing` | Food & beverage processing |
| `cold_chain` | Cold storage & refrigerated distribution |
| `textiles` | Spinning, weaving, dyeing |
| `building_materials` | Cement, brick, marble, aggregates |
| `plastics` | Plastic products & packaging |
| `metal_fabrication` | Metal fabrication & workshops |
| `water_utilities` | Water/wastewater plants & private treatment operators |
| `general_facilities` | Hotels, hospitals, malls, large commercial facilities |

## 3. Questions — answer per sector

For **each** of the 11 keys:

### 3.1 Population

- Number of registered establishments in Egypt (CAPMAS economic census, GAFI, or the relevant
  industrial federation). Break down by size if possible (10–49, 50–249, 250+ employees).
- Number that plausibly own **15+ substantial machines** (`EST` is expected here — state your
  reasoning, e.g. "establishments with 50+ employees in this sector typically operate …").
- Geographic clusters: which governorates / industrial zones (e.g. 10th of Ramadan, 6th of
  October, Sadat City, Borg El Arab, Delta governorates for poultry/feed).

### 3.2 Energy pain

- Typical share of energy in operating cost for this sector in Egypt (%).
- Which energy sources dominate (electricity / natural gas / diesel), and exposure to recent
  Egyptian price changes: diesel price steps, industrial electricity tariff rises, gas price
  for industry. Give the current prices you find, with dates.
- Any sector-specific energy statistic (e.g. kWh/ton cement, energy per poultry house).

### 3.3 Buying signals

- Evidence this sector pays for consulting/audits: active ESCO projects, IFC/EBRD/UNIDO energy
  programmes targeting it, green-financing lines (e.g. GEFF Egypt), export-driven pressure
  (EU CBAM for cement/fertilizer, retailer ESG demands on food exporters).
- Trade associations, chambers, expos, and specialist media where these companies gather
  (names, and dates of the next event if findable).

### 3.4 Decision-makers

- Typical title of the person who would buy this service (owner? plant manager? CFO?
  maintenance manager?) and typical company ownership structure (family-owned share).

## 4. Cross-cutting questions (once, not per sector)

1. Total number of Egyptian manufacturing establishments with 10+ employees, latest year.
2. Industrial electricity tariff table (EGP/kWh by voltage band) and the last two increases.
3. Diesel and natural-gas-for-industry prices, last three changes with dates.
4. Egypt's ESCO market: how many registered ESCOs, typical audit price if findable.
5. Any Egyptian regulation pushing energy audits or equipment efficiency (EgyptERA, Ministry
   of Industry programmes, IDA requirements).
6. Penetration of CMMS/maintenance software among Egyptian mid-size industry (`EST` fine).

## 5. Required output format

**A. One summary table, exactly these columns, one row per sector key** (this table will be
machine-read — keep it clean, numbers only, `EST:` prefix where estimated):

```text
| key | establishments_total | establishments_15plus_machines | energy_share_of_opex_pct | dominant_energy | top_3_governorates | attractiveness_1to5 |
```

**B. Per-sector narrative** (max ~200 words each) covering 3.1–3.4, with inline source
citations `[source, year]`.

**C. Cross-cutting answers** (section 4), numbered.

**D. Top-5 target ranking** — your ranked recommendation of which five sectors to pursue
first, one paragraph of justification each, explicitly weighing: number of reachable clients ×
energy pain × evidence they pay for advice.

**E. Source list** — every source used, with URL and year.

## 6. Source guidance

Prefer, in order: CAPMAS (الجهاز المركزي للتعبئة العامة والإحصاء), Ministry of Trade &
Industry / IDA, GAFI, Federation of Egyptian Industries chamber data, World Bank / IFC / EBRD /
UNIDO / GIZ programme documents, EgyptERA, credible trade press (Enterprise, Al Mal, Daily News
Egypt), then industry reports. Arabic sources are welcome; cite them in Arabic with an English
gloss. **Do not fabricate statistics.** A labelled estimate with stated reasoning beats an
unsourced number.

---
*Brief prepared for the EFF market study. Keys must match exactly — they map to the service's
sector library (`data/profiles.json`) and the results will be loaded into the pricing model.*

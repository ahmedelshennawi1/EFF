# Planning discussion — eff (Equipment Fitness Framework)

I'm launching a new company and want to think through the plan with you. Read the context
below, then engage as a **sceptical co-founder, not a cheerleader** — challenge the weak
parts and tell me what I'm not seeing. You can reply in Egyptian Arabic; I'm comfortable
in both.

---

## 1. What the company is

**eff — Equipment Fitness Framework.** A service that tells industrial and agricultural
operations in Egypt which of their machines to keep, monitor, budget for replacement, or
retire — and what each machine costs them in wasted energy **every day**.

It is a **new independent company**: not part of my existing feasibility-studies practice,
and not owned by any client.

Me: Ahmed Elshennawi, engineer in Egypt. Background in engineering design, feasibility
studies, and ERP. Network concentrated in the Delta (Dakahlia) poultry and agriculture world.

## 2. What the product actually does

From data the client already has (maintenance records, nameplates, fuel invoices), for each
machine:

1. **Fitness score 0–100** over eight weighted indicators — life consumption, reliability,
   efficiency degradation, capacity derating, maintenance-cost burden, physical condition,
   spare-parts supportability, safety/compliance. Verdict: Keep / Monitor / Plan replacement
   / Retire.
2. **Daily energy burn in EGP/day** — what it burns above what its work requires, split into
   *degradation* (maintenance's problem) and *misallocation* (operations' problem).
3. **Duty match** — is this the right size machine for the job? A 500 hp tractor on a
   spraying run scores perfectly healthy yet wastes EGP 86,746/year. The remedy is
   reassignment, not replacement — a saving with zero capital.
4. **Replacement economics** — whether replacing actually saves, on a differential basis
   with an explicit discount rate.
5. **CO2 from the same waste** — computed from the identical excess quantities, so carbon
   and cost can never diverge. Ties into EU CBAM / European buyer ESG demands.
6. **Data confidence** — below 60% coverage it issues **no verdict at all**, only a
   measurement plan. Deliberate, and often the most valuable finding in the first engagement.

## 3. Delivery model (already decided)

**Self-service. No site visits.** The client fills a bilingual data-collection sheet
themselves (2–3 hours per site), sends the file back, I run the analysis and present results.
This is the decision that makes it scalable — it sells the framework, not my calendar.

## 4. Pricing (provisional)

Built bottom-up from effort × EGP 13,000/day desk rate:

- Baseline assessment: **EGP 38,000** (≤25 machines) · **48,000** (26–60) · **69,000** (61–120)
- Annual monitoring retainer: **EGP 42,000 / 78,000 / 130,000** by fleet size
- Add-ons: guided fill-in session 6,500 · data entry 350/asset · optional site visit 18,000/day

Benchmark: typical Egyptian industrial energy audits run EGP 50,000–150,000. I undercut the
floor while carrying no travel cost.

## 5. Market (researched; counts are estimates)

~**6,750** Egyptian companies fit the profile (15+ substantial machines, heavy energy bill,
too small for GE/IBM-class asset-performance platforms, decisions made by gut feel today).
Ranked by targets × energy pain × evidence they pay for advice:

1. **Poultry** — 800 targets, energy ~30% of opex, near-identical fleets farm to farm
2. **Food processing** — 1,200 targets, strongest buying signals (EU retailer ESG, EBRD/UNIDO money)
3. Textiles · building materials (45% energy share + EU CBAM) · cold chain (40% energy share)

**Beachhead: poultry in the Delta**, where my name already opens doors.

**The binding constraint:** at ~4 delivery days per client and ~180 delivery days a year, one
person tops out near **45 clients/year ≈ EGP 4M revenue**. Demand isn't the constraint —
delivery is.

## 6. Where I am today

- **Engine built and tested** — Python, 51 passing tests. Machinery library of 48 equipment
  classes across 11 sectors, extensible from a data file without touching code.
- **Client-facing materials done** — bilingual (Arabic/English) data-collection sheet,
  service offer with pricing, executive brief, 10-slide pitch deck, live dashboard, brand system.
- **Immediate next step: a free pilot with Dakahlia Group** — one of Egypt's top-3 poultry
  producers (~30% of locally bred poultry, exports to 43+ countries), family-owned; the CEO is
  my cousin. Free in exchange for the right to cite them as the first applied reference.
  The brief is written and ready to submit.

## 7. What I want to think through

1. **Company formation** — legal structure in Egypt, licensing, what to register as, and
   timing relative to the pilot. Do I need the entity before the pilot or after?
2. **Does the pricing hold?** Too cheap for the value? Should the *monitoring retainer* be the
   real product and the assessment a loss-leader that buys the relationship?
3. **Pilot → paying clients.** How do I convert one reference into the first five paying
   customers? What specifically happens in weeks 1–12 after the pilot report lands?
4. **The capacity ceiling.** Hire and train, license the method to partners, or turn it into
   software? What signal tells me it's time, and what do I do *now* to keep that door open?
5. **The risk I might be avoiding.** What if the pilot shows my thresholds are miscalibrated,
   or the client's records are so thin that most machines come back "insufficient data"? Is
   that a failure or a product?
6. **The partnership question.** My cousin (the CEO of the pilot client) could be an investor
   or partner. Should I offer that, when, and on what terms — or does taking money from the
   first reference client compromise the independence the whole method is sold on?

## 8. How I want you to engage

Be a sceptical co-founder. Where my reasoning is weak, say so plainly rather than validating
it. Prioritise ruthlessly: tell me the **two or three things that actually matter in the next
90 days** and why everything else can wait. Ask me for facts you need that I haven't given —
don't fill gaps with assumptions.

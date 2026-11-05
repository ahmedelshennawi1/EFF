# EFF Enterprise & Internal Operations Guide

This document details the internal architecture, operations crew, autonomous agents, and marketing workflows that power the EFF service business.

---

## 1. Multi-Agent Autonomous Workforce (`eff_agents/`)

EFF includes a specialized CrewAI multi-agent organization designed to automate enterprise workflows:

```
eff_agents/
├── sales_crew.py       # B2B Lead generation & Facility Management outreach
├── marketing_crew.py   # Value proposition & industrial content creation
├── data_ops_crew.py    # Fleet asset ingestion, sanitization & anomaly triage
├── support_crew.py     # Onboarding support & client advisory synthesis
└── __init__.py
```

### Running the Multi-Agent Crew

```bash
# Install agent dependencies
pip install -r requirements-agents.txt

# Run sales orchestrator
python run_agents.py

# Run full company autonomous pipeline
python run_company.py
```

---

## 2. Marketing & Client Outreach Suite (`marketing/`)

The `marketing/` directory holds production-ready sales collateral, high-resolution visual guides, and outreach templates:

* **Cold Outreach Playbooks (`Cold-Emails-FM.md`)**:
  * Targeted value-driven pitches tailored for top Egyptian Facility Management and real estate operators (EFS Egypt, Contrack FM, Smart Villages, Savills, Enova).
* **Corporate Structure & Org Chart (`EFF-Org-Chart-A0.html`)**:
  * Interactive A0-scale architectural visualization of EFF's organizational units, agents, and client data flows.
* **Print & Pitch Collateral**:
  * `EFF-Brochure-Print.html` & `EFF-Brochure.html`: Two-page executive summary.
  * `EFF-DataKit-Print.html`: Physical onboarding questionnaire.
  * `EFF-Portfolio-Print.html`: Asset audit catalog.
  * `EFF-Pilot-Overview.html`: 14-day 5-machine proof-of-concept proposal.

---

## 3. Data Integration & Pipeline Flow

1. **Client Self-Service**:
   * Client fills `datakit.html` or physical form.
2. **Master Asset Register**:
   * Master fleet data is curated via Google Sheets.
   * `tools/sheet2csv.py` converts the synced table into `data/assets.csv`.
3. **Execution**:
   * Run `python cli.py --html out/report.html` to generate the decision-grade branded client assessment.

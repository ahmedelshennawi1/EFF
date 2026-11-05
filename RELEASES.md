# EFF GitHub Releases Guide

This document contains the official release notes and instructions for publishing releases on GitHub.

---

## 1. Customer & Public Release: `v1.0.0`

**Tag:** `v1.0.0`  
**Release Title:** `v1.0.0 — Equipment Fitness Framework (Web Platform & Core Engine)`  
**Target:** `webapp-ui`  
**Audience:** Clients, Plant Managers, Chief Engineers, External Partners, Evaluators.

### Description / Release Notes:
```markdown
# EFF v1.0.0 — Client Web Platform & Core Evaluation Engine

We are pleased to announce the official v1.0.0 release of **eff** (Equipment Fitness Framework) — a scored, auditable engineering framework that answers:
> *"Should this machine stay in service, be watched, be budgeted for replacement, or be retired now?"*

### 🌐 Live Interactive Platform (GitHub Pages)
Explore the live platform directly in your browser:
* **Home / Portal:** https://ahmedelshennawi1.github.io/EFF/
* **Interactive Fleet Dashboard:** https://ahmedelshennawi1.github.io/EFF/dashboard.html
* **Executive Booklet (العربية):** https://ahmedelshennawi1.github.io/EFF/booklet-ar.html
* **Executive Booklet (English):** https://ahmedelshennawi1.github.io/EFF/booklet-en.html
* **Field Measurement Guide:** https://ahmedelshennawi1.github.io/EFF/guide.html
* **Data Collection Kit:** https://ahmedelshennawi1.github.io/EFF/datakit.html
* **Pricing Calculator:** https://ahmedelshennawi1.github.io/EFF/pricing.html
* **Client Feedback:** https://ahmedelshennawi1.github.io/EFF/feedback.html

### ⚙️ Core Engine Features
* **Pure Python Standard Library:** Zero third-party dependencies required.
* **8 Weighted Degradation Indicators:** Age, Reliability, Efficiency, Capacity Derating, Maintenance Cost, Physical Condition, Supportability, and Safety Compliance.
* **Load-Corrected Efficiency:** Corrects nameplate fuel and power baselines for actual operating loads.
* **Differential Economics:** Compares Equivalent Annual Cost (EAC) of replacement against the cost of keeping, charging only excess energy and downtime.
* **Data Honesty:** Missing data reduces confidence rather than inflating scores. Below 60% confidence reports *Insufficient data*.
* **63 Unit Tests:** 100% green test coverage verifying mathematical and physical accuracy.

### 🚀 Quick Start
```bash
git clone https://github.com/ahmedelshennawi1/EFF.git
cd EFF
python cli.py
python tests/test_eff.py
```
```

---

## 2. Internal Enterprise Release: `v1.0.0-internal`

**Tag:** `v1.0.0-internal`  
**Release Title:** `v1.0.0-internal — Enterprise & Internal Operations Toolkit`  
**Target:** `webapp-ui`  
**Audience:** Internal Operations, Business Development, Engineering Lead.

### Description / Release Notes:
```markdown
# EFF v1.0.0-internal — Enterprise Operations & Autonomous Multi-Agent Workforce

This release bundles the complete internal operational infrastructure of EFF, including autonomous multi-agent crews for business development, marketing playbooks, and organizational models.

### 🤖 Autonomous Multi-Agent Workforce (`eff_agents/`)
Powered by CrewAI and LLM orchestrators:
* **`sales_crew.py`:** B2B lead generation, plant targeting, and Facility Management campaign generation.
* **`marketing_crew.py`:** Value messaging, industrial copy generation, and case study synthesis.
* **`data_ops_crew.py`:** Automated fleet intake, schema verification, and unit slip triage.
* **`support_crew.py`:** Client advisory reports and inquiry assistance.
* **Runners:** `run_agents.py` and `run_company.py`.

### 📊 B2B Sales & Marketing Suite (`marketing/`)
* **Cold Outreach Playbooks:** Tailored campaigns for Egyptian Facility Management leaders (EFS, Contrack FM, Smart Villages, Savills, Enova).
* **EFF Organization Chart (`EFF-Org-Chart-A0.html`):** Interactive A0-scale diagram of business and agent operations.
* **Client Print Collateral:** Print-ready brochures, portfolio catalogs, pilot 5-machine audit agreements, and business cards.

### 🛠️ Internal Setup
```bash
pip install -r requirements-agents.txt
python run_agents.py
```
```

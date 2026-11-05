# Changelog

All notable changes to the **EFF (Equipment Fitness Framework)** project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0-internal] - 2026-11-05
### Added (Internal Enterprise & Operations Stack)
* **Autonomous Multi-Agent Crew (`eff_agents/`)**:
  * `sales_crew.py`: Facility Management and industrial plant B2B outreach engine.
  * `marketing_crew.py`: Value proposition generation and industrial messaging.
  * `data_ops_crew.py`: Fleet asset validation and unit slip triage.
  * `support_crew.py`: Advisory report synthesis and client query handling.
* **Orchestration Scripts**:
  * `run_agents.py`: Command-line driver for executing target company sales cycles.
  * `run_company.py`: Autonomous company lifecycle runner coordinating all crews.
  * `requirements-agents.txt`: Dependency specification for CrewAI and LLM integrations.
* **Enterprise Marketing & Sales Suite (`marketing/`)**:
  * `Cold-Emails-FM.md`: Segmented email campaigns for Egyptian FM leaders (EFS, Contrack, Smart Villages, etc.).
  * `EFF-Org-Chart-A0.html`: High-resolution interactive A0 corporate operational diagram.
  * `docs/INTERNAL.md`: Architectural manual for internal teams.

---

## [1.0.0] - 2026-11-05
### Added (Customer & Core Framework Release)
* **Core Evaluation Engine (`eff/`)**:
  * Pure Python 3 standard library calculation engine (zero third-party dependencies).
  * 8 weighted degradation indicators: Life consumption (AGE), Reliability, Efficiency, Capacity derating, Maintenance cost burden, Physical condition, Supportability, and Safety compliance.
  * Load-corrected baseline adjustments for partial engine/compressor loading.
  * Differential economics: Equivalent Annual Cost (EAC) comparison charging only excess downtime and energy penalty.
  * Non-negotiable data honesty: unmeasured indicators lower confidence rather than scoring zero; below 60% confidence reports "Insufficient data".
  * Automated input integrity checks: Cross-reconciliation of `annual_output_total` vs `rated_output × run_hours` detecting unit slips.
  * 63 comprehensive unit tests passing with 100% green status.
* **Client Web Platform (Bilingual Arabic/English)**:
  * `index.html`: Responsive landing page with light aesthetic and PWA capabilities.
  * `dashboard.html`: Interactive client fleet dashboard for real-time asset evaluation.
  * `booklet-ar.html` & `booklet-en.html`: Executive technical booklets detailing the engineering framework.
  * `guide.html`: Comprehensive field measurement and sensor data acquisition guide.
  * `pricing.html`: Interactive pricing calculator for assessment packages and retainers.
  * `datakit.html`: Self-service equipment data collection form and CSV exporter.
  * `feedback.html`: Client satisfaction questionnaire.
  * PWA support: Web manifest (`manifest.json`), service worker (`sw.js`), and SVG icon (`icon.svg`).
* **CI/CD & Repository Health**:
  * GitHub Pages automated deployment workflow (`.github/workflows/deploy-pages.yml`).
  * Cross-platform Python CI test runner across Python 3.10, 3.11, 3.12 (`.github/workflows/ci.yml`).
  * Standard GitHub community files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `LICENSE` (MIT), Issue & PR templates.

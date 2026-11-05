# Contributing to EFF (Equipment Fitness Framework)

Thank you for your interest in contributing to **eff**! This project is an independent engineering venture delivering a scored, auditable evaluation framework for industrial machinery.

---

## Core Engineering Principles (Non-Negotiable)

These rules are central to the integrity of EFF's decisions and must never be broken:

1. **Standard Library Only for Core Engine**:
   * The `eff/` package and `cli.py` run on pure Python standard library. No third-party dependencies may be added to the core scoring engine.
2. **Missing Data is Never Scored as Zero**:
   * If a parameter is unmeasured, it is excluded and its weight redistributed. Never zero-fill unmeasured indicators.
   * If overall data confidence is below 60%, no verdict is issued; the report outputs **Insufficient data**, never *Keep*.
3. **Differential Economics**:
   * The economic model calculates *excess* wear and *excess* downtime compared to a new unit, not absolute costs.
   * Economics can recommend budgeting (`PLAN_REPLACEMENT`), never forced retirement (`RETIRE_NOW`). Physical condition, safety, or score evidence is mandatory for retirement.
4. **Overrides are Floors**:
   * Safety or regulatory overrides can only escalate a verdict severity, never relax or demote it.
5. **Client-Extensible Machinery Profiles**:
   * Machinery curves, thresholds, and sector archetypes reside in `data/profiles.json`. Never hardcode machine classes directly in Python code.

---

## Development Workflow

### 1. Requirements
* Python 3.10+ (Standard library)
* Modern web browser for testing HTML interfaces

### 2. Running Tests
Before opening a pull request or submitting code, ensure all 63 unit tests pass:

```bash
python tests/test_eff.py
```

To validate machinery profile JSON files:

```bash
python cli.py --check-library
```

### 3. Adding New Machinery Classes
When adding new equipment classes or sectors:
1. Update `data/profiles.json` following the schema of existing classes.
2. Provide both English (`label`) and authentic industry Arabic (`label_ar`) terms.
3. Verify that `python cli.py --check-library` and `python tests/test_eff.py` remain green.

---

## Submitting Pull Requests

1. Fork or branch from `webapp-ui`.
2. Follow PEP 8 guidelines for Python code.
3. Write clean, self-contained tests for any new logic or calculation curves.
4. Update relevant documentation in `docs/` or `README.md`.
5. Submit a pull request with a clear description of the problem solved and test verification output.

---

## Questions and Support

Open an issue in the GitHub repository or contact the maintainer at **ahmedelshennawi1**.

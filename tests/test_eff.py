"""Tests for the scoring, banding and economics logic.

Run:  python -m pytest tests -q      (or)      python tests/test_eff.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eff.economics import assess as econ_assess, crf
from eff.loader import load_assets
from eff.models import Asset
from eff.scoring import (
    interp, life_ratio, score_age, score_capacity, score_compliance,
    score_condition, score_efficiency, score_maint_cost, score_reliability,
    AGE_CURVE,
)
from eff.profiles import INDICATORS
from eff.verdict import assess, band_for_score


# --- curve interpolation -------------------------------------------------

def test_interp_clamps_and_interpolates():
    assert interp(0.0, AGE_CURVE) == 0
    assert interp(-5, AGE_CURVE) == 0            # clamped low
    assert interp(99, AGE_CURVE) == 100          # clamped high
    assert interp(0.25, AGE_CURVE) == 5.0        # midway between (0,0) and (0.5,10)
    assert interp(None, AGE_CURVE) is None


# --- individual indicators -----------------------------------------------

def test_life_ratio_takes_the_worse_of_hours_and_calendar():
    # 29k/30k hours = 0.967 beats the calendar view, so hours must win.
    a = Asset(asset_class="diesel_genset", run_hours=29000,
              design_life_hours=30000, commissioned_year=2022, design_life_years=20)
    assert abs(life_ratio(a) - 0.9667) < 0.001


def test_age_none_when_nothing_known():
    assert score_age(Asset()) is None


def test_efficiency_scores_degradation_not_absolute_consumption():
    good = Asset(specific_consumption=0.265, baseline_specific_consumption=0.265)
    bad = Asset(specific_consumption=0.318, baseline_specific_consumption=0.268)
    assert score_efficiency(good) == 0
    assert score_efficiency(bad) > 70
    # A machine running better than baseline must not be penalised.
    better = Asset(specific_consumption=0.25, baseline_specific_consumption=0.265)
    assert score_efficiency(better) == 0


def test_efficiency_needs_a_baseline():
    assert score_efficiency(Asset(specific_consumption=0.3)) is None


def test_condition_is_not_averaged_away_by_clean_checks():
    """One critical finding must dominate three normal ones."""
    a = Asset(vibration_zone="d", oil_analysis="normal",
              thermography="normal", insulation="good")
    # plain mean would be 23.75; worst-weighted must be far higher
    assert score_condition(a) > 60


def test_compliance_is_worst_of():
    a = Asset(safety_findings=0, emissions_status="non_compliant")
    assert score_compliance(a) == 90


def test_capacity_derating():
    a = Asset(rated_output=200, actual_output=168)  # 16% derate
    assert 40 < score_capacity(a) < 60


def test_maint_cost_uses_replacement_value_not_book_value():
    a = Asset(annual_maint_cost=310000, cumulative_maint_cost=1450000,
              replacement_value=2100000)
    assert score_maint_cost(a) > 60
    assert score_maint_cost(Asset(annual_maint_cost=310000)) is None


def test_reliability_excludes_planned_downtime_by_construction():
    a = Asset(annual_run_hours=3100, annual_downtime_hours=180, unplanned_failures_12m=7)
    assert score_reliability(a) > 50
    healthy = Asset(annual_run_hours=2600, annual_downtime_hours=22, unplanned_failures_12m=1)
    assert score_reliability(healthy) < 30


# --- weighting and confidence --------------------------------------------

def test_missing_data_lowers_confidence_and_does_not_score_zero():
    """A data-poor asset must not be flattered into a KEEP by its blanks."""
    sparse = Asset(asset_class="diesel_genset", commissioned_year=2014,
                   design_life_years=20, oem_support="supported", spare_lead_days=45)
    r = assess(sparse)
    assert r.confidence < 30
    assert not r.decision_grade
    assert "EFFICIENCY" in r.missing
    # Weight was redistributed across measured indicators, not zero-filled:
    # a zero-fill would have driven fitness toward 0.
    assert r.fitness > 0


def test_full_data_is_decision_grade():
    a = Asset(asset_class="diesel_genset", commissioned_year=2019, run_hours=12400,
              design_life_hours=30000, design_life_years=20, annual_run_hours=2600,
              annual_downtime_hours=22, unplanned_failures_12m=1,
              specific_consumption=0.272, baseline_specific_consumption=0.265,
              rated_output=400, actual_output=396, annual_maint_cost=62000,
              cumulative_maint_cost=210000, replacement_value=3800000,
              vibration_zone="a", oil_analysis="normal", thermography="normal",
              insulation="good", oem_support="supported", spare_lead_days=21,
              safety_findings=0, emissions_status="compliant")
    r = assess(a)
    assert r.confidence == 100
    assert r.band == "KEEP"


# --- banding and overrides -----------------------------------------------

def test_band_thresholds():
    assert band_for_score(0) == "KEEP"
    assert band_for_score(24.9) == "KEEP"
    assert band_for_score(25) == "MONITOR"
    assert band_for_score(44.9) == "MONITOR"
    assert band_for_score(45) == "PLAN_REPLACEMENT"
    assert band_for_score(65) == "RETIRE_NOW"
    assert band_for_score(100) == "RETIRE_NOW"


def test_safety_finding_overrides_an_otherwise_healthy_asset():
    a = Asset(asset_class="compressor", commissioned_year=2024, design_life_years=15,
              vibration_zone="a", safety_findings=1)
    r = assess(a)
    assert r.raw_band != "RETIRE_NOW"      # scored fine
    assert r.band == "RETIRE_NOW"          # overridden anyway
    assert any("safety" in n for n in r.overrides)


def test_cumulative_spend_over_replacement_value_forces_retire():
    a = Asset(cumulative_maint_cost=1200000, replacement_value=1000000)
    assert assess(a).band == "RETIRE_NOW"


def test_overrides_never_lower_a_band():
    """An override is a floor, not an assignment."""
    a = Asset(asset_class="production_machine", commissioned_year=1998,
              design_life_years=15, annual_run_hours=4000, annual_downtime_hours=900,
              unplanned_failures_12m=20, vibration_zone="d")
    r = assess(a)
    assert r.raw_band == "RETIRE_NOW"
    assert r.band == "RETIRE_NOW"          # zone D floor is PLAN_REPLACEMENT, must not demote


# --- economics -----------------------------------------------------------

def test_crf_matches_hand_calculation():
    assert abs(crf(0.22, 20) - 0.22431) < 0.0005
    assert abs(crf(0.0, 10) - 0.1) < 1e-9


def test_economics_unavailable_without_a_replacement_quote():
    e = econ_assess(Asset(), rate=0.22)
    assert not e.available
    assert "new_unit_capital" in e.reason


def test_energy_penalty_is_differential_and_never_negative():
    a = Asset(new_unit_capital=1000000, new_unit_life_years=15,
              annual_output_total=100000, energy_price=2.0,
              specific_consumption=0.5, new_unit_specific_consumption=0.6)
    e = econ_assess(a, rate=0.22)
    assert e.energy_penalty == 0          # old unit beats the new one: no penalty

    b = Asset(new_unit_capital=1000000, new_unit_life_years=15,
              annual_output_total=100000, energy_price=2.0,
              specific_consumption=0.6, new_unit_specific_consumption=0.5)
    e2 = econ_assess(b, rate=0.22)
    assert abs(e2.energy_penalty - 20000) < 1e-6   # 100000 * 0.1 * 2.0


def test_only_excess_downtime_is_charged_to_keeping():
    """A new unit fails sometimes too — charging it all biases every asset to replace."""
    a = Asset(new_unit_capital=1000000, new_unit_life_years=15,
              annual_run_hours=1000, annual_downtime_hours=15,
              downtime_cost_per_hour=1000)
    e = econ_assess(a, rate=0.22, benchmark_unavailability=0.02)  # 20 h allowance
    assert e.excess_downtime_hours == 0
    assert e.downtime_term == 0

    b = Asset(new_unit_capital=1000000, new_unit_life_years=15,
              annual_run_hours=1000, annual_downtime_hours=50,
              downtime_cost_per_hour=1000)
    e2 = econ_assess(b, rate=0.22, benchmark_unavailability=0.02)
    assert e2.excess_downtime_hours == 30
    assert e2.downtime_term == 30000


def test_marginal_economic_win_does_not_escalate():
    """Inside the materiality band the result is a tie, and a tie moves nothing."""
    a = Asset(new_unit_capital=1000000, new_unit_life_years=15,
              annual_maint_cost=250000, replacement_value=5000000)
    e = econ_assess(a, rate=0.22, materiality=0.15)
    # keep = 250,000 vs EAC_new = 231,700 -> ahead, but only by ~8%
    assert e.marginal_keep > e.eac_new
    assert not e.replace_favoured


def test_economics_never_escalates_past_plan_replacement():
    """Economics says 'budget for it', never 'stop running a sound machine'."""
    mild = Asset(asset_class="pump", commissioned_year=2014, design_life_years=15,
                 annual_run_hours=4000, annual_downtime_hours=200,
                 unplanned_failures_12m=2, downtime_cost_per_hour=5000,
                 new_unit_capital=200000, new_unit_life_years=15)
    r = assess(mild)
    assert r.economics.replace_favoured
    assert r.raw_band == "MONITOR"
    assert r.band == "PLAN_REPLACEMENT"      # escalated exactly one band

    # Already at PLAN_REPLACEMENT on score alone: economics must not push to RETIRE.
    worse = Asset(asset_class="pump", commissioned_year=2015, design_life_years=15,
                  annual_run_hours=4000, annual_downtime_hours=900,
                  unplanned_failures_12m=8, downtime_cost_per_hour=5000,
                  new_unit_capital=200000, new_unit_life_years=15)
    r2 = assess(worse)
    assert r2.economics.replace_favoured
    assert r2.raw_band == "PLAN_REPLACEMENT"
    assert r2.band == "PLAN_REPLACEMENT"


def test_failing_economics_escalates_the_band():
    """Heavy running cost on a physically sound machine still escalates."""
    a = Asset(asset_class="chiller", commissioned_year=2021, design_life_years=20,
              vibration_zone="a", oil_analysis="normal",
              annual_maint_cost=900000, replacement_value=9000000,
              salvage_value=200000, new_unit_capital=1000000, new_unit_life_years=20)
    r = assess(a)
    assert r.economics.replace_favoured
    assert r.band != r.raw_band
    assert any("economic" in n for n in r.overrides)


def test_efficiency_baseline_is_corrected_for_load():
    """A genset measured at low load must be judged against a low-load baseline."""
    from eff.scoring import corrected_baseline
    full = Asset(asset_class="diesel_genset", baseline_specific_consumption=0.265,
                 load_factor=1.0)
    light = Asset(asset_class="diesel_genset", baseline_specific_consumption=0.265,
                  load_factor=0.25)
    assert corrected_baseline(full) == 0.265
    assert corrected_baseline(light) > 0.31          # penalised baseline at 25% load

    # Uncorrected, a lightly-loaded but healthy genset looks badly degraded.
    a = Asset(asset_class="diesel_genset", specific_consumption=0.33,
              baseline_specific_consumption=0.265, load_factor=0.25)
    assert score_efficiency(a) < 25                  # correctly absolved
    b = Asset(asset_class="diesel_genset", specific_consumption=0.33,
              baseline_specific_consumption=0.265, load_factor=1.0)
    assert score_efficiency(b) > 70                  # same reading at full load is real


def test_no_load_curve_means_no_correction():
    """Classes without a part-load curve are left alone, not given a borrowed one."""
    from eff.scoring import corrected_baseline
    from eff.profiles import part_load_curve
    assert part_load_curve("hammer_mill") is None       # line_critical has no curve
    a = Asset(asset_class="hammer_mill", baseline_specific_consumption=0.58, load_factor=0.25)
    assert corrected_baseline(a) == 0.58


def test_underloaded_genset_is_flagged_as_a_sizing_fault():
    from eff.validate import advisories
    a = Asset(asset_class="diesel_genset", load_factor=0.18)
    assert any("under-loaded" in n for n in advisories(a))
    ok = Asset(asset_class="diesel_genset", load_factor=0.75)
    assert not any("under-loaded" in n for n in advisories(ok))


def test_output_consistency_catches_unit_slips():
    from eff.validate import check_output
    good = Asset(output_unit="m3/h", consumption_unit="kWh/m3", actual_output=268,
                 annual_run_hours=3400, annual_output_total=911200)
    assert check_output(good) is None

    thousandfold = Asset(output_unit="m3/h", consumption_unit="kWh/m3", actual_output=268,
                         annual_run_hours=3400, annual_output_total=911200000)
    assert "too large" in check_output(thousandfold)

    per_minute = Asset(output_unit="m3/min", consumption_unit="kWh/m3", actual_output=5.2,
                       annual_run_hours=3900, annual_output_total=20280)
    assert "too small" in check_output(per_minute)


def test_output_check_reconciles_unit_scales_within_a_family():
    """kg/h rate vs ton totals, m3/h rate vs 1000m3 totals — standard pairings."""
    from eff.validate import check_output, implied_annual_output
    boiler = Asset(output_unit="kg/h", consumption_unit="m3/ton_steam",
                   rated_output=2000, actual_output=1720, load_factor=0.62,
                   annual_run_hours=5200, annual_output_total=6448)
    assert abs(implied_annual_output(boiler) - 6448) < 1        # kg -> tons
    assert check_output(boiler) is None

    fan = Asset(output_unit="m3/h", consumption_unit="kWh/1000m3",
                actual_output=31500, annual_run_hours=7100,
                annual_output_total=223650)
    assert abs(implied_annual_output(fan) - 223650) < 1         # m3 -> 1000m3
    assert check_output(fan) is None

    # Families never cross: a kW rate must not be "converted" into tons.
    mixed = Asset(output_unit="kW", consumption_unit="fuel/ton",
                  rated_output=400, load_factor=0.75, annual_run_hours=2600)
    assert implied_annual_output(mixed) == 400 * 0.75 * 2600    # unscaled


def test_output_check_uses_load_factor_and_handles_per_hour_denominators():
    from eff.validate import implied_annual_output
    # Rated output at the recorded load factor, not flat out.
    genset = Asset(output_unit="kW", consumption_unit="L/kWh", rated_output=400,
                   actual_output=396, load_factor=0.75, annual_run_hours=2600)
    assert implied_annual_output(genset) == 780000

    # L/h means the denominator IS run-hours; there is no rate to derive from.
    forklift = Asset(output_unit="kg", consumption_unit="L/h", rated_output=2500,
                     annual_run_hours=1850)
    assert implied_annual_output(forklift) == 1850


def test_sample_fleet_has_no_false_output_warnings():
    """Correct data must stay quiet, or the advisories become noise people ignore."""
    from eff.validate import check_output
    assets = load_assets(Path(__file__).resolve().parent.parent / "data" / "assets.csv")
    assert all(check_output(a) is None for a in assets)


# --- machinery library ---------------------------------------------------

def test_shipped_library_is_valid():
    """The library ships as a product surface — a broken one must fail loudly."""
    from eff.profiles import load_library
    lib = load_library(strict=False)
    assert lib.validate() == []
    assert len(lib.classes) > 30
    assert len(lib.sectors) >= 10


def test_library_rejects_bad_extensions():
    """A client editing profiles.json must be told exactly what they broke."""
    from eff.profiles import Library, LibraryError
    base = {"default_class": "x", "curves": {"c": [[0, 1], [1, 1]]},
            "archetypes": {"a": {"weights": {k: 12.5 for k in INDICATORS},
                                 "design_life": {"years": 10}}},
            "classes": {"x": {"archetype": "a"}}, "sectors": {}}
    assert Library(dict(base)).validate() == []

    bad_weights = json.loads(json.dumps(base))
    bad_weights["archetypes"]["a"]["weights"]["AGE"] = 40      # now totals 127.5
    assert any("not 100" in p for p in Library(bad_weights).validate())

    bad_sector = json.loads(json.dumps(base))
    bad_sector["sectors"] = {"s": {"classes": ["nope"]}}
    assert any("not defined" in p for p in Library(bad_sector).validate())

    bad_curve = json.loads(json.dumps(base))
    bad_curve["classes"]["x"]["curve"] = "missing"
    assert any("unknown curve" in p for p in Library(bad_curve).validate())

    bad_arch = json.loads(json.dumps(base))
    bad_arch["classes"]["x"]["archetype"] = "ghost"
    try:
        Library(bad_arch)
        assert False, "should have raised on unknown archetype"
    except LibraryError as e:
        assert "ghost" in str(e)


def test_class_inherits_archetype_but_can_override():
    from eff.profiles import library
    lib = library()
    # pellet_mill takes line_critical weights untouched
    assert lib.weights_for("pellet_mill") == lib.archetypes["line_critical"]["weights"]
    # diesel_genset overrides its fuel_burning parent
    assert lib.weights_for("diesel_genset") != lib.archetypes["fuel_burning"]["weights"]
    assert lib.weights_for("diesel_genset")["EFFICIENCY"] == 25


def test_unknown_class_falls_back_and_says_so():
    a = Asset(asset_class="something_we_never_heard_of", commissioned_year=2015,
              design_life_years=15)
    r = assess(a)
    assert r.unknown_class
    assert any("not in the machinery library" in n for n in r.advisories)
    assert r.fitness > 0          # still scored, on generic weights


def test_datakit_matches_the_machinery_library():
    """The client-facing form inlines its own copy of the class list; if it drifts
    from the library, a client fills in a machine the engine cannot score."""
    import re
    from eff.profiles import library
    lib = library()
    kit_path = Path(__file__).resolve().parent.parent / "offer" / "EFF-DataKit.html"
    kit = kit_path.read_text(encoding="utf-8")
    block = kit.split("var CLASSES = {", 1)[1].split("\n};", 1)[0]
    kit_classes = dict(re.findall(r'^\s*([a-z_]+):\["([^"]+)"', block, re.M))

    assert set(kit_classes) == set(lib.classes), (
        f"missing from kit: {sorted(set(lib.classes) - set(kit_classes))}; "
        f"unknown in kit: {sorted(set(kit_classes) - set(lib.classes))}")
    for key, ar in kit_classes.items():
        assert ar == lib.classes[key]["label_ar"], (
            f"{key}: kit says {ar!r}, library says {lib.classes[key]['label_ar']!r}")

    # Sector lists must agree too, or the checklist offers the wrong machines.
    sectors = dict(re.findall(r'^\s*([a-z_]+):\["[^"]+","[^"]+",\[([^\]]*)\]',
                              kit.split("var SECTORS = {", 1)[1].split("\n};", 1)[0], re.M))
    assert set(sectors) == set(lib.sectors)
    for key, raw in sectors.items():
        kit_list = re.findall(r'"([a-z_]+)"', raw)
        assert kit_list == lib.sectors[key]["classes"], f"sector {key} differs"


def test_sector_checklist_is_usable():
    from eff.profiles import library
    rows = library().sector_checklist("poultry")
    keys = [r["class"] for r in rows]
    assert "space_heater" in keys and "ventilation_fan" in keys
    assert all(r["label_ar"] for r in rows)     # Arabic labels present for reports
    try:
        library().sector_checklist("atlantis")
        assert False, "unknown sector should raise"
    except KeyError as e:
        assert "atlantis" in str(e)


# --- duty matching -------------------------------------------------------

def test_oversized_tractor_scores_fit_but_is_flagged_misallocated():
    """The whole point: a misallocated machine is not a worn machine."""
    from eff.duty import assess as duty_assess
    t = Asset(asset_class="tractor", commissioned_year=2019, run_hours=4200,
              annual_run_hours=520, rated_output=373, output_unit="kW",
              duty_task="spraying", duty_power_required=60,
              baseline_specific_consumption=0.25, energy_price=15.5)
    d = duty_assess(t)
    assert d.available and d.verdict == "severely_oversized"
    assert 0.15 < d.ratio < 0.17
    assert d.annual_excess_cost > 50000
    assert 70 < d.recommended_rating < 80

    r = assess(t)
    assert r.band == "KEEP"                    # the machine itself is sound
    assert any("oversized" in n for n in r.advisories)


def test_duty_match_is_quiet_when_correctly_sized():
    from eff.duty import assess as duty_assess
    a = Asset(asset_class="diesel_genset", rated_output=400, duty_power_required=320,
              baseline_specific_consumption=0.265, annual_run_hours=2000, energy_price=15.5)
    d = duty_assess(a)
    assert d.verdict == "matched"
    assert not d.is_mismatched
    assert assess(a).advisories == [] or all("oversized" not in n
                                             for n in assess(a).advisories)


def test_undersized_machine_is_flagged_without_a_fuel_penalty():
    """Overworked equipment wears faster; it does not burn excess fuel."""
    from eff.duty import assess as duty_assess, describe
    a = Asset(asset_class="pump", rated_output=100, duty_power_required=130,
              baseline_specific_consumption=0.5, annual_run_hours=3000, energy_price=2.15)
    d = duty_assess(a)
    assert d.verdict == "undersized"
    assert d.annual_excess_cost is None
    assert "overworked" in describe(d)


def test_duty_match_skipped_for_classes_where_it_is_meaningless():
    from eff.duty import assess as duty_assess
    d = duty_assess(Asset(asset_class="belt_conveyor", rated_output=50,
                          duty_power_required=10))
    assert not d.available
    assert "does not apply" in d.reason


# --- energy burn ---------------------------------------------------------

def test_burn_decomposition_partitions_the_total_gap():
    """wear + allocation must equal actual-vs-ideal exactly — no double counting."""
    from eff.energy import assess as energy_assess
    from eff.profiles import library
    a = Asset(asset_class="diesel_genset", specific_consumption=0.40,
              baseline_specific_consumption=0.265, load_factor=0.22,
              annual_output_total=27720, energy_price=15.5)
    b = energy_assess(a)
    assert b.available and b.basis == "baseline"
    total_direct = max(0.0, b.sec_actual - b.sec_ideal) * 27720 * 15.5 / 365
    assert abs((b.wear_per_day + b.allocation_per_day) - total_direct) < 1e-6
    assert b.wear_per_day > 0 and b.allocation_per_day > 0


def test_healthy_well_loaded_machine_burns_nothing():
    from eff.energy import assess as energy_assess
    a = Asset(asset_class="diesel_genset", specific_consumption=0.262,
              baseline_specific_consumption=0.265, load_factor=0.80,
              annual_output_total=780000, energy_price=15.5)
    b = energy_assess(a)
    assert b.available
    assert b.total_per_day < 1


def test_benchmark_fallback_is_marked_indicative():
    """No baseline: judged against the class benchmark, flagged as indicative."""
    from eff.energy import assess as energy_assess
    a = Asset(asset_class="air_compressor", specific_consumption=0.20,
              annual_output_total=1216800, energy_price=2.15)
    b = energy_assess(a)
    assert b.available and b.basis == "benchmark" and b.indicative
    assert b.wear_per_day > 0            # 0.20 vs benchmark high 0.14

    within = Asset(asset_class="air_compressor", specific_consumption=0.12,
                   annual_output_total=1216800, energy_price=2.15)
    b2 = energy_assess(within)
    assert b2.available and b2.total_per_day == 0   # inside the range: silent


def test_no_benchmark_class_reports_why_not():
    from eff.energy import assess as energy_assess
    a = Asset(asset_class="pump", specific_consumption=0.68,
              annual_output_total=911200, energy_price=2.15)
    b = energy_assess(a)
    assert not b.available
    assert "benchmark" in b.reason


def test_low_power_factor_is_flagged():
    from eff.energy import advisories as en_adv, assess as energy_assess
    a = Asset(asset_class="hammer_mill", power_factor=0.82)
    notes = en_adv(a, energy_assess(a))
    assert any("power factor" in n for n in notes)
    ok = Asset(asset_class="hammer_mill", power_factor=0.95)
    assert not any("power factor" in n for n in en_adv(ok, energy_assess(ok)))


def test_burn_appears_in_assessment_advisories():
    a = Asset(asset_class="diesel_genset", specific_consumption=0.361,
              baseline_specific_consumption=0.268, load_factor=0.22,
              annual_output_total=27720, energy_price=15.5,
              commissioned_year=2018, design_life_years=20)
    r = assess(a)
    assert r.energy.available
    assert any("per day" in n for n in r.advisories)


def test_emissions_derive_from_the_same_excess_as_the_money():
    """Carbon and cost must be two readings of one measurement, never independent."""
    from eff.emissions import assess as em_assess
    from eff.energy import assess as en_assess
    a = Asset(asset_class="diesel_genset", specific_consumption=0.40,
              baseline_specific_consumption=0.265, load_factor=0.22,
              annual_output_total=27720, energy_price=15.5,
              consumption_unit="L/kWh", energy_source="diesel")
    b = en_assess(a)
    e = em_assess(a, b)
    assert e.available
    expected_litres = (b.sec_actual - b.sec_ideal) * 27720
    assert abs(e.excess_units_per_year - expected_litres) < 1e-6
    assert abs(e.kg_per_year - expected_litres * 2.68) < 1e-6
    # No waste, no emissions — they move together or not at all.
    clean = Asset(asset_class="diesel_genset", specific_consumption=0.262,
                  baseline_specific_consumption=0.265, load_factor=0.80,
                  annual_output_total=780000, energy_price=15.5,
                  consumption_unit="L/kWh", energy_source="diesel")
    assert em_assess(clean, en_assess(clean)).kg_per_year == 0


def test_emissions_refuse_mismatched_units():
    """A litre factor must never be applied to a kWh reading."""
    from eff.emissions import assess as em_assess
    from eff.energy import assess as en_assess
    a = Asset(asset_class="hammer_mill", specific_consumption=30,
              baseline_specific_consumption=20, annual_output_total=1000,
              energy_price=2.15, consumption_unit="kWh/ton", energy_source="diesel")
    e = em_assess(a, en_assess(a))
    assert not e.available and "do not match" in e.reason


def test_emissions_silent_without_an_energy_source():
    from eff.emissions import assess as em_assess
    from eff.energy import assess as en_assess
    a = Asset(asset_class="diesel_genset", specific_consumption=0.40,
              baseline_specific_consumption=0.265, load_factor=0.22,
              annual_output_total=27720, energy_price=15.5, consumption_unit="L/kWh")
    e = em_assess(a, en_assess(a))
    assert not e.available and "energy_source" in e.reason


# --- pricing criteria ----------------------------------------------------

def test_fee_is_computed_from_effort_not_looked_up():
    from eff.pricing import config, quote
    c = config()
    small, big = quote(assets=10), quote(assets=100)
    assert big.fee > small.fee
    # the difference is exactly the per-asset effort, priced
    extra_days = 90 * c["effort"]["per_asset_days"]
    assert abs((big.base_days - small.base_days) - extra_days) < 1e-9


def test_modifiers_multiply_and_are_itemised():
    from eff.pricing import quote
    plain = quote(assets=50)
    loaded = quote(assets=50, data_readiness="poor", urgency="expedited")
    assert abs(loaded.total_days - plain.base_days * 1.35 * 1.3) < 1e-9
    names = [n for n, _ in loaded.modifier_lines]
    assert any("poor" in n for n in names) and any("expedited" in n for n in names)
    assert plain.modifier_lines == []          # nothing shown when nothing applies


def test_founding_client_is_free_but_retainer_is_not():
    """A free pilot must not silently make the follow-on retainer free."""
    from eff.pricing import quote
    q = quote(assets=5, tier="proof_of_concept", founding_client=True)
    assert q.fee == 0
    assert q.retainer_per_year > 0
    assert any("Founding" in n for n in (n for n, _ in q.discount_lines))


def test_value_check_flags_both_directions():
    from eff.pricing import quote
    cheap = quote(assets=40, annual_energy_spend=50_000_000)
    dear = quote(assets=40, annual_energy_spend=500_000)
    assert cheap.value_ok is False and "underpriced" in cheap.value_note
    assert dear.value_ok is False and "resistance" in dear.value_note
    ok = quote(assets=40, annual_energy_spend=3_000_000)
    assert ok.value_ok is True


def test_pricing_rejects_bad_inputs():
    from eff.pricing import PricingError, quote
    for kwargs in ({"assets": 50, "tier": "nope"},
                   {"assets": 50, "data_readiness": "excellent"},
                   {"assets": -1},
                   {"assets": 20, "tier": "proof_of_concept"}):   # over the 5-asset cap
        try:
            quote(**kwargs)
            assert False, f"should have raised for {kwargs}"
        except PricingError:
            pass


# --- product carbon intensity --------------------------------------------

def test_region_scales_only_climate_tagged_inputs():
    from eff.product import assess, typical
    ins = typical("potatoes")
    delta = assess("potatoes", "delta", ins)
    valley = assess("potatoes", "new_valley", ins)
    by_key = lambda fp: {l.key: l for l in fp.lines}
    d, v = by_key(delta), by_key(valley)
    # irrigation is climate-tagged: the ideal moves
    assert v["irrigation_water_m3"].ideal_here > d["irrigation_water_m3"].ideal_here
    # freight is not: the ideal is identical
    assert v["road_freight_tkm"].ideal_here == d["road_freight_tkm"].ideal_here


def test_water_carbon_comes_from_the_lift():
    """Water carries no carbon; the pump does. Deeper lift, more carbon."""
    from eff.product import assess
    ins = {"irrigation_water_m3": 100}
    d = assess("potatoes", "delta", ins).lines[0]
    v = assess("potatoes", "new_valley", ins).lines[0]
    assert v.kg_actual > d.kg_actual * 4          # 65 m vs 12 m lift
    from eff.product import config
    c = config()
    expected = (100 * c["pump_kwh_per_m3_per_m"] * c["regions"]["delta"]["water_lift_m"]
                * c["emission_factors"]["electricity_kwh"])
    assert abs(d.kg_actual - expected) < 1e-9


def test_beating_the_ideal_never_offsets_another_line():
    from eff.product import assess
    fp = assess("potatoes", "delta",
                {"field_diesel_l": 5, "fertilizer_n_kg": 20})   # one great, one awful
    diesel = [l for l in fp.lines if l.key == "field_diesel_l"][0]
    assert diesel.gap_kg == 0            # floored, not negative
    assert fp.gap_kg > 0


def test_index_rewards_reaching_the_regional_optimum():
    from eff.product import assess, config, typical
    c = config()
    ideal = {k: v["ideal"] for k, v in c["products"]["potatoes"]["inputs"].items()}
    at_optimum = assess("potatoes", "delta", ideal)
    assert at_optimum.index == 100 and at_optimum.gap_kg == 0
    worse = assess("potatoes", "delta", typical("potatoes"))
    assert worse.index < at_optimum.index


def test_sourced_values_are_distinguished_from_estimates():
    from eff.product import assess, typical
    fp = assess("potatoes", "delta", typical("potatoes"))
    lines = {l.key: l for l in fp.lines}
    assert lines["irrigation_water_m3"].sourced        # FAO crop water requirement
    assert not lines["field_diesel_l"].sourced         # still an eff estimate
    assert 0 < fp.sourced_share < 1


def test_potato_footprint_is_checked_against_published_literature():
    """A screening model landing outside published LCA ranges is wrong until
    proven otherwise — so the check is asserted, not merely displayed."""
    from eff.product import assess, typical
    fp = assess("potatoes", "delta", typical("potatoes"))
    assert fp.within_published_range is True, (
        f"{fp.kg_actual:,.0f} outside {fp.published_range}")


def test_product_rejects_unknown_keys():
    from eff.product import ProductError, assess
    for args in (("nope", "delta", {}), ("potatoes", "atlantis", {}),
                 ("potatoes", "delta", {"moon_dust_kg": 5})):
        try:
            assess(*args)
            assert False, f"should have raised for {args}"
        except ProductError:
            pass


def test_low_confidence_asset_is_never_shown_as_keep():
    """The reader acts on the word, not on the confidence figure beside it."""
    from eff.report import display_band, INSUFFICIENT
    sparse = Asset(asset_class="diesel_genset", commissioned_year=2014,
                   design_life_years=20, oem_support="supported", spare_lead_days=45)
    r = assess(sparse)
    assert r.band == "KEEP"                  # internally it still scores
    assert display_band(r) == INSUFFICIENT   # but it is not presented that way


def test_reports_render_without_error():
    from eff.report import render_html, print_summary
    from eff.loader import load_assets, DEFAULT_CONFIG
    assets = load_assets(Path(__file__).resolve().parent.parent / "data" / "assets.csv")
    assert len(assets) == 13
    results = [assess(a) for a in assets]
    out = render_html(results, DEFAULT_CONFIG)
    assert out.startswith("<!doctype html>")
    assert "Insufficient data" in out          # GEN-03 has almost no readings
    assert "safety finding" in out             # CMP-02 override surfaced


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except Exception:
            failed += 1
            print(f"  FAIL  {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    raise SystemExit(1 if failed else 0)

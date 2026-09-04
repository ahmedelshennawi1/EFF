"""EFF command line.

    python cli.py                          summary of data/assets.csv
    python cli.py --detail                 full breakdown of every asset
    python cli.py --asset GEN-01           one asset in detail
    python cli.py --html out/report.html   branded HTML report
"""

import argparse
import sys
from pathlib import Path

from eff.loader import load_assets, load_config
from eff.report import print_detail, print_summary, render_html, sort_key
from eff.verdict import assess

ROOT = Path(__file__).parent


def _check_library() -> int:
    from eff.profiles import load_library
    lib = load_library(strict=False)
    problems = lib.validate()
    if problems:
        print(f"\n  {len(problems)} problem(s) in the machinery library:\n")
        for p in problems:
            print(f"    - {p}")
        print()
        return 1
    print(f"\n  Machinery library v{lib.version} is sound — "
          f"{len(lib.classes)} classes across {len(lib.sectors)} sectors.\n")
    return 0


def _quote(args) -> int:
    from eff.pricing import PricingError, quote, render
    try:
        q = quote(assets=args.q_assets, sites=args.q_sites, tier=args.q_tier,
                  data_readiness=args.q_data, urgency=args.q_urgency,
                  distinct_classes=args.q_classes, extra_language=args.q_extra_language,
                  founding_client=args.q_founding, retainer_committed=args.q_retainer,
                  annual_energy_spend=args.q_energy_spend)
    except PricingError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(render(q))
    return 0


def _list_products() -> int:
    from eff.product import config
    c = config()
    print("\n  PRODUCTS\n")
    for k, v in c["products"].items():
        print(f"    {k:<16} {v.get('label_en',''):<30} per {v.get('unit','tonne')}")
        for ik, iv in v["inputs"].items():
            tag = f" [{iv['climate']}]" if iv.get("climate") else ""
            print(f"      {ik:<24} ideal {iv['ideal']:>8,.1f} · typical {iv['typical']:>8,.1f}{tag}")
    print("\n  REGIONS\n")
    for k, v in c["regions"].items():
        print(f"    {k:<16} {v.get('label_en',''):<32} lift {v['water_lift_m']:>3} m · "
              f"irrig x{v['irrigation_factor']:.2f} · cool x{v['cooling_factor']:.2f} · "
              f"heat x{v['heating_factor']:.2f}")
    print("\n  Reference figures are planning estimates pending calibration.\n")
    return 0


def _product(args) -> int:
    from eff.product import ProductError, assess, render, typical
    try:
        if args.typical:
            actuals = typical(args.product)
        else:
            actuals = {}
            for pair in args.input:
                if "=" not in pair:
                    print(f"error: --input expects KEY=VALUE, got {pair!r}", file=sys.stderr)
                    return 1
                k, v = pair.split("=", 1)
                actuals[k.strip()] = float(v)
            if not actuals:
                print("error: supply --input KEY=VALUE (repeatable) or --typical",
                      file=sys.stderr)
                return 1
        print(render(assess(args.product, args.region, actuals)))
    except (ProductError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


def _list_sectors() -> int:
    from eff.profiles import library
    lib = library()
    print("\n  SECTORS IN THE MACHINERY LIBRARY\n")
    width = max(len(k) for k in lib.sectors)
    for key in sorted(lib.sectors):
        s = lib.sectors[key]
        print(f"    {key.ljust(width)}  {s.get('label_en', ''):<32} "
              f"{len(s.get('classes', []))} classes")
    print(f"\n  Detail:  python cli.py --sector <name>\n")
    return 0


def _sector_checklist(sector: str) -> int:
    from eff.profiles import library
    lib = library()
    try:
        rows = lib.sector_checklist(sector)
    except KeyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    s = lib.sectors[sector]
    print(f"\n  {s.get('label_en', sector)} — {s.get('label_ar', '')}")
    print(f"  Typical machinery to survey ({len(rows)} classes)\n")
    w = max(len(r["class"]) for r in rows)
    for r in rows:
        print(f"    {r['class'].ljust(w)}  {r['label_en']:<30} {r['unit']}")
        if r["note"]:
            print(f"    {' ' * w}  -> {r['note']}")
    if s.get("note_en"):
        print(f"\n  {s['note_en']}")
    print("\n  This is a starting checklist, not a constraint — any class can be "
          "used in any sector.\n")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Equipment Fitness Framework")
    p.add_argument("--data", type=Path, default=ROOT / "data" / "assets.csv",
                   help="asset CSV (default: data/assets.csv)")
    p.add_argument("--config", type=Path, default=ROOT / "config.json")
    p.add_argument("--asset", help="assess a single asset by id")
    p.add_argument("--detail", action="store_true", help="print every asset in full")
    p.add_argument("--html", type=Path, help="write an HTML report to this path")
    p.add_argument("--rate", type=float, help="override the discount rate, e.g. 0.22")
    p.add_argument("--sectors", action="store_true",
                   help="list the sectors in the machinery library")
    p.add_argument("--sector", help="print the machinery checklist for a sector")
    p.add_argument("--check-library", action="store_true",
                   help="validate data/profiles.json and report any problems")

    g = p.add_argument_group("quoting (pricing criteria)")
    g.add_argument("--quote", action="store_true", help="compute an itemised fee")
    g.add_argument("--q-assets", type=int, default=0, help="number of assets to assess")
    g.add_argument("--q-sites", type=int, default=1, help="number of sites")
    g.add_argument("--q-tier", default="baseline",
                   choices=["proof_of_concept", "baseline", "measurement_setup"])
    g.add_argument("--q-data", default="good", choices=["good", "partial", "poor"],
                   help="how ready the client's records are")
    g.add_argument("--q-urgency", default="standard", choices=["standard", "expedited"])
    g.add_argument("--q-classes", type=int, default=0,
                   help="distinct equipment classes in the fleet")
    g.add_argument("--q-extra-language", action="store_true")
    g.add_argument("--q-founding", action="store_true",
                   help="Founding Client Programme (no fee)")
    g.add_argument("--q-retainer", action="store_true",
                   help="client commits to the monitoring retainer")
    g.add_argument("--q-energy-spend", type=float,
                   help="client's annual energy spend, for the value sanity check")
    f = p.add_argument_group("product carbon intensity")
    f.add_argument("--product", help="product key, e.g. potatoes (see --products)")
    f.add_argument("--region", default="delta", help="region key, e.g. new_valley")
    f.add_argument("--products", action="store_true", help="list products and regions")
    f.add_argument("--typical", action="store_true",
                   help="use the unoptimised reference profile instead of supplied inputs")
    f.add_argument("--input", action="append", metavar="KEY=VALUE", default=[],
                   help="one measured input, repeatable")

    args = p.parse_args(argv)

    if args.check_library:
        return _check_library()
    if args.quote:
        return _quote(args)
    if args.products:
        return _list_products()
    if args.product:
        return _product(args)
    if args.sectors:
        return _list_sectors()
    if args.sector:
        return _sector_checklist(args.sector)

    if not args.data.exists():
        print(f"error: no asset file at {args.data}", file=sys.stderr)
        return 1

    cfg = load_config(args.config)
    if args.rate is not None:
        cfg["discount_rate"] = args.rate

    assets = load_assets(args.data)
    if args.asset:
        assets = [a for a in assets if a.asset_id.lower() == args.asset.lower()]
        if not assets:
            print(f"error: no asset with id {args.asset!r} in {args.data}", file=sys.stderr)
            return 1

    results = [assess(a,
                      rate=cfg["discount_rate"],
                      salvage_decay=cfg["salvage_decay_per_year"],
                      benchmark_unavailability=cfg["benchmark_unavailability"],
                      materiality=cfg["economic_materiality"])
               for a in assets]

    if args.detail or args.asset:
        for r in sorted(results, key=sort_key):
            print_detail(r)
        if len(results) > 1:
            print_summary(results)
    else:
        print_summary(results)

    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html(results, cfg), encoding="utf-8")
        print(f"  HTML report written to {args.html}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

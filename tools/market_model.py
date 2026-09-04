"""Egypt market-sizing model for EFF.

Turns the researched target counts (data/market.json) into revenue potential per
sector under explicit penetration scenarios, ranked by a priority score that
weighs how many clients exist against how much their energy hurts.

    priority = targets x (energy_share / 100) x (attractiveness / 5)

Revenue model per client won: one year-1 engagement fee, plus a monitoring
retainer for the fraction that converts. A capacity line converts the effort
assumption into the maximum clients one consultant can serve, because a
plan that ignores capacity is a wish.

Usage:  python tools/market_model.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    with open(ROOT / "data" / "market.json", encoding="utf-8") as fh:
        m = json.load(fh)

    a = m["assumptions"]
    sectors = m["sectors"]

    total_targets = sum(s["targets"] for s in sectors.values())

    rows = []
    for key, s in sectors.items():
        priority = s["targets"] * (s["energy_share_pct"] / 100.0) * (s["attractiveness"] / 5.0)
        rows.append((key, s, priority))
    rows.sort(key=lambda r: -r[2])
    total_priority = sum(r[2] for r in rows)

    print()
    print("  EGYPT MARKET MODEL — targets are researched estimates (EST), ranking is the point")
    print()
    print(f"  {'sector':<20} {'targets':>7}  {'energy%':>7}  {'attr':>4}  "
          f"{'priority':>8}  {'share':>6}  gemini_rank")
    print("  " + "-" * 74)
    for key, s, p in rows:
        rank = s.get("gemini_rank")
        print(f"  {key:<20} {s['targets']:>7,}  {s['energy_share_pct']:>6}%  "
              f"{s['attractiveness']:>4}  {p:>8,.0f}  {p / total_priority:>5.0%}  "
              f"{rank if rank else '—'}")
    print("  " + "-" * 74)
    print(f"  {'TOTAL':<20} {total_targets:>7,}")

    fee = a["avg_year1_fee_egp"]
    ret = a["retainer_egp"]
    conv = a["retainer_conversion"]
    per_client_y1 = fee + ret * conv

    print(f"\n  Revenue per client won: EGP {fee:,} year-1 fee "
          f"+ {conv:.0%} x EGP {ret:,} retainer = EGP {per_client_y1:,.0f}")

    print(f"\n  {'penetration':<12} {'clients':>8}  {'year-1 revenue':>16}  "
          f"{'recurring/yr':>14}  {'effort (days)':>13}")
    print("  " + "-" * 70)
    capacity_clients = int(a["capacity_days_per_year"] / a["days_effort_per_client"])
    for p in a["penetration_scenarios"]:
        n = round(total_targets * p)
        y1 = n * per_client_y1
        rec = round(n * conv) * ret
        days = n * a["days_effort_per_client"]
        capped = "  << exceeds capacity" if days > a["capacity_days_per_year"] else ""
        print(f"  {p:<12.1%} {n:>8,}  {y1:>16,.0f}  {rec:>14,.0f}  {days:>13,.0f}{capped}")

    print(f"\n  Capacity: one consultant at {a['capacity_days_per_year']} delivery days/year "
          f"= ~{capacity_clients} clients/year")
    print(f"  ({a['days_effort_per_client']} days/client, self-service model). "
          f"Growth past that is hiring or productisation, not marketing.")

    print("\n  FLAGS carried from the research:")
    for f in m["flags"]:
        print(f"    - {f}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

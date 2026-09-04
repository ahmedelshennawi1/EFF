"""Convert a Google Sheets content dump (markdown table) into EFF's asset CSV.

The Drive connector returns spreadsheet content as a pipe-delimited markdown
table with escaped underscores. This reverses that faithfully so the sheet can
be the master register and the CSV a build artifact.

Usage:  python tools/sheet2csv.py <dump.md> <out.csv>
"""

import csv
import sys
from pathlib import Path


def parse_dump(text: str) -> list:
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Skip the empty padding row and the :-: alignment row.
        if all(c == "" for c in cells):
            continue
        if all(set(c) <= {":", "-", " "} and c for c in cells):
            continue
        rows.append([c.replace("\\_", "_") for c in cells])
    if not rows:
        raise SystemExit("no table rows found in the dump")

    header = rows[0]
    if "asset_id" not in header:
        raise SystemExit(f"first table row is not the expected header: {header[:4]}...")

    width = len(header)
    for i, r in enumerate(rows[1:], start=2):
        if len(r) != width:
            raise SystemExit(f"row {i} has {len(r)} cells, expected {width} — "
                             f"a note containing '|' would cause this; remove it in the sheet")
    return rows


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    rows = parse_dump(src.read_text(encoding="utf-8"))
    with open(dst, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    print(f"{dst}: {len(rows) - 1} assets, {len(rows[0])} columns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Merge PDFs into one, with a bookmark per part so a reader can jump sections.

Usage:  python tools/merge_pdf.py <out.pdf> <in1.pdf> <in2.pdf> ...
"""

import sys
from pathlib import Path

from pypdf import PdfWriter, PdfReader

# Bookmark titles keyed by the part filenames build_submission.ps1 produces.
TITLES = {
    "part1-proposal-ar.pdf": "العرض الفني والمالي",
    "part2-deck-ar.pdf": "العرض التقديمي",
    "part3-proposal-en.pdf": "Commercial Proposal (English)",
    "part4-deck-en.pdf": "Pitch Deck (English)",
}


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    out = Path(sys.argv[1])
    parts = [Path(p) for p in sys.argv[2:]]
    missing = [p for p in parts if not p.exists()]
    if missing:
        print(f"error: missing input(s): {', '.join(str(m) for m in missing)}",
              file=sys.stderr)
        return 1

    writer = PdfWriter()
    total = 0
    for p in parts:
        reader = PdfReader(str(p))
        start = total
        for page in reader.pages:
            writer.add_page(page)
            total += 1
        writer.add_outline_item(TITLES.get(p.name, p.stem), start)
        print(f"  + {p.name}: {len(reader.pages)} pages")

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as fh:
        writer.write(fh)
    print(f"\n{out.name}: {total} pages, {out.stat().st_size / 1024:,.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

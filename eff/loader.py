"""CSV and config loading."""

import csv
import json
from pathlib import Path
from typing import List

from .models import Asset

DEFAULT_CONFIG = {
    "discount_rate": 0.22,
    "salvage_decay_per_year": 0.08,
    "benchmark_unavailability": 0.02,
    "economic_materiality": 0.15,
    "currency": "EGP",
    "organisation": "",
    "assessor": "",
}


def load_assets(path: Path) -> List[Asset]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [Asset.from_row(row) for row in csv.DictReader(fh)
                if any((v or "").strip() for v in row.values())]


def load_config(path: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if path and Path(path).exists():
        with open(path, encoding="utf-8") as fh:
            cfg.update(json.load(fh))
    return cfg

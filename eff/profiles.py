"""Machinery library: archetypes, classes and sector checklists.

The library lives in `data/profiles.json` rather than in this module, so a client
can add their own equipment classes or a whole new sector without touching Python.
This module loads it, resolves archetype inheritance, and validates it — an
extensible library is only usable if it tells you when you have broken it.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

INDICATORS = [
    "AGE",
    "RELIABILITY",
    "EFFICIENCY",
    "CAPACITY",
    "MAINT_COST",
    "CONDITION",
    "OBSOLESCENCE",
    "COMPLIANCE",
]

LIBRARY_PATH = Path(__file__).resolve().parent.parent / "data" / "profiles.json"

# Fields a class inherits from its archetype when it does not set its own.
_INHERITED = ("weights", "design_life", "curve", "low_load_threshold", "duty_matched")


class LibraryError(ValueError):
    """The machinery library is malformed."""


class Library:
    def __init__(self, raw: dict):
        self.version = raw.get("version", "?")
        self.default_class = raw.get("default_class", "generic_machine")
        self.target_load = raw.get("target_load", 0.80)
        self.curves = {k: [tuple(p) for p in v]
                       for k, v in raw.get("curves", {}).items() if not k.startswith("_")}
        self.archetypes = {k: v for k, v in raw.get("archetypes", {}).items()
                           if not k.startswith("_")}
        self.sectors = {k: v for k, v in raw.get("sectors", {}).items()
                        if not k.startswith("_")}
        self.classes = {k: self._resolve(k, v)
                        for k, v in raw.get("classes", {}).items() if not k.startswith("_")}

    def _resolve(self, key: str, spec: dict) -> dict:
        arch_name = spec.get("archetype")
        arch = self.archetypes.get(arch_name, {}) if arch_name else {}
        if arch_name and not arch:
            raise LibraryError(f"class '{key}' references unknown archetype '{arch_name}'")

        out = dict(spec)
        for field in _INHERITED:
            if field not in out and field in arch:
                out[field] = arch[field]
        out.setdefault("weights", {})
        out.setdefault("design_life", {"hours": 60000, "years": 15})
        out.setdefault("duty_matched", False)
        out.setdefault("label_en", key.replace("_", " ").title())
        out.setdefault("label_ar", "")
        return out

    # -- validation --------------------------------------------------------

    def validate(self) -> List[str]:
        """Return every problem found. Empty list means the library is sound."""
        problems: List[str] = []

        for name, arch in self.archetypes.items():
            problems += self._check_weights(f"archetype '{name}'", arch.get("weights", {}))
            curve = arch.get("curve")
            if curve and curve not in self.curves:
                problems.append(f"archetype '{name}' references unknown curve '{curve}'")

        for key, cls in self.classes.items():
            problems += self._check_weights(f"class '{key}'", cls["weights"])
            curve = cls.get("curve")
            if curve and curve not in self.curves:
                problems.append(f"class '{key}' references unknown curve '{curve}'")
            dl = cls.get("design_life") or {}
            if not dl.get("hours") and not dl.get("years"):
                problems.append(f"class '{key}' has no usable design life")
            bench = cls.get("benchmark")
            if bench is not None:
                lo, hi = bench.get("low"), bench.get("high")
                if lo is None or hi is None or not (0 < lo < hi):
                    problems.append(f"class '{key}' benchmark must have 0 < low < high")

        for skey, sector in self.sectors.items():
            for cls in sector.get("classes", []):
                if cls not in self.classes:
                    problems.append(
                        f"sector '{skey}' lists class '{cls}', which is not defined")

        if self.default_class not in self.classes:
            problems.append(f"default_class '{self.default_class}' is not defined")

        for cname, curve in self.curves.items():
            xs = [p[0] for p in curve]
            if xs != sorted(xs):
                problems.append(f"curve '{cname}' breakpoints are not in ascending order")

        return problems

    @staticmethod
    def _check_weights(who: str, weights: dict) -> List[str]:
        if not weights:
            return [f"{who} has no weights"]
        missing = [i for i in INDICATORS if i not in weights]
        if missing:
            return [f"{who} is missing weights for {', '.join(missing)}"]
        unknown = [k for k in weights if k not in INDICATORS]
        if unknown:
            return [f"{who} has unknown indicators {', '.join(unknown)}"]
        total = sum(weights.values())
        if abs(total - 100) > 0.01:
            return [f"{who} weights total {total:g}, not 100"]
        return []

    # -- lookups -----------------------------------------------------------

    def klass(self, asset_class: str) -> dict:
        return self.classes.get(asset_class) or self.classes[self.default_class]

    def is_known(self, asset_class: str) -> bool:
        return asset_class in self.classes

    def weights_for(self, asset_class: str) -> Dict[str, float]:
        return dict(self.klass(asset_class)["weights"])

    def design_life_for(self, asset_class: str) -> dict:
        return dict(self.klass(asset_class)["design_life"])

    def part_load_curve(self, asset_class: str) -> Optional[List[Tuple[float, float]]]:
        name = self.klass(asset_class).get("curve")
        return self.curves.get(name) if name else None

    def low_load_threshold(self, asset_class: str) -> Optional[float]:
        return self.klass(asset_class).get("low_load_threshold")

    def duty_matched(self, asset_class: str) -> bool:
        return bool(self.klass(asset_class).get("duty_matched"))

    def benchmark_for(self, asset_class: str) -> Optional[dict]:
        """Planning-grade specific-consumption range, or None where a benchmark
        is meaningless without more context (e.g. pumps without head)."""
        return self.klass(asset_class).get("benchmark")

    def label(self, asset_class: str, lang: str = "en") -> str:
        cls = self.klass(asset_class)
        return cls.get(f"label_{lang}") or cls.get("label_en") or asset_class

    def sector_checklist(self, sector: str) -> List[dict]:
        """The machinery a sector typically runs — a starting asset checklist."""
        s = self.sectors.get(sector)
        if not s:
            raise KeyError(f"unknown sector '{sector}'. Known: {', '.join(sorted(self.sectors))}")
        return [{"class": c, "label_en": self.label(c, "en"), "label_ar": self.label(c, "ar"),
                 "unit": self.classes[c].get("unit", ""),
                 "note": self.classes[c].get("note_en", "")}
                for c in s.get("classes", []) if c in self.classes]


def load_library(path: Path = LIBRARY_PATH, strict: bool = True) -> Library:
    with open(path, encoding="utf-8") as fh:
        lib = Library(json.load(fh))
    if strict:
        problems = lib.validate()
        if problems:
            raise LibraryError("machinery library has problems:\n  - "
                               + "\n  - ".join(problems))
    return lib


_LIB: Optional[Library] = None


def library() -> Library:
    global _LIB
    if _LIB is None:
        _LIB = load_library()
    return _LIB


# -- module-level shims so existing call sites keep working -----------------

def weights_for(asset_class: str) -> Dict[str, float]:
    return library().weights_for(asset_class)


def design_life_for(asset_class: str) -> dict:
    return library().design_life_for(asset_class)


def part_load_curve(asset_class: str) -> Optional[List[Tuple[float, float]]]:
    return library().part_load_curve(asset_class)


def low_load_threshold(asset_class: str) -> Optional[float]:
    return library().low_load_threshold(asset_class)

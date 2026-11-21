"""Retire the separate 24-aircraft test class; retain canonical Australis IDs.

The caller supplies an extracted complete payload. Writes replace file inodes
because build fixtures can share hardlinks with the original payload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

CANONICAL = "ran_cvn_australis_2030"
RETIRED = "ran_cvn_southern_cross_2030"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sections(text: str) -> dict[str, str]:
    headers = list(re.finditer(r"(?m)^\[([^\]\r\n]+)\][ \t]*$", text))
    result = {}
    for i, match in enumerate(headers):
        assert match[1] not in result, f"Duplicate INI section: {match[1]}"
        result[match[1]] = text[match.end():headers[i + 1].start() if i + 1 < len(headers) else len(text)]
    return result


def replace_file(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".class-repair.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def repair(payload: Path) -> dict:
    vessels = payload / "vessels"
    main = vessels / f"{CANONICAL}.ini"
    variants = vessels / f"{CANONICAL}_variants.ini"
    names_path = payload / "language_en/vessel_names.ini"
    assert main.is_file() and variants.is_file() and names_path.is_file()
    main_before, variants_before = digest(main), digest(variants)
    main_sections = sections(main.read_text(encoding="utf-8"))
    assert re.search(r"(?m)^AircraftCapacity=99\s*$", main_sections["FlightDeck"])
    assert re.search(r"(?m)^UnitType=Vessel\s*$", main_sections["General"])
    variant_sections = sections(variants.read_text(encoding="utf-8"))
    assert re.search(r"(?m)^NumberOfVariants=4\s*$", variant_sections["General"])
    for i, hull in enumerate((91, 92, 93, 94), 1):
        assert f"HullnumberTexture=hullnumber_{hull}.png" in variant_sections[f"Variant{i}"]

    names = names_path.read_text(encoding="utf-8")
    before_names_hash = digest(names_path)
    # Remove just the old test section, even if later localization is appended.
    names = re.sub(r"(?ms)^\[" + re.escape(RETIRED) + r"\][ \t]*\n.*?(?=^\[|\Z)", "", names)
    main_names = sections(names)[CANONICAL]
    expected_names = {
        "Variant1": "HMAS Australis 91,Australis 91",
        "Variant2": "HMAS Southern Cross 92,Southern Cross 92",
        "Variant3": "HMAS Federation 93,Federation 93",
        "Variant4": "HMAS Commonwealth 94,Commonwealth 94",
    }
    for key, value in expected_names.items():
        assert f"{key}={value}" in main_names
    names, changed = re.subn(
        r"(?m)^Default=[^\r\n]*$",
        "Default=Australis-class CVN - 99 aircraft,Australis-class CVN",
        names,
    )
    assert changed == 1
    replace_file(names_path, names.rstrip() + "\n")
    removed = []
    for filename in (f"{RETIRED}.ini", f"{RETIRED}_variants.ini"):
        path = vessels / filename
        if path.exists():
            removed.append({"path": f"vessels/{filename}", "sha256": digest(path)})
            path.unlink()

    roots = []
    for path in sorted(vessels.glob("*.ini")):
        if re.search(r"(?m)^UnitType=Vessel\s*$", path.read_text(encoding="utf-8")):
            roots.append(path.stem)
    assert roots == [CANONICAL], roots
    assert set(sections(names)) == {CANONICAL}
    assert digest(main) == main_before
    assert digest(variants) == variants_before
    return {
        "schema": 1,
        "canonical_id": CANONICAL,
        "retired_test_id": RETIRED,
        "class_count": len(roots),
        "class_ids": roots,
        "aircraft_capacity": 99,
        "sister_ships": ["HMAS Australis 91", "HMAS Southern Cross 92", "HMAS Federation 93", "HMAS Commonwealth 94"],
        "removed_files": removed,
        "localization_before_sha256": before_names_hash,
        "localization_after_sha256": digest(names_path),
        "canonical_vessel_and_variants_unchanged": True,
        "old_test_scenarios_require_reselecting_normal_class": True,
        "live_game_tested": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = repair(args.payload)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

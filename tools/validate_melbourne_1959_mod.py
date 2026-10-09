#!/usr/bin/env python3
"""Check original carrier package references before trying it in Sea Power."""

from __future__ import annotations

import configparser
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "game-mod/RAN-Carrier-Original-1959"
ID = "ran_cv_melbourne_1959"


def ini(path: Path) -> configparser.ConfigParser:
    data = configparser.ConfigParser(interpolation=None, strict=True)
    data.optionxform = str
    data.read_string(path.read_text(encoding="utf-8-sig"))
    return data


def main() -> None:
    ship = ini(MOD / f"vessels/{ID}.ini")
    names = ini(MOD / "language_en/vessel_names.ini")
    variants = ini(MOD / f"vessels/{ID}_variants.ini")
    assert names.has_section(ID) and names[ID]["Type"] == "CVL,Light Carrier"
    assert variants["Default"]["Nation"] == "Australia"
    assert variants["Variant1"]["Nation"] == "Australia"
    assert variants["General"]["NumberOfVariants"] == "1"
    assert ship["General"]["UnitType"] == "Vessel"
    assert ship["FlightDeck"]["AircraftCapacity"] == "30"
    assert len(ship["AirGroup"]) == 0  # still unpopulated by design
    assert ship["Models"]["ResourcesMesh"] == "Hull"
    folder = MOD / ship["Models"]["ResourcesFolder"]
    model = folder / ship["Models"]["ResourcesRoot"]
    assert model.is_file()
    geometry = model.read_text(encoding="utf-8")
    groups = set(re.findall(r"(?m)^o (.+)$", geometry))
    assert len(groups) == len(re.findall(r"(?m)^o (.+)$", geometry))
    assert {"Hull", "Deck", "Elevator_1", "Elevator_2", "Propeller_1", "Propeller_2", "Rudder"} <= groups
    assert not ({"3455404959", "hmas_melbourne", "Melbourne_Old.obj"} & set(geometry.split()))
    submodel_names = list(ship["Submodels"].values())
    assert len(submodel_names) == len(set(submodel_names)), "A mesh has multiple submodel mounts"
    assert {ship["Submodels"][f"MainSystems_{i}"] for i in range(1,4)} == {
        "Propeller_1", "Propeller_2", "Rudder"
    }
    assert not {"Propeller_1", "Propeller_2", "Rudder"} & {
        value for key,value in ship["Submodels"].items() if key.startswith("Main_")
    }
    for moving in ("Propeller_1", "Propeller_2", "Rudder"):
        assert "Position" in ship[moving], f"Moving mount has no pivot: {moving}"
    for group in submodel_names:
        assert group in groups, f"Submodel missing from own OBJ: {group}"
    for material in {ship["Models"]["ResourcesMaterial"]} | {
        ship[section]["Material"] for section in ship["Submodels"].values()
    }:
        path = folder / material
        assert path.is_file(), path
        cfg = ini(path)
        for key in ("_MainTex", "_SpecTex", "_BumpMap"):
            assert (MOD / cfg["Textures"][key]).is_file(), cfg["Textures"][key]
    for family in ("Elevator", "LaunchPoint", "RecoveryPoint", "TaxiPath", "DeckZone"):
        count = int(ship["FlightDeck"][f"NumberOf{family}s"])
        assert all(ship.has_section(f"{family}{i}") for i in range(1,count+1))
        assert not ship.has_section(f"{family}{count+1}")
    for i in range(1, int(ship["FlightDeck"]["NumberOfTaxiPaths"])+1):
        path = ship[f"TaxiPath{i}"]
        assert ship.has_section(path["From"]) and ship.has_section(path["To"])
    assert int(ship["Colliders"]["NumberOfColliders"]) == 7
    for i in range(1,8):
        assert ship.has_section(ship["Colliders"][f"Collider{i}"])
    refs = (MOD / f"vessels/{ID}.ini").read_text(encoding="utf-8-sig")
    assert not re.search(r"3455404959|RADF|Melbourne_Old|ran_sea_venom", refs, re.I)
    print(f"[OK] {ID}: {len(groups)} original OBJ groups; {len(list(MOD.rglob('*.*')))} packaged files")
    print("[OK] Own mesh/material/texture references and flight-deck sections are internally consistent")
    print("[LIMIT] This static check cannot prove Sea Power loads the unit or cycles aircraft")


if __name__ == "__main__":
    main()

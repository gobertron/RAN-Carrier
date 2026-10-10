#!/usr/bin/env python3
"""Static reference and layout checks for the opt-in Australis editor test."""
from __future__ import annotations

import argparse
import configparser
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = "ran_cvn_australis_2030"
SHIP_DIR = f"ships/{ID}"
DEST = ROOT / "game-mod/RAN-Carrier-Australis-2030"
METRES_PER_UNIT = 217 / 3.161967


def ini(path: Path) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser(interpolation=None, strict=True)
    cfg.optionxform = str
    cfg.read_string(path.read_text(encoding="utf-8-sig"))
    return cfg


def vector(value: str) -> tuple[float,float,float]:
    points = tuple(map(float,value.split(",")))
    assert len(points) == 3 and all(math.isfinite(x) for x in points), value
    return points


def inside_deck(x: float, z: float, outline: list[tuple[float,float]]) -> bool:
    inside = False
    for (ax,az),(bx,bz) in zip(outline,outline[1:]+outline[:1]):
        if (az > z) != (bz > z) and x < ax+(bx-ax)*(z-az)/(bz-az):
            inside = not inside
    return inside


def main(destination: Path = DEST) -> None:
    ship = ini(destination / f"vessels/{ID}.ini")
    variants = ini(destination / f"vessels/{ID}_variants.ini")
    names = ini(destination / "language_en/vessel_names.ini")
    info = ini(destination / "_info.ini")
    assert ship["General"]["UnitType"] == "Vessel"
    assert ship["FlightDeck"]["AircraftCapacity"] == "99"
    assert ship["MainPowerSystem"]["Type"] == "Nuclear"
    assert not ship["AirGroup"], "Air group must wait for aircraft compatibility"
    assert ship["WeaponSystems"]["NumberOfWeaponSystems"] == "0"
    assert ship["SensorSystems"]["NumberOfSensorSystems"] == "1"
    assert names.has_section(ID) and names[ID]["Type"].startswith("CVN,")
    assert variants["General"]["NationFlagReference"] == "Flag1"
    assert variants["Default"]["Nation"] == variants["Variant1"]["Nation"] == "Australia"
    assert variants["General"]["NumberOfVariants"] == "1"
    assert "Australis" in info["Language_en"]["Name"]

    base = destination / ship["Models"]["ResourcesFolder"]
    obj = base / ship["Models"]["ResourcesRoot"]
    assert obj.is_file()
    assert ship["Models"]["ResourcesMesh"] == "Hull"
    content = obj.read_text(encoding="utf-8")
    names_in_obj = re.findall(r"(?m)^o ([^\r\n]+)$",content)
    groups = set(names_in_obj)
    assert len(groups) == len(names_in_obj)
    assert {"Hull","Deck","Rudder","Propeller_1","Propeller_2",
            "Surface_Hatch","Surface_Sensor"} <= groups
    assert len(groups) <= 20, "Static materials should be batched"
    count = len(re.findall(r"(?m)^v ",content))
    assert count > 400
    for row in re.findall(r"(?m)^f (.+)$",content):
        indices = [int(token.split("/")[0]) for token in row.split()]
        assert len(indices) == 3 and all(1 <= i <= count for i in indices)
    assert (base / f"{ID}.mtl").is_file()

    registered = list(ship["Submodels"].values())
    assert len(registered) == len(set(registered))
    assert set(registered) == groups - {"Hull"} | {"Flag1"}
    assert [ship["Submodels"][f"MainSystems_{i}"] for i in (1,2,3)] == [
        "Propeller_1","Propeller_2","Rudder"]
    assert "Rudder" not in [value for key,value in ship["Submodels"].items()
                            if key.startswith("Main_")]
    for name in groups - {"Hull"}:
        part = ship[name]
        assert part["Mesh"] == name
        mat = base / part["Material"]
        assert mat.is_file(),mat
        material = ini(mat)
        for key in ("_MainTex","_SpecTex","_BumpMap"):
            path = destination / material["Textures"][key]
            assert path.is_file(),path
            assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    # Unlike the failed Melbourne prototype, the moving sections explicitly
    # resolve their root file and have one mount each. Only a game test can
    # tell whether this avoids its rudder initialization exception.
    for name in ("Propeller_1","Propeller_2","Rudder"):
        part = ship[name]
        assert part["ResourcesMeshFolder"] == SHIP_DIR + "/"
        assert part["RootMesh"] == f"{ID}.obj"
        vector(part["Position"])

    deck = ship["FlightDeck"]
    for family in ("Elevator","LaunchPoint","RecoveryPoint","TaxiPath","DeckZone"):
        count = int(deck[f"NumberOf{family}s"])
        assert count > 0
        assert all(ship.has_section(f"{family}{i}") for i in range(1,count+1))
        assert not ship.has_section(f"{family}{count+1}")
    assert int(deck["NumberOfElevators"]) == 4
    assert int(deck["NumberOfLaunchPoints"]) == 7
    assert int(deck["NumberOfRecoveryPoints"]) == 5
    assert ship["RecoveryPoint1"]["Arrested"] == "True"
    deck_outline = ship["DeckZone5"]
    assert deck_outline["Type"] == "Deck"
    outline = []
    for i in range(1,int(deck_outline["NumberOfPoints"])+1):
        x,y,z = vector(deck_outline[f"Point{i}"])
        outline.append((x*METRES_PER_UNIT,z*METRES_PER_UNIT))
    assert len(outline) == 17
    assert math.isclose(max(x for x,_ in outline)-min(x for x,_ in outline),88,
                        abs_tol=.001)
    assert math.isclose(max(z for _,z in outline)-min(z for _,z in outline),370,
                        abs_tol=.001)
    for i in range(1,int(deck["NumberOfTaxiPaths"])+1):
        route = ship[f"TaxiPath{i}"]
        assert ship.has_section(route["From"]) and ship.has_section(route["To"])
        assert route["Waypoints"].strip()
        for item in route["Waypoints"].split("|"):
            x,y,z=vector(item)
            assert inside_deck(x*METRES_PER_UNIT,z*METRES_PER_UNIT,outline), (i,item)
            assert abs(y - 22.16/METRES_PER_UNIT) < 1e-5
    for i in range(1,int(deck["NumberOfDeckZones"])+1):
        section = ship[f"DeckZone{i}"]
        assert all(f"Point{j}" in section
                   for j in range(1,int(section["NumberOfPoints"])+1))
    for section_name in ("ControlSystem","MainPowerSystem","FlightDeck",
                         "PropulsionSystem1","PropulsionSystem2","RudderSystem1"):
        collider = ship[section_name].get("Collider")
        assert collider and ship.has_section(collider), (section_name,collider)
    colliders = ship["Colliders"]
    assert colliders["NumberOfMeshColliders"] == "0"
    assert int(colliders["NumberOfColliders"]) == len([
        key for key in colliders if re.fullmatch(r"Collider\d+",key)])
    assert not re.search(r"3455404959|3491248180|3574957049|hmas_melbourne",
                         (destination/f"vessels/{ID}.ini").read_text(encoding="utf-8-sig"))
    print(f"[OK] {ID}: {len(groups)} OBJ groups, {len(registered)} submodels")
    print("[OK] 4 lifts, 3 fixed-wing catapults, 4 vertical spots, 5 recovery points")
    print("[OK] Rudder/propeller mounts, materials, names, routes and colliders resolve")
    print("[LIMIT] Sea Power loading, flight operations and animation require in-game QA")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination",type=Path,default=DEST)
    main(parser.parse_args().destination)

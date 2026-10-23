#!/usr/bin/env python3
"""Static reference and layout checks for the opt-in Australis editor test."""
from __future__ import annotations

import argparse
import configparser
import json
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


def check_stock(ship, destination: Path, original: Path) -> None:
    """Fail before installation if a stock system or round is unavailable."""
    for family,filename in (("SensorSystem","sensors.ini"),("WeaponSystem","weapons.ini")):
        local = destination/"systems"/filename
        local_names = set(ini(local).sections()) if local.is_file() else set()
        stock = original/"systems"/filename
        if not stock.is_file():
            raise FileNotFoundError(f"Required stock catalogue missing: {stock}")
        stock_names = set(re.findall(r"(?m)^\[([^\]\r\n]+)\]",stock.read_text(encoding="utf-8-sig")))
        count = int(ship[family+"s"]["NumberOf"+family+"s"])
        for i in range(1,count+1):
            system = ship[f"{family}{i}"]
            if system["Type"] == "Visual": continue
            assert system["SystemName"] in local_names|stock_names, (family,i,"missing stock profile")
    rounds = {value for name in ship.sections() for key,value in ship[name].items()
              if re.fullmatch(r"Ammunition\d*|Countermeasure",key)}
    for name in rounds:
        assert (original/"ammunition"/(name+".ini")).is_file(), (name,"missing stock ammunition")
    print(f"[OK] Installed stock catalogues and {len(rounds)} ammunition references resolve")


def main(destination: Path = DEST, stock_root: Path | None = None) -> None:
    ship = ini(destination / f"vessels/{ID}.ini")
    variants = ini(destination / f"vessels/{ID}_variants.ini")
    names = ini(destination / "language_en/vessel_names.ini")
    info = ini(destination / "_info.ini")
    assert ship["General"]["UnitType"] == "Vessel"
    assert ship["FlightDeck"]["AircraftCapacity"] == "99"
    assert ship["MainPowerSystem"]["Type"] == "Nuclear"
    assert not ship["AirGroup"], "Air group must wait for aircraft compatibility"
    assert ship["WeaponSystems"]["NumberOfWeaponSystems"] == "21"
    assert ship["SensorSystems"]["NumberOfSensorSystems"] == "11"
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
            "Surface_Hatch","Surface_Sensor","coll_hull_main"} <= groups
    assert len(groups) <= 30, "Static details are batched; five guns need ten moving objects"
    object_faces: dict[str,int] = {}
    object_vertices: dict[str,list[tuple[float,float,float]]] = {}
    current_object = None
    for line in content.splitlines():
        if line.startswith("o "):
            current_object = line[2:]
            object_faces[current_object] = 0
            object_vertices[current_object] = []
        elif line.startswith("v "):
            object_vertices[current_object].append(tuple(map(float,line.split()[1:4])))
        elif line.startswith("f "):
            assert current_object is not None
            object_faces[current_object] += 1
    assert all(object_faces[name] >= 12 for name in
               ("Hull", "Deck", "Rudder", "Propeller_1", "Propeller_2",
                "coll_hull_main")), object_faces
    vertex_count = len(re.findall(r"(?m)^v ",content))
    uv_count = len(re.findall(r"(?m)^vt ",content))
    normal_count = len(re.findall(r"(?m)^vn ",content))
    assert vertex_count > 400 and uv_count == vertex_count and normal_count > 100
    for normal in re.findall(r"(?m)^vn (.+)$",content):
        xyz=tuple(float(item) for item in normal.split())
        assert len(xyz)==3 and math.isclose(sum(a*a for a in xyz),1,abs_tol=2e-5)
    for row in re.findall(r"(?m)^f (.+)$",content):
        indices = [[int(index) for index in token.split("/")] for token in row.split()]
        assert len(indices) == 3 and all(len(token) == 3 for token in indices)
        assert all(1 <= vertex <= vertex_count and 1 <= uv <= uv_count
                   and 1 <= normal <= normal_count
                   for vertex,uv,normal in indices)
    assert (base / f"{ID}.mtl").is_file()

    registered = list(ship["Submodels"].values())
    assert len(registered) == len(set(registered))
    assert set(registered) == groups - {"Hull", "coll_hull_main"} | {"Flag1"}
    assert [ship["Submodels"][f"MainSystems_{i}"] for i in (1,2,3)] == [
        "Propeller_1","Propeller_2","Rudder"]
    assert "Rudder" not in [value for key,value in ship["Submodels"].items()
                            if key.startswith("Main_")]
    for name in groups - {"Hull", "coll_hull_main"}:
        part = ship[name]
        assert part["Mesh"] == name
        mat = base / part["Material"]
        assert mat.is_file(),mat
        material = ini(mat)
        for key in ("_MainTex","_SpecTex","_BumpMap"):
            path = destination / material["Textures"][key]
            assert path.is_file(),path
            assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
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
    assert int(deck["NumberOfLaunchPoints"]) == 9
    assert int(deck["NumberOfRecoveryPoints"]) == 5
    # The first four hatch-coloured boxes are the actual exported platforms.
    # Measure their geometry rather than trusting a second copy of the layout.
    hatch = object_vertices["Surface_Hatch"]
    lift_bounds = []
    for i in range(1,5):
        vertices = hatch[(i-1)*8:i*8]
        low = [min(v[axis] for v in vertices)*METRES_PER_UNIT for axis in range(3)]
        high = [max(v[axis] for v in vertices)*METRES_PER_UNIT for axis in range(3)]
        assert abs(high[0]-low[0]-22) < .001, (i,"lift width")
        assert abs(high[2]-low[2]-26) < .001, (i,"lift length")
        centre = ((low[0]+high[0])/2,high[1],(low[2]+high[2])/2)
        for key in ("SpawnPosition","RidePosition"):
            position = tuple(p*METRES_PER_UNIT for p in vector(ship[f"Elevator{i}"][key]))
            assert math.dist(position,centre) < .0002, (i,key,"off platform centre")
        assert float(ship[f"Elevator{i}"]["SpawnRotation"]) == 0
        # Stock F-14A deck/ground-pivot terms, plus the engine's 0.012 ride
        # allowance. The full-span 19.545 x 19.1 m reference box must fit.
        f14_shift = (-.074+.012+.0126)*METRES_PER_UNIT
        assert centre[0]-19.545/2 >= low[0] and centre[0]+19.545/2 <= high[0]
        assert centre[2]+f14_shift-19.1/2 >= low[2]
        assert centre[2]+f14_shift+19.1/2 <= high[2]
        lift_bounds.append((low[0],high[0],low[2],high[2]))
    port_lift = vector(ship["Elevator3"]["SpawnPosition"])
    main_island = ship["DeckZone8"]
    island_z = [vector(main_island[f"Point{i}"])[2]
                for i in range(1,int(main_island["NumberOfPoints"])+1)]
    assert port_lift[0] < 0 and min(island_z) <= port_lift[2] <= max(island_z), \
        "Port lift must remain abreast of the main island"
    assert abs(port_lift[2]*METRES_PER_UNIT+32) < .001
    assert ship["RecoveryPoint1"]["Arrested"] == "True"
    deck_outline = ship["DeckZone7"]
    assert deck_outline["Type"] == "Deck"
    outline = []
    for i in range(1,int(deck_outline["NumberOfPoints"])+1):
        x,y,z = vector(deck_outline[f"Point{i}"])
        outline.append((x*METRES_PER_UNIT,z*METRES_PER_UNIT))
    assert len(outline) == 17
    assert math.isclose(max(x for x,_ in outline)-min(x for x,_ in outline),82,
                        abs_tol=.001)
    assert math.isclose(max(z for _,z in outline)-min(z for _,z in outline),370,
                        abs_tol=.001)
    # Measure the actual exported metal track meshes, independently of the
    # generator constants, and compare with the game's launch definitions.
    tracks = object_vertices["Surface_Track"]
    actual_catapults = []
    for i in range(1,6):
        track = tracks[(i-1)*8:i*8]
        for x,y,z in track:
            assert inside_deck(x*METRES_PER_UNIT,z*METRES_PER_UNIT,outline), (i,"metal track off deck")
            assert 0 <= y*METRES_PER_UNIT-22 < .08, (i,"track should be deck-flush")
        start = tuple((a+b)/2 for a,b in zip(track[0],track[3]))
        end = tuple((a+b)/2 for a,b in zip(track[1],track[2]))
        launch = ship[f"LaunchPoint{i}"]
        px,_,pz = vector(launch["Position"])
        assert math.hypot(px-start[0],pz-start[2]) < 2e-6, (i,"track start")
        dx,dz = end[0]-start[0],end[2]-start[2]
        assert abs(float(launch["Rotation"])-math.degrees(math.atan2(dx,dz))) < .002, (i,"heading")
        assert abs(float(launch["CatapultLength"])-math.hypot(dx,dz)*METRES_PER_UNIT) < .01
        assert abs(float(launch["CatapultLength"])-95) < .01
        heading = math.degrees(math.atan2(dx,dz))
        if i <= 3:
            assert abs(heading) < .002 and start[2]*METRES_PER_UNIT > 80, (i,"bow track")
            assert "SupportedClasses" not in launch
        else:
            assert abs(heading+6) < .002 and start[0] < 0 and start[2] < 0, (i,"port-waist track")
            assert end[0] < start[0] and end[0] < 0
            assert launch["SupportedClasses"] == "usn_a-7e"
        length = math.hypot(dx,dz)
        direction = (dx/length,dz/length)
        actual_catapults.append((start,end,direction))
        # Measure the actual deflector behind each track, including its
        # orientation. A heading change must rotate its markings and panel.
        deflector = hatch[32+(i-1)*8:40+(i-1)*8]
        centre = tuple(sum(v[axis] for v in deflector)/8 for axis in (0,2))
        expected = (start[0]-18/METRES_PER_UNIT*direction[0],
                    start[2]-18/METRES_PER_UNIT*direction[1])
        assert math.dist(centre,expected)*METRES_PER_UNIT < .001, (i,"deflector placement")
        along = (deflector[3][0]-deflector[0][0],deflector[3][2]-deflector[0][2])
        assert abs(math.degrees(math.atan2(*along))-heading) < .003, (i,"deflector heading")
    waist_starts = [actual_catapults[i][0] for i in (3,4)]
    assert abs(abs(waist_starts[1][2]-waist_starts[0][2])*METRES_PER_UNIT-21) < .001
    # The first five gold objects are the new compact launch shuttles;
    # white guides follow the eight lift-edge stripes in their batch.
    gold = object_vertices["Surface_Gold"]
    white = object_vertices["Surface_White"]
    for i,(start,end,direction) in enumerate(actual_catapults,1):
        shuttle = gold[(i-1)*8:i*8]
        centre = tuple(sum(v[axis] for v in shuttle)/8 for axis in (0,2))
        assert math.dist(centre,(start[0],start[2]))*METRES_PER_UNIT < .001, (i,"shuttle alignment")
    for x,y,z in white[64:144]:
        assert inside_deck(x*METRES_PER_UNIT,z*METRES_PER_UNIT,outline), "painted guide off deck"
    # No track is allowed to float over the sea. The outer waist finishes
    # inside the deck edge; departure continues outboard once airborne.
    for i,(start,end,direction) in enumerate(actual_catapults,1):
        for n in range(96):
            x = start[0]*METRES_PER_UNIT+n*direction[0]
            z = start[2]*METRES_PER_UNIT+n*direction[1]
            assert inside_deck(x,z,outline), (i,"track runs off the deck")
    # Check the user's stock A-7E reference at all five catapults, with
    # wings open. This is a staging footprint check, not a taxi simulation.
    obstacles = list(lift_bounds)
    for name in ("DeckZone8","DeckZone9"):
        zone = ship[name]
        points = [vector(zone[f"Point{i}"]) for i in range(1,int(zone["NumberOfPoints"])+1)]
        obstacles.append((min(v[0] for v in points)*METRES_PER_UNIT,
                          max(v[0] for v in points)*METRES_PER_UNIT,
                          min(v[2] for v in points)*METRES_PER_UNIT,
                          max(v[2] for v in points)*METRES_PER_UNIT))
    for i in range(1,6):
        launch = ship[f"LaunchPoint{i}"]
        x,_,z = (v*METRES_PER_UNIT for v in vector(launch["Position"]))
        angle = math.radians(float(launch["Rotation"]))
        for along in (-14.06/2,0,14.06/2):
            for across in (-11.8/2,0,11.8/2):
                px = x+along*math.sin(angle)+across*math.cos(angle)
                pz = z+along*math.cos(angle)-across*math.sin(angle)
                assert inside_deck(px,pz,outline), (i,"A-7E off deck")
                assert all(not(x0 <= px <= x1 and z0 <= pz <= z1)
                           for x0,x1,z0,z1 in obstacles), (i,"A-7E overlaps lift or island")
    # Independently check real exported corridors and the safety interlocks.
    # The extra rollout is a plan-view obstruction check, not blast analysis.
    for i,(start,end,direction) in enumerate(actual_catapults,1):
        sx,sz = start[0]*METRES_PER_UNIT,start[2]*METRES_PER_UNIT
        for n in range(156):
            x,z = sx+n*direction[0],sz+n*direction[1]
            if z > 185: break
            for x0,x1,z0,z1 in obstacles:
                gap = math.hypot(max(x0-x,x-x1,0),max(z0-z,z-z1,0))
                assert gap >= 12-.001, (i,"launch corridor overlaps island/lift")
    interlocks = {1:"2,4,5",2:"1,3,4,5",3:"2,4,5",4:"1,2,3,5,6,7",5:"1,2,3,4,6,7"}
    for i,blocks in interlocks.items():
        assert ship[f"LaunchPoint{i}"]["BlocksLaunchPoints"] == blocks
        assert ship[f"LaunchPoint{i}"]["TakeoffRequiresFreeLaunchpoints"] == blocks
    assert float(deck["LaunchDelay"]) == 1
    left = vector(ship["LaunchPoint1"]["Position"])
    right = vector(ship["LaunchPoint3"]["Position"])
    assert abs((right[0]-left[0])*METRES_PER_UNIT-28) < .001
    for i in range(6,10):
        launch=ship[f"LaunchPoint{i}"]
        blocks=launch.get("BlocksLaunchPoints","")
        assert blocks == ("4,5" if i<=7 else "")
        assert not ({"1","2","3"}&set(blocks.split(","))), "Helicopters must leave bow catapults available"
        if i<=7: assert launch["TakeoffRequiresFreeLaunchpoints"] == blocks
    for i in range(1,int(deck["NumberOfTaxiPaths"])+1):
        route = ship[f"TaxiPath{i}"]
        assert ship.has_section(route["From"]) and ship.has_section(route["To"])
        assert route["Waypoints"].strip()
        for item in route["Waypoints"].split("|"):
            x,y,z=vector(item)
            assert inside_deck(x*METRES_PER_UNIT,z*METRES_PER_UNIT,outline), (i,item)
            assert abs(y - 22/METRES_PER_UNIT) < 1e-5
        if route["To"].startswith("LaunchPoint") and int(route["To"][11:]) <= 5:
            launch = ship[route["To"]]
            end = vector(route["Waypoints"].split("|")[-1])
            position = vector(launch["Position"])
            angle = math.radians(float(launch["Rotation"]))
            expected = (position[0]-20/METRES_PER_UNIT*math.sin(angle),
                        position[2]-20/METRES_PER_UNIT*math.cos(angle))
            assert math.hypot(end[0]-expected[0],end[2]-expected[1])*METRES_PER_UNIT < .001, \
                (i,"taxi approach not aligned to launch track")
    for i in range(1,int(deck["NumberOfDeckZones"])+1):
        section = ship[f"DeckZone{i}"]
        assert all(f"Point{j}" in section
                   for j in range(1,int(section["NumberOfPoints"])+1))
    for section_name in ("ControlSystem","MainPowerSystem","FlightDeck",
                         "PropulsionSystem1","PropulsionSystem2","RudderSystem1"):
        collider = ship[section_name].get("Collider")
        assert collider and ship.has_section(collider), (section_name,collider)
    colliders = ship["Colliders"]
    assert colliders["NumberOfMeshColliders"] == "1"
    assert colliders["MeshCollider1"] == ship["Models"]["ResourcesMeshHullCollider"] == "coll_hull_main"
    assert int(colliders["NumberOfColliders"]) == len([
        key for key in colliders if re.fullmatch(r"Collider\d+",key)])
    assert not re.search(r"3455404959|3491248180|3574957049|hmas_melbourne",
                         (destination/f"vessels/{ID}.ini").read_text(encoding="utf-8-sig"))
    assert ship["Particles"]["Cavitation"] == "ships/particles/usn_cvn_nimitz_cavitation"
    foam = ship["Foam"]
    assert foam["SternFoamTexture"] == "ships/particles/wake/Ceto_Propwash"
    assert foam["HullFoamTexture"] == "ships/particles/wake/Ceto_Hullwake"
    vector(foam["SternFoamPosition"])
    vector(foam["HullFoamPosition"])
    fit = json.loads((destination/"combat-fit.json").read_text())
    crew = fit["crew"]
    assert crew["ships_company"]+crew["air_wing"]+crew["staff"] == crew["total"] == 5300
    assert crew["berths"] == 5800 and crew["berths"] >= crew["total"]
    assert sum(fit["weight_budget_tonnes"].values()) == float(ship["Physics"]["Displacement"]) == 112000
    assert fit["hangar"]["proposed_aircraft_allocation"]+fit["hangar"]["proposed_deck_allocation"] == 99
    hotel = fit["hotel_services"]
    assert (hotel["watermakers"]-1)*hotel["each_watermaker_m3_per_day"] >= crew["total"]*hotel["fresh_water_litres_per_person_day"]/1000
    local_sensors = ini(destination/"systems/sensors.ini")
    local_weapons = ini(destination/"systems/weapons.ini")
    assert local_sensors["RAN_Australis_OECM"]["Type"] == "Offensive"
    assert local_weapons["RAN_Australis_RAM21"]["NumberOfAttachments"] == "21"
    for family in ("SensorSystem","WeaponSystem","DecoySystem"):
        count = int(ship[family+"s"]["NumberOf"+family+"s"])
        for i in range(1,count+1):
            assert ship.has_section(f"{family}{i}")
    vls = [ship[s] for s in ship.sections() if s.startswith("WeaponSystem") and ship[s].get("SystemName")=="MK41"]
    assert len(vls) == 4 and sum(int(s["NumberOfContainers"]) for s in vls) == 80
    for name in ship.sections():
        if not re.fullmatch(r"WeaponSystem\d+",name): continue
        system = ship[name]
        if "AssociatedMagazine" in system: assert ship.has_section(system["AssociatedMagazine"])
        for key in ("AssociatedSensors","AssociatedSearchSensors"):
            assert all(ship.has_section(s) for s in system.get(key,"").split(",") if s)
        count = int(system.get("NumberOfContainers",0))
        for i in range(1,count+1):
            assert system[f"Container{i}"] == "Dummy"
            vector(system[f"Container{i}_Position"])
    # Regression for the actual AlignTurret exception: the normal-gun loader
    # reads Gun1..GunN, whereas the CIWS loader reads Gun. Resolve those exact
    # keys to original moving OBJ objects, not merely to existing INI sections.
    guns=[ship[s] for s in ship.sections() if re.fullmatch(r"WeaponSystem\d+",s)
          and ship[s]["Type"] in ("Gun","CIWS")]
    assert len(guns)==5
    moving_names={v for k,v in ship["Submodels"].items() if k.startswith("MainSystems_")}
    for gun in guns:
        if gun["Type"]=="Gun":
            assert gun["NumberOfGuns"]=="1"
            barrel=gun["Gun1"]
        else: barrel=gun["Gun"]
        mount=gun["Mount"]
        assert barrel in groups and mount in groups and barrel!="Dummy"
        assert {barrel,mount} <= moving_names
        assert gun["ContainerBase"] == barrel
        assert ship[barrel]["Parent"] == mount
        assert gun["IsMountRotatable"] == gun["AreContainersRotatable"] == "True"
        assert object_faces[barrel] >= 12 and object_faces[mount] >= 12
        assert min(v[2] for v in object_vertices[barrel]) > 0
        assert int(ship[gun["AssociatedMagazine"]]["Ammunition1_Count"]) > 0
    assert local_weapons["RAN_Australis_30mm"]["RoundsMax"] == "400"
    for part in registered:
        parent=ship[part].get("Parent")
        if parent: assert parent in registered and parent!=part
    # Tyre-contact coordinates must match the mesh surface; the engine adds
    # GroundPivot itself. The old 22.16 m route height visibly floated tyres.
    surface=max(v[1] for v in object_vertices["Deck"])
    assert abs(surface*METRES_PER_UNIT-22)<.001
    for i in range(4):
        platform=hatch[i*8:(i+1)*8]
        assert abs((max(v[1] for v in platform)-surface)*METRES_PER_UNIT-.002)<.0002, \
            "Lift platform must be within two millimetres of deck"
    assert all(surface < y <= surface+.009/METRES_PER_UNIT
               for x,y,z in white), "Deck paint must be millimetres above the contact plane"
    for i in range(5):
        deflector=hatch[32+i*8:40+i*8]
        assert abs(max(v[1] for v in deflector)*METRES_PER_UNIT-22.002)<.0002, \
            "Stowed deflector must be flush with deck"
    for x,y,z in hatch[232:264]:
        assert y <= surface+.0022/METRES_PER_UNIT, "Closed laser hatches must remain within two millimetres of deck"
    for i in range(1,6):
        assert abs(vector(ship[f"LaunchPoint{i}"]["Position"])[1]-surface)<1e-6
    assert abs(vector(ship["RecoveryPoint1"]["Position"])[1]-surface)<1e-6
    for i in range(6,10):
        pad=hatch[72+(i-6)*40:112+(i-6)*40]
        assert len(pad)==40
        pad_top=max(v[1] for v in pad)
        assert abs(pad_top*METRES_PER_UNIT-22.002)<.0002
        centre=(sum(v[0] for v in pad)/40,pad_top,sum(v[2] for v in pad)/40)
        assert math.dist(vector(ship[f"LaunchPoint{i}"]["Position"]),centre)*METRES_PER_UNIT<.0002
        assert math.dist(vector(ship[f"RecoveryPoint{i-4}"]["Position"]),centre)*METRES_PER_UNIT<.0002
    # The actual recovery zone and exported cable ends must share one nine
    # degree port axis; wires cross that axis at ninety degrees.
    assert float(ship["RecoveryPoint1"]["Rotation"]) == -9
    recovery=ship["DeckZone6"]
    corners=[vector(recovery[f"Point{i}"]) for i in range(1,5)]
    start=tuple((a+b)/2 for a,b in zip(corners[0],corners[1]))
    end=tuple((a+b)/2 for a,b in zip(corners[2],corners[3]))
    dx,dz=end[0]-start[0],end[2]-start[2]
    assert abs(math.degrees(math.atan2(dx,dz))+9)<.002
    assert math.dist((start[0],start[2]),(end[0],end[2]))*METRES_PER_UNIT > 185
    for i in range(4):
        wire=gold[40+i*8:48+i*8]
        wx,wz=wire[1][0]-wire[0][0],wire[1][2]-wire[0][2]
        assert abs((wx*dx+wz*dz)/(math.hypot(wx,wz)*math.hypot(dx,dz)))<.0001
    # Six wrapped rear windows follow all bridge faces, below a reduced mast.
    panes=object_vertices["Surface_Glass"][-48:]
    assert len(panes)==48
    centres=[(sum(v[0] for v in panes[i:i+8])/8,
              sum(v[2] for v in panes[i:i+8])/8) for i in range(0,48,8)]
    cx=sum(x for x,z in centres)/6;cz=sum(z for x,z in centres)/6
    assert len({(x>cx,z>cz) for x,z in centres})==4
    assert all(31.9 < y*METRES_PER_UNIT < 33.6 for x,y,z in panes)
    aft=ship["DeckZone9"]
    aft_points=[vector(aft[f"Point{i}"]) for i in range(1,int(aft["NumberOfPoints"])+1)]
    assert abs((max(v[2] for v in aft_points)-min(v[2] for v in aft_points))*METRES_PER_UNIT-29.9)<.001
    for i in range(6,10):
        x,y,z=vector(ship[f"LaunchPoint{i}"]["Position"])
        island=ship["DeckZone8" if i<=7 else "DeckZone9"]
        front=max(vector(island[f"Point{j}"])[2] for j in range(1,int(island["NumberOfPoints"])+1))
        assert (z-front)*METRES_PER_UNIT > 11.5
    # Main-deck defensive mounts need no-parking footprints, and no strike
    # missile or removed area-defence round may remain in the native stores.
    assert int(deck["NumberOfDeckZones"])==17
    assert all(ship[f"DeckZone{i}"]["Type"]=="NoPark" for i in range(10,18))
    for system in vls:
        assert vector(system["MountPosition"])[1]*METRES_PER_UNIT > 22
        magazine=ship[system["AssociatedMagazine"]]
        assert magazine["NumberOfAmmunitionTypes"]=="1"
        assert magazine["Ammunition1"]=="usn_rim-7m"
        assert magazine["Ammunition1_Count"]=="20"
    ammunition={value for name in ship.sections() for key,value in ship[name].items()
                if re.fullmatch(r"Ammunition\d*",key)}
    assert not {"usn_rim-66e","usn_rgm-109c"}&ammunition
    assert ship["AI"]["ASuW_Capability"]=="0"
    current,capacity=map(int,deck["FlightDeck_AmmoCapacity"].split("/"))
    budget=fit["aviation_ammunition"]
    assert current==capacity==budget["capacity_points"]==6000000
    assert capacity>=budget["planning_aircraft"]*budget["planning_sorties_per_aircraft"]*budget["planning_points_per_sortie"]
    assert deck["FlightDeck_NumberOfAccountableAmmunitionCategories"]=="0"
    if stock_root is not None: check_stock(ship,destination,stock_root)
    print(f"[OK] {ID}: {len(groups)} OBJ groups, {len(registered)} submodels")
    print(f"[OK] {vertex_count} vertices with UVs and {normal_count} indexed face normals")
    print("[OK] 4 lifts, 3 bow + 2 port-waist steam CATOBAR tracks, 4 vertical spots, 5 recovery points")
    print("[OK] Four 22 x 26 m lifts; ride/spawn centres and F-14A reference footprint fit")
    print("[OK] A-7E open-wing staging footprint clear at all five catapults")
    print("[OK] 82 m deck; launch tracks, rotated deflectors and taxi approaches align")
    print("[OK] Bow-pair / waist / recovery interlocks; forward helicopter pair blocks waist lanes only")
    print("[OK] Flush lifts/pads, thin deck paint and matching tyre-contact positions")
    print("[OK] Closed laser hatches and stowed deflectors are flush; nine-degree recovery and perpendicular wires")
    print("[OK] Smaller rear tower with six-face glazing; eight defensive deck no-parking zones")
    print("[OK] Five guns have real yaw/barrel meshes; normal guns resolve NumberOfGuns/Gun1")
    print("[OK] 6,000,000 aviation-ammunition points; RIM-66E and RGM-109 removed")
    print("[OK] 5300 embarked / 5800 berths; 112000 t concept mass budget balances")
    print("[OK] 80 VLS cells, 21 weapon systems, 11 sensors and two towed decoys configured")
    print("[OK] Rudder/propeller mounts, materials, effects, names, routes and colliders resolve")
    print("[LIMIT] Sea Power loading, flight operations and animation require in-game QA")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination",type=Path,default=DEST)
    parser.add_argument("--stock-root",type=Path,help="StreamingAssets/original for stock reference checks")
    args = parser.parse_args()
    main(args.destination,args.stock_root)

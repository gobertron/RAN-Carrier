#!/usr/bin/env python3
"""Build the first independent RAN carrier integration milestone.

All hull geometry comes from this repository's original model study. The
output uses no Royal Australian Defence Forces or other Workshop assets.
The vessel INI is a native-format prototype and still needs in-game QA.
"""

from __future__ import annotations

import argparse
import re
import shutil
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOD_NAME = "RAN-Carrier-Original-1959"
VESSEL_ID = "ran_cv_melbourne_1959"
MODEL_ID = "ran_cvl_melbourne_1959"
MODEL_DIR = f"ships/{MODEL_ID}"
SOURCE = ROOT / "game-scale-models/ships" / MODEL_ID
DEST = ROOT / "game-mod" / MOD_NAME
SCALE = 3.162 / 217.0
DECK_Y = 15.5 * SCALE
COLORS = {
    "hull": (150, 162, 172, 255),
    "underwater": (125, 51, 52, 255),
    "deck": (71, 84, 97, 255),
    "island": (170, 182, 192, 255),
    "glass": (28, 57, 76, 255),
    "white": (232, 236, 236, 255),
    "gold": (231, 189, 92, 255),
    "dark": (39, 51, 61, 255),
}


def png(rgba: tuple[int, int, int, int]) -> bytes:
    """Small self-authored RGBA texture with no Pillow requirement."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    row = b"\0" + bytes(rgba) * 8
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">2I5B", 8, 8, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(row * 8))
            + chunk(b"IEND", b""))


def append_box_obj(obj: str, name: str, center: tuple[float, float, float],
                   extents: tuple[float, float, float], first: int) -> str:
    x, y, z = center
    dx, dy, dz = extents
    verts = [(x + sx*dx/2, y + sy*dy/2, z + sz*dz/2)
             for sx, sy, sz in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                                (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    faces = ((0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),
             (0,4,7,3),(1,2,6,5))
    lines = [f"o {name}", "usemtl dark"]
    lines += ["v " + " ".join(f"{v:.6f}" for v in p) for p in verts]
    for face in faces:
        for i in (1,2):
            lines.append("f " + " ".join(str(first+j) for j in (face[0], face[i], face[i+1])))
    return obj + "\n".join(lines) + "\n"


def build_obj() -> str:
    obj = (SOURCE / f"{MODEL_ID}.obj").read_text(encoding="utf-8")
    # Section names are global in the game's vessel INI. A mesh named
    # FlightDeck would collide with the required [FlightDeck] gameplay section.
    if obj.count("o FlightDeck\n") != 1:
        raise ValueError("Expected exactly one authoring FlightDeck mesh")
    obj = obj.replace("o FlightDeck\n", "o Deck\n", 1)
    first = len(re.findall(r"(?m)^v ", obj)) + 1
    for name, center, extents in (
        ("Propeller_1", (-.075,-.095,-1.35), (.035,.035,.04)),
        ("Propeller_2", (.075,-.095,-1.35), (.035,.035,.04)),
        ("Rudder", (0,-.09,-1.40), (.018,.10,.08)),
    ):
        obj = append_box_obj(obj, name, center, extents, first)
        first += 8
    return obj


def vector(x: float, y: float, z: float) -> str:
    return f"{x:.4f},{y:.4f},{z:.4f}"


def zone(kind: str, name: str, points: list[tuple[float,float]]) -> str:
    lines = [f"Type={kind}", f"NumberOfPoints={len(points)}"]
    lines += [f"Point{i}={vector(x, DECK_Y + .02, z)}" for i,(x,z) in enumerate(points,1)]
    lines += [f"Name={name}"]
    return "\n".join(lines)


def vessel_ini() -> str:
    # Positive Z is the bow, as in the supplied native carrier examples.
    deck = [(-38*.36,-217*.5),(38*.35,-217*.5),(38*.49,-217*.38),
            (38*.49,217*.30),(38*.38,217*.5),(-38*.34,217*.5),
            (-38*.48,217*.31),(-38*.55,-217*.12),(-38*.54,-217*.32)]
    deck = [(x*SCALE,z*SCALE) for x,z in deck]
    mat_parts = {
        "UnderwaterHull":"underwater", "Deck":"deck", "Island":"island",
        "Bridge":"island", "BridgeGlass":"glass", "Mast":"island",
        "Funnel":"dark", "AirRadar":"dark", "SurfaceRadar":"dark",
        "Elevator_1":"hull", "Elevator_2":"hull", "Catapult_1":"gold",
        "Catapult_2":"gold", "SonarDome":"dark", "Propeller_1":"dark",
        "Propeller_2":"dark", "Rudder":"dark",
    }
    mat_parts.update({f"LandingEdge_{s}":"white" for s in (-1,1)})
    mat_parts.update({f"Centreline_{i}":"white" for i in range(14)})
    mat_parts.update({f"Sponson_{i}":"hull" for i in range(1,5)})
    mat_parts.update({f"AA_Base_{i}":"island" for i in range(1,5)})
    mat_parts.update({f"AA_Gun_{i}_{s}":"dark" for i in range(1,5) for s in (-1,1)})
    mat_parts.update({"NoisemakerPort":"dark", "NoisemakerStarboard":"dark"})
    submodels = "\n".join(f"Main_{i}={name}" for i,name in enumerate(mat_parts,1))
    submodels += "\nMainSystems_1=Propeller_1\nMainSystems_2=Propeller_2\nMainSystems_3=Rudder"
    submodel_sections = "\n\n".join(
        f"[{name}]\nMesh={name}\nMaterial={material}_mat.ini"
        for name,material in mat_parts.items()
    )
    zones = "\n\n".join(
        f"[DeckZone{i}]\n{zone(kind,name,points)}"
        for i,kind,name,points in (
            (1,"Runway","Bow catapult starboard",[(.01,.72),(.14,.72),(.14,1.42),(.01,1.42)]),
            (2,"Runway","Bow catapult port",[(-.15,.72),(-.02,.72),(-.02,1.42),(-.15,1.42)]),
            (3,"Runway","Angled recovery",[(.04,-1.42),(.16,-1.42),(-.10,.62),(-.21,.62)]),
            (4,"Deck","Flight deck",deck),
            (5,"NoPark","Island",[(.15,-.30),(.27,-.30),(.27,.04),(.15,.04)]),
        )
    )
    # AirGroup remains empty until historically suitable, game-original
    # aircraft have been identified. Capacity and deck routing can be tested.
    return f"""; Original 1959 RAN Melbourne prototype. No Workshop file is needed.
; Game-format study based on native Sea Power vessel reference syntax.
[General]
UnitType=Vessel
Length=217
Beam=24
CompartmentsHeight=0.25
ArmorType=Minor
DefaultCameraDistance=5.25
CameraPivotHeight=0.25

[OpticalView]
Views=binocular_7x50,binocular_10x50
DefaultView=binocular_7x50
Range=12000

[Physics]
Displacement=20000
MaxForwardVelocity=25
MaxBackwardVelocity=7
LinearDrag=0.97
MaxAccelerationFactor=0.20
MinAccelerationFactor=0.1
RudderTurnRate=1.5
RudderForce=0.3
TiltFactor=5.5
PitchFactor=0.0
TrimDepth=3
TrimAngle=-0.2
CenterToKeelDist=0.0

[Buoyancy]
Density=0.5
OutOfWaterDrag=25
SubmergedDrag=25
CavitationSpeed=4

[SensorData]
VisualIdentificationRange=15
IRSignature=VeryLarge
RCS=VeryLarge
BaseNoise=180
FlowNoise=1
CavitationNoise=7
BladesCount=2
MinNoiseClassificationTreshold=4
ElectricFrequency=60

[AI]
UnitCostValue=10000
UnitScoreValue=10
Role=Carrier,CVS
AAW_Capability=1
ASuW_Capability=1
ASW_Capability=1
MissilesToSaturate=6
TorpedoesToSaturate=3

[ControlSystem]
Collider=coll_ph

[MainPowerSystem]
Type=Steam
HorsePower=42000
ArmorType=Minor
IsCoveredByMainArmor=True
Collider=coll_engine

[PropulsionSystems]
NumberOfPropulsionSystems=2
[PropulsionSystem1]
Mount=Propeller_1
RotationDirection=Left
Collider=coll_prop_port
[PropulsionSystem2]
Mount=Propeller_2
RotationDirection=Right
Collider=coll_prop_stbd

[RudderSystems]
NumberOfRudderSystems=1
[RudderSystem1]
Mount=Rudder
Collider=coll_rudder

[AirGroup]
; Add a historically suitable 30-aircraft game-original group after unit QA.

[FlightDeck]
AircraftCapacity=30
NumberOfElevators=2
NumberOfLaunchPoints=3
NumberOfRecoveryPoints=2
NumberOfTaxiPaths=8
NumberOfDeckZones=5
ForwardsTaxiVelocity=12
BackwardsTaxiVelocity=-8
SlowTaxiVelocity=5
LaunchDelay=9
GroundCrewCount=8
DeckParkSlots=16
LandingSpeeds=300,220,140
HoldWaypoints=-2.7,2000,-6|-1.9,2000,-6.6|-1.1,2000,-6|-1.9,2000,-4.7
HoldStackSeparation=1000
HoldEnterDistance=3
HelicopterHoldWaypoints=1,400,-2.92|1,400,-1.46
HelicopterHoldStackSeparation=300
HelicopterHoldEnterDistance=2
HelicopterInitialWaypoint=-1,300,1
FlightDeck_AmmoCapacity=193000/193000
FlightDeck_NumberOfAccountableAmmunitionCategories=0
ArmorType=Minor
Collider=coll_hangar

[Elevator1]
AssociatedLaunchPoints=1,2
Mesh=Dummy
SpawnPosition={vector(.19,DECK_Y+.02,.73)}
SpawnRotation=270
RidePosition={vector(.19,DECK_Y+.02,.73)}
RideRotation=-90

[Elevator2]
AssociatedLaunchPoints=3
Mesh=Dummy
SpawnPosition={vector(.19,DECK_Y+.02,-.57)}
SpawnRotation=270
RidePosition={vector(.19,DECK_Y+.02,-.57)}
RideRotation=-90

[LaunchPoint1]
AllowedType=Plane,VTOL
Position={vector(.08,DECK_Y+.03,.76)}
Rotation=0
[LaunchPoint2]
AllowedType=Plane,VTOL
Position={vector(-.08,DECK_Y+.03,.76)}
Rotation=0
[LaunchPoint3]
AllowedType=Helicopter
Position={vector(-.12,DECK_Y+.03,-.55)}
Rotation=0

[RecoveryPoint1]
AllowedType=Plane,VTOL
AssociatedElevators=1,2
BlocksLaunchPoints=1,2,3
BlocksRecoveryPoints=2
Position={vector(.06,DECK_Y+.03,-1.40)}
ExitPosition={vector(-.12,DECK_Y+.03,.48)}
Rotation=353
CircuitWaypoints=0.5,800,-4.5|0.5,800,2.5|-0.75,800,3.2|-2,800,2.2|-2,500,-2.5|-0.75,500,-3.5|0.42,500,-3
LandingInterval=50
Arrested=True

[RecoveryPoint2]
AllowedType=Helicopter
AssociatedElevators=2
BlocksLaunchPoints=3
BlocksRecoveryPoints=1
Position={vector(-.12,DECK_Y+.03,-.75)}
Rotation=0
CircuitWaypoints=0.5,300,-4.5|0.5,300,2.5|-0.75,300,3.2|-2,300,2.2|-2,300,-2.5|-0.75,300,-3.5|0.42,300,-3
FinalApproachPath=0.8,300|0.4,200|0,100
LandingInterval=80

[TaxiPath1]
From=Elevator1
To=LaunchPoint1
Waypoints={vector(.13,DECK_Y+.03,.73)}
[TaxiPath2]
From=Elevator1
To=LaunchPoint2
Waypoints={vector(0,DECK_Y+.03,.68)}
[TaxiPath3]
From=Elevator2
To=LaunchPoint1
Waypoints={vector(0,DECK_Y+.03,0)}
[TaxiPath4]
From=Elevator2
To=LaunchPoint2
Waypoints={vector(-.10,DECK_Y+.03,0)}
[TaxiPath5]
From=Elevator2
To=LaunchPoint3
Waypoints={vector(-.04,DECK_Y+.03,-.55)}
[TaxiPath6]
From=RecoveryPoint1
To=Elevator1
Waypoints={vector(-.17,DECK_Y+.03,.30)}
[TaxiPath7]
From=RecoveryPoint1
To=Elevator2
Waypoints={vector(-.18,DECK_Y+.03,-.40)}
[TaxiPath8]
From=RecoveryPoint2
To=Elevator2
Waypoints={vector(0,DECK_Y+.03,-.57)}

{zones}

[SensorSystems]
NumberOfSensorSystems=1
[SensorSystem1]
Type=Visual
SystemName=Optics
Mount=Dummy
MountPosition={vector(.20,.40,-.10)}

[WeaponSystems]
NumberOfWeaponSystems=0

[Compartments]
Compartment1FirePosition={vector(0,.18,1)}
Compartment2FirePosition={vector(0,.18,0)}
Compartment3FirePosition={vector(0,.18,-1)}

[Models]
LODLevels=1
LOD1Distance=1.0
ResourcesFolder={MODEL_DIR}/
ResourcesRoot={MODEL_ID}.obj
ResourcesMesh=Hull
ResourcesMaterial=hull_mat.ini
ResourcesMeshHullCollider={MODEL_ID}.obj

[Submodels]
{submodels}

{submodel_sections}

[Colliders]
UseKinematicCollision=True
NumberOfMeshColliders=0
NumberOfColliders=7
Collider1=coll_ph
Collider2=coll_engine
Collider3=coll_prop_port
Collider4=coll_prop_stbd
Collider5=coll_rudder
Collider6=coll_hangar
Collider7=coll_deck

[coll_ph]
Collider=Box
Position={vector(0,.08,0)}
Rotation=0,0,0
Scale=0.36,0.22,3.1
[coll_engine]
Collider=Box
Position={vector(0,.08,-.48)}
Rotation=0,0,0
Scale=0.26,0.14,1.0
[coll_prop_port]
Collider=Box
Position={vector(-.075,-.095,-1.35)}
Rotation=0,0,0
Scale=.04,.04,.20
[coll_prop_stbd]
Collider=Box
Position={vector(.075,-.095,-1.35)}
Rotation=0,0,0
Scale=.04,.04,.20
[coll_rudder]
Collider=Box
Position={vector(0,-.09,-1.4)}
Rotation=0,0,0
Scale=.04,.12,.15
[coll_hangar]
Collider=Box
Position={vector(0,.17,0)}
Rotation=0,0,0
Scale=.32,.12,2.5
[coll_deck]
Collider=Box
Position={vector(0,DECK_Y,0)}
Rotation=0,0,0
Scale=.55,.025,3.16
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode("utf-8"))


def build(destination: Path) -> None:
    if not SOURCE.is_dir():
        raise FileNotFoundError(SOURCE)
    destination.mkdir(parents=True, exist_ok=True)
    ship_dir = destination / MODEL_DIR
    ship_dir.mkdir(parents=True, exist_ok=True)
    (ship_dir / f"{MODEL_ID}.obj").write_text(build_obj(), encoding="utf-8")
    shutil.copy2(SOURCE / f"{MODEL_ID}.mtl", ship_dir / f"{MODEL_ID}.mtl")
    (ship_dir / "normal.png").write_bytes(png((128,128,255,255)))
    (ship_dir / "specular.png").write_bytes(png((35,35,35,255)))
    for name, color in COLORS.items():
        (ship_dir / f"{name}.png").write_bytes(png(color))
        write(ship_dir / f"{name}_mat.ini", "[Shader]\nPath=Marmoset/Bumped Specular IBL\n\n"
              f"[Textures]\n_MainTex={MODEL_DIR}/{name}.png\n"
              f"_SpecTex={MODEL_DIR}/specular.png\n"
              f"_BumpMap={MODEL_DIR}/normal.png\n")
    write(destination / "vessels" / f"{VESSEL_ID}.ini", vessel_ini())
    write(destination / "vessels" / f"{VESSEL_ID}_variants.ini", """[General]
NationFlagReference=Flag1
NumberOfVariants=1

[Default]
ResourcesFlagFolder=ships/materials/textures/
FlagTexture=flag_australia
Nation=Australia
ServiceDate=1955|1967

[Variant1]
ResourcesFlagFolder=ships/materials/textures/
FlagTexture=flag_australia
Nation=Australia
ServiceDate=1955|1967
""")
    write(destination / "language_en/vessel_names.ini", f"""[{VESSEL_ID}]
Type=CVL,Light Carrier
Default=Melbourne 1959 RAN design,Melbourne 1959
DefaultDescription=Original Australian light-carrier prototype with a 30 aircraft capacity. Flight operations and combat systems are awaiting in-game validation.
Variant1=Melbourne R21 Original,Melbourne R21 Original
""")
    write(destination / "_info.ini", """[Language_en]
Name=RAN Carrier Original 1959 Prototype
Description=Independent original Australian carrier geometry and game-format integration prototype. No Workshop dependency.

[Compatibility]
ApproximateVersion=0.8.5
""")
    (destination / "README.txt").write_text(
        "RAN Carrier Original 1959 Prototype\n"
        "Original 1959 hull, flight-deck geometry and 30-aircraft capacity.\n"
        "No RADF or other Workshop dependency. Uses only built-in Sea Power\n"
        "visual optics and Australian flag resources. The air group is\n"
        "unpopulated; launch, recovery, sensors and weapons need game QA.\n"
        "Disable the old Melbourne Test before comparing the editor list.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEST)
    args = parser.parse_args()
    build(args.destination)
    print(f"[OK] Built original, Workshop-independent milestone at {args.destination}")


if __name__ == "__main__":
    main()

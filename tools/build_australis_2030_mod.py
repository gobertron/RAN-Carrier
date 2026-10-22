#!/usr/bin/env python3
"""Build a standalone, opt-in Sea Power editor-test package for Australis.

The builder writes only under game-mod/RAN-Carrier-Australis-2030 (or an
explicit --destination). It never changes a live installation or Workshop.
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "australis-2030"
sys.dont_write_bytecode = True
sys.path.insert(0, str(DESIGN))
from build import (  # noqa: E402
    AFT_ISLAND_BASE, CATAPULTS, COLORS, DECK, DECK_SURFACE_Y, ELEVATORS,
    LANDING_LANE_A, LANDING_LANE_B, MAIN_ISLAND_BASE, VERTICAL_SPOTS, geometry,
    WIDTH_SCALE,
)
from generate_source_models import Mesh  # noqa: E402
from rebuild_game_scale import METRES_PER_UNIT  # noqa: E402

ID = "ran_cvn_australis_2030"
MOD_NAME = "RAN-Carrier-Australis-2030"
SHIP_DIR = f"ships/{ID}"
DEST = ROOT / "game-mod" / MOD_NAME
SCALE = 1 / METRES_PER_UNIT
DECK_HEIGHT = DECK_SURFACE_Y * SCALE
LAUNCH_ASSOC = ((1,2),(3,2),(1,2),(4,5,6,7))


def vec(x: float, y: float, z: float) -> str:
    return f"{x*WIDTH_SCALE*SCALE:.6f},{y*SCALE:.6f},{z*SCALE:.6f}"


def point(x: float, z: float, above: float = .16) -> str:
    return vec(x, DECK_SURFACE_Y + above, z)


def write_ini(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + content.replace("\n", "\r\n").encode("utf-8"))


def png(rgba: tuple[int, int, int, int]) -> bytes:
    """Tiny original solid-color texture; no Workshop texture is copied."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">2I5B", 8, 8, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\0" + bytes(rgba)*8)*8))
            + chunk(b"IEND", b""))


def model(ship: Path) -> dict[str, str]:
    """Combine static details by material to keep native submodel count small."""
    source = geometry()
    out = Mesh()
    materials = {}
    for src,dst in (("HardChineHull","Hull"),("FacetedFlightDeck","Deck")):
        name,v,faces,mat = next(part for part in source.parts if part[0] == src)
        out.add(dst,v,faces,mat)
        materials[dst] = mat
    for material in COLORS:
        elements = [(v,faces) for name,v,faces,mat in source.parts
                    if mat == material and name not in
                    ("HardChineHull","FacetedFlightDeck")]
        if not elements:
            continue
        vertices,all_faces = [],[]
        for v,faces in elements:
            offset = len(vertices)
            vertices.extend(v)
            all_faces.extend([[index+offset for index in f] for f in faces])
        name = "Surface_" + material.capitalize()
        out.add(name,vertices,all_faces,material)
        materials[name] = material
    # The rudder/propeller box vertices are local to these moving mounts.
    for name,dims in {"Propeller_1": (.55,.55,.55),
                      "Propeller_2": (.55,.55,.55),
                      "Rudder": (.25,1.1,1.05)}.items():
        out.box(name,0,0,0,*dims,"dark")
        materials[name] = "dark"
    # Collision geometry is a separate OBJ object. It is never listed as a
    # visible submodel, but the game can use it in preference to its fallback.
    out.box("coll_hull_main",0,10,0,52*WIDTH_SCALE,20,320,"hull")
    path = ship / f"{ID}.obj"
    out.save(path, scale=SCALE)
    # Working Workshop carrier OBJ files carry v/vt/vn face indices. The
    # earlier prototype exported bare vertex indices, which may cause the
    # game loader to omit a moving mesh. Give this solid-colour prototype
    # planar UVs and explicit flat normals without changing its geometry.
    obj_lines = ["# Original Australis geometry; approximate Sea Power units",
                 f"mtllib {ID}.mtl"]
    vertex_offset = 0
    normal_offset = 0
    for name,vertices,faces,material in out.parts:
        obj_lines.append(f"o {name}")
        obj_lines.extend("v " + " ".join(f"{axis*SCALE:.6f}" for axis in vertex)
                         for vertex in vertices)
        obj_lines.extend(f"vt {(vertex[0]/20)%1:.6f} {(vertex[2]/20)%1:.6f}"
                         for vertex in vertices)
        normals: list[str] = []
        triangles: list[tuple[int,int,int,int]] = []
        for face in faces:
            for i in range(1,len(face)-1):
                a,b,c = face[0],face[i],face[i+1]
                p,q,r = vertices[a],vertices[b],vertices[c]
                ux,uy,uz = (q[j]-p[j] for j in range(3))
                vx,vy,vz = (r[j]-p[j] for j in range(3))
                nx,ny,nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
                length = math.sqrt(nx*nx+ny*ny+nz*nz)
                if length < 1e-12:
                    raise ValueError(f"Degenerate triangle in {name}")
                normals.append(f"vn {nx/length:.6f} {ny/length:.6f} {nz/length:.6f}")
                normal_offset += 1
                triangles.append((a,b,c,normal_offset))
        obj_lines.extend(normals)
        obj_lines.append(f"usemtl {material}")
        obj_lines.append("s off")
        for a,b,c,n in triangles:
            obj_lines.append("f " + " ".join(
                f"{vertex_offset+j}/{vertex_offset+j}/{n}" for j in (a+1,b+1,c+1)))
        vertex_offset += len(vertices)
    path.write_text("\n".join(obj_lines)+"\n",encoding="utf-8")
    assert len({part[0] for part in out.parts}) == len(out.parts)
    return materials


def section(name: str, entries: list[str] | str) -> str:
    return f"[{name}]\n" + ("\n".join(entries) if isinstance(entries, list) else entries) + "\n"


def zone(name: str, kind: str, coords: list[tuple[float, float]]) -> str:
    return "\n".join([f"Type={kind}", f"NumberOfPoints={len(coords)}"]
                     + [f"Point{i}={point(x,z,.02)}"
                        for i,(x,z) in enumerate(coords,1)]
                     + [f"Name={name}"])


def catapult_zone(start: tuple[float,float],
                  end: tuple[float,float]) -> list[tuple[float,float]]:
    (x,z),(ex,ez) = start,end
    direction = (ex-x, ez-z)
    norm = math.hypot(*direction)
    lateral = (-direction[1]*5/norm, direction[0]*5/norm)
    return [(x+lateral[0],z-3+lateral[1]), (x-lateral[0],z-3-lateral[1]),
            (ex-lateral[0],ez-lateral[1]), (ex+lateral[0],ez+lateral[1])]


def routes() -> list[tuple[str, str, list[tuple[float,float]]]]:
    """Single-aircraft demonstration taxi routes; not a deck-cycle analysis."""
    out: list[tuple[str,str,list[tuple[float,float]]]] = []
    for e, launches in enumerate(LAUNCH_ASSOC[:3],1):
        for launch in launches:
            (sx,sz),(ex,ez) = CATAPULTS[launch-1]
            length = math.hypot((ex-sx)*WIDTH_SCALE,ez-sz)
            approach = (sx-20*(ex-sx)/length,sz-20*(ez-sz)/length)
            if e == 1: way = [(0,-48),(0,32),approach]
            elif e == 2: way = [(23,50),approach]
            else: way = [(-30,ELEVATORS[2][1]+12),(-28,32),approach]
            out.append((f"Elevator{e}",f"LaunchPoint{launch}",way))
    for i,(x,z) in enumerate(VERTICAL_SPOTS,4):
        out.append(("Elevator4",f"LaunchPoint{i}",[(10,-128),(x,z-12)]))
    out += [
        ("RecoveryPoint1","Elevator1",[(-25,-62),(0,-50)]),
        ("RecoveryPoint1","Elevator2",[(-26,-35),(0,46),(23,63)]),
        ("RecoveryPoint1","Elevator3",[(-30,50),(-34,ELEVATORS[2][1]+8)]),
    ]
    for i,(x,z) in enumerate(VERTICAL_SPOTS,2):
        if i < 5:
            out.append((f"RecoveryPoint{i}","Elevator4",[(10,-128)]))
        else:
            out.append((f"RecoveryPoint{i}","Elevator1",[(10,-61)]))
    return out


def vessel_ini(material: dict[str,str]) -> str:
    moving = {"Propeller_1","Propeller_2","Rudder"}
    static = [name for name in material if name not in moving
              and name not in ("Hull", "coll_hull_main")]
    mounts = {"Propeller_1": (-7,-6,-147),
              "Propeller_2": (7,-6,-147),
              "Rudder": (0,-5,-153)}
    parts = [
        "; Independent Australis editor test. No third-party assets repackaged.",
        section("General",[
            "UnitType=Vessel","DefaultCameraDistance=8.0",
            "MinCameraDistanceForeAft=3.2","MinCameraDistanceBroadside=1.5",
            "CameraPivotHeight=0.34","Length=370",f"Beam={44*WIDTH_SCALE:g}",
            "CompartmentsHeight=0.25","ArmorType=Moderate",
            f"FrontalArea={2450*WIDTH_SCALE:g}","SideArea=13200",
            f"BottomArea={25500*WIDTH_SCALE:g}"]),
        section("OpticalView",[
            "Views=binocular_7x50,binocular_10x50",
            "DefaultView=binocular_7x50"]),
        section("AirGroup",[
            "; Empty while aircraft compatibility and the 99-place deck cycle",
            "; are tested. This avoids a dependency on RADF or the F-111N pack."]),
        section("FlightDeck",[
            "AircraftCapacity=99","NumberOfElevators=4",
            "NumberOfLaunchPoints=7","NumberOfRecoveryPoints=5",
            f"NumberOfTaxiPaths={len(routes())}","NumberOfDeckZones=7",
            "ForwardsTaxiVelocity=12","BackwardsTaxiVelocity=-8",
            "SlowTaxiVelocity=6","LaunchDelay=1","GroundCrewCount=16",
            "DeckParkSlots=44","LandingWhileLaunching=False",
            "HelicopterInitialWaypoint=-1,300,1",
            "HoldWaypoints=-2.7,2000,-6|-1.9,2000,-6.6|-1.1,2000,-6|-1.9,2000,-4.7",
            "LandingSpeeds=350,240,150","HoldStackSeparation=1000",
            "HoldEnterDistance=3",
            "HelicopterHoldWaypoints=1,400,-2.92|1,400,-1.46",
            "HelicopterHoldStackSeparation=500","HelicopterHoldEnterDistance=2",
            "FlightDeck_AmmoCapacity=1200000/1200000",
            "FlightDeck_NumberOfAccountableAmmunitionCategories=0",
            "ArmorType=Moderate","Collider=coll_hangar"]),
    ]
    for i,(x,z) in enumerate(ELEVATORS,1):
        inner_x = (34 if x > 0 else -34)
        parts.append(section(f"Elevator{i}",[
            "AssociatedLaunchPoints="+",".join(map(str,LAUNCH_ASSOC[i-1])),
            "Mesh=Dummy",f"SpawnPosition={point(inner_x,z)}",
            "SpawnRotation=-90",f"RidePosition={point(inner_x,z)}",
            "RideRotation=-90","EmbarkTime=10","RecycleTime=15"]))
    for i,((x,z),(ex,ez)) in enumerate(CATAPULTS,1):
        rotation = math.degrees(math.atan2((ex-x)*WIDTH_SCALE,ez-z))
        interlock = "1,3" if i == 2 else "2"
        parts.append(section(f"LaunchPoint{i}",[
            "AllowedType=Plane,VTOL",f"Position={point(x,z)}",
            f"BlocksLaunchPoints={interlock}",
            f"TakeoffRequiresFreeLaunchpoints={interlock}",
            f"Rotation={rotation:.3f}","CatapultParticles=None",
            f"CatapultLength={math.hypot((ex-x)*WIDTH_SCALE,ez-z):.3f}"]))
    for i,(x,z) in enumerate(VERTICAL_SPOTS,4):
        parts.append(section(f"LaunchPoint{i}",[
            "AllowedType=Helicopter,VTOL",
            f"Position={point(x,z)}","Rotation=-12"]))
    touchdown = LANDING_LANE_A + (LANDING_LANE_B-LANDING_LANE_A)*.36
    parts.append(section("RecoveryPoint1",[
        "AllowedType=Plane,VTOL","AssociatedElevators=1,2,3",
        "BlocksLaunchPoints=1,2,3,4,5,6,7",
        "BlocksRecoveryPoints=2,3,4,5",
        f"Position={point(*touchdown)}",f"ExitPosition={point(*LANDING_LANE_B)}",
        "Rotation="+f"{math.degrees(math.atan2((LANDING_LANE_B[0]-LANDING_LANE_A[0])*WIDTH_SCALE,LANDING_LANE_B[1]-LANDING_LANE_A[1])):.3f}",
        "CircuitWaypoints=0.5,800,-4.5|0.5,800,2.5|-0.75,800,3.2|-2,800,2.2|-2,500,-2.5|-0.75,500,-3.5|0.42,500,-3",
        "LandingInterval=56","Arrested=True"]))
    for i,(x,z) in enumerate(VERTICAL_SPOTS,2):
        elevator = 4 if i < 5 else 1
        other = [str(j) for j in range(1,6) if j != i]
        parts.append(section(f"RecoveryPoint{i}",[
            "AllowedType=Helicopter,VTOL",f"AssociatedElevators={elevator}",
            "BlocksRecoveryPoints="+",".join(other),
            f"Position={point(x,z)}","Rotation=-12",
            "HelicopterCircuitWaypoints=0,300,-2|0,300,-1",
            "FinalApproachPath=0.8,300|0.4,200|0,100",
            "LandingInterval=80"]))
    for i,(frm,to,waypoints) in enumerate(routes(),1):
        parts.append(section(f"TaxiPath{i}",[
            f"From={frm}",f"To={to}",
            "Waypoints="+"|".join(point(x,z) for x,z in waypoints)]))
    deckzones = [(f"Catapult {i}", "Runway",catapult_zone(*route))
                 for i,route in enumerate(CATAPULTS,1)]
    a,b = LANDING_LANE_A,LANDING_LANE_B
    deckzones += [("Angled recovery","Runway",
                   [(a[0]-11,a[1]),(a[0]+11,a[1]),
                    (b[0]+11,b[1]),(b[0]-11,b[1])]),
                  ("Flight deck","Deck",DECK),
                  ("Main island","NoPark",MAIN_ISLAND_BASE),
                  ("Aft island","NoPark",AFT_ISLAND_BASE)]
    for i,(name,kind,coords) in enumerate(deckzones,1):
        parts.append(section(f"DeckZone{i}",zone(name,kind,coords)))
    parts += [
        section("Physics",[
            f"Displacement={120000*WIDTH_SCALE:g}","MaxForwardVelocity=30",
            "MaxBackwardVelocity=7","LinearDrag=0.97",
            "MaxAccelerationFactor=0.20","MinAccelerationFactor=0.08",
            "RudderTurnRate=1.25","RudderForce=0.35",
            "TiltFactor=7.0","PitchFactor=0.0",
            "TrimDepth=0.0","TrimAngle=0.0","CenterToKeelDist=0.0"]),
        section("Buoyancy",[
            "Density=0.5","OutOfWaterDrag=25","SubmergedDrag=25",
            "CavitationSpeed=4"]),
        section("SensorData",[
            "VisualIdentificationRange=15.0","IRSignature=VeryLarge",
            "RCS=VeryLarge","BaseNoise=170","FlowNoise=1",
            "CavitationNoise=10","BladesCount=2",
            "MinNoiseClassificationTreshold=5","ElectricFrequency=60"]),
        section("AI",[
            "UnitCostValue=12000","UnitScoreValue=15","Role=Carrier",
            "AAW_Capability=1","ASuW_Capability=1","ASW_Capability=1",
            "MissilesToSaturate=16","TorpedoesToSaturate=5"]),
        section("ControlSystem",["Collider=coll_bridge",
                                 "ArmorType=Minor","ModuleType=CIC"]),
        section("MainPowerSystem",[
            "Type=Nuclear","HorsePower=280000","ArmorType=Moderate",
            "IsCoveredByMainArmor=True","Collider=coll_engine"]),
        section("PropulsionSystems","NumberOfPropulsionSystems=2"),
        section("PropulsionSystem1",[
            "Mount=Propeller_1","RotationDirection=Left",
            "Collider=coll_prop_port"]),
        section("PropulsionSystem2",[
            "Mount=Propeller_2","RotationDirection=Right",
            "Collider=coll_prop_stbd"]),
        section("RudderSystems","NumberOfRudderSystems=1"),
        section("RudderSystem1",["Mount=Rudder","Collider=coll_rudder"]),
        section("SensorSystems","NumberOfSensorSystems=1"),
        section("SensorSystem1",[
            "Type=Visual","SystemName=Optics","Mount=Dummy",
            f"MountPosition={vec(33,40,5)}"]),
        section("WeaponSystems","NumberOfWeaponSystems=0"),
        section("Compartments",[
            f"Compartment1FirePosition={vec(0,15,95)}",
            f"Compartment2FirePosition={vec(0,15,0)}",
            f"Compartment3FirePosition={vec(0,15,-95)}"]),
        section("Models",[
            "LODLevels=1","LOD1Distance=1.0",
            "; Original-game carrier bundle is a resource fallback only.",
            "AssetBundleMeshes=/AssetBundles/StandaloneWindows/ships",
            "AssetBundleMaterials=/AssetBundles/StandaloneWindows/ships",
            "AssetBundleMesh=usn_cvn_nimitz",
            "AssetBundleDamagedMesh=usn_cvn_nimitz_d",
            "AssetBundleMaterial=usn_cvn_nimitz_mat",
            "AssetBundleMeshHullCollider=usn_cvn_nimitz_coll_hull",
            f"ResourcesFolder={SHIP_DIR}/",f"ResourcesRoot={ID}.obj",
            "ResourcesMesh=Hull","ResourcesMaterial=hull_mat.ini",
            "ResourcesMeshHullCollider=coll_hull_main"]),
        section("Submodels",[
            *[f"Main_{i}={name}" for i,name in enumerate(static,1)],
            "MainSystems_1=Propeller_1","MainSystems_2=Propeller_2",
            "MainSystems_3=Rudder","General_1=Flag1"]),
    ]
    for name in static:
        parts.append(section(name,[
            f"Mesh={name}",f"Material={material[name]}_mat.ini"]))
    for name in ("Propeller_1","Propeller_2","Rudder"):
        parts.append(section(name,[
            f"ResourcesMeshFolder={SHIP_DIR}/",f"RootMesh={ID}.obj",
            f"Mesh={name}",f"Material={material[name]}_mat.ini",
            f"Position={vec(*mounts[name])}"]))
    parts.append(section("Flag1",[
        "ResourcesMeshFolder=ships/usn_ddg_adams/",
        "RootMesh=usn_ddg_adams",
        "Mesh=usn_ddg_adams_animatedflag",
        "ResourcesMaterialFolder=ships/materials/",
        # The stock Adams flag already has its mast offset baked in. The
        # former extra 50 m placed it high above our 55 m enclosed mast.
        "Material=flag_us",f"Position={vec(33,25,10)}",
        "Rotation=270,90,0"]))
    colliders = {
        "coll_bridge": ("Box",(33,34,2),(14,22,60)),
        "coll_engine": ("Box",(0,4,-45),(30,12,75)),
        "coll_prop_port": ("Box",(-7,-6,-147),(2,3,8)),
        "coll_prop_stbd": ("Box",(7,-6,-147),(2,3,8)),
        "coll_rudder": ("Box",(0,-5,-153),(2,5,10)),
        "coll_hangar": ("Box",(0,15,0),(48,10,245)),
        "coll_deck": ("Box",(0,22,0),(76,2,355)),
        "coll_hull": ("Box",(0,2,0),(48,26,335)),
    }
    parts.append(section("Colliders",[
        "UseKinematicCollision=True","NumberOfMeshColliders=1",
        "MeshCollider1=coll_hull_main",
        f"NumberOfColliders={len(colliders)}",
        *[f"Collider{i}={name}" for i,name in enumerate(colliders,1)]]))
    for name,(kind,pos,dims) in colliders.items():
        parts.append(section(name,[
            f"Collider={kind}",f"Position={vec(*pos)}","Rotation=0,0,0",
            f"Scale={vec(*dims)}"]))
    parts.append(section("Particles",[
        "BowWave=ships/particles/bowwave","PropWash=ships/particles/propwash",
        "Cavitation=ships/particles/usn_cvn_nimitz_cavitation",
        f"BowWavePosition={vec(0,0,170)}",
        f"PropWashPosition={vec(0,-5,-155)}"]))
    # Rudder initialization reads the stern foam trail's transform. Without
    # [Foam], Sea Power never creates that object and throws a null reference.
    parts.append(section("Foam",[
        "HullFoamTexture=ships/particles/wake/Ceto_Hullwake",
        f"HullFoamPosition={vec(0,0,53)}",
        "HullFoamDuration=20","HullFoamSize=0.95",
        "HullFoamSpacing=0.55","HullFoamExpansion=0.055",
        "HullFoamMomentum=0","HullFoamSpin=0","HullFoamAlpha=2",
        "HullFoamJitter=0.25",
        "SternFoamTexture=ships/particles/wake/Ceto_Propwash",
        f"SternFoamPosition={vec(0,0,-150)}",
        "SternFoamDuration=65","SternFoamSize=0.95",
        "SternFoamSpacing=0.45","SternFoamExpansion=0.025",
        "SternFoamMomentum=0.01","SternFoamSpin=0",
        "SternFoamAlpha=2","SternFoamJitter=0.25",
        "OverlayHeightTexture=ships/particles/wake/bowwave_hm",
        "OverlayHeightMaskTexture=ships/particles/wake/bowwave_hm",
        "OverlayHeightMaxAlpha=0.1",
        "OverlayNormalTexture=ships/particles/wake/bowwave_normal",
        "OverlayNormalMaskTexture=ships/particles/wake/bowwave_normal",
        "OverlayNormalMaxAlpha=10.0",
        "OverlayFoamTexture=ships/particles/wake/bowwave_tx2",
        "OverlayFoamMaskTexture=ships/particles/wake/bowwave_mask",
        "OverlayFoamMaxAlpha=1.0","KelvinWaves=7.65,7.65",
        "VelocityForMaxParticles=15"]))
    return "\n".join(parts)


def build(destination: Path = DEST) -> None:
    ship = destination / SHIP_DIR
    ship.mkdir(parents=True, exist_ok=True)
    materials = model(ship)
    (ship / "normal.png").write_bytes(png((128,128,255,255)))
    (ship / "specular.png").write_bytes(png((35,35,35,255)))
    for name, hexcolor in COLORS.items():
        rgb = tuple(bytes.fromhex(hexcolor.removeprefix("#")))
        (ship / f"{name}.png").write_bytes(png((*rgb,255)))
        write_ini(ship / f"{name}_mat.ini",
                  "[Shader]\nPath=Marmoset/Bumped Specular IBL\n\n"
                  "[Textures]\n"
                  f"_MainTex={SHIP_DIR}/{name}.png\n"
                  f"_SpecTex={SHIP_DIR}/specular.png\n"
                  f"_BumpMap={SHIP_DIR}/normal.png\n")
    write_ini(destination / f"vessels/{ID}.ini", vessel_ini(materials))
    write_ini(destination / f"vessels/{ID}_variants.ini",
              "[General]\nNationFlagReference=Flag1\nNumberOfVariants=1\n\n"
              "[Default]\nResourcesFlagFolder=ships/materials/textures/\n"
              "FlagTexture=flag_australia\nNation=Australia\n"
              "ServiceDate=2025|2055\n\n"
              "[Variant1]\nResourcesFlagFolder=ships/materials/textures/\n"
              "FlagTexture=flag_australia\nNation=Australia\n"
              "ServiceDate=2025|2055\n")
    write_ini(destination / "language_en/vessel_names.ini",
              f"[{ID}]\nType=CVN,Aircraft Carrier\n"
              "Default=Australis class 2030,Australis 2030\n"
              "DefaultDescription=Original future RAN carrier prototype. "
              "99-aircraft target; carrier deck operations await in-game tests.\n"
              "Variant1=HMAS Australis test,HMAS Australis test\n")
    write_ini(destination / "_info.ini",
              "[Language_en]\nName=RAN Australis 2030 Editor Prototype\n"
              "Description=Independent Australian carrier model and flight-deck test. "
              "No RADF or Workshop files are bundled.\n\n"
              "[Compatibility]\nApproximateVersion=0.8.5\n")
    (destination / "README.txt").write_text(
        "RAN Australis 2030 Editor Prototype\n"
        "This is an opt-in editor test of an original mesh and native-style "
        "carrier deck routes. It has no air group, no operational laser, radar "
        "or ECM, and no tested deck animation. The 99-aircraft count is a design "
        "target. A stock Sea Power Nimitz bundle is named as a runtime fallback; "
        "no stock or Workshop asset bytes are copied.\n"
        "The user confirmed mission loading and original hull rendering on "
        "22 October 2026 after the Foam section was added. This revision "
        "uses an 82 m deck with more widely separated outer catapults, a "
        "staggered interlocked centre track and independent aft helicopter "
        "launch spots. LaunchDelay=1 is a shared one-second minimum, not a "
        "guarantee of synchronized launches. Flight operations need game QA.\n"
        "Test with the failed Melbourne prototype disabled. If the editor "
        "errors, collect the current logs, withdraw only this mod, and share "
        "the latest Sea Power Player.log.\n",
        encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEST)
    args = parser.parse_args()
    build(args.destination)
    print(f"[OK] Built {MOD_NAME}: {args.destination}")
    print("[STATUS] User confirmed hull loading; slimmer deck and launch changes await game QA")


if __name__ == "__main__":
    main()

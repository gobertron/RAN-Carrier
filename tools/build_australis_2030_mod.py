#!/usr/bin/env python3
"""Build a standalone, opt-in Sea Power editor-test package for Australis.

The builder writes only under game-mod/RAN-Carrier-Australis-2030 (or an
explicit --destination). It never changes a live installation or Workshop.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import zlib
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "australis-2030"
sys.dont_write_bytecode = True
sys.path.insert(0, str(DESIGN))
from build import (  # noqa: E402
    AFT_ISLAND_BASE, CATAPULTS, COLORS, DECK, DECK_SURFACE_Y, ELEVATORS,
    LANDING_LANE_A, LANDING_LANE_B, MAIN_ISLAND_BASE, VERTICAL_SPOTS, geometry,
    WIDTH_SCALE, BOW_CATAPULT_IDS, WAIST_CATAPULT_IDS, CATAPULT_INTERLOCKS,
    HELO_INTERLOCKS, HELO_ELEVATORS, LIFT_SURFACE_Y, HELIPAD_SURFACE_Y,
    catapult_point, landing_point, LASERS,
)
from generate_source_models import Mesh  # noqa: E402
from rebuild_game_scale import METRES_PER_UNIT  # noqa: E402
from combat_fit import FIT, native_sections, custom_profiles, gun_mounts, deck_weapon_zones  # noqa: E402



from enclosed_deck import BAYS, BY_KEY, moving_specs, add_meshes
from build_internal_arrangement import make_arrangement
from naval_hull import collision_mesh,design
from waterjet_geometry import JET_CENTRES,IMPELLER_CENTRES,STEERING_INDICES,add_impeller,add_steering_nozzle,wet_hull

IMPELLERS=[f'WaterjetImpeller{i}' for i in range(1,9)]
STEERING=[f'WaterjetSteering{i}' for i in STEERING_INDICES]
PROPULSION_MODELS=IMPELLERS+STEERING

def moving_model_specs():
    result=moving_specs()
    for mount in gun_mounts():
        result += [dict(name=mount["mount"],parent=BY_KEY[f"{mount['label']}_{mount['index'] }"].root,position=(0,1,0)),dict(name=mount["barrel"],parent=mount["mount"],position=(0,0,0))]
    return result

ID = "ran_cvn_australis_2030"
MOD_NAME = "RAN-Carrier-Australis-2030"
SHIP_DIR = f"ships/{ID}"
DEST = ROOT / "game-mod" / MOD_NAME
SCALE = 1 / METRES_PER_UNIT
DECK_HEIGHT = DECK_SURFACE_Y * SCALE
LAUNCH_ASSOC = ((1,2,3),(1,2,3),(1,2,3,4),(1,2,3,6,5))
# Native FlightDeckAircraftSupportPoint keys, verified against the supplied
# engine schema. Do not restrict aircraft classes, roles or VTOL loadouts.
AIRCRAFT_SIZE_SUPPORT = ["SupportsSmall=True", "SupportsLarge=True", "SupportsVeryLarge=True"]


def weapon_model_names():
    # Roots precede their dependent yaw/elevation submodels.
    yield from (r['name'] for r in moving_model_specs())


def vec(x: float, y: float, z: float) -> str:
    return f"{x*WIDTH_SCALE*SCALE:.6f},{y*SCALE:.6f},{z*SCALE:.6f}"


def point(x: float, z: float, above: float = 0) -> str:
    # Sea Power already adds each aircraft's GroundPivot correction. These
    # are tyre-contact heights, not the aircraft model's centre or pivot.
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
    gun_parts = {f"{mount['label']}_{part}_{mount['index']}"
                 for mount in gun_mounts() for part in ("Housing","Barrel")}
    gun_parts.update(spec["name"] for spec in moving_model_specs())
    gun_parts.update(f"InternalLift_{i}" for i in range(1,5))
    moved_source={}
    for b in BAYS:
        if b.key.startswith(('ESSM_','RAM_','SRBOC_','Nulka_')):
            kind,index=b.key.rsplit('_',1)
            moved_source[b.root]=[p for p in source.parts if p[0].startswith(f'{kind}_Housing_{index}') or p[0].startswith(f'{kind}_Tube_{index}_') or p[0]==f'{kind}_Launcher_{index}']
            gun_parts.update(p[0] for p in moved_source[b.root])
    for src,dst in (("HardChineHull","Hull"),("FacetedFlightDeck","Deck"),("UnderwaterBody","UnderwaterHull")):
        name,v,faces,mat = next(part for part in source.parts if part[0] == src)
        out.add(dst,v,faces,mat)
        materials[dst] = mat
    # Keep the wet ducts and fixed nozzles separately identifiable for audits.
    for name,v,faces,mat in source.parts:
        if name.startswith('Waterjet'):
            out.add(name,v,faces,mat);materials[name]=mat
    for material in COLORS:
        elements = [(v,faces) for name,v,faces,mat in source.parts
                    if mat == material and name not in
                    ("HardChineHull","FacetedFlightDeck","UnderwaterBody") and name not in gun_parts and not name.startswith('Waterjet')]
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
    for name in IMPELLERS:
        add_impeller(out,name);materials[name]='dark'
    for name in STEERING:
        add_steering_nozzle(out,name);materials[name]='edge'
    # Original moving yaw bodies and elevation barrels. Each gun resolves
    # to a real registered object rather than a placeholder dictionary key.
    for mount in gun_mounts():
        out.box(mount["mount"],0,0,0,2.8,1.7,3,"island")
        materials[mount["mount"]]="island"
        out.box(mount["barrel"],0,0,1.8,.3,.22,2.1,"dark")
        materials[mount["barrel"]]="dark"
    for i in range(1,5):
        out.box(f"LiftPlatform{i}",0,-.085,0,22,.17,26,"hatch")
        materials[f"LiftPlatform{i}"]="hatch"
    for i in range(1,5):
        out.box(f"PVLS_{i}_LaunchBase",0,0,0,.001,.001,.001,"dark")
        materials[f"PVLS_{i}_LaunchBase"]="dark"
    add_meshes(out,local=True)
    for root,parts_to_move in moved_source.items():
        b=next(b for b in BAYS if b.root==root)
        target=next(i for i,p in enumerate(out.parts) if p[0]==root)
        name,v,f,mat=out.parts[target]
        verts=v.tolist();faces=[list(x) for x in f]
        for _,sv,sf,_ in parts_to_move:
            offset=len(verts);verts.extend((sv-np.array((b.x,b.y,b.z))).tolist())
            faces.extend([[i+offset for i in face] for face in sf])
        out.parts[target]=(name,np.array(verts),faces,mat)
    materials.update({s["name"]:("hatch" if "Door" in s["name"] else "dark")
                      for s in moving_model_specs() if s["name"] not in materials})
    # Collision geometry is a separate OBJ object. It is never listed as a
    # visible submodel, but the game can use it in preference to its fallback.
    from build import hull_outline
    cv,cf=collision_mesh(DECK,hull_outline(.985,1.,1.),hull_outline(1.01,1.,1.),WIDTH_SCALE)
    out.add("coll_hull_main",cv,cf,"hull")
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
        normal_ids = {}
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
                row=f"vn {nx/length:.6f} {ny/length:.6f} {nz/length:.6f}"
                if row not in normal_ids:
                    normals.append(row);normal_offset+=1;normal_ids[row]=normal_offset
                triangles.append((a,b,c,normal_ids[row]))
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
    route = (start,end)
    length = math.hypot((end[0]-start[0])*WIDTH_SCALE,end[1]-start[1])
    return [catapult_point(route,along,across)
            for along,across in ((-3,-5),(-3,5),(length,5),(length,-5))]


def routes():
    """Native directed taxi graph; all four lifts serve all three catapults.

    X values below are physical metres.  Port-side longitudinal access avoids
    the island footprints and the three helicopter pad centres.  These are
    centreline routes, not a swept-clearance approval for every add-on aircraft.
    Shared access and the arrested-recovery corridor remain native queues.
    """
    out=[]
    def author(points):
        return [(x/WIDTH_SCALE,z) for x,z in points]
    corridor=-14.
    bow_crossing=44.
    for e,(x,z) in enumerate(ELEVATORS,1):
        for launch in (1,2,3):
            approach=catapult_point(CATAPULTS[launch-1],-20)
            ax,az=approach[0]*WIDTH_SCALE,approach[1]
            if launch<=2:
                # All lifts join the same port access lane before lining up.
                # Bow aircraft approach the staging point facing forward.
                physical=[(corridor,z),(corridor,bow_crossing),
                          (ax,bow_crossing),(ax,az)]
            else:
                # Approach the waist shuttle from aft, rather than crossing
                # the main island or a non-origin lift shaft.
                aft=-50. if e<=3 else -68.
                physical=[(corridor,z),(corridor,aft),(ax,aft),(ax,az)]
            out.append((f'Elevator{e}',f'LaunchPoint{launch}',author(physical)))
        # The recovery endpoint is already the forward end of the angled lane.
        # Leave it toward port access, then enter only the assigned lift.
        physical=[(corridor,26.),(corridor,z)]
        out.append(('RecoveryPoint1',f'Elevator{e}',author(physical)))
    for launch,e,way in ((4,3,[(11,-1),(11,2)]),
                         (5,4,[(13,-50),(13.6,-71)]),
                         (6,4,[(-9,-50),(-9,-132),(20.2,-132),(20.2,-124)])):
        out.append((f'Elevator{e}',f'LaunchPoint{launch}',author(way)))
        # Recovery order is aft, front, middle.
        recovery={6:2,4:3,5:4}[launch]
        out.append((f'RecoveryPoint{recovery}',f'Elevator{e}',author(list(reversed(way)))))
    return out


def vessel_ini(material: dict[str,str]) -> str:
    moving = set(PROPULSION_MODELS)
    moving.update(name for mount in gun_mounts()
                  for name in (mount["mount"],mount["barrel"]))
    moving.update(s["name"] for s in moving_model_specs())
    moving.update(f"LiftPlatform{i}" for i in range(1,5))
    moving.update(f"PVLS_{i}_LaunchBase" for i in range(1,5))
    static = [name for name in material if name not in moving
              and name not in ("Hull", "coll_hull_main")]
    mounts={name:(x/WIDTH_SCALE,y,z) for name,(x,y,z) in zip(IMPELLERS,IMPELLER_CENTRES)}
    mounts.update({f'WaterjetSteering{i}':(JET_CENTRES[i-1][0]/WIDTH_SCALE,*JET_CENTRES[i-1][1:]) for i in STEERING_INDICES})
    parts = [
        "; Independent Australis editor test. No third-party assets repackaged.",
        section("General",[
            "UnitType=Vessel",f"NumberOfDCTeams={FIT['damage_control']['teams']}","DefaultCameraDistance=8.0",
            "MinCameraDistanceForeAft=3.2","MinCameraDistanceBroadside=1.5",
            "CameraPivotHeight=0.34","Length=370",f"Beam={44*WIDTH_SCALE:g}",
            "CompartmentsHeight=0.25","ArmorType=Moderate",
            f"FrontalArea={2450*WIDTH_SCALE:g}","SideArea=13200",
            f"BottomArea={25500*WIDTH_SCALE:g}"]),
        section("OpticalView",[
            "Views=binocular_7x50,binocular_10x50",
            "DefaultView=binocular_7x50"]),
        section("AirGroup",[
            "; 5,300 embarked personnel; 99 aircraft is a design target.",
            "; Empty while aircraft compatibility and the 99-place deck cycle",
            "; are tested. This avoids a dependency on RADF or the F-111N pack."]),
        section("FlightDeck",[
            "AircraftCapacity=99","NumberOfElevators=4",
            "NumberOfLaunchPoints=6","NumberOfRecoveryPoints=4",
            f"NumberOfTaxiPaths={len(routes())}","NumberOfDeckZones=15",
            "ForwardsTaxiVelocity=15","BackwardsTaxiVelocity=-10",
            "SlowTaxiVelocity=10","SpawnInterval=1","LaunchDelay=1","GroundCrewCount=16",
            "DeckParkSlots=44","LandingWhileLaunching=True",
            "HelicopterInitialWaypoint=-1,300,1",
            "HoldWaypoints=-2.7,2000,-6|-1.9,2000,-6.6|-1.1,2000,-6|-1.9,2000,-4.7",
            "LandingSpeeds=350,240,150","HoldStackSeparation=1000",
            "HoldEnterDistance=3",
            "HelicopterHoldWaypoints=1,400,-2.92|1,400,-1.46",
            "HelicopterHoldStackSeparation=500","HelicopterHoldEnterDistance=2",
            f"FlightDeck_AmmoCapacity={FIT['aviation_ammunition']['capacity_points']}/{FIT['aviation_ammunition']['capacity_points']}",
            "FlightDeck_NumberOfAccountableAmmunitionCategories=0",
            "ArmorType=Moderate","Collider=coll_hangar"]),
    ]
    for i,(x,z) in enumerate(ELEVATORS,1):
        parts.append(section(f"Elevator{i}",[
            "AssociatedLaunchPoints="+",".join(map(str,LAUNCH_ASSOC[i-1])),
            *AIRCRAFT_SIZE_SUPPORT,
            f"Mesh=LiftPlatform{i}",f"SpawnPosition={point(x,z,11.8-DECK_SURFACE_Y)}",
            "SpawnRotation=0",f"RidePosition={point(x,z,11.8-DECK_SURFACE_Y)}","RideRotation=0",
            f"MoveDownAnimation=Lift{i}Down",f"MoveUpAnimation=Lift{i}Up","StartsLowered=False","CloseDoorsAfterTaxi=False","RequiresFreeLaunchpoint=True","EmbarkTime=10","RecycleTime=15"]))
    for i,((x,z),(ex,ez)) in enumerate(CATAPULTS,1):
        rotation = math.degrees(math.atan2((ex-x)*WIDTH_SCALE,ez-z))
        interlock = ",".join(map(str,CATAPULT_INTERLOCKS[i]))
        parts.append(section(f"LaunchPoint{i}",[
            "AllowedType=Plane,VTOL,STOL", *AIRCRAFT_SIZE_SUPPORT,
            f"Position={point(x,z)}",
            f"BlocksLaunchPoints={interlock}",
            f"TakeoffRequiresFreeLaunchpoints={interlock}",
            f"Rotation={rotation:.3f}","CatapultParticles=None",
            f"CatapultLength={math.hypot((ex-x)*WIDTH_SCALE,ez-z):.3f}"]))
    for i,(x,z) in enumerate(VERTICAL_SPOTS,4):
        blocks=",".join(map(str,HELO_INTERLOCKS[i]))
        parts.append(section(f"LaunchPoint{i}",[
            "AllowedType=Helicopter", *AIRCRAFT_SIZE_SUPPORT,
            f"Position={point(x,z,HELIPAD_SURFACE_Y-DECK_SURFACE_Y)}","Rotation=-12",
            *([f"BlocksLaunchPoints={blocks}",f"TakeoffRequiresFreeLaunchpoints={blocks}"] if blocks else [])]))
    touchdown = LANDING_LANE_A + (LANDING_LANE_B-LANDING_LANE_A)*.36
    parts.append(section("RecoveryPoint1",[
        "AllowedType=Plane,VTOL,STOL", *AIRCRAFT_SIZE_SUPPORT,
        "AssociatedElevators=1,2,3,4",
        "; Recovery taxi crosses shared launch access; queue new departures.",
        "BlocksLaunchPoints=1,2,3,4,5,6",
        "BlocksRecoveryPoints=2,3,4",
        f"Position={point(*touchdown)}",f"ExitPosition={point(*LANDING_LANE_B)}",
        "Rotation="+f"{math.degrees(math.atan2((LANDING_LANE_B[0]-LANDING_LANE_A[0])*WIDTH_SCALE,LANDING_LANE_B[1]-LANDING_LANE_A[1])):.3f}",
        "CircuitWaypoints=0.5,800,-4.5|0.5,800,2.5|-0.75,800,3.2|-2,800,2.2|-2,500,-2.5|-0.75,500,-3.5|0.42,500,-3",
        "LandingInterval=56","Arrested=True"]))
    for i,pad in enumerate((2,0,1),2):
        x,z=VERTICAL_SPOTS[pad];elevator=HELO_ELEVATORS[pad];launch=pad+4
        parts.append(section(f"RecoveryPoint{i}",[
            "AllowedType=Helicopter",*AIRCRAFT_SIZE_SUPPORT,
            f"BlocksLaunchPoints=3,{launch}",f"AssociatedElevators={elevator}",
            "BlocksRecoveryPoints=1",
            f"Position={point(x,z,HELIPAD_SURFACE_Y-DECK_SURFACE_Y)}","Rotation=-12",
            "HelicopterCircuitWaypoints=0,300,-2|0,300,-1",
            "FinalApproachPath=0.8,300|0.4,200|0,100","LandingInterval=25"]))
    for i,(frm,to,waypoints) in enumerate(routes(),1):
        parts.append(section(f"TaxiPath{i}",[
            f"From={frm}",f"To={to}",
            "Waypoints="+"|".join(point(x,z) for x,z in waypoints)]))
    deckzones = [(f"{'Bow' if i in BOW_CATAPULT_IDS else 'Port-waist'} catapult {i}",
                  "Runway",catapult_zone(*route))
                 for i,route in enumerate(CATAPULTS,1)]
    deckzones += [("Angled recovery","Runway",
                   [landing_point(t,across) for t,across in
                    ((0,-11.3),(0,11.3),(1,11.3),(1,-11.3))]),
                  ("Flight deck","Deck",DECK),
                  ("Main island","NoPark",MAIN_ISLAND_BASE),
                  ("Aft island","NoPark",AFT_ISLAND_BASE)]
    for name,(x,z,w,l) in deck_weapon_zones():
        deckzones.append((name,"NoPark",[((x+dx)/WIDTH_SCALE,z+dz)
                         for dx,dz in ((-w/2,-l/2),(w/2,-l/2),(w/2,l/2),(-w/2,l/2))]))
    for i,(name,kind,coords) in enumerate(deckzones,1):
        parts.append(section(f"DeckZone{i}",zone(name,kind,coords)))
    parts += [
        section("Physics",[
            f"Displacement={FIT['full_load_displacement_tonnes']}","MaxForwardVelocity=30",
            "; Astern, Stop, Creep, Slow, Standard, Full, Flank (knots).",
            "; Standard matches native fixed-wing air-operations target.",
            "TelegraphVelocities=-7,0,6,12,20,30,30",
            "MaxBackwardVelocity=7","LinearDrag=0.97",
            "MaxAccelerationFactor=0.20","MinAccelerationFactor=0.08",
            "RudderTurnRate=1.25","RudderForce=0.35",
            "TiltFactor=2.0","PitchFactor=0.0",
            "TrimDepth=0.0","TrimAngle=0.0",f"CenterToKeelDist={11.5/METRES_PER_UNIT:.9f}",f"CenterOfMass={vec(0,7.,float(wet_hull()[2]['wet_centre_of_buoyancy_xyz_m'][2]))}"]),
        section("Buoyancy",[
            "Density=0.5","OutOfWaterDrag=75","SubmergedDrag=75",
            "CavitationSpeed=4"]),
        section("SensorData",[
            "VisualIdentificationRange=15.0","IRSignature=VeryLarge",
            "RCS=VeryLarge","BaseNoise=170","FlowNoise=1",
            "CavitationNoise=10","BladesCount=8",
            "MinNoiseClassificationTreshold=5","ElectricFrequency=60"]),
        section("AI",[
            "UnitCostValue=12000","UnitScoreValue=15","Role=Carrier",
            "AAW_Capability=3","ASuW_Capability=0","ASW_Capability=1",
            "HasChaff=True",
            "MissilesToSaturate=16","TorpedoesToSaturate=5"]),
        section("ControlSystem",["Collider=coll_bridge",
                                 "ArmorType=Minor","ModuleType=CIC"]),
        section("MainPowerSystem",[
            "Type=Nuclear","HorsePower=280000","ArmorType=Moderate",
            "IsCoveredByMainArmor=True","Collider=coll_engine"]),
        section("PropulsionSystems","NumberOfPropulsionSystems=8"),
        *[section(f'PropulsionSystem{i}',[f'Mount=WaterjetImpeller{i}',
             'RotationDirection='+('Left' if i<=4 else 'Right'),f'Collider=coll_waterjet_{i}']) for i in range(1,9)],
        section("RudderSystems","NumberOfRudderSystems=4"),
        *[section(f'RudderSystem{j}',[f'Mount=WaterjetSteering{i}',f'Collider=coll_steering_{i}']) for j,i in enumerate(STEERING_INDICES,1)],
        *native_sections(section,vec,WIDTH_SCALE),
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
            *[f'MainSystems_{i}={name}' for i,name in enumerate(PROPULSION_MODELS,1)],
            *[f"MainSystems_{i}={name}" for i,name in enumerate(
              weapon_model_names(),len(PROPULSION_MODELS)+1)],
            *[f"Main_{len(static)+i}=LiftPlatform{i}" for i in range(1,5)],
            *[f"MainSystems_{len(list(weapon_model_names()))+len(PROPULSION_MODELS)+i}=PVLS_{i}_LaunchBase" for i in range(1,5)],
            "General_1=Flag1"]),
        section("Animations",["NumberOfAnimationReferences=1","AnimationFile_1=ran_australis_lifts"]),
    ]
    for name in static:
        parts.append(section(name,[
            f"Mesh={name}",f"Material={material[name]}_mat.ini"]))
    for name in PROPULSION_MODELS:
        parts.append(section(name,[
            f"ResourcesMeshFolder={SHIP_DIR}/",f"RootMesh={ID}.obj",
            f"Mesh={name}",f"Material={material[name]}_mat.ini",
            f"Position={vec(*mounts[name])}"]))
    for mount in gun_mounts():
        x,y,z=mount["position"]
        for key in ("mount","barrel"):
            name=mount[key]
            rows=[f"ResourcesMeshFolder={SHIP_DIR}/",f"RootMesh={ID}.obj",
                  f"Mesh={name}",f"Material={material[name]}_mat.ini"]
            rows += ([f"Position={vec(x/WIDTH_SCALE,y+1,z)}",
                      "Rotation=0,"+("90" if x>0 else "-90")+",0"]
                     if key=="mount" else
                     [f"Parent={mount['mount']}","Position=0,0,0"])
            if True:
                spec=next(s for s in moving_model_specs() if s["name"]==name)
                rows=[r for r in rows if not r.startswith(("Parent=","Position="))]
                rows += [f"Parent={spec['parent']}","Position="+",".join(f"{v/METRES_PER_UNIT:.9f}" for v in spec["position"])]
            parts.append(section(name,rows))
    for spec in moving_specs():
        name=spec['name']
        rows=[f"ResourcesMeshFolder={SHIP_DIR}/",f"RootMesh={ID}.obj",f"Mesh={name}",
              f"Material={material[name]}_mat.ini", "Position="+",".join(f"{v/METRES_PER_UNIT:.9f}" for v in spec["position"])]
        parts.append(section(name,rows))
    for i,(x,z) in enumerate(ELEVATORS,1):
        parts.append(section(f"LiftPlatform{i}",[f"Mesh=LiftPlatform{i}","Material=hatch_mat.ini",f"Position={vec(x,LIFT_SURFACE_Y,z)}"]))
    for i in range(1,5):
        parts.append(section(f"PVLS_{i}_LaunchBase",[f"Mesh=PVLS_{i}_LaunchBase","Material=dark_mat.ini",f"Parent=PVLS_{i}_Lift",f"Position=0,{3.16/METRES_PER_UNIT:.9f},0","Rotation=-90,0,0"]))
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
        "coll_hangar": ("Box",(0,15,0),(48,10,245)),
        "coll_deck": ("Box",(0,22,0),(76,2,355)),
        "coll_hull": ("Box",(0,2,0),(48,26,335)),
    }
    colliders.update({f'coll_waterjet_{i}':('Box',(x/WIDTH_SCALE,y,z),(3.2/WIDTH_SCALE,3.2,9.0)) for i,(x,y,z) in enumerate(IMPELLER_CENTRES,1)})
    colliders.update({f'coll_steering_{i}':('Box',(JET_CENTRES[i-1][0]/WIDTH_SCALE,JET_CENTRES[i-1][1],JET_CENTRES[i-1][2]-1.2),(3.6/WIDTH_SCALE,4.5,4.5)) for i in STEERING_INDICES})
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
        f"PropWashPosition={vec(0,-3.6,-184)}"]))
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
        f"SternFoamPosition={vec(0,0,-180)}",
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


def update_flight_deck_config(path: Path) -> None:
    """Apply only aviation sections to an existing authored vessel definition.

    Hull-number variants and other native class registration stay untouched.
    This avoids rebuilding geometry simply to update its route graph.
    """
    import configparser
    import re
    path=Path(path)
    original=path.read_text(encoding="utf-8-sig")
    current=configparser.ConfigParser(interpolation=None)
    current.optionxform=str
    current.read_string(original)
    materials={"Hull":"hull", "coll_hull_main":"hull"}
    for name in current["Submodels"].values():
        if name=="Flag1":continue
        materials[name]=Path(current[name]["Material"]).name.removesuffix("_mat.ini")
    generated=vessel_ini(materials)
    def blocks(text):
        return re.split(r"(?m)(?=^\[)",text)
    replacement={}
    taxi=[]
    for block in blocks(generated):
        match=re.match(r"\[([^]\n]+)\]",block)
        if not match:continue
        name=match.group(1)
        if re.fullmatch(r"TaxiPath\d+",name):taxi.append(block)
        else:replacement[name]=block
    wanted={"FlightDeck",*(f"Elevator{i}" for i in range(1,5)),
            *(f"LaunchPoint{i}" for i in range(1,7)),
            *(f"RecoveryPoint{i}" for i in range(1,5)),
            *(f"LiftPlatform{i}" for i in range(1,5))}
    result=[];taxi_inserted=False;seen=set()
    for block in blocks(original):
        match=re.match(r"\[([^]\n]+)\]",block)
        if not match:result.append(block);continue
        name=match.group(1)
        if re.fullmatch(r"TaxiPath\d+",name):
            if not taxi_inserted:result.extend(taxi);taxi_inserted=True
            continue
        if name in wanted:result.append(replacement[name]);seen.add(name)
        else:result.append(block)
    if seen!=wanted:raise ValueError("Missing expected authored aviation sections: "+str(wanted-seen))
    if not taxi_inserted:result.extend(taxi)
    write_ini(path,"".join(result))


def build(destination: Path = DEST) -> None:
    # Remove only our obsolete, unbound legacy animation asset.
    (destination/'animations/animations_ran_cvn_australis_2030_ciws.ini').unlink(missing_ok=True)
    ship = destination / SHIP_DIR
    ship.mkdir(parents=True, exist_ok=True)
    materials = model(ship)
    make_arrangement(destination,[(x*WIDTH_SCALE,z) for x,z in ELEVATORS],BAYS,
                     [(x*WIDTH_SCALE,z) for x,z in LASERS])
    (destination/'enclosed-deck.json').write_text(json.dumps({
        'schema':1,'requires':'RAN.Australis.DeckController.dll','deployment_seconds':.75,
        'hold_after_last_shot_seconds':300,'stow_seconds':10,
        'motions':moving_specs()},indent=2)+'\n')
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
              "370 m, 112000 t, 5300 embarked design targets. Five steam CATOBAR "
              "lanes, three bow and two port-waist; Ford/Zumwalt-inspired combat fit with declared stock proxies.\n"
              "Variant1=HMAS Australis test,HMAS Australis test\n")
    write_ini(destination / "_info.ini",
              "[Language_en]\nName=RAN Australis 2030 Editor Prototype v0.5.1\n"
              "Description=Independent Australian carrier model and flight-deck test. "
              "No RADF or Workshop files are bundled.\n\n"
              "[Compatibility]\nApproximateVersion=0.8.5\n")
    sensor_profiles,weapon_profiles = custom_profiles(section,METRES_PER_UNIT)
    write_ini(destination / "systems/sensors.ini",sensor_profiles)
    write_ini(destination / "systems/weapons.ini",weapon_profiles)
    (destination / "combat-fit.json").write_text(json.dumps(FIT,indent=2)+"\n")
    (destination / "README.txt").write_text(
        "RAN Australis 2030 Editor Prototype\n"
        "This is an opt-in editor test of an original mesh and native-style "
        "carrier deck routes. The air group is user-selected and starts empty. "
        "Targets: 99 aircraft, 5300 embarked, 5800 berths, 112000 t full load. "
        "Five native damage-control repair teams are configured in General.NumberOfDCTeams. Check the fresh carrier damage-control panel in game. "
        "Five 95 m steam CATOBAR tracks: three bow and two shallow 6-degree "
        "port-waist lanes, staggered 21 m. Flush metal tracks, small shuttles, "
        "white guides and segmented deflectors are static visual details. "
        "All five rolling lanes accept Plane, VTOL and STOL; four dedicated spots "
        "accept Helicopter and VTOL. Automatic discovery accepts correctly installed "
        "carrier-capable aircraft with no class, size, role or loadout exclusions. "
        "Combat-fit.json declares modern "
        "targets and stock proxies: Mk41 with Sea Sparrow defensive rounds, plus Sea Sparrow in the "
        "ESSM and 21-round RAM-form launchers, Phalanx, 30 mm, SPY-1A, "
        "SLQ-32, original offensive ECM, SRBOC and two Nixie decoys. "
        "Nulka and lasers remain visual positions. New combat behaviour "
        "and flight-deck animation require in-game testing. A stock Sea "
        "Power Nimitz bundle is named as a runtime fallback; "
        "no stock or Workshop asset bytes are copied.\n"
        "The user confirmed mission loading and original hull rendering on "
        "22 October 2026 after the Foam section was added. This revision "
        "uses an 82 m main deck and four helipads: ahead of the forward lift, beside the main tower, beside the rear tower and aft of the rear tower. "
        "The upper hull contains full lift trunks and weapon wells. An original 280 x 50 x 8 m hangar floor and lift-trunk walls are included. Internal-arrangement.json records 36 mixed folded reference parking slots, 151 room envelopes for 5800 planning berths and separate machinery, fuel, magazine and hotel spaces. These are space reservations, not engineered equipment/cabins or a verified 99-aircraft operating cycle. "
        "Four internal lifts serve the main tower: one forward, two inline alongside and one between the islands, "
        "behind the waist launch run. Four 22 x 26 m lifts use centred ride/spawn positions "
        "and fore-and-aft parking, checked against the stock F-14A reference. "
        "All five catapult staging positions and aligned approaches are checked "
        "with A-7E, F-14A and a 25 m span x 30 m length reference envelope. "
        "LaunchDelay=1 is a shared one-second minimum, not a "
        "guarantee of synchronized launches. Bow 1/3 can be paired; waist "
        "launches block all bow lanes, each other and all four vertical spots. "
        "The four helipads are clear of the runway footprints. Conservative vertical/fixed-wing interlocks remain until flight-cycle QA. "
        "All recovery points explicitly block all launches. Native eligibility does not "
        "verify every aircraft model: swept taxi turns, rotor clearance and mixed "
        "deck operations still need game QA.\n"
        "The rear island is narrower, shorter and lower with six-face wraparound glazing. "
        "The arrested-recovery axis is 9 degrees to port and its wires are perpendicular. "
        "Four defensive VLS banks and four missile housings occupy main-deck edge positions "
        "with NoPark zones. RIM-66E and RGM-109 are removed. Sea Sparrow retains stock "
        "guidance; the vertical-launch proxy requires in-game checking. "
        "All weapons and decoys now sit inside enclosed deck bays. AnchorChain is required; "
        "deploy after committed aircraft clear in 0.75 simulation seconds, hold 300 seconds "
        "after the last actual shot, then lower and close over 10 seconds. Aviation "
        "remains locked until stowed. In-game QA is pending. "
        "All five guns use original moving yaw bodies and elevation barrels. The normal "
        "30 mm guns now provide NumberOfGuns/Gun1, correcting the null barrel that caused "
        "WeaponSystemGun.AlignTurret to fail. This correction still needs an in-game firing test.\n"
        "Aircraft contact points use the actual deck/pad/lift surface heights; the former "
        "16 cm taxi/launch offset is removed. Aviation stores now contain 6000000/6000000 "
        "ammo points, with no individual ammunition-category caps. Stock aircraft gun and "
        "countermeasure capacities are retained. Select an armed loadout and Ready the aircraft. "
        "Use a fresh carrier in a new mission so saved ammunition and old deck positions do "
        "not override this revision.\n"
        "The rebuilt deck has lift platforms and painted helipads at 22.002 m, only 2 mm above the main deck. "
        "Contact coordinates follow those exported surfaces. Ordinary deck markings are "
        "millimetres thick; stowed blast deflectors and closed laser hatches sit within 2 mm of the deck. "
        "Visible arresting wires rise 3 cm and launch shuttles 6 cm above deck.\n"
        "Test with the failed Melbourne prototype disabled. If the editor "
        "errors, collect the current logs, withdraw only this mod, and share "
        "the latest Sea Power Player.log.\n",
        encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEST)
    args = parser.parse_args()
    if args.destination.resolve()!=DEST.resolve():
        parser.error('The current four-ship driver builds under game-mod; use tools/rebuild_recovery.py and the transactional installer.')
    from rebuild_recovery import main as rebuild_current_fleet
    rebuild_current_fleet()


if __name__ == "__main__":
    main()

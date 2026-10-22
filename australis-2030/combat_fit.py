"""Original Australis fit and game adapters. Positions/dimensions are metres.

Modern equipment names are design targets. Native stock proxies are declared
explicitly; their presence does not implement the modern systems' performance.
"""
FIT = {
    "crew": {"ships_company": 2850, "air_wing": 2250, "staff": 200,
             "total": 5300, "berths": 5800},
    "full_load_displacement_tonnes": 112000,
    "weight_budget_tonnes": {"structure": 42000, "machinery": 12500,
        "ship_and_aviation_outfit": 15000, "combat_and_electronics": 5000,
        "aviation_fuel": 9000, "aircraft_and_wing_equipment": 6500,
        "ordnance_and_stores": 5500, "water_and_fluids": 4500,
        "crew_and_provisions": 2500, "design_allowance": 9500},
    "hangar": {"length_m": 245, "width_m": 30, "height_m": 8,
        "proposed_aircraft_allocation": 36, "proposed_deck_allocation": 63,
        "parking_layout_validated": False},
    "hotel_services": {"fresh_water_litres_per_person_day": 150,
        "watermakers": 3, "each_watermaker_m3_per_day": 450,
        "meals_per_person_day": 3, "provision_days": 60},
    "targets": {"mk57_style_vls_cells": 80, "essm_launchers": 2,
        "ram_21_round_launchers": 2, "phalanx": 3, "mk46_style_30mm": 2,
        "srboc_launchers": 8, "nulka_launchers": 4, "towed_decoys": 2,
        "retractable_laser_positions": 4,
        "radar": "SPY-6(V)3/EASR-style volume search and SPY-3-style multifunction faces",
        "ew": "SLQ-32/SEWIP-style passive warning and defensive/offensive jamming"},
    "native_proxies": {"vls_launcher": "MK41", "area_defence": "usn_rim-66e",
        "land_attack": "usn_rgm-109c", "essm": "usn_rim-7m",
        "ram": "21-position original launcher with usn_rim-7m; SARH, not RAM guidance",
        "30mm": "original gun profile with rn_cal_30mm",
        "search_radar": "SPY-1A", "surface_radar": "SPS-67",
        "air_traffic": "SPN-43", "esm": "AN/SLQ-32_ESM",
        "defensive_ecm": "AN/SLQ-32", "chaff": "Mk_36_SRBOC",
        "towed_decoy": "SLQ-25_Nixie",
        "nulka": "visual positions only; active hovering behaviour unimplemented",
        "lasers": "visual hatches only; weapon/animation unimplemented"},
    "native_combat_tested": False,
}
VLS_BANKS = [(-46,110),(46,110),(-46,-92),(46,-92)]
SAM_POS = [(-44,18,-157),(44,18,-157)]
RAM_POS = [(-44,18,137),(44,18,137)]
CIWS_POS = [(-44,19,148),(44,19,-65),(-44,19,-166)]
GUN_POS = [(44,18,148),(-44,18,-65)]
CHAFF_POS = [(side*43,18,z) for side in (-1,1) for z in (-169,-116,-38,126)]
NULKA_POS = [(side*44,18,z) for side in (-1,1) for z in (-74,74)]


def cells(x,z):
    return [(x+side*.9,z+(row-4.5)*1.7) for row in range(10) for side in (-1,1)]


def add_geometry(mesh,width_scale):
    def box(name,x,y,z,w,h,l,material):
        mesh.box(name,x/width_scale,y,z,w/width_scale,h,l,material)
    def shelf(name,x,y,z,w,h,l):
        side = 1 if x>0 else -1
        inner,outer = abs(x)-w/2,abs(x)+w/2
        outline = [(inner,z-l/2),(outer-1.5,z-l/2),(outer,z-l/2+1.2),
                   (outer,z+l/2-1.2),(outer-1.5,z+l/2),(inner,z+l/2)]
        outline = [(side*px/width_scale,pz) for px,pz in outline]
        if side<0: outline.reverse()
        bottom = [(side*inner/width_scale+(px-side*inner/width_scale)*.58,
                   y-h*1.6,pz) for px,pz in outline]
        top = [(px,y+h/2,pz) for px,pz in outline]
        n=len(outline)
        faces=[list(reversed(range(n))),list(range(n,2*n))]
        faces += [[i,(i+1)%n,n+(i+1)%n,n+i] for i in range(n)]
        mesh.add(name,bottom+top,faces,"hull")
    # Outboard shelves below the flight-deck edge. Original blockout only;
    # structural support, exhaust separation and firing clearance need design.
    for i,(x,z) in enumerate(VLS_BANKS,1):
        shelf(f"PVLS_Sponson_{i}",x*.80,15.8,z,25,2.2,21)
        box(f"PVLS_Bank_{i}",x,17,z,4.6,1.2,19,"dark")
        for j,(cx,cz) in enumerate(cells(x,z),1):
            box(f"PVLS_Cell_{i}_{j:02d}",cx,17.7,cz,1.45,.18,1.35,"hatch")
    groups = [("ESSM",SAM_POS),("RAM",RAM_POS),("CIWS",CIWS_POS),("Mk46",GUN_POS)]
    for kind,positions in groups:
        for i,(x,y,z) in enumerate(positions,1):
            shelf(f"{kind}_Shelf_{i}",x*.80,y-2,z,24,1.4,7)
            box(f"{kind}_Pedestal_{i}",x,y-.5,z,2.2,1.6,2.2,"dark")
            box(f"{kind}_Housing_{i}",x,y+1,z,3,1.7,2.8,"island")
            if kind in ("CIWS","Mk46"):
                box(f"{kind}_Barrel_{i}",x+(1.9 if x>0 else -1.9),y+1,z,2.1,.22,.3,"dark")
            else:
                rows,columns = (3,7) if kind == "RAM" else (2,4)
                for row in range(rows):
                    for col in range(columns):
                        box(f"{kind}_Tube_{i}_{row}_{col}",x+(1.56 if x>0 else -1.56),
                            y+.5+row*.35,z+(col-(columns-1)/2)*.33,.12,.22,.22,"dark")
    for kind,positions in (("SRBOC",CHAFF_POS),("Nulka",NULKA_POS)):
        for i,(x,y,z) in enumerate(positions,1):
            shelf(f"{kind}_Shelf_{i}",x*.82,y-1.5,z,21,1,2.8)
            box(f"{kind}_Launcher_{i}",x,y,z,1.7,1.2,1.5,"dark")


def native_sections(section,vec,width_scale):
    """Supported stock schema and explicitly named compatibility adapters."""
    def p(x,y,z): return vec(x/width_scale,y,z)
    result = []
    sensors = [("Visual","Optics",(30,40,5)),
        ("Radar","SPY-1A",(30,49,10)), ("Radar","SPS-67",(30,36,-89)),
        ("Radar","SPN-43",(30,42,-89)), ("Radar","MK-95",(28,40,12)),
        ("Radar","MK-95",(35,40,12)), ("Radar","SPG-62",(28,35,-89)),
        ("Radar","SPG-62",(35,35,-89)), ("ESM","AN/SLQ-32_ESM",(30,50,10)),
        ("ECM","AN/SLQ-32",(30,48,10)),
        ("ECM","RAN_Australis_OECM",(30,51,10))]
    result.append(section("SensorSystems",f"NumberOfSensorSystems={len(sensors)}"))
    for i,(kind,name,pos) in enumerate(sensors,1):
        result.append(section(f"SensorSystem{i}",[f"Type={kind}",f"SystemName={name}",
            "Mount=Dummy",f"MountPosition={p(*pos)}",*([] if i==1 else ["Collider=coll_bridge"])]))
    weapons = []
    mags = []
    def magazine(name,rounds):
        mags.append(section(name,[f"NumberOfAmmunitionTypes={len(rounds)}",
            *[line for i,(ammo,count) in enumerate(rounds,1)
              for line in (f"Ammunition{i}={ammo}",f"Ammunition{i}_Count={count}")],
            "Collider=coll_engine","ModuleType=SmallMagazine"]))
    def missile(profile,pos,mag,containers,arcs="-180,180",vls=False):
        rows = ["Type=Missile",f"SystemName={profile}","Mount=Dummy",
            f"MountPosition={p(*pos)}","IsMountRotatable=False",
            "AssociatedSensors=SensorSystem2,SensorSystem5,SensorSystem6,SensorSystem7,SensorSystem8",
            "AssociatedSearchSensors=SensorSystem1,SensorSystem2,SensorSystem3",
            "ContainerBase=Dummy",f"NumberOfContainers={len(containers)}","AreContainersRotatable=False",
            f"FiringArcs={arcs}","ElevationArc=5,90",f"AssociatedMagazine={mag}",
            f"PreloadAmmunition={'False' if vls else 'True'}",
            "WorksStandalone=False","Collider=coll_engine"]
        for j,(dx,dy,dz) in enumerate(containers,1):
            rows += [f"Container{j}=Dummy",f"Container{j}_Position={p(dx,dy,dz)}",
                     f"Container{j}_Rotation="+("-90,0,0" if vls else ("-20,90,0" if pos[0]>0 else "-20,-90,0"))]
        weapons.append(rows)
    for i,pos in enumerate(SAM_POS,1):
        mag=f"Magazine_ESSM_Proxy_{i}"
        magazine(mag,[("usn_rim-7m",8)])
        missile("MK29",pos,mag,[(0,0,0)],"0,180" if pos[0]>0 else "-180,0")
    for i,(x,z) in enumerate(VLS_BANKS,1):
        mag=f"Magazine_PVLS_{i}"
        magazine(mag,[("usn_rim-66e",16),("usn_rgm-109c",4)])
        missile("MK41",(x,17.8,z),mag,[(cx-x,0,cz-z) for cx,cz in cells(x,z)],vls=True)
    for i,pos in enumerate(RAM_POS,1):
        mag=f"Magazine_RAM_Proxy_{i}"
        magazine(mag,[("usn_rim-7m",21)])
        missile("RAN_Australis_RAM21",pos,mag,[(0,0,0)],"0,180" if pos[0]>0 else "-180,0")
    magazine("Magazine_CIWS",[("usn_cal_20mm_apds",12000)])
    magazine("Magazine_30mm",[("rn_cal_30mm",2000)])
    for profile,kind,positions,mag in [("MK15_Blk1","CIWS",CIWS_POS,"Magazine_CIWS"),
            ("RAN_Australis_30mm","Gun",GUN_POS,"Magazine_30mm")]:
        for pos in positions:
            weapons.append([f"Type={kind}",f"SystemName={profile}","Mount=Dummy",
                f"MountPosition={p(*pos)}","IsMountRotatable=False","ContainerBase=Dummy",
                "Gun=Dummy","AreContainersRotatable=False","Automatic=True",
                "AssociatedSearchSensors=SensorSystem1,SensorSystem2,SensorSystem3",
                "FiringArcs="+("0,180" if pos[0]>0 else "-180,0"),
                "ElevationArc=-10,85",f"AssociatedMagazine={mag}",
                "WorksStandalone=True","Collider=coll_engine"])
    for pos in CHAFF_POS:
        weapons.append(["Type=Chaff","SystemName=Mk_36_SRBOC","Mount=Dummy",
            f"MountPosition={p(*pos)}","ContainerBase=Dummy","Ammunition=all_ship_chaff_late",
            "NumberOfEffects=6","DelayBetweenLaunches=0.1","EffectOffset=80,140,100",
            "WorksStandalone=True"])
    result.append(section("WeaponSystems",f"NumberOfWeaponSystems={len(weapons)}"))
    result += [section(f"WeaponSystem{i}",rows) for i,rows in enumerate(weapons,1)]
    result += mags
    result.append(section("DecoySystems","NumberOfDecoySystems=2"))
    for i,x in enumerate((-8,8),1):
        result.append(section(f"DecoySystem{i}",["SystemName=SLQ-25_Nixie",
            "Countermeasure=usn_an_slq_25_nixie_decoy","CableLength=579","Depth=50",
            "CablePart=effects/ships/emitters/Towed_Array_Line",
            f"AttachmentPointPosition={p(x,1,-172)}",f"StowedPosition={p(x,1,-170)}",
            "StowedRotation=0,0,0","CableAttachmentOffset=0","CableRetractRate=3",
            "CableSinkRate=0.015","MinDeploySpeed=5","MaxDeploySpeed=25"]))
    return result


def custom_profiles(section,metres_per_unit):
    radar = section("RAN_Australis_OECM",["Kind=ECM","Type=Offensive",
        "Frequencies=UHF-Band,L-Band,S-Band,C-Band,X-Band,Ku-Band",
        "MaxRange=250","PeakPower=30","Gain=12","JamConeViewArcs=60",
        "ModuleType=SmallSensor","; Original game-balance values, not SEWIP specifications."])
    attachments = [f"AttachmentPosition{i}={(col-3)*.33/metres_per_unit:.6f},{(row-1)*.35/metres_per_unit:.6f},0"
        for i,(row,col) in enumerate(((r,c) for r in range(3) for c in range(7)),1)]
    weapons = section("RAN_Australis_RAM21",["NumberOfAttachments=21",*attachments,
        "HorizontalDegreesPerSecond=0","VerticalDegreesPerSecond=0","ReloadTime=0",
        "MoveToRestPositionTime=0","Warmup=False","ModuleType=SmallLauncher",
        "SmokeEffect=effects/weapons/emitters/LauncherSmokeSmall",
        "; Form-factor proxy firing stock Sea Sparrow, not RIM-116 performance."])
    weapons += section("RAN_Australis_30mm",["HorizontalDegreesPerSecond=90",
        "VerticalDegreesPerSecond=60","FireRate=200","RoundsLoaded=400",
        "ReloadTime=120","RecoilTime=0.1","RecoilStrength=0.0002",
        "Effect=effects/weapons/emitters/usn_phalanx_burst","EffectPosition=0,0,0",
        "SpawnPosition=0,0,0","ModuleType=SmallTurret",
        "; Original 30 mm game adapter; ammunition is stock rn_cal_30mm."])
    return radar,weapons

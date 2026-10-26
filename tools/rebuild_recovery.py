#!/usr/bin/env python3
"""Reconstruct the native fleet from the recovered source, without game files."""
from pathlib import Path
import sys,shutil,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'australis-2030'),str(ROOT/'tools')]
import build_australis_2030_mod as base
import recovery_details as details
from build import ELEVATORS,WIDTH_SCALE
from enclosed_deck import BAYS,moving_specs
from rebuild_game_scale import METRES_PER_UNIT as UNIT

ROSTER=[('ran_cvn_australis_2030','Australis',91),('ran_cvn_southern_cross_2030','Southern Cross',92),('ran_cvn_federation_2030','Federation',93),('ran_cvn_commonwealth_2030','Commonwealth',94)]
PACKAGE=ROOT/'game-mod/RAN-Carrier-Australis-2030'

def main():
    base.build()
    for ship_id,name,number in ROSTER:
        details.HULL_NUMBER=number
        folder=PACKAGE/'ships'/ship_id;folder.mkdir(parents=True,exist_ok=True)
        # Build original geometry for each painted number, then adapt resource paths.
        materials=base.model(folder)
        if ship_id!=base.ID:
            for p in (PACKAGE/'ships'/base.ID).iterdir():
                if p.suffix in ('.png','.ini'):shutil.copy2(p,folder/p.name)
            obj=folder/(base.ID+'.obj');obj.rename(folder/(ship_id+'.obj'))
            mtl=folder/(base.ID+'.mtl');mtl.rename(folder/(ship_id+'.mtl'))
            for p in folder.glob('*.ini'):
                p.write_bytes(p.read_bytes().replace(base.ID.encode(),ship_id.encode()))
            p=folder/(ship_id+'.obj');p.write_text(p.read_text().replace(base.ID,ship_id))
        text=base.vessel_ini(materials).replace(base.ID,ship_id)
        base.write_ini(PACKAGE/'vessels'/f'{ship_id}.ini',text)
        variants=(PACKAGE/'vessels'/f'{base.ID}_variants.ini').read_text(encoding='utf-8-sig')
        base.write_ini(PACKAGE/'vessels'/f'{ship_id}_variants.ini',variants)
    names=[]
    for ship_id,name,n in ROSTER:
        names.append(base.section(ship_id,["Type=CVN,Aircraft Carrier",f"Default=Australis class 2030,{name}",f"Variant1=HMSCS {name} {n},{name} {n}",f"DefaultDescription=Experimental eight-waterjet build v0.8.2. Hull {n}; four lifts, three helicopter pads and five repair teams. In-game QA pending."]))
    base.write_ini(PACKAGE/'language_en/vessel_names.ini','\n'.join(names))
    base.write_ini(PACKAGE/'_info.ini','[Language_en]\nName=RAN Australis Fleet v0.8.2 Lift Lighting\nDescription=Experimental eight-waterjet conversion. Preliminary screening only; native propulsion approximation. Requires AnchorChain.\n\n[Compatibility]\nApproximateVersion=0.8.5\n')
    rows=[base.section('Animations',['NumberOfAnimations=8',*[f'Animation{i*2-1}=Lift{i}Up\nAnimation{i*2}=Lift{i}Down' for i in range(1,5)]])]
    for i,(x,z) in enumerate(ELEVATORS,1):
        for direction,a,b in (('Up',11.8,22.002),('Down',22.002,11.8)):
            key=f'Lift{i}{direction}';seq=key+'Sequence'
            rows.append(base.section(key,['NumberOfSequencesToPlay=1',f'Sequence1={seq}',f'Sequence1_Model=LiftPlatform{i}']))
            rows.append(base.section(seq,['NumberOfSteps=2',f'Step1=0|{x*WIDTH_SCALE/UNIT:.9f},{a/UNIT:.9f},{z/UNIT:.9f}|none|Linear',f'Step2=6|{x*WIDTH_SCALE/UNIT:.9f},{b/UNIT:.9f},{z/UNIT:.9f}|none|Smooth']))
    base.write_ini(PACKAGE/'animations/ran_australis_lifts.ini','\n'.join(rows))
    shutil.copy2(ROOT/'addon/bin/RAN.Australis.DeckController.dll',PACKAGE/'RAN.Australis.DeckController.dll')
    # Reference envelope is separate from the visibly perforated wet surface.
    # It is not registered as a model, so it cannot cap the waterjet mouths.
    from naval_hull import design
    from generate_source_models import Mesh
    reference=Mesh();v,f,*_=design()
    reference.add('HydrostaticEnvelope',v,f,'underwater')
    reference.save(PACKAGE/'hydrostatics-envelope.obj',scale=1/UNIT)
    from audit_naval_hull import audit
    audit(PACKAGE)
    from screen_waterjet_engineering import screen,write_outputs
    # Screening uses actual exported geometry, explicit assumptions and a
    # resistance sensitivity range, not a purported CFD-derived prediction.
    engineering=screen(PACKAGE)
    write_outputs(engineering,PACKAGE)
    (PACKAGE/'night-lighting.json').write_text(json.dumps(details.LIGHTS,indent=2)+'\n')
    from lift_lighting import profiles,DECK_LEVEL_M,LOWER_LEVEL_M,OFF_DEPTH_M,FULL_DEPTH_M
    (PACKAGE/'lift-lighting.json').write_text(json.dumps(dict(
        schema=1,groups=profiles([(x*WIDTH_SCALE,z) for x,z in ELEVATORS]),
        deck_level_m=DECK_LEVEL_M,lower_level_m=LOWER_LEVEL_M,
        off_depth_m=OFF_DEPTH_M,full_depth_m=FULL_DEPTH_M,
        gating='Actual independent platform height, every controller tick; smoothstep fade in both directions',
        daytime_operation=True,missing_or_invalid_platform='Off',
        lens_material='Non-emissive; ordinary recessed wall fitting',
        in_game_tested=False),indent=2)+'\n')
    (PACKAGE/'recovery-release.json').write_text(json.dumps(dict(version='0.8.2-lift-lighting',recovered_base='0.5.1',exact_reproduction_of_lost_v060=False,roster=ROSTER,repair_teams=5,catapults=3,lifts=4,helicopter_pads=3,helo_preference=['aft','front','middle'],long_range_defence='40 stock RIM-66E proxy rounds; not SM-6, no ballistic-missile defence claim',native_lift_animation_seconds=6,waterjets=8,steering_nozzles=4,operating_speeds_kn=dict(astern=-7,stop=0,creep=6,slow=12,standard=20,full=30,flank=30),propulsion_status='Preliminary engineering screen only; native conventional propulsion approximation',in_game_tested=False,limitations=['Stock RIM-66E guidance and range are retained.','Helicopter pads can operate independently; shared lifts and recovery/taxi lanes still queue.','Full 99-aircraft deck cycle, night appearance and combat require in-game testing.','Hull spaces are reservations; upright hydrostatics use an explicitly assumed planning CG, with real/in-game stability unverified.']),indent=2)+'\n')
    (PACKAGE/'README.txt').write_text((ROOT/'RECOVERY-README.md').read_text())
    print('[OK] Four numbered ships, native lift animations and controller packaged')

if __name__=='__main__':main()

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
    # One native class mesh serves all four named variants. Historical meshes
    # remain reference assets; only the active shared hull is rebuilt.
    details.HULL_NUMBER=91
    base.build()
    base.write_ini(PACKAGE/'_info.ini','[Language_en]\nName=RAN Australis Fleet v0.8.5 Naval Details\nDescription=Experimental eight-waterjet conversion. Preliminary screening only; native propulsion approximation. Requires AnchorChain.\n\n[Compatibility]\nApproximateVersion=0.8.5\n')
    rows=[base.section('Animations',['NumberOfAnimations=8',*[f'Animation{i*2-1}=Lift{i}Up\nAnimation{i*2}=Lift{i}Down' for i in range(1,5)]])]
    for i,(x,z) in enumerate(ELEVATORS,1):
        for direction,a,b in (('Up',11.8,22.002),('Down',22.002,11.8)):
            key=f'Lift{i}{direction}';seq=key+'Sequence'
            rows.append(base.section(key,['NumberOfSequencesToPlay=1',f'Sequence1={seq}',f'Sequence1_Model=LiftPlatform{i}']))
            rows.append(base.section(seq,['NumberOfSteps=2',f'Step1=0|{x*WIDTH_SCALE/UNIT:.9f},{a/UNIT:.9f},{z/UNIT:.9f}|none|Linear',f'Step2=6|{x*WIDTH_SCALE/UNIT:.9f},{b/UNIT:.9f},{z/UNIT:.9f}|none|Smooth']))
    base.write_ini(PACKAGE/'animations/ran_australis_lifts.ini','\n'.join(rows))
    shutil.copy2(ROOT/'addon/bin/RAN.Australis.DeckController.dll',PACKAGE/'RAN.Australis.DeckController.dll')
    from class_list import apply_class_list
    apply_class_list(PACKAGE)
    import naval_fittings
    visual=dict(naval_fittings.LAST_REPORT)
    visual['version']='0.8.5-naval-details'
    visual['obj_sha256']=hashlib.sha256((PACKAGE/'ships'/base.ID/(base.ID+'.obj')).read_bytes()).hexdigest()
    visual['ini_sha256']=hashlib.sha256((PACKAGE/'vessels'/(base.ID+'.ini')).read_bytes()).hexdigest()
    (PACKAGE/'naval-fittings.json').write_text(json.dumps(visual,indent=2)+'\n')
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
    (PACKAGE/'recovery-release.json').write_text(json.dumps(dict(version='0.8.5-naval-details',recovered_base='0.5.1',exact_reproduction_of_lost_v060=False,roster=ROSTER,repair_teams=5,catapults=3,lifts=4,helicopter_pads=3,helo_preference=['aft','front','middle'],long_range_defence='40 stock RIM-66E proxy rounds; not SM-6, no ballistic-missile defence claim',native_lift_animation_seconds=6,controller_version='0.8.2',installer_hotfix='Stock catalogue section inventory tolerates repeated divider headings; own INIs stay strict',waterjets=8,steering_nozzles=4,operating_speeds_kn=dict(astern=-7,stop=0,creep=6,slow=12,standard=20,full=30,flank=30),propulsion_status='Preliminary engineering screen only; native conventional propulsion approximation',in_game_tested=False,limitations=['Stock RIM-66E guidance and range are retained.','Helicopter pads can operate independently; shared lifts and recovery/taxi lanes still queue.','Full 99-aircraft deck cycle, night appearance and combat require in-game testing.','Hull spaces are reservations; upright hydrostatics use an explicitly assumed planning CG, with real/in-game stability unverified.']),indent=2)+'\n')
    (PACKAGE/'README.txt').write_text((ROOT/'RECOVERY-README.md').read_text())
    print('[OK] Shared naval-detail hull, four numbered variants, native lift cycles and controller packaged')

if __name__=='__main__':main()

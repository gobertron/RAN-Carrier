#!/usr/bin/env python3
"""Reserve non-overlapping internal spaces inside the shipped original mesh."""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'australis-2030'))
from internal_arrangement import (Space,HANGAR,VERSION,shafts,weapon_spaces,
    essential_spaces,parking_spaces,accommodation_candidates,overlaps,laser_spaces)
from internal_fit import HullEnvelope,validate_arrangement

def make_arrangement(destination,lifts,bays,lasers):
    destination=Path(destination)
    obj=destination/'ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj'
    hull=HullEnvelope.from_obj(obj)
    reserved=shafts(lifts)+weapon_spaces(bays)+laser_spaces(lasers)+essential_spaces()
    candidates=[]
    for room in accommodation_candidates():
        if any(overlaps(room.bounds,s.bounds) for s in reserved):continue
        if hull.margin(room.bounds)<.35:continue
        candidates.append(room)
    capacity=sum(s.berths for s in candidates)
    if capacity<5800:raise ValueError(f'Only {capacity} planning berths fit in {len(candidates)} rooms')
    rooms=[];remaining=5800
    for s in candidates:
        if remaining<=0:break
        count=min(remaining,s.berths)
        rooms.append(Space(s.name,s.category,s.bounds,count,s.note))
        remaining-=count
    used={s.name for s in rooms}
    service=[]
    for s in candidates:
        if s.name in used:continue
        service.append(Space(s.name.replace('Berthing','Hotel/workshop'),'hotel_service',s.bounds,
                             note='Additional mess, sanitary, recreation, stores or workshop reservation'))
        if sum(v.area for v in service)>=3000:break
    assert sum(v.area for v in service)>=3000,'Hotel services lack floor allowance'
    data={'schema':1,'version':VERSION,'origin':'Original Australis game-model general-arrangement blockout',
          'game_obj_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),
          'hangar_bounds_m':HANGAR,'hangar_clear_length_width_height_m':[280,50,8],
          'hangar_towing_spine_bounds_m':[-10.5,-4.5,11.8,19.8,-137,143],
          'parking_reference_mix':{'large_folded_12_by_20_5_m':24,'compact_uav_9_by_11_m':8,'folded_rotor_9_by_14_m':4},
          'parking_slots':[s.record() for s in parking_spaces()],
          'spaces':[s.record() for s in reserved+rooms+service],
          'targets':{'aircraft_total':99,'hangar_reference_slots':36,'flight_deck_allocation_unvalidated':63,
                     'embarked':5300,'berths':5800,'aviation_fuel_tonnes':9000},
          'limitations':['Reference mixed parking boxes only; unfolded dimensions and towing turns depend on the chosen aircraft.',
                        '63-aircraft flight-deck parking and the complete 99-aircraft operating cycle remain unverified.',
                        'Cabins are space and occupancy reservations; bunk details, stairs, ventilation and evacuation are not engineered.',
                        'Machinery/fuel/magazine zones are conceptual; actual equipment, piping, protection, structure and stability remain unverified.',
                        'Native six-second lift animations are bound; actual loaded-aircraft lift cycles need in-game testing.']}
    out=destination/'internal-arrangement.json';out.write_text(json.dumps(data,indent=2)+'\n')
    result=validate_arrangement(destination,obj)
    (destination/'internal-fit-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"[OK] Internal fit: {len(rooms)} berthing envelopes / 5800 berths, 36 mixed hangar slots, {len(service)} additional hotel/service envelopes")
    return data

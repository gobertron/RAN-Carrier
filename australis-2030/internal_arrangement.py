"""Original game-model space reservations; not shipyard construction drawings.

Physical metres, +X starboard, +Y up, +Z forward. Aircraft boxes are folded
parking references, not copies of real aircraft or universal fit guarantees.
"""
from dataclasses import dataclass, asdict
import math

VERSION = '0.7.0-recovery'
HANGAR = (-25., 25., 11.8, 19.8, -137., 143.)
LIFT_CLEARANCE = .35
HULL_MARGIN = .30

@dataclass(frozen=True)
class Space:
    name: str
    category: str
    bounds: tuple
    berths: int = 0
    note: str = ''

    @property
    def area(self):
        a,b,c,d,e,f=self.bounds
        return (b-a)*(f-e)

    @property
    def volume(self):
        return self.area*(self.bounds[3]-self.bounds[2])

    def record(self):
        return dict(asdict(self),floor_area_m2=round(self.area,3),volume_m3=round(self.volume,3))

def overlaps(a,b,clearance=0.):
    return all(min(a[i+1],b[i+1])-max(a[i],b[i]) > -clearance+1e-8 for i in (0,2,4))

def expanded(b,amount):
    return tuple(v+(-amount if i%2==0 else amount) for i,v in enumerate(b))

def corners(b):
    return [(x,y,z) for x in b[:2] for y in b[2:4] for z in b[4:]]

def shafts(lifts):
    return [Space(f'Lift shaft {i}','lift',
                  (x-11-LIFT_CLEARANCE,x+11+LIFT_CLEARANCE,11.45,22.,z-13-LIFT_CLEARANCE,z+13+LIFT_CLEARANCE))
            for i,(x,z) in enumerate(lifts,1)]

def weapon_spaces(bays):
    return [Space(b.key+' well','weapon',
                  (b.x-b.width/2-.2,b.x+b.width/2+.2,15.9,22.002,b.z-b.length/2-.2,b.z+b.length/2+.2))
            for b in bays if b.roof==22.]

def laser_spaces(positions):
    return [Space(f'Laser reservation {i}','laser',
                  (x-2.6,x+2.6,16.2,22.,z-3.1,z+3.1),
                  note='Space reserved for a future visual/functional laser mechanism; not an implemented weapon')
            for i,(x,z) in enumerate(positions,1)]

def essential_spaces():
    # Broad concept zones only. No reactor internals or fabricated machinery
    # specifications. Actual mass, piping and safety arrangements are unverified.
    return [
        Space('Machinery and power reservation','machinery',(-8,8,-4.2,7.8,-74,46)),
        Space('Forward auxiliary machinery','machinery',(-8,8,-4.2,7.8,48,77)),
        Space('Aft auxiliary machinery','machinery',(-8,8,-4.2,7.8,-107,-77)),
        Space('Forward aviation magazine reservation','magazine',(-7,7,-4.2,1.8,82,104)),
        Space('Aft aviation magazine reservation','magazine',(-7,7,-4.2,1.8,-136,-111)),
        Space('Distributed aviation fuel tank reservation','fuel',(-7,7,-8.8,-4.7,-116,116)),
        Space('Forward catapult machinery reservation','aviation_service',(-13,13,11.8,19.8,148,169)),
        Space('Forward hotel and medical lower deck','hotel_service',(-8,8,2.3,4.9,82,122)),
        Space('Forward hotel and medical upper deck','hotel_service',(-8,8,5.2,7.8,82,122)),
        Space('Aft hotel and damage-control lower deck','hotel_service',(-8,8,2.3,4.9,-148,-111)),
        Space('Aft hotel and damage-control upper deck','hotel_service',(-8,8,5.2,7.8,-148,-111)),
    ]

def parking_spaces():
    """36 mixed reference slots; separate six-metre port towing spine.

    24 large folded 12 x 20.5 m, eight compact/UAV 9 x 11 m and four
    folded-rotor 9 x 14 m slots. Dimensions include local parking allowance;
    manoeuvring with actual aircraft remains a separate test.
    """
    out=[]
    def row(label,x,start,kinds):
        z=start
        for kind in kinds:
            width,length={'large':(12,20.5),'compact':(9,11),'rotor':(9,14)}[kind]
            out.append(Space(f'{label}-{len(out)+1:02d} {kind}','aircraft',
                             (x-width/2,x+width/2,11.802,17.802,z,z+length),
                             note=kind+' folded planning slot'))
            z+=length
    row('Port',-17.5,-132,['large']*12+['compact']*2)
    row('Centre aft',3,-136.5,['large']*4+['compact']*2)
    row('Centre forward',3,27,['large']*4+['compact']*3)
    row('Starboard aft',18,-135,['large']*2+['rotor']*2)
    row('Starboard forward',18,96,['large']*2)
    row('Starboard freed lift',18,-1,['rotor']*2)
    row('Starboard pocket',18,27,['compact'])
    return out

def accommodation_candidates():
    """Two-metre gaps between columns and between sixteen-metre rooms.

    Room widths vary with the hull section at 4 m2 per planned berth. Washrooms, dining,
    medical and other hotel services are reserved separately. Occupancy is
    a planning density; bunks/doors and human egress are not detailed.
    """
    for deck,y in reversed(list(enumerate((-6.8,-3.7,-.6,2.5,5.6,8.7),1))):
        columns={-6.8:[(-11.5,5),(11,4)],-3.7:[(-13,6),(12,5)],-.6:[(-14,8),(13,7)],
                 2.5:[(-15,10),(14.5,9)],5.6:[(-18,14),(17,14)],
                 8.7:[(-33,8),(-22,10),(-10,10),(0,6),(10,10),(22,10),(33,8)]}[y]
        for z in range(-144,145,18):
            for x,width in columns:
                yield Space(f'Berthing D{deck} X{x:+g} Z{z:+d}','accommodation',
                            (x-width/2,x+width/2,y,y+2.6,z-8,z+8),int(width*16/4))

def add_game_geometry(mesh,width_scale,lifts):
    """Actual original hangar floor and three-sided lift trunks in the package.

    Open port faces join the hangar. Platforms stay at flight-deck height in
    this prototype; this does not invent a native elevator animation.
    """
    def box(name,b,material):
        a,c,d,e,f,g=b
        mesh.box(name,(a+c)/2/width_scale,(d+e)/2,(f+g)/2,
                 (c-a)/width_scale,e-d,g-f,material)
    a,b,c,d,e,f=HANGAR
    box('HangarDeck',(a,b,c-.15,c,e,f),'dark')
    for s in shafts(lifts):
        a,b,c,d,e,f=s.bounds
        # Shaft floor below the hangar landing plane, three enclosing walls;
        # the inboard/port doorway stays open across its full width.
        box(s.name.replace(' ','_')+'_Floor',(a,b,11.45,11.60,e,f),'hull')
        box(s.name.replace(' ','_')+'_OuterWall',(b-.15,b,11.60,20.3,e,f),'hull')
        box(s.name.replace(' ','_')+'_ForwardWall',(a,b,11.60,20.3,f-.15,f),'hull')
        box(s.name.replace(' ','_')+'_AftWall',(a,b,11.60,20.3,e,e+.15),'hull')

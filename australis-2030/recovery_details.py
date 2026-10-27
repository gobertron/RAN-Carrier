"""Original naval details for the reconstructed recovery release; metres."""
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HULL_NUMBER=91
LIGHTS=[]
for z in range(-150,151,30):
    for x in (-29,29):
        LIGHTS.append(dict(position=(x,22.25,z),color=(.15,.38,.8),range=5,intensity=.22,kind='guide'))
for z in range(-120,141,35):
    for x in (-18,18):
        LIGHTS.append(dict(position=(x,19.35,z),color=(1.,.88,.65),range=13,intensity=.9,kind='hangar'))
for x,z in ((26,50),(26,-45),(30,-116),(30,86)):
    LIGHTS.append(dict(position=(x,24,z),color=(1.,.82,.55),range=8,intensity=.35,kind='task'))

def detail_mesh(mesh,width_scale,deck,lift_centres=None):
    def box(n,x,y,z,w,h,l,mat):mesh.box(n,x/width_scale,y,z,w/width_scale,h,l,mat)
    # Cut actual turret pockets through both island roofs. Split top faces around
    # the moving covers; imported CAD/game data is not used.
    from shapely.geometry import Polygon,box as rectangle
    from shapely.ops import triangulate
    for part_name,cx,cz,roof in (('IntegratedBridge',30.3,-11,44.),('AftEnclosedMast',30.3,-88,37.84)):
        hole=rectangle((cx-3.2)/width_scale,cz-3.2,(cx+3.2)/width_scale,cz+3.2)
        idx=next(i for i,p in enumerate(mesh.parts) if p[0]==part_name)
        name,v,faces,mat=mesh.parts[idx];vv=v.tolist();ff=[]
        for face in faces:
            poly=Polygon([(v[j][0],v[j][2]) for j in face])
            if all(abs(v[j][1]-roof)<.001 for j in face):
                rem=poly.difference(hole)
                for tri in triangulate(rem):
                    if rem.covers(tri.representative_point()) and rem.covers(tri):
                        pts=list(tri.exterior.coords)[:3];offset=len(vv)
                        vv.extend((x,roof,z) for x,z in pts);ff.append([offset,offset+2,offset+1])
            else:ff.append(face)
        mesh.parts[idx]=(name,np.array(vv),ff,mat)
    from naval_fittings import add_naval_fittings
    add_naval_fittings(mesh,width_scale)
    # Arrested-landing tyre streaks: narrow, broken, subdued paint.
    for row in range(18):
        z=-130+row*6.5;x=3-(z+166)*math.tan(math.radians(9))
        for side in (-1,1):
            box(f'TyreMark_{row}_{side}',x+side*2.2,22.004,z,.11,.001,2+(row%4)*.6,'dark')
    for i,l in enumerate(LIGHTS):
        x,y,z=l['position'];box(f'LampFixture_{i}',x,y,z,.32,.12,.48,'hatch')
        box(f'LampLens_{i}',x,y+.065,z,.19,.025,.30,'laser' if l['kind']=='guide' else 'white')
    if lift_centres is not None:
        from lift_lighting import add_fixtures
        add_fixtures(mesh,width_scale,lift_centres)
    # Recessed green touchdown guidance, red port and green starboard navigation lenses.
    for j in range(12):
        z=-151+j*14;x=3-(z+166)*math.tan(math.radians(9))
        for side in (-1,1):box(f'LandingLight_{j}_{side}',x+side*9.9,22.008,z,.17,.012,.35,'laser')
    # Hull numbers are supplied by native per-variant enlarged number textures.

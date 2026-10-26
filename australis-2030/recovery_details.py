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
    # Replace the long ribbon windows: small panes follow all six raked faces.
    mesh.parts[:]=[p for p in mesh.parts if not p[0].startswith('BridgeWindow')]
    base=[(28,-17),(34,-19),(38,-12),(38,26),(32,33),(28,27)]
    def ring(y):
        t=(y-36.6)/7.4
        return [(x+(33+(x-33)*.82-x)*t,y,z+(7+(z-7)*.84-z)*t) for x,z in base]
    lo,hi=ring(41.8),ring(43.05)
    for face in range(6):
        a,b=np.array(lo[face]),np.array(lo[(face+1)%6]);c,d=np.array(hi[face]),np.array(hi[(face+1)%6])
        length=np.linalg.norm(b-a);n=max(1,int(length/1.2));normal=np.cross(b-a,c-a);normal/=np.linalg.norm(normal);normal*=.055
        for j in range(n):
            u,v=(j+.08)/n,(j+.92)/n
            points=[a+(b-a)*u+normal,a+(b-a)*v+normal,c+(d-c)*v+normal,c+(d-c)*u+normal]
            # Closed thin pane, correctly projected from physical X to author frame.
            verts=[tuple(p*np.array((1,1,1))) for p in points]+[tuple(p-normal*.5) for p in points]
            mesh.add(f'BridgePane_{face}_{j}',verts,[[0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]],'glass')
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
    # Island watertight doors and dog handles. Located on actual island faces.
    for j,(x,y,z) in enumerate(((26.2,24,-12),(38.5,24,6),(27.8,24,-88))):
        box(f'NavalDoor_{j}',x,y,z,.1,1.95,.85,'edge')
        box(f'DoorInset_{j}',x-.065,y,z,.08,1.68,.65,'hatch')
        for dy in (-.6,0,.6):box(f'DoorDogs_{j}_{dy}',x-.13,y+dy,z+.31,.12,.08,.17,'dark')
    # Hull-side doors follow an actual hull cross-section at y=14.
    hull=next(p for p in mesh.parts if p[0]=='HardChineHull')
    verts=hull[1]
    def shell_x(z,side):
        hits=[]
        for f in hull[2]:
            for k in range(1,len(f)-1):
                a,b,c=verts[[f[0],f[k],f[k+1]]];den=(b[2]-c[2])*(a[1]-c[1])+(c[1]-b[1])*(a[2]-c[2])
                if abs(den)<1e-10:continue
                u=((b[2]-c[2])*(14-c[1])+(c[1]-b[1])*(z-c[2]))/den;v=((c[2]-a[2])*(14-c[1])+(a[1]-c[1])*(z-c[2]))/den
                if min(u,v,1-u-v)>=-1e-8:hits.append(u*a[0]+v*b[0]+(1-u-v)*c[0])
        return (max(hits) if side>0 else min(hits))*width_scale
    for side in (-1,1):
        for j,z in enumerate((-126,-62,0,62,125)):
            x=shell_x(z,side)+side*.07
            box(f'HullDoor_{side}_{j}',x,14,z,.12,2.0,1.0,'edge')
            box(f'HullDoorHandle_{side}_{j}',x+side*.08,14,z+.3,.12,.07,.2,'dark')
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
    # Original painted numerals: stencil-like geometry on deck and each island side.
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',48)
    im=Image.new('L',(90,60));ImageDraw.Draw(im).text((0,-8),str(HULL_NUMBER),font=font,fill=255)
    im=im.resize((36,22))
    for yy in range(im.height):
        start=None
        for xx in range(im.width+1):
            on=xx<im.width and im.getpixel((xx,yy))>160
            if on and start is None:start=xx
            if start is not None and not on:
                w=xx-start;cx=(start+xx)/2
                box(f'PaintNumberDeck_{yy}_{start}',20+(cx-18)*.15,22.009,149+(11-yy)*.19,w*.15,.003,.19,'white')
                tower_y=30+(11-yy)*.11
                tower_x=(26+1.17*(tower_y-22)/15)*width_scale-.025
                box(f'PaintNumberTower_{yy}_{start}',tower_x,tower_y,8+(cx-18)*.11,.025,.11,w*.11,'white')
                start=None

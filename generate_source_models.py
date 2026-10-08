#!/usr/bin/env python3
"""Author and render original model studies; this script makes no game writes."""
from pathlib import Path

import json, math

import numpy as np

COLORS = {'hull': '#96a2ac','underwater':'#7d3334','deck':'#475461','island':'#aab6c0',
          'glass':'#1c394c','white':'#e8ecec','gold':'#e7bd5c','dark':'#27333d','laser':'#64dbd2'}

def triangulate(points):
    """Ear-clip a simple X/Z polygon, returning counter-clockwise faces."""
    p=np.asarray(points,dtype=float)
    area=sum(p[i,0]*p[(i+1)%len(p),1]-p[(i+1)%len(p),0]*p[i,1] for i in range(len(p)))
    ids=list(range(len(p))) if area>0 else list(range(len(p)-1,-1,-1))
    faces=[]
    def cross(a,b,c):
        u=b-a;v=c-a
        return u[0]*v[1]-u[1]*v[0]
    while len(ids)>3:
        for j,b in enumerate(ids):
            a=ids[j-1];c=ids[(j+1)%len(ids)]
            if cross(p[a],p[b],p[c])<=1e-8:continue
            if any(cross(p[a],p[b],p[k])>=-1e-8 and cross(p[b],p[c],p[k])>=-1e-8 and cross(p[c],p[a],p[k])>=-1e-8 for k in ids if k not in (a,b,c)):continue
            faces.append([a,b,c]);ids.pop(j);break
        else:raise ValueError('Deck outline cannot be triangulated')
    faces.append(ids)
    return faces

class Mesh:
    def __init__(self): self.parts=[]
    def add(self, name, verts, faces, mat):
        v=np.array(verts,dtype=float)
        f=[list(x) for x in faces]
        volume=sum(np.dot(v[x[0]],np.cross(v[x[i]],v[x[i+1]]))/6 for x in f for i in range(1,len(x)-1))
        if volume<0:f=[list(reversed(x)) for x in f]
        self.parts.append((name,v,f,mat))
    def box(self,name,x,y,z,dx,dy,dz,mat='island'):
        v=[[x+a*dx/2,y+b*dy/2,z+c*dz/2] for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        self.add(name,v,[[0,3,2,1],[4,5,6,7],[0,1,5,4],[3,7,6,2],[0,4,7,3],[1,2,6,5]],mat)
    def prism(self,name,points,low,high,mat='deck'):
        n=len(points);v=[[x,low,z] for x,z in points]+[[x,high,z] for x,z in points]
        cap=triangulate(points)
        f=[list(x) for x in cap]+[[n+i for i in reversed(x)] for x in cap]
        area=sum(points[i][0]*points[(i+1)%n][1]-points[(i+1)%n][0]*points[i][1] for i in range(n))
        f += [[i,i+n,(i+1)%n+n,(i+1)%n] for i in range(n)]
        if area<0:f=[list(reversed(x)) if len(x)==4 else x for x in f]
        self.add(name,v,f,mat)
    def cylinder(self,name,x,y,z,r,h,mat='island',n=16):
        self.prism(name,[(x+r*math.cos(2*math.pi*i/n),z+r*math.sin(2*math.pi*i/n)) for i in range(n)],y,y+h,mat)
    def stripe(self,name,a,b,width,y,mat='white'):
        d=np.array(b)-a; norm=np.linalg.norm(d)
        if norm==0:return
        off=np.array([-d[1],d[0]])*width/(2*norm)
        self.prism(name,[np.array(a)+off,np.array(b)+off,np.array(b)-off,np.array(a)-off],y,y+0.04,mat)
    def triangles(self):
        for name,v,faces,mat in self.parts:
            for f in faces:
                for i in range(1,len(f)-1):yield name,v[[f[0],f[i],f[i+1]]],mat
    def save(self,path,scale=1):
        path.parent.mkdir(parents=True,exist_ok=True)
        mtl=path.with_suffix('.mtl')
        mtl.write_text(''.join('newmtl '+k+'\nKd '+' '.join(f'{int(c[i:i+2],16)/255:.5f}' for i in (1,3,5))+'\nKa 0.15 0.15 0.15\nKs 0.1 0.1 0.1\nNs 20\n\n' for k,c in COLORS.items()))
        out=['# RAN Carrier Restart: original model study; coordinates in metres',f'mtllib {mtl.name}'];offset=1
        for name,v,faces,mat in self.parts:
            out += [f'o {name}',f'usemtl {mat}']
            out += ['v '+' '.join(f'{a*scale:.6f}' for a in p) for p in v]
            for f in faces:
                out += ['f '+' '.join(str(offset+j) for j in [f[0],f[i],f[i+1]]) for i in range(1,len(f)-1)]
            offset += len(v)
        path.write_text('\n'.join(out)+'\n')

def geometry(s):
    m=Mesh();L=s['length_m'];W=s['deck_width_m'];old=s['year']<1960
    H=15.5 if old else 20; B=W*(.65 if old else .47)
    # Rounded sectioned hull, visibly different from the flat flight deck.
    zs=np.linspace(-L*.48,L*.495,37)
    rows=[];wet=[]
    for z in zs:
        q=(z+L*.48)/(L*.975)
        wf=(.72+.28*math.sin(math.pi*min(q/.7,1)/2))*(1-.97*max((q-.76)/.24,0)**1.5)
        half=B*.5*wf
        rows.append([[-half*.97,0,z],[-half,3,z],[-half*.99,H-1.3,z],
                     [half*.99,H-1.3,z],[half,3,z],[half*.97,0,z]])
        wet.append([[-half*.60,-8.5,z],[-half*.93,-3,z],[-half*.97,0,z],
                    [half*.97,0,z],[half*.93,-3,z],[half*.60,-8.5,z]])
    v=[p for row in rows for p in row];f=[]
    for j in range(len(rows)-1):
        for i in range(6):f.append([j*6+i,j*6+(i+1)%6,(j+1)*6+(i+1)%6,(j+1)*6+i])
    f += [[i for i in range(5,-1,-1)],[(len(rows)-1)*6+i for i in range(6)]]
    m.add('Hull',v,f,'hull')
    m.add('UnderwaterHull',[p for row in wet for p in row],f,'underwater')
    angle=s['year']>=1959
    if not angle:
        outline=[(-W*.43,-L*.49),(W*.43,-L*.49),(W*.5,-L*.3),(W*.5,L*.38),(W*.40,L*.5),(-W*.40,L*.5),(-W*.5,L*.38),(-W*.5,-L*.3)]
    else:
        outline=[(-W*.36,-L*.5),(W*.35,-L*.5),(W*.49,-L*.38),(W*.49,L*.30),(W*.38,L*.5),(-W*.34,L*.5),(-W*.48,L*.31),(-W*.55,-L*.12),(-W*.54,-L*.32)]
    m.prism('FlightDeck',outline,H-1,H,'deck')
    island_x=W*.365; island_z=-L*.08
    futuristic=s['year']>=2000
    if futuristic:
        p=[(island_x-W*.065,island_z-L*.11),(island_x+W*.065,island_z-L*.11),(island_x+W*.045,island_z+L*.11),(island_x-W*.045,island_z+L*.11)]
        m.prism('Island',p,H,H+12,'island')
        m.box('Bridge',island_x,H+14,island_z+L*.06,W*.14,3,L*.09)
        m.box('BridgeGlass',island_x-W*.071,H+14,island_z+L*.06,.18,1.6,L*.085,'glass')
        m.prism('IntegratedMast',[(island_x-4,island_z-4),(island_x+4,island_z-4),(island_x+3,island_z+3),(island_x-3,island_z+3)],H+12,H+27,'island')
        if s['year']>=2009:
            m.box('AviationIsland',island_x,H+6,-L*.28,W*.1,12,L*.075)
            m.box('AviationGlass',island_x-W*.051,H+10,-L*.28,.18,2,L*.065,'glass')
    else:
        m.box('Island',island_x,H+4,island_z,W*(.16 if old else .12),8,L*.20)
        m.box('Bridge',island_x-W*.015,H+10,island_z+L*.035,W*.16,4,L*.08)
        m.box('BridgeGlass',island_x-W*.096,H+10,island_z+L*.035,.15,1.7,L*.07,'glass')
        m.cylinder('Mast',island_x,H+12,island_z-4,.8 if old else 1.2,14)
        if s['propulsion']=='Steam':m.box('Funnel',island_x,H+8,island_z-L*.05,W*.075,10,L*.045,'dark')
        if s['year']>=1950:
            m.box('AirRadar',island_x,H+27,island_z-4,W*.15,3,.7,'dark')
            m.box('SurfaceRadar',island_x,H+20,island_z+L*.04,W*.1,.9,.5,'dark')
    # Visible lifts, rails, catapult tracks and a landing lane.
    n_lifts=2 if old else 4
    for j in range(n_lifts):
        x=(W*.40 if j<3 else -W*.42);z=L*([.23,-.18,-.34,-.22][j])
        m.box(f'Elevator_{j+1}',x,H+.08,z,10 if old else 18,.16,12 if old else 20,'hull')
    cats=1 if s['year']<1959 else (2 if old else 4)
    for j in range(cats):
        x=W*([.14,-.15,-.30,-.39][j]);z=L*(.24 if j<2 else -.10)
        m.stripe(f'Catapult_{j+1}',(x,z),(x+.8,z+L*.23),.7,H+.11,'gold')
    if angle:a=(W*.12,-L*.44);b=(-W*.30,L*.20)
    else:a=(0,-L*.45);b=(0,L*.44)
    lane=7 if old else 12
    for sign in [-1,1]:m.stripe(f'LandingEdge_{sign}',(a[0]+sign*lane,a[1]),(b[0]+sign*lane,b[1]),.25,H+.12)
    for k in range(14):
        p=np.array(a)+(np.array(b)-a)*(k/14);q=np.array(a)+(np.array(b)-a)*((k+.45)/14)
        m.stripe(f'Centreline_{k}',p,q,.35,H+.13)
    # Defensive mounts lie below the flight deck, away from the landing lane.
    for k,(x,z) in enumerate([(-W*.48,L*.28),(W*.46,L*.28),(-W*.44,-L*.40),(W*.43,-L*.40)]):
        m.box(f'Sponson_{k+1}',x,H-1.2,z,5 if old else 7,1.4,7 if old else 10,'hull')
        m.cylinder(f'AA_Base_{k+1}',x,H-.5,z,1.2 if old else 1.8,2,'island')
        if s['year']>=1980:m.cylinder(f'CIWS_Radome_{k+1}',x,H+1.5,z,.8,1.9,'white')
        else:
            for side in (-1,1):m.box(f'AA_Gun_{k+1}_{side}',x+side*.3,H+1.2,z,.25,.25,3,'dark')
        if s['year']>=2020:
            m.box(f'LaserMount_{k+1}',x,H+1.5,z,2.2,2,2.8,'island')
            m.box(f'LaserAperture_{k+1}',x,H+1.5,z+1.5,1.2,1.2,.15,'laser')
    m.cylinder('SonarDome',0,-9,L*.38,3.4 if not old else 1.5,2,'dark')
    for sign in [-1,1]:
        m.box('NoisemakerPort' if sign<0 else 'NoisemakerStarboard',sign*B*.25,H-4,-L*.45,1.4,1.4,2,'dark')
        if s['year']>=1960:
            tx=sign*W*.42;tz=L*.12
            m.box(f'ASW_Sponson_{sign}',tx,H-3,tz,5,1.5,7,'hull')
            for j in range(3):m.box(f'ASW_Tube_{sign}_{j}',tx+(j-1)*.65,H-1.8,tz,.45,.5,3,'dark')
            if s['year']>=1968:m.box(f'ASW_Launcher_{sign}',tx,H-2.0,tz-7,3,2.1,4,'island')
        if s['year']>=1968:
            m.box(f'SAM_Sponson_{sign}',sign*W*.44,H-1.7,L*.39,6,1.3,8,'hull')
            m.box(f'SAM_Launcher_{sign}',sign*W*.44,H-.1,L*.39,3.8,2.4,3,'island')
    if s['offensive_ecm_modules']:
        ey=H+28
        m.box('OffensiveECM_Module',island_x,ey,island_z,5,2.4,4.2,'island')
        for sign in (-1,1):m.box(f'OffensiveECM_Array_{sign}',island_x+sign*2.6,ey,island_z,.15,1.8,3.5,'dark')
    return m

def render(s,m,path,top=False):
    # Orthographic, per-pixel depth buffer: long deck triangles must not hide
    # the island, as a polygon-centre painter sort would do.
    from PIL import Image, ImageDraw, ImageFont
    width,height=1725,885
    rgb=np.empty((height,width,3),dtype=np.uint8);rgb[:]=[15,24,33]
    depth=np.full((height,width),-np.inf)
    az=math.radians(-85 if top else -57);el=math.radians(89.9 if top else 26)
    direction=np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)])
    right=np.array([-math.sin(az),math.cos(az),0]);up=np.cross(direction,right)
    tris=list(m.triangles());world=np.concatenate([t[:,[0,2,1]] for _,t,_ in tris])
    projected=np.column_stack([world@right,world@up]);lo=projected.min(axis=0);hi=projected.max(axis=0)
    scale=min((width-240)/(hi[0]-lo[0]),(height-245)/(hi[1]-lo[1]))
    centre=(hi+lo)/2
    light=np.array([.3,-.4,.86]);light/=np.linalg.norm(light)
    for _,tri,mat in tris:
        w=tri[:,[0,2,1]];xy=np.column_stack([w@right,w@up]);xy=(xy-centre)*scale
        xy[:,0]+=width/2;xy[:,1]=height*.56-xy[:,1];z=w@direction
        xmin=max(0,int(np.floor(xy[:,0].min())));xmax=min(width-1,int(np.ceil(xy[:,0].max())))
        ymin=max(0,int(np.floor(xy[:,1].min())));ymax=min(height-1,int(np.ceil(xy[:,1].max())))
        if xmax<xmin or ymax<ymin:continue
        a,b,c=xy;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-6:continue
        xx,yy=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5)
        u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;q=1-u-v
        zz=u*z[0]+v*z[1]+q*z[2];view=depth[ymin:ymax+1,xmin:xmax+1]
        mask=(u>=-1e-6)&(v>=-1e-6)&(q>=-1e-6)&(zz>view)
        n=np.cross(w[1]-w[0],w[2]-w[0]);n/=max(np.linalg.norm(n),1e-9)
        shade=.68+.32*abs(n@light)
        colour=np.array([int(COLORS[mat][i:i+2],16) for i in (1,3,5)])*shade
        view[mask]=zz[mask];rgb[ymin:ymax+1,xmin:xmax+1][mask]=colour.astype(np.uint8)
    im=Image.fromarray(rgb);draw=ImageDraw.Draw(im)
    def font(size,bold=False):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',size)
    draw.text((77,33),s['name'].upper(),font=font(32,True),fill='#eef3f4')
    draw.text((77,86),f"{s['aircraft_capacity']} aircraft  ·  {s['propulsion']}  ·  {s['length_m']:g} m  ·  {s['deck_width_m']:g} m flight deck",font=font(22),fill='#8fd0d0')
    draw.text((77,831),'Original RAN design study / geometry blockout / not an in-game screenshot',font=font(18),fill='#94a4b1')
    im.save(path)

ROOT = Path(__file__).resolve().parent

def validate(s,m):
    from collections import Counter
    if sum(x['count'] for x in s['air_group'])!=s['aircraft_capacity']:
        raise ValueError(s['id']+': air group does not match capacity')
    if s['offensive_ecm_modules'] not in (0,1):raise ValueError('More than one ECM module')
    assert not any('ef111' in x['role'].lower() for x in s['air_group'])
    triangles=0
    for name,v,faces,mat in m.parts:
        assert np.all(np.isfinite(v)), name
        edges=Counter();directed=Counter()
        for f in faces:
            assert min(f)>=0 and max(f)<len(v),name
            for i in range(1,len(f)-1):
                a,b,c=v[[f[0],f[i],f[i+1]]]
                assert np.linalg.norm(np.cross(b-a,c-a))>1e-9,name
                triangles+=1
            for a,b in zip(f,f[1:]+f[:1]):
                edges[tuple(sorted((a,b)))]+=1;directed[(a,b)]+=1
        assert all(n==2 for n in edges.values()),name+' has an open construction surface'
        assert all(directed[(a,b)]==directed[(b,a)] for a,b in directed),name+' has inconsistent winding'
        assert mat in COLORS,name
    return dict(unit=s['id'],capacity=s['aircraft_capacity'],air_group_total=sum(x['count'] for x in s['air_group']),
                offensive_ecm_modules=s['offensive_ecm_modules'],parts=len(m.parts),triangles=triangles,
                finite_vertices=True,valid_faces=True,nonzero_triangles=True,closed_construction_parts=True,
                game_integration_tested=False)

def main():
    from PIL import Image,ImageDraw,ImageFont
    designs=json.loads((ROOT/'fleet-source.json').read_text())['designs']
    assert len(designs)==14
    assert [s['aircraft_capacity'] for s in designs]==[30,30,30,30,68,68,69,69,98,98,98,98,98,99]
    assert sum(s['offensive_ecm_modules'] for s in designs)==8
    (ROOT/'previews').mkdir(exist_ok=True)
    results=[]
    for i,s in enumerate(designs):
        m=geometry(s);results.append(validate(s,m))
        m.save(ROOT/'metre-source-models'/f"{s['id']}.obj")
        render(s,m,ROOT/'previews'/f"{s['id']}.png")
        if s['year'] in (1959,2002,2009,2023):render(s,m,ROOT/'previews'/f"{s['id']}_deck.png",top=True)
        print(f"[{int((i+1)*90/len(designs)):3}%] {s['id']}: {s['aircraft_capacity']} aircraft; geometry checked",flush=True)
    W,H=3840,3490
    overview=Image.new('RGB',(W,H),'#0f1821');d=ImageDraw.Draw(overview)
    fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans'
    def font(n,bold=False):return ImageFont.truetype(fontpath+('-Bold' if bold else '')+'.ttf',n)
    d.text((100,45),'RAN CARRIER RESTART',font=font(68,True),fill='#edf3f4')
    d.text((100,138),'14 model studies | exact air-wing requirements | one shipboard offensive ECM module',font=font(31),fill='#8fd0d0')
    d.text((100,190),'Original geometry rendered here. Sea Power integration and deck trials remain pending.',font=font(29),fill='#a7b4bd')
    tileW,tileH=1212,615
    for i,s in enumerate(designs):
        im=Image.open(ROOT/'previews'/f"{s['id']}.png").convert('RGB')
        im.thumbnail((tileW,tileH),Image.Resampling.LANCZOS)
        col,row=i%3,i//3;x=70+col*1240;y=270+row*625
        overview.paste(im,(x+(tileW-im.width)//2,y+(tileH-im.height)//2))
    x,y=70+2*1240,270+4*625
    d.rounded_rectangle((x+30,y+50,x+1150,y+565),radius=18,outline='#294656',width=3)
    lines=['DESIGN SOURCE','Metre-scale OBJ/MTL models','Air and surface radar plans','Active sonar, ASW and decoys','Eight shipboard offensive ECM modules','Four laser mount studies in 2023','Model views normalised per panel','No installation or Workshop upload']
    for i,line in enumerate(lines):d.text((x+75,y+100+i*51),line,font=font(30,i==0),fill='#8fd0d0' if i==0 else '#b9c8d0')
    d.text((100,3428),'8 October 2026 | Fictional RAN lineage | Model studies, not in-game screenshots',font=font(25),fill='#8d9da9')
    overview.save(ROOT/'RAN-Carrier-Restart.png')
    (ROOT/'validation.json').write_text(json.dumps({'requirements_checked':True,'models':results,'engine_validation':'Pending installed sources and in-game trials'},indent=2)+'\n')
    print('[100%] Fourteen model studies, overview and validation manifest complete',flush=True)

if __name__=='__main__':main()

"""Original inboard bays. Physical metres; no workshop assets/dependencies."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Bay:
    key: str
    x: float
    z: float
    width: float = 6.4
    length: float = 6.4
    stroke: float = 5.
    axis: str = 'x'
    y: float = 19.
    roof: float = 22.
    @property
    def root(self): return self.key+'_Lift'
    def door(self, side): return self.key+'_Door_'+side

BAYS = tuple([Bay('CIWS_1',-30.5,158,axis='z'),Bay('CIWS_2',29.4,-142),Bay('CIWS_3',-25,-158)]
    +[Bay('Mk46_'+str(i),x,z) for i,(x,z) in enumerate([(20,158),(-30,-68)],1)]
    +[Bay('CIWS_4',30.3,-11,6.4,6.4,3.08,'x',40.92,44.) ,Bay('CIWS_5',30.3,-88,6.4,6.4,3.08,'x',34.76,37.84)]
    +[Bay(k+'_'+str(i),x,z,4.6,4.4) for k,ps in [('ESSM',[(-32,-112),(32,104)]),('RAM',[(-32,-48),(32,118)])] for i,(x,z) in enumerate(ps,1)]
    +[Bay('PVLS_'+str(i),x,z,4.6,19,0,'z') for i,(x,z) in enumerate([(-32,-135),(32,140),(-32,-92),(23,-148)],1)]
    +[Bay('SRBOC_'+str(i),x,z,2,2,4) for i,(x,z) in enumerate([(-24,-169),(-27,-116),(-30,-38),(-30,126),(24,-169),(16,-157),(18,-179),(27,126)],1)]
    +[Bay('Nulka_'+str(i),x,z,2,2,0) for i,(x,z) in enumerate([(-9,-176),(-30,74),(9,-176),(18,-146)],1)])
BY_KEY={b.key:b for b in BAYS}

def moving_specs():
    out=[]
    for b in BAYS:
        out.append(dict(name=b.root,parent=None,position=(b.x,b.y,b.z),stroke=b.stroke,axis='y',travel=(b.roof+.08-b.y) if b.stroke else 0))
        for side,sign in [('L',-1),('R',1)]:
            d=(b.width if b.axis=='x' else b.length)/4
            x,z=b.x,b.z
            if b.axis=='x': x+=sign*d
            else: z+=sign*d
            out.append(dict(name=b.door(side),parent=None,position=(x,b.roof,z),stroke=0,axis=b.axis,travel=sign*d*2))
    return out

def add_meshes(mesh, local=False, width_scale=1):
    for b in BAYS:
        def box(name,pos,dim,mat):
            x,y,z=pos;w,h,l=dim
            mesh.box(name,x/width_scale,y,z,w/width_scale,h,l,mat)
        x,y,z=(0,0,0) if local else (b.x,b.y,b.z)
        box(b.root,(x,y-.15,z),(min(4.8,b.width-.2),.3,min(5.8,b.length-.2)),'dark')
        for side,sign in [('L',-1),('R',1)]:
            w,l=b.width,b.length;dx=dz=0
            if b.axis=='x':w/=2;dx=sign*b.width/4
            else:l/=2;dz=sign*b.length/4
            pos=(0,0,0) if local else (b.x+dx,b.roof,b.z+dz)
            box(b.door(side),pos,(w,.004,l),'hatch')

def perforate(mesh,outline,width_scale,low,high,extra_openings=()):
    """Z-slab trapezoids cut exact rectangular wells without optional libraries.

    Original outline vertices stay first for cross-checks. Independent closed
    slabs have coincident internal walls, but no top/bottom faces span a well.
    """
    holes=[((b.x-b.width/2)/width_scale,(b.x+b.width/2)/width_scale,b.z-b.length/2,b.z+b.length/2) for b in BAYS if b.roof==22.]
    holes += [(a/width_scale,b/width_scale,c,d) for a,b,c,d in extra_openings]
    zs=sorted(set([z for x,z in outline]+[z for h in holes for z in h[2:]]))
    verts=[(x,low,z) for x,z in outline]+[(x,high,z) for x,z in outline];faces=[]
    def bounds(z):
        xs=[]
        for (x1,z1),(x2,z2) in zip(outline,outline[1:]+outline[:1]):
            if min(z1,z2)<=z<=max(z1,z2) and z1!=z2:
                xs.append(x1+(z-z1)*(x2-x1)/(z2-z1))
        return min(xs),max(xs)
    for za,zb in zip(zs,zs[1:]):
        if zb<=min(z for x,z in outline) or za>=max(z for x,z in outline):continue
        mid=(za+zb)/2; la,ra=bounds(za);lb,rb=bounds(zb)
        blocked=sorted((a,b) for a,b,c,d in holes if c<mid<d)
        # All openings must remain inboard for their entire longitudinal span.
        for a,b in blocked:
            assert a>max(la,lb) and b<min(ra,rb),(a,b,za,zb,'bay off deck')
        lefta,leftb=la,lb
        for a,b in blocked+[(ra,rb)]:
            righta,rightb=(a,a) if (a,b)!=(ra,rb) else (ra,rb)
            if min(righta-lefta,rightb-leftb)>1e-8:
                points=[(lefta,za),(righta,za),(rightb,zb),(leftb,zb)];o=len(verts)
                verts += [(x,y,z) for y in (low,high) for x,z in points]
                faces += [[o+i for i in f] for f in [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]]
            lefta=leftb=b
    mesh.add('FacetedFlightDeck',verts,faces,'deck')
    # Remove the original hull roof: the perforated deck supplies its roof.
    name,v,f,mat=mesh.parts[0]
    assert name=='HardChineHull'
    mesh.parts[0]=(name,v,f[1:],mat)


def bay_clearance_rectangles():
    """Well walls and fully open covers in physical X/Z metres."""
    for b in BAYS:
        if b.roof!=22.:continue
        yield b.key+' well',(b.x-b.width/2-.2,b.x+b.width/2+.2,b.z-b.length/2-.2,b.z+b.length/2+.2)
        for sign in (-1,1):
            x,z,w,l=b.x,b.z,b.width,b.length
            if b.axis=='x':x+=sign*.75*w;w/=2
            else:z+=sign*.75*l;l/=2
            yield b.key+' open cover',(x-w/2,x+w/2,z-l/2,z+l/2)

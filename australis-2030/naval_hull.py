"""Original, centreline-symmetric game hull and preliminary geometric hydrostatics.

Physical metres: X starboard, Y above design waterline, Z forward.
This establishes geometric plausibility, not structural or seaworthiness approval.
"""
import math
from functools import lru_cache
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import triangulate

LENGTH_WL=362.6
HALF_LENGTH=LENGTH_WL/2
BEAM_WL=41.
DRAFT=11.5
TARGET_MASS=112000.
SEA_DENSITY=1.025  # tonnes per cubic metre, planning reference only
WIDTH_KNOTS=[(-181.3,18.),(-168,18.6),(-148,19.5),(-120,20.),(-80,20.5),
             (60,20.5),(100,20.),(125,18.5),(145,14.),(165,7.5),(178,1.5),(181.3,.2)]
DEPTH_KNOTS=[(-181.3,8.),(-170,8.8),(-155,9.7),(-130,10.8),(-95,11.5),
             (80,11.5),(118,11.3),(145,9.9),(165,6.6),(178,2.1),(181.3,.5)]
PROP_CENTRES=((-9.,-8.25,-166.),(9.,-8.25,-166.))
RUDDER_CENTRES=((-9.,-1.8,-175.),(9.,-1.8,-175.))
PROP_RADIUS=3.

def smooth_curve(knots,x):
    """Shape-preserving piecewise cubic Hermite interpolation, no overshoot."""
    k=np.asarray(knots,float);xs=k[:,0];ys=k[:,1];h=np.diff(xs);delta=np.diff(ys)/h
    slopes=np.zeros(len(k))
    for i in range(1,len(k)-1):
        if delta[i-1]*delta[i]>0:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1]
            slopes[i]=(w1+w2)/(w1/delta[i-1]+w2/delta[i])
    for i,j,sgn in ((0,1,1),(-1,-2,-1)):
        h0,h1=(h[0],h[1]) if i==0 else (h[-1],h[-2])
        d0,d1=(delta[0],delta[1]) if i==0 else (delta[-1],delta[-2])
        m=((2*h0+h1)*d0-h0*d1)/(h0+h1)
        if m*d0<=0:m=0.
        elif d0*d1<0 and abs(m)>3*abs(d0):m=3*d0
        slopes[i]=m
    xx=np.asarray(x,float);ii=np.clip(np.searchsorted(xs,xx,side='right')-1,0,len(xs)-2)
    t=np.clip((xx-xs[ii])/h[ii],0,1)
    out=(2*t**3-3*t**2+1)*ys[ii]+(t**3-2*t**2+t)*h[ii]*slopes[ii]+(-2*t**3+3*t**2)*ys[ii+1]+(t**3-t**2)*h[ii]*slopes[ii+1]
    return float(out) if out.ndim==0 else out

def stations():
    # Include all upper-deck longitudinal vertices so its exact polygon is retained.
    upper_z=(-185,-170,-168,-138,-114,-76,-41,-33,0,60,72,123,125,161,163,185)
    ts=sorted(set(np.linspace(-1,1,97).tolist()+[z/185 for z in upper_z]))
    return np.asarray(ts)*HALF_LENGTH

def cap_faces(vertices,indices,axes,normal_axis,sign):
    """Triangulate planar caps without zero-area fans through collinear vertices."""
    coords=[tuple(vertices[i][list(axes)]) for i in indices]
    poly=Polygon(coords);lookup={tuple(round(a,10) for a in xy):i for xy,i in zip(coords,indices)}
    faces=[]
    for tri in triangulate(poly):
        if not poly.covers(tri):continue
        ids=[lookup[tuple(round(a,10) for a in xy)] for xy in list(tri.exterior.coords)[:3]]
        a,b,c=np.asarray([vertices[i] for i in ids])
        if np.cross(b-a,c-a)[normal_axis]*sign<0:ids.reverse()
        faces.append(ids)
    assert abs(sum(Polygon([coords[indices.index(i)] for i in f]).area for f in faces)-poly.area)<1e-5
    return faces

def mesh_integrals(vertices,faces):
    triangles=np.asarray([[vertices[f[0]],vertices[f[j]],vertices[f[j+1]]] for f in faces for j in range(1,len(f)-1)])
    a,b,c=triangles[:,0],triangles[:,1],triangles[:,2]
    dv=np.einsum('ij,ij->i',a,np.cross(b,c))/6
    volume=float(dv.sum());centroid=(dv[:,None]*(a+b+c)/4).sum(axis=0)/volume
    return volume,centroid

def section_exponent(z,exponent):
    # A locally full transom section houses eight jet throats; forward bilges
    # retain the calibrated hull exponent. Smooth blend ends before midbody.
    blend=smooth_curve([(-181.3,1.),(-160.,1.),(-135.,0.),(181.3,0.)],z)
    return .45*blend+exponent*(1.-blend)


def submerged_mesh(exponent):
    zs=stations();vs=np.sin(np.linspace(0,math.pi/2,25))
    verts=[]
    for z in zs:
        b=smooth_curve(WIDTH_KNOTS,z);d=smooth_curve(DEPTH_KNOTS,z)
        shape=.32+.68*np.maximum(0,np.cos(vs*math.pi/2))**section_exponent(z,exponent)
        verts.extend((b*f,-d*v,z) for v,f in zip(vs,shape))
        verts.extend((-b*f,-d*v,z) for v,f in zip(vs[::-1],shape[::-1]))
    verts=np.asarray(verts);n=len(vs)*2;faces=[]
    for station in range(len(zs)-1):
        a=station*n;b=a+n
        for j in range(len(vs)-1):
            triangles=([a+j,b+j,b+j+1],[a+j,b+j+1,a+j+1])
            for tri in triangles:
                faces.append(list(tri))
                mirrored=[(i//n)*n+(n-1-i%n) for i in tri]
                faces.append(mirrored[::-1])
        for j in (len(vs)-1,n-1):faces.append([a+j,b+j,b+(j+1)%n,a+(j+1)%n])
    faces+=cap_faces(verts,list(range(n)),(0,1),2,-1)
    faces+=cap_faces(verts,list(range((len(zs)-1)*n,len(zs)*n)),(0,1),2,1)
    volume,_=mesh_integrals(verts,faces)
    if volume<0:faces=[f[::-1] for f in faces]
    return verts,faces

@lru_cache(maxsize=1)
def design():
    # Calibrate the NET wet boundary to design displacement, including the
    # genuinely floodable jet ducts. Gross closed-envelope mass is larger.
    from waterjet_geometry import _wet_hull_from_envelope
    target_volume=TARGET_MASS/SEA_DENSITY
    gross_volume_target=target_volume+900.
    for outer in range(6):
        low,high=.45,2.5
        for _ in range(36):
            exponent=(low+high)/2;v,f=submerged_mesh(exponent);vol,_=mesh_integrals(v,f)
            if vol>gross_volume_target:low=exponent
            else:high=exponent
        v,f=submerged_mesh((low+high)/2);volume,centre=mesh_integrals(v,f)
        _,_,wet=_wet_hull_from_envelope(v,f,volume)
        error=target_volume-wet['wet_volume_m3']
        if abs(error)*SEA_DENSITY<.05:break
        gross_volume_target+=error
    assert abs(error)*SEA_DENSITY<.05,('Net waterjet displacement calibration failed',error)
    return v,f,(low+high)/2,volume,centre

def polygon_bounds(outline,z):
    xs=[]
    for (x1,z1),(x2,z2) in zip(outline,outline[1:]+outline[:1]):
        if z1!=z2 and min(z1,z2)-1e-8<=z<=max(z1,z2)+1e-8:
            t=(z-z1)/(z2-z1);xs.append(x1+(x2-x1)*t)
    assert xs,(z,outline)
    return min(xs),max(xs)

def upper_mesh(outlines,width_scale):
    """Preserve the approved upper polygons; transition into the symmetric waterline."""
    zs=stations();ts=zs/HALF_LENGTH;n=len(zs);rings=[]
    for y,outline in outlines:
        bounds=[polygon_bounds([(x*width_scale,z) for x,z in outline],float(t*185)) for t in ts]
        rings.append([(b,y,float(t*185)) for t,(a,b) in zip(ts,bounds)]+[(a,y,float(t*185)) for t,(a,b) in zip(ts[::-1],bounds[::-1])])
    upper=np.asarray(rings[-1]);wl=np.asarray([(smooth_curve(WIDTH_KNOTS,z),0,z) for z in zs]+[(-smooth_curve(WIDTH_KNOTS,z),0,z) for z in zs[::-1]])
    for y in (6.75,4.5,2.25,0.):
        t=y/9.;ring=wl*(1-t)+upper*t;ring[:,1]=y;rings.append(ring)
    verts=np.concatenate(rings);m=2*n;faces=[]
    faces+=cap_faces(verts,list(range(m)),(0,2),1,1)
    for k in range(len(rings)-1):
        a=k*m;b=a+m
        for j in range(m):faces.append([a+j,a+(j+1)%m,b+(j+1)%m,b+j])
    faces+=cap_faces(verts,list(range(len(verts)-m,len(verts))),(0,2),1,-1)
    return verts,faces

def add_hull(mesh,deck,equipment,hangar,width_scale):
    uv,uf=upper_mesh([(20.3,deck),(15.,equipment),(9.,hangar)],width_scale)
    # The perforated deck replaces the upper cap. Its code removes face zero;
    # keep exactly one tagged top face here, even though that face is not exported.
    upper_cap=[i for i,p in enumerate(uv) if abs(p[1]-20.3)<1e-8]
    uf=[f for f in uf if not all(abs(uv[i,1]-20.3)<1e-8 for i in f)]
    author=uv.copy();author[:,0]/=width_scale
    mesh.add('HardChineHull',author,[upper_cap]+uf,'hull')
    from waterjet_geometry import wet_hull
    v,f,_=wet_hull();author=v.copy();author[:,0]/=width_scale
    mesh.add('UnderwaterBody',author,f,'underwater')

def collision_mesh(deck,equipment,hangar,width_scale):
    """Small convex native collider: Sea Power sets MeshCollider.convex=True.

    Detailed visible geometry remains separate. At most 108 support vertices
    keep the triangular convex hull below Unity's 255-polygon limit.
    """
    from scipy.spatial import ConvexHull
    _,_,exponent,_,_=design();points=[]
    for z in (-181.3,-168.,-145.,-100.,0.,100.,145.,168.,181.3):
        b=smooth_curve(WIDTH_KNOTS,z);d=smooth_curve(DEPTH_KNOTS,z)
        for fraction in (0.,.65,1.):
            x=b*(.32+.68*max(0,math.cos(fraction*math.pi/2))**section_exponent(z,exponent))
            for side in (-1,1):points.append((side*x,-d*fraction,z))
    for y,outline in ((22.,deck),(15.,equipment),(9.,hangar)):
        points.extend((x*width_scale,y,z) for x,z in outline)
    v=np.asarray(points);hull=ConvexHull(v);faces=[]
    for face,equation in zip(hull.simplices,hull.equations):
        face=list(map(int,face));a,b,c=v[face]
        if np.dot(np.cross(b-a,c-a),equation[:3])<0:face.reverse()
        faces.append(face)
    assert len(faces)<=255,('Native convex collider polygon budget exceeded',len(faces))
    return v,faces


def orient_solid(vertices,faces):
    """Orient each closed component consistently, then give it outward normals."""
    import collections
    vertices=np.asarray(vertices);faces=[list(f) for f in faces]
    edges=collections.defaultdict(list)
    for i,f in enumerate(faces):
        for a,b in zip(f,f[1:]+f[:1]):edges[tuple(sorted((a,b)))].append((i,1 if a<b else -1))
    assert all(len(v)==2 for v in edges.values()),'Appendage is not a closed component'
    adjacency=collections.defaultdict(list)
    for pair in edges.values():
        (a,da),(b,db)=pair;adjacency[a].append((b,-da*db));adjacency[b].append((a,-da*db))
    signs={}
    for first in range(len(faces)):
        if first in signs:continue
        signs[first]=1;todo=[first];component=[]
        while todo:
            a=todo.pop();component.append(a)
            for b,relative in adjacency[a]:
                expected=signs[a]*relative
                if b in signs:assert signs[b]==expected,'Non-orientable component'
                else:signs[b]=expected;todo.append(b)
        for i in component:
            if signs[i]<0:faces[i].reverse()
        if mesh_integrals(vertices,[faces[i] for i in component])[0]<0:
            for i in component:faces[i].reverse()
    return faces


def add_propeller(mesh,name):
    """Five original swept/pitched blades about the native longitudinal spin axis."""
    def circle(z,r):return [(r*math.cos(a),r*math.sin(a),z) for a in np.linspace(0,2*math.pi,17)[:-1]]
    rings=[circle(z,r) for z,r in ((.55,.42),(.1,.6),(-.5,.5),(-.8,.08))]
    v=np.asarray([p for ring in rings for p in ring]);f=[];n=16
    for k in range(len(rings)-1):
        for j in range(n):f.append([k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j])
    f+=cap_faces(v,list(range(n)),(0,1),2,1)
    f+=cap_faces(v,list(range(len(v)-n,len(v))),(0,1),2,-1)
    verts=v.tolist();faces=[list(a) for a in f]
    for blade in range(5):
        rings=[]
        for radius,width,sweep,pitch in ((.5,.25,0,.05),(1.3,.55,.13,.18),(2.2,.5,.26,.32),(3.,.12,.4,.45)):
            angle=blade*2*math.pi/5+sweep;c,s=math.cos(angle),math.sin(angle)
            ring=[]
            for lateral,axial in ((-width,-.06),(width,-.06),(width,.06),(-width,.06)):
                ring.append((radius*c-lateral*s,radius*s+lateral*c,axial+pitch*lateral))
            rings.append(ring)
        off=len(verts);verts.extend(p for ring in rings for p in ring)
        faces.append([off+3,off+2,off+1,off])
        for k in range(3):
            for j in range(4):faces.append([off+k*4+j,off+k*4+(j+1)%4,off+(k+1)*4+(j+1)%4,off+(k+1)*4+j])
        faces.append([off+12,off+13,off+14,off+15])
    mesh.add(name,verts,orient_solid(verts,faces),'dark')

def add_rudder(mesh,name):
    foil=[(0,1.7),(.18,1.15),(.27,.3),(.13,-1.1),(.025,-2.),(-.025,-2.),(-.13,-1.1),(-.27,.3),(-.18,1.15)]
    verts=[]
    for y,taper,shift in ((-.6,1.,0),(-2.5,1.,-.1),(-5.,.83,-.4),(-7.3,.65,-.7)):
        verts.extend((x*taper,y,z*taper+shift) for x,z in foil)
    v=np.asarray(verts);n=len(foil);faces=[]
    for k in range(3):
        for j in range(n):faces.append([k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j])
    faces+=cap_faces(v,list(range(n)),(0,2),1,1)
    faces+=cap_faces(v,list(range(len(v)-n,len(v))),(0,2),1,-1)
    mesh.add(name,v,orient_solid(v,faces),'dark')

def shaft_geometry(mesh,width_scale):
    def tube(name,a,b,r):
        a,b=np.asarray(a),np.asarray(b);axis=(b-a)/np.linalg.norm(b-a)
        u=np.cross(axis,(1,0,0));u/=np.linalg.norm(u);w=np.cross(axis,u)
        verts=[p+r*(math.cos(t)*u+math.sin(t)*w) for p in (a,b) for t in np.linspace(0,2*math.pi,13)[:-1]]
        n=12;faces=[[j,(j+1)%n,n+(j+1)%n,n+j] for j in range(n)]
        # Tube ends are concealed inside the fairings and propeller hubs.
        v=np.asarray(verts);v[:,0]/=width_scale;mesh.add(name,v,faces,'dark')
    for i,(x,y,z) in enumerate(PROP_CENTRES,1):
        tube(f'PropellerShaft_{i}',(x,-4.8,-135),(x,y,z+.35),.28)
        # Paired shaft supports are visual structure, not a stress calculation.
        tube(f'ShaftBracket_{i}',(x*.70,-3.5,-158),(x,y,-161),.20)
    for i,(x,y,z) in enumerate(RUDDER_CENTRES,1):
        tube(f'RudderStock_{i}',(x,-.1,z),(x,-3.0,z),.20)


def add_bilge_keels(mesh,width_scale):
    _,_,exponent,_,_=design()
    zs=np.linspace(-85,75,25)
    fraction=.70
    shape=.32+.68*math.cos(fraction*math.pi/2)**exponent
    for side in (-1,1):
        verts=[]
        for z in zs:
            rootx=side*smooth_curve(WIDTH_KNOTS,z)*shape
            rooty=-smooth_curve(DEPTH_KNOTS,z)*fraction
            verts.extend(((rootx/width_scale,rooty,z),((rootx+side*.9)/width_scale,rooty-.45,z),((rootx+side*.9)/width_scale,rooty-.51,z),(rootx/width_scale,rooty-.06,z)))
        faces=[[3,2,1,0]]
        for k in range(len(zs)-1):
            for j in range(4):faces.append([k*4+j,k*4+(j+1)%4,(k+1)*4+(j+1)%4,(k+1)*4+j])
        off=len(verts)-4;faces.append([off,off+1,off+2,off+3])
        mesh.add(f'BilgeKeel_{side}',verts,orient_solid(verts,faces),'underwater')

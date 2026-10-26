"""Eight original waterjet units and true inlet/outlet openings, physical metres.

The installation is a packaging prototype, not a matched manufacturer's design.
The closed envelope in naval_hull.design is distinct from this visible wet shell.
"""
from functools import lru_cache
from collections import defaultdict
import math
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import triangulate, unary_union

OUTLET_BORE=2.35
OUTLET_RADIUS=OUTLET_BORE/2
OUTER_RADIUS=1.35
TRANSOM_Z=-181.3
JET_Y=-3.6
JET_X=(-13.3,-9.5,-5.7,-1.9,1.9,5.7,9.5,13.3)
JET_CENTRES=tuple((x,JET_Y,TRANSOM_Z) for x in JET_X)
IMPELLER_CENTRES=tuple((x,JET_Y,-173.3) for x in JET_X)
STEERING_INDICES=(1,2,7,8)
INTAKE_WIDTH=2.70
INTAKE_LENGTH=9.60
INTAKE_CENTRE_Z=-163.5
NOZZLE_AFT_Z=-183.10
N_CIRCLE=32

def intake_footprint(x):
    """Rounded footprint projected onto the X,Z plane; not hydraulic face area."""
    radius=.65
    core=Polygon([(x-INTAKE_WIDTH/2+radius,INTAKE_CENTRE_Z-INTAKE_LENGTH/2+radius),
                  (x+INTAKE_WIDTH/2-radius,INTAKE_CENTRE_Z-INTAKE_LENGTH/2+radius),
                  (x+INTAKE_WIDTH/2-radius,INTAKE_CENTRE_Z+INTAKE_LENGTH/2-radius),
                  (x-INTAKE_WIDTH/2+radius,INTAKE_CENTRE_Z+INTAKE_LENGTH/2-radius)])
    return core.buffer(radius,quad_segs=4)

def _triangulated(poly):
    if poly.is_empty:return []
    if poly.geom_type=='MultiPolygon':return [t for p in poly.geoms for t in _triangulated(p)]
    return [list(t.exterior.coords)[:3] for t in triangulate(poly) if poly.covers(t) and t.area>1e-10]

def _ring_z(x,y,z,r,n=N_CIRCLE):
    return np.array([(x+r*math.cos(t),y+r*math.sin(t),z) for t in np.linspace(0,2*math.pi,n,endpoint=False)])

def _weld(vertices,faces):
    lookup={};verts=[];fs=[]
    for f in faces:
        row=[]
        for i in f:
            p=vertices[i];key=tuple(round(float(a),8) for a in p)
            if key not in lookup:lookup[key]=len(verts);verts.append(p)
            row.append(lookup[key])
        if len(set(row))==len(row):fs.append(row)
    return np.asarray(verts),fs

def _boundary_loops(vertices,faces):
    edges=defaultdict(list)
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):edges[tuple(sorted((a,b)))].append((a,b))
    boundary=[row[0] for row in edges.values() if len(row)==1]
    assert all(len(row) in (1,2) for row in edges.values()),'Nonmanifold cut hull'
    links=defaultdict(list)
    for a,b in boundary:links[a].append(b);links[b].append(a)
    assert all(len(row)==2 for row in links.values()),'Intake boundary is not a simple ring'
    loops=[];unused=set(links)
    while unused:
        first=min(unused);loop=[first];prev=None;cur=first
        while True:
            nxt=next(n for n in links[cur] if n!=prev)
            if nxt==first:break
            loop.append(nxt);prev,cur=cur,nxt
        unused.difference_update(loop);loops.append(loop)
    return loops

def _loft(vertices,faces,ring_a,ring_b):
    """Zipper loft two ordered rings, allowing unequal vertex counts."""
    na,nb=len(ring_a),len(ring_b);ia=ib=0
    while ia<na or ib<nb:
        ta=(ia+1)/na if ia<na else math.inf
        tb=(ib+1)/nb if ib<nb else math.inf
        a=ring_a[ia%na];b=ring_b[ib%nb]
        if abs(ta-tb)<1e-10:
            an=ring_a[(ia+1)%na];bn=ring_b[(ib+1)%nb]
            faces.extend(([a,an,bn],[a,bn,b]));ia+=1;ib+=1
        elif ta<tb:
            faces.append([a,ring_a[(ia+1)%na],b]);ia+=1
        else:
            faces.append([a,ring_b[(ib+1)%nb],b]);ib+=1

def _resample_order(vertices,loop,axes,centre,start_angle=0):
    """Order a convex loop around its centroid, beginning near a shared ray."""
    centre=np.asarray(centre);p=vertices[loop][:,axes]-centre
    angles=np.mod(np.arctan2(p[:,1],p[:,0])-start_angle,2*math.pi)
    return [loop[i] for i in np.argsort(angles)]

def _wet_hull_from_envelope(src,srcfaces,envelope_volume):
    """Cut 8 bottom mouths + 8 transom bores, then join with internal wet ducts.

    The reference hull top at Y=0 stays intact. All cuts are made by subtracting
    polygons from actual shell triangles. No original hull face spans a mouth.
    This is a renderable internal duct surface, not CFD geometry certification.
    """
    from naval_hull import orient_solid,mesh_integrals
    mouths=tuple(intake_footprint(x) for x in JET_X)
    mouth_union=unary_union(mouths)
    bores=tuple(Point(x,JET_Y).buffer(OUTLET_RADIUS,quad_segs=N_CIRCLE//4) for x in JET_X)
    bore_union=unary_union(bores)
    verts=[];faces=[]
    for f in srcfaces:
        for j in range(1,len(f)-1):
            tri=src[[f[0],f[j],f[j+1]]]
            is_transom=bool(np.max(np.abs(tri[:,2]-TRANSOM_Z))<1e-7)
            is_bottom=bool(np.max(tri[:,1])<-.000001 or (np.min(tri[:,1])<-.001 and np.max(tri[:,2])>INTAKE_CENTRE_Z-INTAKE_LENGTH/2 and np.min(tri[:,2])<INTAKE_CENTRE_Z+INTAKE_LENGTH/2))
            axes=(0,1) if is_transom else (0,2)
            cutter=bore_union if is_transom else mouth_union
            poly=Polygon(tri[:,axes])
            candidate=is_transom or is_bottom
            if not candidate or poly.area<1e-10 or not poly.intersects(cutter):
                off=len(verts);verts.extend(tri);faces.append([off,off+1,off+2]);continue
            clipped=poly.difference(cutter)
            origin=tri[0];matrix=np.array([tri[1,list(axes)]-tri[0,list(axes)],tri[2,list(axes)]-tri[0,list(axes)]]).T
            normal=np.cross(tri[1]-tri[0],tri[2]-tri[0])
            for coords in _triangulated(clipped):
                points=[]
                for xy in coords:
                    u,w=np.linalg.solve(matrix,np.asarray(xy)-origin[list(axes)])
                    points.append(origin+u*(tri[1]-origin)+w*(tri[2]-origin))
                if np.dot(np.cross(points[1]-points[0],points[2]-points[0]),normal)<0:points.reverse()
                off=len(verts);verts.extend(points);faces.append([off,off+1,off+2])
    verts,faces=_weld(verts,faces)
    loops=_boundary_loops(verts,faces)
    assert len(loops)==16,('Expected 8 real mouths and 8 real outlet bores',len(loops))
    bottom=[];transom=[]
    for loop in loops:
        centre=verts[loop].mean(axis=0)
        (transom if abs(centre[2]-TRANSOM_Z)<1e-5 else bottom).append((centre[0],loop))
    bottom.sort();transom.sort();assert len(bottom)==len(transom)==8
    vertices=verts.tolist();duct_faces=[];duct_metadata=[]
    # Intake lofts turn into a horizontal pump tunnel at z=-171.8. The pump
    # impellers sit at -173.3; the tube continues to the open transom bore.
    for i,(x,(_,inlet),(_,outlet)) in enumerate(zip(JET_X,bottom,transom),1):
        inlet=_resample_order(verts,inlet,(0,2),(x,INTAKE_CENTRE_Z))
        outlet=_resample_order(verts,outlet,(0,1),(x,JET_Y))
        ring=_ring_z(x,JET_Y,-171.8,OUTLET_RADIUS)
        pump=list(range(len(vertices),len(vertices)+len(ring)));vertices.extend(ring)
        local=[]
        _loft(vertices,local,inlet,pump)
        _loft(vertices,local,pump,outlet)
        duct_faces.extend(local)
        duct_vertices=np.asarray(vertices)[sorted({j for face in local for j in face})]
        duct_metadata.append(dict(index=i,inlet_vertices=len(inlet),outlet_vertices=len(outlet),projected_intake_area_m2=mouths[i-1].area,
                                  inlet_xyz_bounds=[verts[inlet].min(axis=0).tolist(),verts[inlet].max(axis=0).tolist()],
                                  wet_duct_xyz_bounds=[duct_vertices.min(axis=0).tolist(),duct_vertices.max(axis=0).tolist()]))
    all_faces=faces+duct_faces
    # Mirror the positive half including duct triangulation. This avoids a
    # tiny geometric asymmetry from unrelated transom-cap triangulations.
    clipped_vertices=[];clipped_faces=[]
    for face in all_faces:
        for j in range(1,len(face)-1):
            poly=[np.asarray(vertices[k]) for k in (face[0],face[j],face[j+1])]
            result=[]
            for a,b in zip(poly,poly[1:]+poly[:1]):
                ain=a[0]>=-1e-9;bin=b[0]>=-1e-9
                if ain:result.append(a.copy())
                if ain!=bin:
                    p=a+(b-a)*(-a[0]/(b[0]-a[0]));p[0]=0.;result.append(p)
            if len(result)<3:continue
            if all(abs(p[0])<1e-8 for p in result):continue
            for k in range(1,len(result)-1):
                tri=[result[0],result[k],result[k+1]]
                if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))<1e-10:continue
                off=len(clipped_vertices);clipped_vertices.extend(tri);clipped_faces.append([off,off+1,off+2])
                mirrored=[p*np.array([-1.,1.,1.]) for p in tri]
                off=len(clipped_vertices);clipped_vertices.extend(mirrored);clipped_faces.append([off+2,off+1,off])
    vv,all_faces=_weld(clipped_vertices,clipped_faces);vertices=vv.tolist()
    all_faces=orient_solid(np.asarray(vertices),all_faces)
    volume,centre=mesh_integrals(np.asarray(vertices),all_faces)
    metadata=dict(open_intakes=8,open_outlets=8,closed_wet_boundary=True,envelope_volume_m3=envelope_volume,wet_volume_m3=volume,
                  floodable_duct_volume_m3=envelope_volume-volume,wet_centre_of_buoyancy_xyz_m=centre.tolist(),ducts=duct_metadata,
                  note='Rendered duct lofts are preliminary. Duct-corrected geometric displacement is not detailed loading or certified hydrostatics.')
    # The final mesh is mirrored from starboard, so expose equally mirrored
    # port reservation bounds rather than pre-mirror tessellation details.
    for i in range(4):
        right=metadata['ducts'][7-i];left=metadata['ducts'][i]
        for key in ('wet_duct_xyz_bounds','inlet_xyz_bounds'):
            a,b=right[key]
            left[key]=[[-b[0],a[1],a[2]],[-a[0],b[1],b[2]]]
        left['inlet_vertices']=right['inlet_vertices'];left['outlet_vertices']=right['outlet_vertices']
    return np.asarray(vertices),all_faces,metadata

@lru_cache(maxsize=1)
def wet_hull():
    from naval_hull import design
    src,srcfaces,_,volume,_=design()
    return _wet_hull_from_envelope(src,srcfaces,volume)


def add_static_waterjets(mesh,width_scale):
    """Stationary collars, visible flow straighteners and installation detail."""
    from naval_hull import orient_solid
    for i,(x,y,z) in enumerate(JET_CENTRES,1):
        # An annular transom collar has a genuinely hollow throat. Interior
        # bore comes from wet_hull, so no disc closes the flow path.
        vv=[]
        for zz,rr in ((z+.20,OUTER_RADIUS),(z-.20,OUTER_RADIUS),(z-.20,OUTLET_RADIUS),(z+.20,OUTLET_RADIUS)):
            vv.extend(_ring_z(x,y,zz,rr))
        ff=[];n=N_CIRCLE
        for k in range(4):
            for j in range(n):ff.append([k*n+j,k*n+(j+1)%n,((k+1)%4)*n+(j+1)%n,((k+1)%4)*n+j])
        v=np.asarray(vv);v[:,0]/=width_scale
        mesh.add(f'WaterjetTransomCollar{i}',v,orient_solid(v,ff),'edge')
        if i not in STEERING_INDICES:
            _add_nozzle(mesh,f'WaterjetFixedNozzle{i}',(x,y,z),width_scale,steering=False)
        # Straightening vanes sit behind the rotating impeller, wholly inside
        # the tunnel. No protruding external propeller is fitted.
        for k in range(5):
            t=k*2*math.pi/5
            c,s=math.cos(t),math.sin(t)
            a=np.array((x+.18*c,y+.18*s,-177.0));b=np.array((x+1.12*c,y+1.12*s,-177.0))
            normal=np.array((-s,c,0))*.035
            vv=[p+normal*side+np.array((0,0,axial)) for p in (a,b) for side,axial in ((-1,-.15),(1,-.15),(1,.15),(-1,.15))]
            ff=[[0,3,2,1],[4,5,6,7]]+[[j,(j+1)%4,4+(j+1)%4,4+j] for j in range(4)]
            v=np.asarray(vv);v[:,0]/=width_scale
            mesh.add(f'WaterjetStator{i}_{k}',v,orient_solid(v,ff),'edge')

def _add_nozzle(mesh,name,centre,width_scale=1.,steering=False):
    from naval_hull import orient_solid
    x,y,z=centre;verts=[];n=N_CIRCLE
    # Convergent thin-walled outlet sleeve: upstream pivot to aft exit.
    for zz,rr in ((z-.12,OUTER_RADIUS),(z-1.8,1.30),(z-1.8,OUTLET_RADIUS),(z-.12,OUTLET_RADIUS)):
        verts.extend(_ring_z(x,y,zz,rr))
    faces=[]
    for k in range(4):
        for j in range(n):faces.append([k*n+j,k*n+(j+1)%n,((k+1)%4)*n+(j+1)%n,((k+1)%4)*n+j])
    v=np.asarray(verts);v[:,0]/=width_scale
    mesh.add(name,v,orient_solid(v,faces),'edge')
    if steering:
        # Raised reverse-bucket shell, open on its flow-facing underside;
        # visual parked state only, no simulated reversal actuation.
        # Compact parked bucket proxy and supporting arms; no structural
        # hinge or reversal actuator design is claimed for these solids.
        mesh.box(name+'_ReverseBucket',x/width_scale,y+1.55,z-1.,2.9/width_scale,.22,1.5,'hatch')
        for side in (-1,1):
            mesh.box(name+f'_BucketArm{side}',(x+side*1.43)/width_scale,y+1.05,z-.65,.12/width_scale,1.05,.18,'dark')

def add_steering_nozzle(mesh,name):
    """Local Y-axis steerable assembly. Position at JET_CENTRES[index]."""
    _add_nozzle(mesh,name,(0.,0.,0.),1.,steering=True)
    # Merge assembly pieces into the registered moving part so raised bucket
    # and its arms follow the same yaw transform as the nozzle.
    rows=[p for p in mesh.parts if p[0]==name or p[0].startswith(name+'_')]
    if len(rows)>1:
        vv=[];ff=[]
        for _,v,f,_ in rows:
            off=len(vv);vv.extend(v);ff.extend([[j+off for j in face] for face in f])
        mesh.parts[:]=[p for p in mesh.parts if not (p[0]==name or p[0].startswith(name+'_'))]
        mesh.add(name,vv,ff,'edge')

def add_impeller(mesh,name):
    """Local Z-axis internal rotor, eight pitched blades in a 2.35 m bore."""
    from naval_hull import orient_solid
    verts=[];faces=[]
    # Rounded low-profile hub, independent closed rotor components.
    n=24
    for z,r in ((-.38,.12),(-.20,.28),(.20,.28),(.38,.12)):
        verts.extend(_ring_z(0,0,z,r,n))
    for k in range(3):
        for j in range(n):faces.append([k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j])
    faces.extend(([j for j in range(n)][::-1],[3*n+j for j in range(n)]))
    for k in range(8):
        off=len(verts);rings=[]
        for radius,chord,sweep in ((.25,.20,0),(.7,.24,.18),(1.13,.15,.32)):
            t=k*2*math.pi/8+sweep;c,s=math.cos(t),math.sin(t)
            rings.append([(radius*c-q*s,radius*s+q*c,a+.5*q) for q,a in ((-chord,-.035),(chord,-.035),(chord,.035),(-chord,.035))])
        verts.extend(p for ring in rings for p in ring)
        faces.append([off+3,off+2,off+1,off])
        for kk in range(2):
            for j in range(4):faces.append([off+kk*4+j,off+kk*4+(j+1)%4,off+(kk+1)*4+(j+1)%4,off+(kk+1)*4+j])
        faces.append([off+8,off+9,off+10,off+11])
    mesh.add(name,verts,orient_solid(verts,faces),'dark')

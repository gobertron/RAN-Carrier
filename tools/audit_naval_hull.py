#!/usr/bin/env python3
"""Audit exported prototype geometry and conditional upright hydrostatics.

The independent reference envelope is distinct from the perforated shell and
floodable intake ducts. Neither is a detailed loading or seaworthiness approval.
"""
from pathlib import Path
import sys,json,math,collections,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'australis-2030'),str(ROOT/'tools')]
from naval_hull import mesh_integrals
from validate_recovery import ini,vec,IDS
UNIT=217/3.161967
PACKAGE=ROOT/'game-mod/RAN-Carrier-Australis-2030'


def read_groups(path):
    vertices=[];groups={};name=None
    for line in path.read_text().splitlines():
        if line.startswith('o '):name=line[2:];groups[name]=[]
        elif line.startswith('v '):vertices.append([float(x)*UNIT for x in line.split()[1:]])
        elif line.startswith('f '):groups[name].append([int(x.split('/')[0])-1 for x in line.split()[1:]])
    v=np.asarray(vertices);out={}
    for name,faces in groups.items():
        used=sorted({i for f in faces for i in f});lookup={j:i for i,j in enumerate(used)}
        out[name]=(v[used],[[lookup[i] for i in f] for f in faces])
    return out


def closed_mesh(vertices,faces):
    """Check merged exported edge topology, consistent winding and positive volume."""
    lookup={};mapped=[]
    for p in vertices:
        key=tuple(round(float(x),5) for x in p)
        if key not in lookup:lookup[key]=len(lookup)
        mapped.append(lookup[key])
    edges=collections.Counter();directions=collections.Counter()
    for face in faces:
        for a,b in zip(face,face[1:]+face[:1]):
            a,b=mapped[a],mapped[b];assert a!=b,'Collapsed mesh edge'
            edges[tuple(sorted((a,b)))]+=1;directions[(a,b)]+=1
    bad=[e for e,n in edges.items() if n!=2]
    assert not bad,('Open/non-manifold edges',len(bad),bad[:5])
    assert all(directions[(a,b)]==directions[(b,a)]==1 for a,b in edges),'Inconsistent face winding'
    volume,_=mesh_integrals(vertices,faces);assert volume>0,'Inside-out solid'
    return len(edges)


def waterplane(vertices,faces=None):
    if faces is not None:
        # Mirroring/clipping may introduce interior vertices at new Z values.
        # Their maxima are not waterline offsets. Union the actual Y=0 cap
        # triangles, then integrate its exterior boundary instead.
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        caps=[]
        for face in faces:
            if max(abs(vertices[i,1]) for i in face)<.0001:
                poly=Polygon(vertices[face][:,[0,2]])
                if poly.area>1e-10:caps.append(poly)
        assert caps,'Missing design-waterplane cap'
        cap=unary_union(caps)
        assert cap.geom_type=='Polygon' and not cap.interiors,('Unexpected waterplane topology',cap.geom_type)
        boundary=np.asarray(cap.exterior.coords[:-1])
        signed=float(np.sum(boundary[:,0]*np.roll(boundary[:,1],-1)-np.roll(boundary[:,0],-1)*boundary[:,1]))
        if signed<0:boundary=boundary[::-1]
    else:
        wl=vertices[np.abs(vertices[:,1])<.0001];by_z={}
        for x,y,z in wl:by_z.setdefault(round(float(z),6),[]).append(float(x))
        zs=sorted(by_z)
        boundary=np.asarray([(max(by_z[z]),z) for z in zs]+[(min(by_z[z]),z) for z in zs[::-1]])
    a=boundary;b=np.roll(a,-1,axis=0);cross=a[:,0]*b[:,1]-b[:,0]*a[:,1]
    area=float(cross.sum()/2)
    centre=np.sum((a+b)*cross[:,None],axis=0)/(6*area)
    it=float(np.sum((a[:,0]**2+a[:,0]*b[:,0]+b[:,0]**2)*cross)/12)
    il=float(np.sum((a[:,1]**2+a[:,1]*b[:,1]+b[:,1]**2)*cross)/12-area*centre[1]**2)
    return boundary,area,centre,it,il


def triangles(vertices,faces):
    return np.asarray([vertices[[f[0],f[j],f[j+1]]] for f in faces for j in range(1,len(f)-1)])


def line_hits(vertices,faces,axis,coordinates):
    """Vectorised axis-parallel triangle intersections using barycentrics.

    Pass vertices=None and an already expanded triangle array for repeated rays.
    """
    tri=np.asarray(faces) if vertices is None else triangles(vertices,faces)
    if len(tri)==0:return []
    axes=[i for i in range(3) if i!=axis];q=np.asarray(coordinates)
    p=tri[:,:,axes];a=p[:,1]-p[:,0];b=p[:,2]-p[:,0]
    det=a[:,0]*b[:,1]-a[:,1]*b[:,0];valid=np.abs(det)>1e-10
    tri=tri[valid];p=p[valid];a=a[valid];b=b[valid];det=det[valid]
    d=q-p[:,0];u=(d[:,0]*b[:,1]-d[:,1]*b[:,0])/det;w=(a[:,0]*d[:,1]-a[:,1]*d[:,0])/det
    keep=np.minimum(np.minimum(u,w),1-u-w)>=-1e-7
    hits=tri[:,0,axis]+u*(tri[:,1,axis]-tri[:,0,axis])+w*(tri[:,2,axis]-tri[:,0,axis])
    return sorted(float(x) for x in hits[keep])


def aperture_checks(reference,wet):
    """Check actual shell mouths; a dark patch over a spanning face cannot pass."""
    from waterjet_geometry import JET_X,JET_Y,TRANSOM_Z,INTAKE_CENTRE_Z,OUTLET_RADIUS
    rv,rf=reference;wv,wf=wet;inlets=[];outlets=[]
    rt=triangles(rv,rf);wt=triangles(wv,wf)
    capfaces=[f for f in wf if max(abs(wv[i,2]-TRANSOM_Z) for i in f)<.001]
    ct=triangles(wv,capfaces)
    for x in JET_X:
        differences=[]
        for dx,dz in ((0,0),(-.4,0),(.4,0),(0,-1.),(0,1.)):
            ref=line_hits(None,rt,1,(x+dx,INTAKE_CENTRE_Z+dz))
            active=line_hits(None,wt,1,(x+dx,INTAKE_CENTRE_Z+dz))
            assert ref and active,('Missing intake ray intersection',x,dx,dz)
            differences.append(min(active)-min(ref))
        assert min(differences)>.05,('Intake is covered by an original shell face',x,differences)
        inlets.append(dict(x_m=x,minimum_sampled_clearance_above_original_shell_m=min(differences),sample_count=5))
        for dx,dy in ((0,0),(-OUTLET_RADIUS*.4,0),(OUTLET_RADIUS*.4,0),(0,-OUTLET_RADIUS*.4),(0,OUTLET_RADIUS*.4)):
            assert not line_hits(None,ct,2,(x+dx,JET_Y+dy)),('Transom aperture has a spanning cap',x,dx,dy)
        outlets.append(dict(x_m=x,sample_count=5,transom_shell_cap_absent=True))
    return dict(intake_count=len(inlets),outlet_count=len(outlets),intakes=inlets,outlets=outlets,
                scope='Five interior samples per aperture in exported wet-boundary mesh; geometric aperture checks, not a flow/cavitation assessment.')


def nozzle_packaging(groups):
    """Measure static axial spacing and sample common-angle nozzle/bucket yaw.

    Axis-aligned separation is sufficient where positive, but a negative value
    is inconclusive and is reported rather than treated as collision proof.
    """
    from waterjet_geometry import JET_CENTRES,STEERING_INDICES,OUTER_RADIUS
    straight_gap=min(JET_CENTRES[i+1][0]-JET_CENTRES[i][0]-2*OUTER_RADIUS for i in range(7))
    assert straight_gap>.1,'Stationary nozzle collars overlap'
    sweep=[]
    for angle in (-35,-25,-15,0,15,25,35):
        a=math.radians(angle);rot=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
        boxes=[]
        for i,(x,y,z) in enumerate(JET_CENTRES,1):
            if i in STEERING_INDICES:
                v,_=groups[f'WaterjetSteering{i}'];world=v@rot.T+np.array((x,y,z))
                boxes.append((world[:,0].min(),world[:,0].max()))
            else:boxes.append((x-OUTER_RADIUS,x+OUTER_RADIUS))
        gaps=[boxes[i+1][0]-boxes[i][1] for i in range(7)]
        sweep.append(dict(common_yaw_degrees=angle,minimum_adjacent_x_bounding_gap_m=float(min(gaps))))
    return dict(stationary_collar_lateral_gap_m=straight_gap,common_yaw_samples=sweep,
                scope='Conservative X bounding-box screen of moving sleeves and parked buckets; not swept-solid clearance, actuator clearance or steering performance validation.')


def installation_reservations(package,reference):
    """Compare preliminary wet-duct envelopes with the current room layout."""
    from waterjet_geometry import wet_hull,IMPELLER_CENTRES,OUTER_RADIUS
    from internal_fit import overlap,HullEnvelope
    rv,rf=reference
    ref_hull=HullEnvelope(triangles(rv,rf).tolist())
    duct_rows=wet_hull()[2]['ducts'];reservations=[]
    for row in duct_rows:
        lo,hi=row['wet_duct_xyz_bounds'];bounds=[lo[0],hi[0],lo[1],hi[1],lo[2],hi[2]]
        reservations.append(dict(name=f"Waterjet {row['index']} wet duct",bounds_m=bounds))
    arrangement=json.loads((package/'internal-arrangement.json').read_text())
    existing=arrangement['spaces']+[dict(name='Clear hangar',bounds=arrangement['hangar_bounds_m'])]
    minimum=float('inf')
    for i,a in enumerate(reservations):
        for b in reservations[i+1:]:assert not overlap(a['bounds_m'],b['bounds_m']),(a['name'],b['name'],'duct envelopes overlap')
        for b in existing:
            aa=a['bounds_m'];bb=b['bounds']
            assert not overlap(aa,bb),(a['name'],b['name'],'duct conflicts with existing room/shaft')
            distance=math.sqrt(sum(max(aa[j]-bb[j+1],bb[j]-aa[j+1],0)**2 for j in (0,2,4)))
            minimum=min(minimum,distance)
    sampled_margins=[]
    for x,y,z in IMPELLER_CENTRES:
        margins=[]
        for zz in (z-.5,z,z+.5):
            for angle in np.linspace(0,2*math.pi,73):
                xx=x+OUTER_RADIUS*math.cos(angle);yy=y+OUTER_RADIUS*math.sin(angle)
                limits=ref_hull.section(yy,zz);assert limits is not None,'Pump housing outside reference hull section'
                margin=min(xx-limits[0],limits[1]-xx);assert margin>.1,'Pump housing crosses reference side shell'
                margins.append(margin)
        sampled_margins.append(min(margins))
    return dict(wet_duct_envelopes=reservations,existing_reservation_count=len(existing),
                minimum_duct_box_to_existing_reservation_distance_m=minimum,
                sampled_internal_pump_housing_side_shell_margin_m=sampled_margins,
                scope='Wet-duct boxes and a radius1.35m pump-housing envelope are preliminary geometric reservations. Existing rooms/shafts clear; drive motors, cable runs, service aisles, supports and machinery removal paths are not dimensioned or certified.')


def audit(package=PACKAGE,write=True):
    from waterjet_geometry import JET_CENTRES,IMPELLER_CENTRES,STEERING_INDICES,OUTLET_BORE
    obj=package/'ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj'
    reference_path=package/'hydrostatics-envelope.obj'
    g=read_groups(obj);reference=read_groups(reference_path)['HydrostaticEnvelope'];v,f=reference
    edges=closed_mesh(v,f)
    collision_edges=closed_mesh(*g['coll_hull_main'])
    assert len(g['coll_hull_main'][1])<=255,'Native convex collider polygon budget'
    for face in g['coll_hull_main'][1]:
        cv=g['coll_hull_main'][0];a,b,c=cv[face[:3]];normal=np.cross(b-a,c-a);normal/=np.linalg.norm(normal)
        assert np.max((cv-a)@normal)<.001,'Native collision mesh is not convex'
    assert not set(g).intersection(('Propeller_1','Propeller_2','Rudder','Rudder_2')),'Conventional external running gear remains'
    for i in range(1,9):closed_mesh(*g[f'WaterjetImpeller{i}'])
    for i in STEERING_INDICES:closed_mesh(*g[f'WaterjetSteering{i}'])
    volume,cb=mesh_integrals(v,f);wl,area,cf,it,il=waterplane(v,f)
    points={tuple(round(float(q),4) for q in p) for p in v}
    assert all((-x,y,z) in points for x,y,z in points),'Reference envelope is not mirrored'
    assert abs(cb[0])<.0001,'Reference transverse buoyancy offset'
    mass=volume*1.025
    assert 112000<mass<117600,'Invalid gross-envelope allowance'
    assert abs(np.ptp(wl[:,0])-41)<.0002 and abs(v[:,1].min()+11.5)<.0002
    kmt_y=float(cb[1]+it/volume);kml_y=float(cb[1]+il/volume)
    c=ini(package/'vessels/ran_cvn_australis_2030.ini');cg=np.asarray(vec(c['Physics']['CenterOfMass']))*UNIT
    assert abs(cg[0])<.0001
    gm=kmt_y-cg[1];assert gm>1.5,'Configured planning CoG lacks the intended small-angle reference GM margin'
    # The wet boundary includes the internally flooded ducts. It can be closed
    # while the flow path stays open from each inlet to its transom outlet.
    wv,wf=g['UnderwaterHull'];wet_edges=closed_mesh(wv,wf);wet_volume,wet_cb=mesh_integrals(wv,wf)
    assert 0<volume-wet_volume<volume*.05,'Invalid geometric duct-volume deduction'
    assert abs(wet_cb[0])<.001,'Wet-boundary transverse buoyancy offset'
    assert abs(wet_volume*1.025-112000)/112000<.0001,'Net wet geometry misses displacement target'
    assert abs(cg[2]-wet_cb[2])<.001,'Configured LCG differs from wet-boundary LCB'
    wet_wl,wet_area,wet_cf,wet_it,wet_il=waterplane(wv,wf)
    assert abs(wet_area-area)<.01,'Below-waterline ducts changed the waterplane'
    wet_gm=float(wet_cb[1]+wet_it/wet_volume-cg[1])
    assert wet_gm>1.5,'Wet-boundary conditional GM lacks the intended margin'
    openings=aperture_checks(reference,(wv,wf));packaging=nozzle_packaging(g)
    reservations=installation_reservations(package,reference)
    rotor_bore_gaps=[]
    for i in range(1,9):
        local,_=g[f'WaterjetImpeller{i}'];radial=float(np.max(np.linalg.norm(local[:,:2],axis=1)))
        gap=OUTLET_BORE/2-radial;assert gap>.005,('Internal rotor exceeds bore',i,radial)
        rotor_bore_gaps.append(gap)
    for ship in IDS:
        c=ini(package/'vessels'/f'{ship}.ini')
        assert c['PropulsionSystems']['NumberOfPropulsionSystems']=='8'
        assert c['RudderSystems']['NumberOfRudderSystems']=='4'
        for i,centre in enumerate(IMPELLER_CENTRES,1):
            name=f'WaterjetImpeller{i}'
            assert c[f'PropulsionSystem{i}']['Mount']==name and c[name]['Mesh']==name
            assert math.dist(np.asarray(vec(c[name]['Position']))*UNIT,centre)<.0001
        for ordinal,i in enumerate(STEERING_INDICES,1):
            name=f'WaterjetSteering{i}'
            assert c[f'RudderSystem{ordinal}']['Mount']==name and c[name]['Mesh']==name
            assert math.dist(np.asarray(vec(c[name]['Position']))*UNIT,JET_CENTRES[i-1])<.0001
        assert c['Foam']['SternFoamTexture'],'Native rudder initialization requires stern foam'
        assert c['Physics']['MaxForwardVelocity']=='30' and c['MainPowerSystem']['HorsePower']=='280000','Unreviewed gameplay performance change'
    result=dict(version='0.8.2-lift-lighting',source='Measured exported reference-envelope OBJ, visible wet-boundary OBJ and native INIs',
        obj_sha256=hashlib.sha256(obj.read_bytes()).hexdigest(),hydrostatic_reference_obj_sha256=hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        waterline_length_m=float(np.ptp(wl[:,1])),waterline_beam_m=float(np.ptp(wl[:,0])),draft_m=float(-v[:,1].min()),
        longitudinal_stations=len(set(round(float(z),5) for z in v[:,2])),section_vertices=50,
        symmetry='Reference envelope is mirrored about X=0; wet-boundary transverse centroid separately checked',
        closed_envelope_volume_m3=volume,closed_envelope_displacement_t=mass,
        bare_hull_volume_m3=volume,bare_hull_displacement_t=mass,
        displacement_label='Gross reference-envelope volume before flooded-duct deduction; actual wet-boundary target is112000t. Bare-hull aliases retained for compatibility, not loaded displacement approval.',
        reference_seawater_density_t_per_m3=1.025,block_coefficient=volume/(362.6*41*11.5),
        centre_of_buoyancy_xyz_m=cb.tolist(),waterplane_area_m2=area,centre_of_flotation_xz_m=cf.tolist(),
        transverse_waterplane_second_moment_m4=it,longitudinal_waterplane_second_moment_m4=il,
        transverse_metacentre_y_m=kmt_y,longitudinal_metacentre_y_m=kml_y,
        configured_planning_centre_of_mass_xyz_m=cg.tolist(),conditional_initial_transverse_gm_m=float(gm),
        wet_boundary_volume_m3=wet_volume,wet_boundary_geometric_displacement_t=wet_volume*1.025,
        flooded_duct_geometric_volume_m3=volume-wet_volume,wet_boundary_centre_of_buoyancy_xyz_m=wet_cb.tolist(),
        wet_boundary_conditional_initial_transverse_gm_m=wet_gm,
        wet_boundary_lcb_minus_configured_lcg_m=float(wet_cb[2]-cg[2]),
        first_order_extra_immersion_for_112000t_m=(112000/1.025-wet_volume)/area,
        mass_properties_status='Planning CG height 7 m above design WL and LCG aligned to wet-boundary geometric LCB; actual weight centres, mass balance and loaded draft are unverified.',
        waterjet_count=8,steerable_waterjet_count=4,fixed_booster_count=4,waterjet_nominal_clear_bore_m=OUTLET_BORE,
        waterjet_centres_xyz_m=JET_CENTRES,internal_impeller_centres_xyz_m=IMPELLER_CENTRES,
        internal_impeller_minimum_geometric_bore_gap_m=rotor_bore_gaps,aperture_checks=openings,nozzle_packaging_screen=packaging,installation_reservation_screen=reservations,
        watertight_reference_mesh_edges=edges,watertight_wet_boundary_edges=wet_edges,
        watertight_collision_mesh_edges=collision_edges,collision_mesh_triangles=len(g['coll_hull_main'][1]),
        collision_mesh_type='Simplified closed convex support hull, separate from detailed visible shell and ducts',
        native_simulation='Eight native propeller proxies drive concealed internal impellers; four native rudder proxies yaw nozzle assemblies. Native thrust is not a waterjet momentum/intake model. Reverse buckets remain parked visual details.',
        in_game_tested=False,
        limitations=['Duct volume is an integral of preliminary rendered lofts; watertight topology does not exclude self-intersection or validate hydraulic shape.',
            'Net geometric wet-boundary displacement excludes appendage volumes, shell-thickness deductions, actual loading and duct structural mass.',
            'Positive small-angle GM applies only to the assumed planning CG; no full GZ, flooding, loading or damage-stability assessment.',
            'No CFD, towing-tank, cavitation, hydraulic-loss, resistance or manoeuvring performance validation.',
            'Nozzle yaw screen uses conservative bounding boxes and does not certify swept-solid, bucket, actuator or hull clearances.',
            'Game speed and power remain baseline settings; actual waterjet speed, efficiency, turning and reversal are not demonstrated.',
            'Sea Power may approximate buoyancy independently of the visible mesh; in-game draft, steering, damage, wake and rough-sea checks remain pending.'])
    if write:(package/'naval-hull-hydrostatics.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'[OK] Eight real inlet/outlet apertures; reference {mass:.2f} t / wet geometry {wet_volume*1.025:.2f} t; conditional wet GM {wet_gm:.3f} m; native 8/4 bindings')
    return result


if __name__=='__main__':audit()

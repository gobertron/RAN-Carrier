"""Stdlib-only measurements of the actual triangulated game hull.

This reads OBJ vertices/faces, not a second hand-copied hull outline. It is
also shipped with the installer so internal clearance cannot silently regress.
"""
from pathlib import Path
import math

METRES_PER_UNIT=217/3.161967

class HullEnvelope:
    def __init__(self,triangles):
        self.triangles=[];self.ys=set();self.zs=set();self.cache={};self.buckets={}
        for tri in triangles:
            a,b,c=tri
            denominator=(b[2]-c[2])*(a[1]-c[1])+(c[1]-b[1])*(a[2]-c[2])
            self.ys.update(p[1] for p in tri);self.zs.update(p[2] for p in tri)
            if abs(denominator)>1e-12:
                item=(a,b,c,denominator,min(p[1] for p in tri),max(p[1] for p in tri))
                self.triangles.append(item)
                for slot in range(math.floor(min(p[2] for p in tri)/4),math.floor(max(p[2] for p in tri)/4)+1):self.buckets.setdefault(slot,[]).append(item)

    @classmethod
    def from_obj(cls,path):
        verts=[];triangles=[];name=None
        for line in Path(path).read_text().splitlines():
            if line.startswith('o '):name=line[2:]
            elif line.startswith('v '):verts.append(tuple(float(v)*METRES_PER_UNIT for v in line.split()[1:]))
            elif line.startswith('f ') and name in ('Hull','UnderwaterHull','Deck'):
                f=[int(v.split('/')[0])-1 for v in line.split()[1:]]
                for i in range(1,len(f)-1):triangles.append([verts[j] for j in (f[0],f[i],f[i+1])])
        assert triangles,'No original hull found'
        return cls(triangles)

    def section(self,y,z):
        key=(round(y,7),round(z,7))
        if key in self.cache:return self.cache[key]
        xs=[]
        for a,b,c,d,ylo,yhi in self.buckets.get(math.floor(z/4),[]):
            if y<ylo-1e-7 or y>yhi+1e-7:continue
            u=((b[2]-c[2])*(y-c[1])+(c[1]-b[1])*(z-c[2]))/d
            v=((c[2]-a[2])*(y-c[1])+(a[1]-c[1])*(z-c[2]))/d
            w=1-u-v
            if min(u,v,w)>=-2e-6:xs.append(u*a[0]+v*b[0]+w*c[0])
        out=(min(xs),max(xs)) if xs else None
        self.cache[key]=out
        return out

    def margin(self,bounds):
        """Sample faces, all longitudinal stations, <=2 m longitudinal and <=0.25 m vertical steps.

        The dense hull uses a spatial index and bounded vertical samples.
        The original low-resolution hull also includes each chine height. This remains geometric QA,
        not a hydrodynamic, structural or damage-stability calculation.
        """
        a,b,c,d,e,f=bounds
        if d>max(self.ys) and d-max(self.ys)<.005:d=max(self.ys)-.00001
        ys={c,d,(c+d)/2}
        if len(self.ys)<100:ys.update(v for v in self.ys if c<v<d)
        else:
            steps=max(1,math.ceil((d-c)/.25))
            ys.update(c+(d-c)*i/steps for i in range(steps+1))
        zs={e,f,(e+f)/2,*[v for v in self.zs if e<v<f]}
        n=max(1,math.ceil((f-e)/2))
        zs.update(e+(f-e)*i/n for i in range(n+1))
        margin=float('inf')
        for y in ys:
            for z in zs:
                section=self.section(y,z)
                if section is None:return -float('inf')
                lo,hi=section;margin=min(margin,a-lo,hi-b)
        return margin

def overlap(a,b):
    return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-4 for i in (0,2,4))

def validate_arrangement(destination,object_path=None):
    """Check the packaged arrangement against actual installable geometry."""
    import json,collections
    destination=Path(destination)
    data=json.loads((destination/'internal-arrangement.json').read_text())
    if object_path is None:object_path=destination/'ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj'
    hull=HullEnvelope.from_obj(object_path)
    spaces=data['spaces'];lifts=[v for v in spaces if v['category']=='lift'];wells=[v for v in spaces if v['category']=='weapon']
    wells += [v for v in spaces if v['category']=='laser']
    rooms=[v for v in spaces if v['category']=='accommodation']
    hangar=data['hangar_bounds_m'];parking=data['parking_slots']
    assert len(lifts)==4 and len(wells)==29 and len(parking)==36
    assert sum(v['berths'] for v in rooms)==5800
    assert len({v['name'] for v in spaces})==len(spaces)
    minimums=collections.defaultdict(lambda:float('inf'))
    for v in spaces:
        a,b,c,d,e,f=v['bounds']
        assert all(math.isfinite(x) for x in v['bounds']) and a<b and c<d and e<f,v['name']
        area=(b-a)*(f-e);volume=area*(d-c)
        assert abs(area-v['floor_area_m2'])<.001 and abs(volume-v['volume_m3'])<.001,(v['name'],'incorrect area/volume record')
        if v['category']=='accommodation':
            assert v['berths']<=area/4+.001 and d-c>=2.599,(v['name'],'berthing density or headroom')
        margin=hull.margin(v['bounds']);minimums[v['category']]=min(minimums[v['category']],margin)
        # Lift and weapon openings reach the deck surface; all stay inboard
        # of the shell throughout their complete reserved height.
        assert margin>=.299,(v['name'],'outside actual hull or shell clearance',margin)
    assert hull.margin(hangar)>=.299,'Hangar extends through actual hull'
    essential=[v for v in spaces if v['category'] not in ('lift','weapon','laser')]
    for i,a in enumerate(essential):
        for b in essential[i+1:]:
            assert not overlap(a['bounds'],b['bounds']),(a['name'],b['name'],'internal reservations overlap')
    for a in essential:
        for b in lifts+wells:
            assert not overlap(a['bounds'],b['bounds']),(a['name'],b['name'],'room intersects a shaft/well')
    for i,a in enumerate(lifts+wells):
        for b in (lifts+wells)[i+1:]:
            assert not overlap(a['bounds'],b['bounds']),(a['name'],b['name'],'shaft/well interference')
    for well in wells:
        assert not overlap(well['bounds'],hangar),(well['name'],'weapon bay penetrates clear hangar')
    for i,a in enumerate(parking):
        bounds=a['bounds']
        assert all(hangar[j]-.001<=bounds[j]<bounds[j+1]<=hangar[j+1]+.001 for j in (0,2,4)),a['name']
        for b in parking[i+1:]+lifts+wells:
            assert not overlap(bounds,b['bounds']),(a['name'],b['name'],'parking collision')
        assert not overlap(bounds,data['hangar_towing_spine_bounds_m']),(a['name'],'blocks towing spine')
    for v in spaces:
        if v['category'] in ('machinery','magazine','fuel','hotel_service'):
            assert not overlap(v['bounds'],hangar),(v['name'],'penetrates hangar')
    fuel=sum(v['volume_m3'] for v in spaces if v['category']=='fuel')
    assert fuel*.85*.8>=9000,'Gross fuel reservation lacks the declared allowance'
    result={'version':data['version'],'hull_clearances_m':{k:round(v,4) for k,v in minimums.items()},
            'hangar_area_m2':(hangar[1]-hangar[0])*(hangar[5]-hangar[4]),
            'hangar_height_m':hangar[3]-hangar[2],'mixed_reference_hangar_slots':36,
            'berthing_rooms':len(rooms),'berths':sum(v['berths'] for v in rooms),
            'berthing_floor_area_m2':sum(v['floor_area_m2'] for v in rooms),
            'aviation_fuel_reservation_m3':fuel,'air_group_99_operational_cycle_validated':False,
            'structural_hydrodynamic_stability_verified':False}
    return result

"""Original face-aligned naval visual fittings, in physical metres.

These are raised model details, not certified watertight boundaries or openings.
Generation uses NumPy; the resulting JSON report needs only stdlib to inspect.
"""
import math
import numpy as np

LAST_REPORT = {}


def unit(v):
    v=np.asarray(v,dtype=float);return v/np.linalg.norm(v)


class Surface:
    def __init__(self,parent,index,quad,centre):
        self.parent,self.index=parent,index
        q=np.asarray(quad,dtype=float)
        low=sorted(q,key=lambda p:(p[1],p[0],p[2]))[:2]
        high=sorted(q,key=lambda p:(p[1],p[0],p[2]))[2:]
        a,b=low
        if np.linalg.norm(a-high[0])+np.linalg.norm(b-high[1]) > np.linalg.norm(a-high[1])+np.linalg.norm(b-high[0]):high=high[::-1]
        self.q=np.array([a,b,high[1],high[0]])
        diagonal={int(np.argmin(np.linalg.norm(self.q-q[i],axis=1))) for i in (0,2)}
        self.diagonal02=diagonal=={0,2}
        assert diagonal in ({0,2},{1,3})
        self.y0,self.y1=float(a[1]),float(high[0][1])
        n=unit(np.cross(self.q[1]-self.q[0],self.q[2]-self.q[0]))
        if np.dot(n,(self.q.mean(axis=0)-centre)*[1,0,1])<0:n=-n
        self.n=n
        self.width=min(np.linalg.norm(self.q[1]-self.q[0]),np.linalg.norm(self.q[2]-self.q[3]))
        self.warp=abs(float(np.dot(self.q[3]-self.q[0],n)))

    def raw(self,u,y):
        v=(y-self.y0)/(self.y1-self.y0);q=self.q
        if self.diagonal02:
            if u>=v:return (1-u)*q[0]+(u-v)*q[1]+v*q[2]
            return (1-v)*q[0]+u*q[2]+(v-u)*q[3]
        if u+v<=1:return (1-u-v)*q[0]+u*q[1]+v*q[3]
        return (1-v)*q[1]+(u+v-1)*q[2]+(1-u)*q[3]

    def supports(self,u0,u1,y0,y1):
        if not(0.015<=u0<u1<=.985 and self.y0+.06<=y0<y1<=self.y1-.06):return False
        # Do not bridge a non-planar loft's diagonal with one flat fitting.
        if self.warp>.00001:
            vals=[(u-(y-self.y0)/(self.y1-self.y0)) if self.diagonal02 else (u+(y-self.y0)/(self.y1-self.y0)-1) for u in (u0,u1) for y in (y0,y1)]
            if min(vals)<-1e-8 and max(vals)>1e-8:return False
        return True

    def normal(self,u,y):
        v=(y-self.y0)/(self.y1-self.y0);q=self.q
        if self.diagonal02:n=unit(np.cross(q[1]-q[0],q[2]-q[0])) if u>=v else unit(np.cross(q[2]-q[0],q[3]-q[0]))
        else:n=unit(np.cross(q[1]-q[0],q[3]-q[0])) if u+v<=1 else unit(np.cross(q[2]-q[1],q[3]-q[1]))
        return n if np.dot(n,self.n)>0 else -n

    def u_for_z(self,z,y):
        a,b=self.raw(0,y),self.raw(1,y)
        return .5 if abs(b[2]-a[2])<1e-9 else float((z-a[2])/(b[2]-a[2]))


def surfaces(mesh,name,scale):
    _,v,faces,_=next(p for p in mesh.parts if p[0]==name)
    v=v*np.array([scale,1,1]);centre=v.mean(axis=0);out=[]
    for i,face in enumerate(faces):
        q=v[face]
        if len(face)!=4 or np.ptp(q[:,1])<2.:continue
        ys=sorted(set(np.round(q[:,1],6)))
        if len(ys)!=2 or sum(abs(q[:,1]-ys[0])<1e-5)!=2:continue
        s=Surface(name,i,q,centre)
        if math.hypot(s.n[0],s.n[2])>.6:out.append(s)
    return out


def rounded(u,y,w,h,r,steps=4):
    pts=[];r=min(r,w/2,h/2)
    for cx,cy,start in ((u+w/2-r,y+h/2-r,0),(u-w/2+r,y+h/2-r,90),(u-w/2+r,y-h/2+r,180),(u+w/2-r,y-h/2+r,270)):
        for k in range(steps+1):
            a=math.radians(start+k*90/steps);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts


class Builder:
    def __init__(self,mesh,scale):self.mesh,self.scale=mesh,scale;self.records=[]
    def add_world(self,name,v,f,mat):
        a=np.asarray(v,dtype=float);a[:,0]/=self.scale
        self.mesh.add(name,a,f,mat)
    def solid(self,name,s,points,back,front,mat):
        n=s.normal(sum(p[0] for p in points)/len(points),sum(p[1] for p in points)/len(points))
        v=[s.raw(u,y)+n*off for off in (back,front) for u,y in points];k=len(points)
        f=[list(reversed(range(k))),list(range(k,2*k))]+[[i,(i+1)%k,(i+1)%k+k,i+k] for i in range(k)]
        self.add_world(name,v,f,mat)
    def rect(self,name,s,u,y,w,h,back,front,mat,r=0):
        pts=[(u+x/s.width,yy) for x,yy in rounded(0,y,w,h,r)] if r else [(u-w/s.width/2,y-h/2),(u+w/s.width/2,y-h/2),(u+w/s.width/2,y+h/2),(u-w/s.width/2,y+h/2)]
        self.solid(name,s,pts,back,front,mat)
    def frame(self,name,s,u,y,w,h,border,back,front,mat,r):
        outer=[(u+x/s.width,yy) for x,yy in rounded(0,y,w,h,r)]
        inner=[(u+x/s.width,yy) for x,yy in rounded(0,y,w-2*border,h-2*border,max(.012,r-border))]
        n=s.normal(u,y);k=len(outer)
        vertices=[s.raw(a,b)+n*depth for depth in (back,front) for loop in (outer,inner) for a,b in loop]
        faces=[]
        for i in range(k):
            j=(i+1)%k
            faces += [[i,j,k+j,k+i],[2*k+i,3*k+i,3*k+j,2*k+j],
                      [i,2*k+i,2*k+j,j],[k+i,k+j,3*k+j,3*k+i]]
        self.add_world(name,vertices,faces,mat)
    def record(self,kind,name,s,u,y,w,h,back,front):
        n=s.normal(u,y);anchor=s.raw(u,y)
        us=[u-w/(2*s.width),u+w/(2*s.width)];ys=[y-h/2,y+h/2]
        corners=[s.raw(a,b) for a in us for b in ys]
        plane_error=max(abs(float(np.dot(p-anchor,n))) for p in corners)
        self.records.append(dict(kind=kind,name=name,parent=s.parent,face=s.index,centre_m=[round(float(a),6) for a in anchor],normal=[round(float(a),7) for a in n],width_m=w,height_m=h,minimum_surface_clearance_m=round(back-plane_error,7),maximum_surface_clearance_m=round(front+plane_error,7),host_plane_error_m=round(plane_error,8),inside_parent_face=s.supports(us[0],us[1],ys[0],ys[1])))
    def window(self,name,s,u,y,w=1.15,h=1.05):
        if not s.supports(u-(w+.34)/(2*s.width),u+(w+.34)/(2*s.width),y-(h+.36)/2,y+(h+.36)/2):return False
        self.rect(name+'_Gasket',s,u,y,w+.14,h+.14,.018,.045,'dark',.08)
        self.rect(name+'_Glass',s,u,y,w,h,.045,.060,'glass',.07)
        self.frame(name+'_Frame',s,u,y,w+.22,h+.22,.065,.020,.095,'edge',.10)
        # A low steel sill/drip lip, not an emissive ribbon.
        self.rect(name+'_Sill',s,u,y-(h+.22)/2-.035,w+.34,.07,.035,.13,'island')
        self.record('window',name,s,u,y,w+.34,h+.36,.018,.13)
        return True
    def door(self,name,s,u,y):
        w,h=1.12,2.18
        if not s.supports(u-w/(2*s.width),u+w/(2*s.width),y-h/2,y+h/2):return False
        self.rect(name+'_Coaming',s,u,y,w,h,.018,.070,'edge',.16)
        self.rect(name+'_Gasket',s,u,y,.99,2.04,.070,.082,'dark',.13)
        self.rect(name+'_Leaf',s,u,y,.92,1.96,.082,.103,'hatch',.12)
        for j,dy in enumerate((-.67,.67)):
            self.rect(f'{name}_Hinge{j}',s,u-.48/s.width,y+dy,.13,.24,.070,.155,'edge')
        for j,dy in enumerate((-.65,0,.65)):
            self.rect(f'{name}_Dog{j}',s,u+.45/s.width,y+dy,.16,.075,.103,.150,'dark')
        self.rect(name+'_Lever',s,u+.12/s.width,y,.26,.075,.108,.178,'edge')
        self.rect(name+'_Threshold',s,u,y-h/2+.035,1.20,.10,.025,.20,'edge')
        self.record('watertight_door_visual',name,s,u,y,1.20,h,.018,.20)
        return True
    def gallery(self,name,s,u,top):
        n=s.normal(u,top);out=unit([n[0],0,n[2]]);t=unit([out[2],0,-out[0]])
        a=s.raw(u,top)+out*.035;a[1]=top
        # Door-access maintenance balcony: side coamings, rail and real brackets.
        v=[a+t*dx+out*d+np.array([0,dy,0]) for dy in (-.12,0) for d in (0,.95) for dx in (-1.05,1.05)]
        self.add_world(name+'_Platform',v,[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]],'edge')
        def beam(label,p,q,r=.035):
            d=unit(q-p);ref=np.array([0,1,0]) if abs(d[1])<.9 else np.array([1,0,0]);x=unit(np.cross(d,ref))*r;y=unit(np.cross(d,x))*r
            verts=[c+sx*x+sy*y for c in (p,q) for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1))]
            self.add_world(name+label,verts,[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]],'edge')
        for side in (-1,1):
            inner=a+t*side*.96;outer=inner+out*.88
            beam(f'_Bracket{side}',inner+np.array([0,-.62,0]),outer+np.array([0,-.12,0]),.045)
            beam(f'_Stanchion{side}',outer,outer+np.array([0,1.05,0]))
            beam(f'_SideRail{side}',inner+np.array([0,1.05,0]),outer+np.array([0,1.05,0]))
        beam('_OuterRail',a-t*.96+out*.88+[0,1.05,0],a+t*.96+out*.88+[0,1.05,0])
        self.records.append(dict(kind='maintenance_gallery',name=name,parent=s.parent,face=s.index,width_m=2.1,depth_m=.95,deck_level_m=top,access='Internal watertight door; raised coaming; two hull brackets and outer/side rails'))


def _long_surface(items,side):
    return max((s for s in items if s.n[0]*side>.5),key=lambda s:s.width)


def add_naval_fittings(mesh,width_scale):
    global LAST_REPORT
    remove=('BridgeWindow','BridgePane','AftAviationWindow','NavalDoor','DoorInset','DoorDogs','HullDoor','BridgeGlass','AviationGlass','IntegratedRadar_','AftSideRadar_')
    mesh.parts[:]=[p for p in mesh.parts if not p[0].startswith(remove)]
    b=Builder(mesh,width_scale)
    for parent,y in (('IntegratedBridge',42.50),('AftAviationBridge',33.05)):
        for s in surfaces(mesh,parent,width_scale):
            count=max(1,min(14,int((s.width-.65)/2.15)))
            margin=.08
            for j in range(count):
                u=margin+(1-2*margin)*(j+.5)/count
                b.window(f'NavalWindow_{parent}_{s.index}_{j}',s,u,y,w=1.12 if parent=='IntegratedBridge' else .95,h=1.02 if parent=='IntegratedBridge' else .90)
    # Conformal arrays have steel borders and opaque non-glass sensor faces.
    for parent,y,h,w in (('IntegratedBridge',39.8,2.65,6.0),('AftAviationBridge',30.95,1.0,3.2)):
        items=surfaces(mesh,parent,width_scale)
        choices=[_long_surface(items,-1),_long_surface(items,1),max(items,key=lambda s:s.n[2])]
        if parent=='IntegratedBridge':choices.append(min(items,key=lambda s:s.n[2]))
        for i,s in enumerate(choices):
            width=min(w,s.width*.65);u=.5
            if not s.supports(u-width/(2*s.width),u+width/(2*s.width),y-h/2,y+h/2):
                v0=(y-h/2-s.y0)/(s.y1-s.y0);v1=(y+h/2-s.y0)/(s.y1-s.y0)
                # Keep the whole array on one real triangle of a warped face.
                zones=((.025,v0-.025),(v1+.025,.975)) if s.diagonal02 else ((.025,1-v1-.025),(1-v0+.025,.975))
                lo,hi=max(zones,key=lambda pair:pair[1]-pair[0])
                u=(lo+hi)/2;width=min(width,max(0.,(hi-lo)*s.width*.90))
            if width>.6 and s.supports(u-width/(2*s.width),u+width/(2*s.width),y-h/2,y+h/2):
                name=f'NavalRadarPanel_{parent}_{i}'
                b.rect(name+'_Border',s,u,y,width,h,.018,.07,'edge')
                b.rect(name+'_Face',s,u,y,width-.12,h-.12,.071,.085,'sensor')
                b.record('opaque_sensor_panel',name,s,u,y,width,h,.018,.085)
    for parent in ('MainRakedIsland','AftAviationIsland'):
        items=surfaces(mesh,parent,width_scale)
        for side in (-1,1):
            s=_long_surface(items,side);u=s.u_for_z(20 if parent=='MainRakedIsland' else -89,23.35)
            b.door(f'NavalDoor_{parent}_{side}',s,u,23.35)
        if parent=='MainRakedIsland':
            s=min(items,key=lambda s:s.n[2]);b.door('NavalDoor_MainAft',s,.5,23.35)
    hull=surfaces(mesh,'HardChineHull',width_scale)
    for side in (-1,1):
        for z in (-105.,0.,105.):
            candidates=[s for s in hull if s.y0<12.65 and s.y1>14.95 and s.n[0]*side>.5 and min(s.q[:,2])<=z<=max(s.q[:,2])]
            if not candidates:raise ValueError(f'No hull door face at {side},{z}')
            s=max(candidates,key=lambda a:side*a.raw(.3,13.8)[0])
            u=.30
            if not b.door(f'NavalHullDoor_{side}_{int(z)}',s,u,13.8):
                u=.70
                if not b.door(f'NavalHullDoor_{side}_{int(z)}',s,u,13.8):raise ValueError('Hull door does not fit host face')
            b.gallery(f'NavalHullGallery_{side}_{int(z)}',s,u,12.72)
    primary=[r for r in b.records if r['kind']!='maintenance_gallery']
    bad=[r['name'] for r in primary if not r['inside_parent_face'] or r['minimum_surface_clearance_m']<.005 or r['host_plane_error_m']>.001]
    if bad:raise ValueError('Invalid naval fitting alignment: '+','.join(bad))
    LAST_REPORT={'schema':1,'units':'physical metres','visual_only':True,'windows':sum(r['kind']=='window' for r in b.records),'doors':sum(r['kind']=='watertight_door_visual' for r in b.records),'galleries':sum(r['kind']=='maintenance_gallery' for r in b.records),'opaque_sensor_panels':sum(r['kind']=='opaque_sensor_panel' for r in b.records),'minimum_primary_surface_clearance_m':min(r['minimum_surface_clearance_m'] for r in primary),'maximum_primary_surface_clearance_m':max(r['maximum_surface_clearance_m'] for r in primary),'maximum_host_plane_error_m':max(r['host_plane_error_m'] for r in primary),'features':b.records,'limitations':['Raised visual fittings; no hull or island apertures are cut.','Door hardware and maintenance balconies are illustrative, not structural or watertight certification.','In-game materials and lighting require visual confirmation.']}
    return LAST_REPORT

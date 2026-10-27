from pathlib import Path
import sys,math,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,PngImagePlugin
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT
sys.path[:0]=[str(SOURCE/'tools'),str(SOURCE/'australis-2030'),str(SOURCE)]
from build_current_game_preview import load_current_mesh
from build import COLORS
from lift_lighting import profiles
from render_current_views import _basis
mesh,obj,ini=load_current_mesh();CX,CZ=27.5,82.
BOUNDS=((0,CX-11.5,True),(0,CX+11.5,False),(1,11.4,True),(1,22.2,False),(2,CZ-13.5,True),(2,CZ+13.5,False))
lamps=profiles([(CX,CZ)])[0]['fixtures']
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BOLD=FONT.replace('.ttf','-Bold.ttf')
def font(n,b=False):return ImageFont.truetype(BOLD if b else FONT,n)
def clip(poly,axis,value,above):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  aa=a[axis]>=value-1e-9 if above else a[axis]<=value+1e-9
  bb=b[axis]>=value-1e-9 if above else b[axis]<=value+1e-9
  if aa:out.append(a)
  if aa!=bb:out.append(a+(b-a)*((value-a[axis])/(b[axis]-a[axis])))
 return out

def triangles(height):
 out=[]
 for name,v,faces,mat in mesh.parts:
  if name in ('Hull','Deck') or (not name.startswith('Surface_') and name!='LiftPlatform1'):continue
  if name=='LiftPlatform1':v=v.copy();v[:,1]+=height-v[:,1].max()
  for face in faces:
   for k in range(1,len(face)-1):
    tri=v[[face[0],face[k],face[k+1]]]
    if any((tri[:,axis].max()<value-1e-8 if above else tri[:,axis].min()>value+1e-8) for axis,value,above in BOUNDS):continue
    poly=list(tri)
    for axis,value,above in BOUNDS:
     poly=clip(poly,axis,value,above)
     if len(poly)<3:break
    for j in range(1,len(poly)-1):
     tt=np.asarray([poly[0],poly[j],poly[j+1]])
     if np.linalg.norm(np.cross(tt[1]-tt[0],tt[2]-tt[0]))>1e-9:out.append((tt,mat))
 return out

def render(height,on):
 W,H=1350,1300;direction,right,up=_basis(162,34)
 tris=triangles(height);world=np.concatenate([t[:,(0,2,1)] for t,m in tris]);pr=np.column_stack((world@right,world@up));lo,hi=pr.min(0),pr.max(0);centre=(lo+hi)/2
 scale=min((W-90)/(hi[0]-lo[0]),(H-140)/(hi[1]-lo[1]));sc=np.array([W/2,H/2+15])
 depth=np.full((H,W),-np.inf,np.float32);pos=np.zeros((H,W,3),np.float32);normal=np.zeros_like(pos);base=np.zeros_like(pos)
 for tri,mat in tris:
  t=tri[:,(0,2,1)];xy=(np.column_stack((t@right,t@up))-centre)*scale;xy[:,1]*=-1;xy+=sc;z=t@direction
  xmin=max(0,math.floor(xy[:,0].min()));xmax=min(W-1,math.ceil(xy[:,0].max()));ymin=max(0,math.floor(xy[:,1].min()));ymax=min(H-1,math.ceil(xy[:,1].max()))
  if xmax<xmin or ymax<ymin:continue
  a,b,c=xy;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-8:continue
  xx=np.arange(xmin,xmax+1)[None,:]+.5;yy=np.arange(ymin,ymax+1)[:,None]+.5
  u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;q=1-u-v
  dd=u*z[0]+v*z[1]+q*z[2];reg=depth[ymin:ymax+1,xmin:xmax+1];mask=(u>=-1e-7)&(v>=-1e-7)&(q>=-1e-7)&(dd>reg)
  if not mask.any():continue
  n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=np.linalg.norm(n)
  points=u[:,:,None]*tri[0]+v[:,:,None]*tri[1]+q[:,:,None]*tri[2]
  color=np.array([int(COLORS[mat][i:i+2],16) for i in (1,3,5)],np.float32)/255
  reg[mask]=dd[mask];pos[ymin:ymax+1,xmin:xmax+1][mask]=points[mask];normal[ymin:ymax+1,xmin:xmax+1][mask]=n;base[ymin:ymax+1,xmin:xmax+1][mask]=color
 occupied=np.isfinite(depth);key=np.array([-1,.8,-.2]);key/=np.linalg.norm(key)
 shade=.42+.48*np.maximum(0,(normal*key).sum(2));rgb=base*shade[:,:,None]
 if on:
  for lamp in lamps:
   pp=np.asarray(lamp['position'],np.float32);delta=pos-pp;dist=np.linalg.norm(delta,axis=2);unit=delta/np.maximum(dist[:,:,None],1e-5)
   pitch,yaw,_=np.radians(lamp['rotation_degrees']);direc=np.array([np.sin(yaw)*np.cos(pitch),-np.sin(pitch),np.cos(yaw)*np.cos(pitch)])
   cone=(unit*direc).sum(2);outer=math.cos(math.radians(lamp['spot_angle']/2));inner=math.cos(math.radians(lamp['spot_angle']/2-7))
   cone=np.clip((cone-outer)/(inner-outer),0,1);cone=cone*cone*(3-2*cone)
   diffuse=np.maximum(0,(-unit*normal).sum(2));atten=np.maximum(0,1-dist/lamp['range'])**2
   power=cone*diffuse*atten*lamp['intensity']*9
   rgb+=base*np.asarray(lamp['color'])[None,None,:]*power[:,:,None]
 # Soft studio surface shading and approximate local spots, not Unity photometry.
 rgb=np.clip(rgb,0,1);bg=np.linspace(0,1,H)[:,None,None];background=(np.array([.075,.115,.16])*(1-bg)+np.array([.035,.065,.095])*bg);background=np.repeat(background,W,1)
 rgb=np.where(occupied[:,:,None],rgb,background)
 return Image.fromarray((rgb*255).astype('uint8')),len(tris)

lower,n1=render(11.8,True);upper,n2=render(22.002,False)
canvas=Image.new('RGB',(3000,1710),'#10202d');draw=ImageDraw.Draw(canvas)
draw.text((90,48),'AUSTRALIS · LIFT WALL LIGHTING',font=font(46,True),fill='#edf5f5')
draw.text((90,112),'v0.8.3 · first lift cutaway · actual model geometry',font=font(27),fill='#9ec9d0')
draw.line((90,165,2910,165),fill='#3c5969',width=2)
canvas.paste(lower,(90,265));canvas.paste(upper,(1560,265))
draw.text((110,195),'LOWERED · WALL LIGHTS ON',font=font(30,True),fill='#eddbb4')
draw.text((1580,195),'DECK LEVEL · WALL LIGHTS OFF',font=font(30,True),fill='#dce8ed')
draw.text((110,239),'Platform at 11.8 m · eight recessed wall fittings',font=font(23),fill='#a9bdc7')
draw.text((1580,239),'Platform flush at 22.002 m · shaft lighting disabled',font=font(23),fill='#a9bdc7')
draw.line((90,1575,2910,1575),fill='#3c5969',width=2)
draw.text((90,1601),'Surrounding hull and deck omitted to expose the lift. Lamp shading is illustrative; this is not an in-game screenshot.',font=font(25),fill='#a8bec9')
draw.text((90,1642),'Lights follow the actual lift height independently and fade out before the platform reaches the flight deck.',font=font(25),fill='#a8bec9')
out=ROOT/'australis-2030/previews/Australis-v0.8.3-Lift-Cutaway.png';meta=PngImagePlugin.PngInfo();meta.add_text('Source','Actual exported v0.8.3 OBJ and INI; clipped cutaway, illustrative lamp shading');meta.add_text('OBJ SHA256',hashlib.sha256(obj.read_bytes()).hexdigest());canvas.save(out,pnginfo=meta,optimize=True)
prov={'source_obj_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'source_ini_sha256':hashlib.sha256(ini.read_bytes()).hexdigest(),'crop_bounds':'First lift only; surrounding hull/deck omitted','rendered_triangles':[n1,n2],'lighting':'Illustrative Lambert spotlight shading using actual fixture profiles; no Unity renderer, shadows or gameplay validation','states_m':[11.8,22.002],'fixture_count':len(lamps)}
(ROOT/'australis-2030/previews/Australis-v0.8.3-Lift-Cutaway-Provenance.json').write_text(json.dumps(prov,indent=2)+'\n');print(out);print(prov)

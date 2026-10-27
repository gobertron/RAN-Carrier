#!/usr/bin/env python3
"""Render v0.8.5 directly from the current native OBJ, INI and number atlases.

Number glyphs are a deterministic flat-colour approximation of the game's
actual PNG texture, projected through each exported panel's real OBJ UVs.
No historical fleet meshes, invented windows or generated imagery are used.
"""
from pathlib import Path
import configparser
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'australis-2030'), str(ROOT)]
from fleet_preview_build_current_game_preview import load_current_mesh
import fleet_preview_build_3d_viewer as viewer
import render_current_views as renderer
from build import COLORS as BASE_COLORS
from enclosed_deck import BAYS
from generate_source_models import Mesh

PACKAGE = ROOT/'game-mod/RAN-Carrier-Australis-2030'
DESIGN = ROOT/'australis-2030'
PREVIEWS = DESIGN/'previews'
VIEWERS = DESIGN/'viewer'
CANONICAL = 'ran_cvn_australis_2030'
VERSION = '0.8.5-naval-details'
ROSTER = [('Australis',91),('Southern Cross',92),('Federation',93),('Commonwealth',94)]
COLORS = dict(BASE_COLORS)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ini(path):
    value = configparser.ConfigParser(interpolation=None)
    value.optionxform = str
    value.read(path,encoding='utf-8-sig')
    return value


def read_number_quads(obj, native_mesh):
    """Use the already transformed native HullNumbers mesh for world XYZ."""
    faces=[];uvs=[];active=False
    for line in obj.read_text().splitlines():
        if line.startswith('o '):
            active=line[2:]=='HullNumbers'
        elif line.startswith('vt '):
            uvs.append(tuple(map(float,line.split()[1:3])))
        elif active and line.startswith('f '):
            parts=[token.split('/') for token in line.split()[1:]]
            if any(len(token)<2 or not token[1] for token in parts):
                raise ValueError('Native number panel lacks a UV index')
            faces.append([(int(token[0])-1,int(token[1])-1) for token in parts])
    part=next(part for part in native_mesh.parts if part[0]=='HullNumbers')
    used=sorted({v for face in faces for v,_ in face})
    world=dict(zip(used,part[1]))
    if len(faces)%2:
        raise ValueError('Expected two exported triangles per number panel')
    out=[]
    for index in range(0,len(faces),2):
        pair=faces[index:index+2]
        ordered=[]
        for face in pair:
            for vertex in face:
                if vertex not in ordered:ordered.append(vertex)
        if len(ordered)!=4:
            raise ValueError('Number panel is not a two-triangle quad')
        coords=np.array([world[v] for v,_ in ordered]);uv=np.array([uvs[t] for _,t in ordered])
        seed=pair[0]
        a=np.array([[*uvs[t],1.] for _,t in seed])
        xyz=np.array([world[v] for v,_ in seed])
        affine=np.linalg.solve(a,xyz)
        fit=np.c_[uv,np.ones(4)]@affine
        error=float(np.max(np.linalg.norm(fit-coords,axis=1)))
        if error>2e-5:
            raise ValueError('Number panel UV projection does not match its exported vertices')
        normal=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);normal/=np.linalg.norm(normal)
        triangles=[[world[v] for v,_ in face] for face in pair]
        out.append({'index':index//2,'uv':uv,'xyz':coords,'triangles':triangles,
                    'affine':affine,'normal':normal,'fit_error_m':error})
    return out


def add_projected_number(mesh,quads,atlas):
    image=Image.open(atlas).convert('RGB')
    result=[]
    # Native texture colours; antialiasing becomes a reproducible 3-colour mask.
    ink=np.array((223,235,234),dtype=np.float64)
    outline=np.array((37,56,67),dtype=np.float64)
    for panel in quads:
        uv=panel['uv'];umin,vmin=uv.min(axis=0);umax,vmax=uv.max(axis=0)
        # Pixel bounds derive from the real UV region, never a guessed ship ID.
        crop=image.crop((round(umin*image.width),round((1-vmax)*image.height),
                         round(umax*image.width),round((1-vmin)*image.height)))
        background=np.array(crop.getpixel((0,0)),dtype=np.float64)
        sample_w=384
        sample_h=max(24,round(sample_w*crop.height/crop.width))
        sample=np.asarray(crop.resize((sample_w,sample_h),Image.Resampling.LANCZOS),dtype=np.float64)
        palette=np.stack((background,ink,outline))
        labels=np.argmin(np.sum((sample[:,:,None,:]-palette[None,None,:,:])**2,axis=3),axis=2)
        names=[]
        for label,color in enumerate(palette):
            name='native_number_'+('background_' if label==0 else 'ink_' if label==1 else 'outline_')+''.join(f'{round(c):02x}' for c in color)
            COLORS[name]='#'+''.join(f'{round(c):02x}' for c in color)
            names.append(name)
        # Preserve the exact exported background triangles and their winding.
        background_vertices=np.array([v for tri in panel['triangles'] for v in tri])
        mesh.parts.append((f'PreviewHullNumberPanel{panel["index"]}',background_vertices,[[0,1,2],[3,4,5]],names[0]))
        def xyz(x,y):
            u=umin+(umax-umin)*x/sample_w
            v=vmax-(vmax-vmin)*y/sample_h
            return np.array((u,v,1.))@panel['affine']+panel['normal']*.0008
        # Merge equal horizontal runs vertically, reducing the offline payload.
        rectangles=[];open_runs={}
        for y in range(sample_h+1):
            runs=[]
            if y<sample_h:
                x=0
                while x<sample_w:
                    label=int(labels[y,x]);start=x;x+=1
                    while x<sample_w and labels[y,x]==label:x+=1
                    if label:runs.append((start,x,label))
            current=set(runs)
            for key,top in list(open_runs.items()):
                if key not in current:
                    rectangles.append((*key,top,y));del open_runs[key]
            for key in runs:open_runs.setdefault(key,y)
        by_label={1:([],[]),2:([],[])}
        for x0,x1,label,y0,y1 in rectangles:
            vertices,faces=by_label[label];start=len(vertices)
            points=[xyz(x0,y0),xyz(x1,y0),xyz(x1,y1),xyz(x0,y1)]
            if np.dot(np.cross(points[1]-points[0],points[2]-points[0]),panel['normal'])<0:
                points=list(reversed(points))
            vertices.extend(points);faces.extend(([start,start+1,start+2],[start,start+2,start+3]))
        for label,(vertices,faces) in by_label.items():
            if vertices:mesh.parts.append((f'PreviewHullNumberPanel{panel["index"]}Ink{label}',np.array(vertices),faces,names[label]))
        result.append({'panel':panel['index'],'uv_bounds':[float(umin),float(vmin),float(umax),float(vmax)],
            'background_rgb':background.astype(int).tolist(),'projected_rectangles':len(rectangles),
            'mask_resolution':[sample_w,sample_h],'affine_max_error_m':panel['fit_error_m'],
            'normal':panel['normal'].tolist()})
    return result


def native_variant_meshes():
    native,obj,config=load_current_mesh(PACKAGE,CANONICAL)
    quads=read_number_quads(obj,native)
    variants=ini(PACKAGE/'vessels'/f'{CANONICAL}_variants.ini')
    fleet=[]
    for index,(name,number) in enumerate(ROSTER,1):
        row=variants[f'Variant{index}']
        atlas=PACKAGE/row['ResourcesHullnumberFolder']/row['HullnumberTexture']
        mesh=Mesh();mesh.parts=[part for part in native.parts if part[0]!='HullNumbers']
        projected=add_projected_number(mesh,quads,atlas)
        fleet.append({'id':f'{CANONICAL}:Variant{index}','name':f'HMSCS {name} {number}',
            'mesh':mesh,'obj_sha256':sha(obj),'ini_sha256':sha(config),
            'atlas':str(atlas.relative_to(PACKAGE)),'atlas_sha256':sha(atlas),
            'number_projection':projected})
    return fleet,obj,config


def clip_triangles(triangles,bounds):
    """Clip, rather than merely select, exported triangles for detail views."""
    out=[]
    for name,triangle,material in triangles:
        polygon=[v.copy() for v in triangle]
        for axis,(lo,hi) in enumerate(bounds):
            for edge,sign in ((lo,1),(hi,-1)):
                clipped=[]
                for j,current in enumerate(polygon):
                    previous=polygon[j-1]
                    dc=(current[axis]-edge)*sign;dp=(previous[axis]-edge)*sign
                    if (dc>=0)!=(dp>=0):
                        clipped.append(previous+(current-previous)*(dp/(dp-dc)))
                    if dc>=0:clipped.append(current)
                polygon=clipped
                if not polygon:break
            if not polygon:break
        for j in range(1,len(polygon)-1):
            tri=np.array((polygon[0],polygon[j],polygon[j+1]))
            if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))>1e-10:
                out.append((name,tri,material))
    if not out:raise ValueError('No native geometry in detail crop')
    return out


def render_detail(triangles,title,bounds,azimuth,elevation,revision,path,caption):
    clipped=clip_triangles(triangles,bounds)
    renderer._render(clipped,COLORS,title,azimuth,elevation,revision,path,caption=caption,
                     footer='Current native geometry cropped for clarity · PNG texture approximation · not gameplay')


def montage(paths,out,title,subtitle,revision):
    tiles=[]
    for path in paths:
        with Image.open(path) as image:tiles.append(image.convert('RGB').resize((1200,700),Image.Resampling.LANCZOS))
    columns=2 if len(tiles)>1 else 1;rows=math.ceil(len(tiles)/columns)
    image=Image.new('RGB',(columns*1200,rows*700+130),'#101c27')
    draw=ImageDraw.Draw(image)
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    draw.text((40,24),title,font=ImageFont.truetype(font,32),fill='#eef4f4')
    draw.text((40,75),subtitle,font=ImageFont.truetype(font,21),fill='#a8cdd1')
    for i,tile in enumerate(tiles):image.paste(tile,((i%columns)*1200,130+(i//columns)*700))
    metadata=PngImagePlugin.PngInfo()
    metadata.add_text("Source revision",revision)
    metadata.add_text("Description","Current exported model crop montage; number textures approximated from native PNG atlases")
    image.save(out,optimize=True,pnginfo=metadata)


def verify_javascript(path):
    for attrs,script in re.findall(r'<script([^>]*)>(.*?)</script>',path.read_text(),re.S):
        if 'application/json' in attrs:json.loads(script);continue
        with tempfile.NamedTemporaryFile(mode='w',suffix='.js') as test:
            test.write(script);test.flush();subprocess.run(['node','--check',test.name],check=True)


def main():
    PREVIEWS.mkdir(parents=True,exist_ok=True);VIEWERS.mkdir(parents=True,exist_ok=True)
    fleet,obj,config=native_variant_meshes();mesh=fleet[0]['mesh']
    revision=viewer.model_revision(mesh,COLORS)
    for bay in BAYS:
        kind,index=bay.key.rsplit('_',1)
        if kind in ('CIWS','Mk46'):
            for part in ('Mount','Gun'):
                viewer.MOTIONS[f'{kind}_{part}_{index}']=('y',bay.roof+.08-bay.y if bay.stroke else 0)
    viewer.TEMPLATE=viewer.TEMPLATE.replace('v0.8.2 LIFT LIGHTING','v0.8.5 NAVAL DETAILS')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Australis 2030 — current model photos and 3D','Australis-class v0.8.5 — current naval detailing')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('<h1>Australis 2030</h1>','<h1>HMSCS Australis 91</h1>')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('</style>','#deploy,#laserStatus{display:none}\n</style>')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('let liftTarget = 0, liftProgress = 0;','let liftTarget = 1, liftProgress = 1;')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('id="moveLifts">Raise all four lifts','id="moveLifts">Lower all four lifts')
    viewer.TEMPLATE=viewer.TEMPLATE.replace("if (mesh.category === 'lifts') offset[1] = liftProgress * 10.202;",
        "if (mesh.category === 'lifts') offset[1] = (liftProgress - 1) * 10.202;")
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Two bow + one port-waist catapult. Four lifts and three helipads. Aircraft support: fixed-wing carrier aircraft, VTOL/STOL and helicopters.',
        'Two bow + one port-waist catapult. All four lifts start at deck level. Three rear pads are helicopter-only.')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Actual design-model views, not in-game screenshots.',
        'Current v0.8.5 OBJ and INI geometry. Number appearance is projected from the actual per-variant PNG atlas, using approximate texture sampling and studio shading. This is not Unity rendering or a gameplay screenshot.')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Original model sources and installers are included in the numbered release package.',
        'One Australis-class with four named variants. Enlarged numbers, framed bridge glazing and naval doors align to the current exported surfaces. Lifts lower only on demand in the native game; this preview control illustrates their travel.')
    renderer.CAPTION='v0.8.5 · enlarged numbers · aligned naval windows and doors · lifts UP'
    photos=renderer.render_current_views(mesh,COLORS,PREVIEWS,revision)
    triangles=list(mesh.triangles())
    fittings_path=PACKAGE/'naval-fittings.json'
    if fittings_path.is_file():
        features=json.loads(fittings_path.read_text())['features']
        hull=next(item for item in features if item['name']=='NavalHullDoor_1_0')
        hx,hy,hz=hull['centre_m'];nx,ny,nz=hull['normal']
        hull_bounds=((hx-2.3,hx+2.7),(hy-2.1,hy+2.0),(hz-2.3,hz+2.3))
        hull_az=math.degrees(math.atan2(nz,nx));hull_el=math.degrees(math.asin(ny))+3
    else:
        hull_bounds=((37,42),(11.8,15.8),(-1,6));hull_az=-.5;hull_el=12
    with tempfile.TemporaryDirectory(prefix='australis-v085-details-') as folder:
        folder=Path(folder)
        specs=[('main','Main island windows and doors',((22,39),(21.8,55),(-35,43)),-125,14),
               ('aft','Aft aviation island',((25,40),(21.8,44),(-110,-65)),-125,15),
               ('main_starboard','Main island starboard',((22,39),(21.8,55),(-35,43)),-55,14),
               ('hull','Hull-side naval door and service gallery',hull_bounds,hull_az,hull_el)]
        details=[]
        for key,title,bounds,azimuth,elevation in specs:
            path=folder/(key+'.png');render_detail(triangles,title,bounds,azimuth,elevation,revision,path,'Framed glazing and watertight-door appearance · actual model surfaces');details.append(path)
        out=PREVIEWS/'Australis-v0.8.5-Naval-Details.png'
        montage(details,out,'AUSTRALIS v0.8.5 · NAVAL DETAILING','Current exported mesh · surfaces cropped for clarity · studio shading',revision)
        number_specs=[('deck','Flight-deck number',((13,27),(21.8,22.4),(142,156)),None,None),
                      ('port','Port island number',((22,29),(25,36),(0,15)),-180,5),
                      ('starboard','Starboard island number',((33,39),(25,36),(0,15)),0,5)]
        numbers=[]
        for key,title,bounds,azimuth,elevation in number_specs:
            path=folder/('number_'+key+'.png');render_detail(triangles,title,bounds,azimuth,elevation,revision,path,'Number appearance projected from the native variant PNG');numbers.append(path)
        family=Image.new('RGB',(2400,1400),'#101c27');draw=ImageDraw.Draw(family)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',32)
        draw.text((65,30),'NATIVE VARIANT NUMBER ATLASES',font=font,fill='#eef4f4')
        for i,ship in enumerate(fleet):
            x=65+(i%2)*1200;y=110+(i//2)*630
            draw.text((x,y),ship['name'],font=font,fill='#a8cdd1')
            with Image.open(PACKAGE/ship['atlas']) as atlas:
                tile=atlas.crop((0,0,atlas.width,atlas.height//2)).resize((1070,535),Image.Resampling.LANCZOS)
                family.paste(tile,(x,y+55))
        family_path=folder/'number_family.png';family.save(family_path);numbers.append(family_path)
        number_out=PREVIEWS/'Australis-v0.8.5-Hull-Numbers.png'
        montage(numbers,number_out,'AUSTRALIS v0.8.5 · ENLARGED HULL NUMBERS','Same 91–94 texture atlases and UV-mapped panels used by the native class',revision)
    photos += [{'id':'naval_details','title':'Naval windows and doors','caption':'Current exported fittings, cropped and shaded for inspection.','path':out},
               {'id':'hull_numbers','title':'Enlarged hull numbers','caption':'Actual native panel geometry with atlas-derived texture approximation.','path':number_out}]
    for key,title,azimuth,elevation in [('waterjets','Stern waterjets',-90,-4),('underwater','Underwater hull',-55,-23)]:
        path=PREVIEWS/f'australis_2030_current_{key}.png'
        renderer._render(triangles,COLORS,title,azimuth,elevation,revision,path)
        photos.append({'id':key,'title':title,'caption':renderer.CAPTION,'path':path})
    output=VIEWERS/'Australis-v0.8.5-Fleet-3D.html'
    viewer.build_viewer(mesh,COLORS,output,photos=photos,fleet=fleet)
    if output.stat().st_size>3_000_000:raise ValueError('Viewer exceeds practical self-contained size')
    verify_javascript(output)
    shutil.copy2(output,VIEWERS/'australis_2030_3d.html')
    shutil.copy2(photos[0]['path'],PREVIEWS/'Australis-v0.8.5-Full-Ship.png')
    for source,target in [('starboard','perspective'),('port_waist','port_waist'),('bow','bow')]:
        shutil.copy2(PREVIEWS/f'australis_2030_current_{source}.png',PREVIEWS/f'australis_2030_{target}.png')
    provenance={'version':VERSION,'revision':revision,'source':'Current canonical native OBJ, INI and per-variant PNG atlases',
        'obj_sha256':sha(obj),'ini_sha256':sha(config),
        'number_panels_sha256':sha(PACKAGE/'number-panels.json') if (PACKAGE/'number-panels.json').is_file() else None,
        'naval_fittings_sha256':sha(PACKAGE/'naval-fittings.json') if (PACKAGE/'naval-fittings.json').is_file() else None,'native_class':'Australis-class','fleet':[
            {k:v for k,v in ship.items() if k!='mesh'} for ship in fleet],
        'viewer':str(output.relative_to(DESIGN)),'viewer_sha256':sha(output),'viewer_bytes':output.stat().st_size,
        'native_number_texture_preview':'Approximate 384-pixel-wide nearest-palette mask projected through actual native panel UVs; backgrounds preserve exported triangles',
        'default_lift_pose':'Actual native upper-stop coordinates, top surface 22.002 m; initial viewer offset zero',
        'lift_control':'(progress - 1) × 10.202 m, where progress starts at 1',
        'lighting':'Studio Lambert shading; no Unity renderer, runtime illumination or gameplay validation',
        'omitted':['stock runtime flag','collision-only meshes'],
        'photos':[{'id':photo['id'],'file':photo['path'].name,'sha256':sha(photo['path'])} for photo in photos]}
    (PREVIEWS/'Australis-v0.8.5-Render-Provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (DESIGN/'model/presentation-manifest.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({'viewer':str(output),'bytes':output.stat().st_size,'ships':len(fleet),'photos':len(photos),'obj_sha256':sha(obj)},indent=2))


if __name__=='__main__':main()

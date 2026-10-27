#!/usr/bin/env python3
"""One native Australis class with four numbered variants.

The game groups separate vessel definitions as dated subclasses.  Its native
variant loader supports per-variant hull-number textures, so one shared hull
can expose all four ship names without changing the carrier's systems.
"""
from pathlib import Path
import configparser
import hashlib
import json
import math
import re
import shutil

CANONICAL = 'ran_cvn_australis_2030'
ROSTER = (
    (CANONICAL, 'Australis', 91),
    ('ran_cvn_southern_cross_2030', 'Southern Cross', 92),
    ('ran_cvn_federation_2030', 'Federation', 93),
    ('ran_cvn_commonwealth_2030', 'Commonwealth', 94),
)
UNIT = 217 / 3.161967
WIDTH_SCALE = 82 / 88
MARKER = '# BEGIN NATIVE CLASS HULL-NUMBER PANELS'
ATLAS_FOLDER = f'ships/{CANONICAL}/'
ARCHIVE = 'compatibility-reference/v0.8.3'


def read_ini(path):
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str
    with Path(path).open(encoding='utf-8-sig') as source:
        cfg.read_file(source)
    return cfg


def write_ini(path, text):
    Path(path).write_bytes(b'\xef\xbb\xbf' + (text.replace('\r\n', '\n').rstrip()+'\n').replace('\n', '\r\n').encode())


def _number_atlas(folder, number):
    # Asset generation requires Pillow; validation and the installer do not.
    from PIL import Image, ImageDraw, ImageFont
    colors = {'deck': '#394953', 'island': '#9aacb3', 'white': '#dfebea', 'outline': '#253843'}
    image = Image.new('RGB', (1024, 1024), colors['deck'])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 512, 1023, 1023), fill=colors['island'])
    font_path = Path('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf')
    if not font_path.is_file():font_path = font_path.with_name('DejaVuSans-Bold.ttf')
    font = ImageFont.truetype(str(font_path), 640)
    # Original, legible block paint.  Separate masks compensate for the deck
    # and island panels' different physical aspect ratios.
    mask = Image.new('L', (1400, 900))
    ImageDraw.Draw(mask).text((30, 0), str(number), font=font, fill=255)
    mask = mask.crop(mask.getbbox())
    from PIL import ImageFilter, ImageOps
    boxes = {}
    for region, top, width, height in (('deck', 0, 800, 380), ('island', 512, 820, 384)):
        glyph = mask.resize((width, height), Image.Resampling.LANCZOS)
        x, y = (1024-width)//2, top+(512-height)//2
        dark = ImageOps.expand(glyph,border=4).filter(ImageFilter.MaxFilter(9))
        image.paste(colors['outline'], (x-4, y-4), dark)
        image.paste(colors['white'], (x, y), glyph)
        boxes[region] = [x, y, x+width, y+height]
    path = folder / f'hullnumber_{number}.png'
    image.save(path)
    return {'number': number, 'texture': path.name,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'glyph_pixel_bounds': boxes}


def _surface_mesh(text):
    """Read only the actual exported lower-island support triangles."""
    vertices, triangles, name = [], [], None
    for line in text.splitlines():
        if line.startswith('o '):name = line[2:]
        elif line.startswith('v '):vertices.append(tuple(float(v)*UNIT for v in line.split()[1:4]))
        elif line.startswith('f ') and name == 'Surface_Island':
            indices = [int(v.split('/')[0])-1 for v in line.split()[1:]]
            triangles.extend(tuple(vertices[j] for j in (indices[0],indices[i],indices[i+1]))
                             for i in range(1,len(indices)-1))
    assert triangles, 'Missing exported island surface'
    return triangles


def _surface_hit(triangles, y, z, side):
    """Intersect an X ray with the exported island, retaining its true normal."""
    hits = []
    for a,b,c in triangles:
        den = (b[2]-c[2])*(a[1]-c[1])+(c[1]-b[1])*(a[2]-c[2])
        if abs(den)<1e-12:continue
        u = ((b[2]-c[2])*(y-c[1])+(c[1]-b[1])*(z-c[2]))/den
        v = ((c[2]-a[2])*(y-c[1])+(a[1]-c[1])*(z-c[2]))/den
        if min(u,v,1-u-v)<-1e-7:continue
        ab = [b[j]-a[j] for j in range(3)]; ac = [c[j]-a[j] for j in range(3)]
        n = [ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
        length = math.sqrt(sum(q*q for q in n))
        n = [q/length for q in n]
        if n[0]*side<0:n = [-q for q in n]
        hits.append(((u*a[0]+v*b[0]+(1-u-v)*c[0], y, z),tuple(n)))
    assert hits, ('Number panel misses exported island', y, z)
    return (min if side<0 else max)(hits,key=lambda h:h[0][0])


def _number_panels(text):
    deck = [(14.6,22.012,144.6),(14.6,22.012,153.4),
            (25.4,22.012,153.4),(25.4,22.012,144.6)]
    panels = [dict(name='BowDeckNumber', region='deck', vertices_m=deck,
                   uv=[(0,.5),(0,1),(1,1),(1,.5)], normal=(0,1,0),
                   offset_m=.012, panel_width_m=10.8, panel_height_m=8.8,
                   glyph_width_m=10.8*800/1024, glyph_height_m=8.8*380/512)]
    triangles = _surface_mesh(text)
    for side, label in ((-1,'PortIslandNumber'),(1,'StarboardIslandNumber')):
        origin,normal = _surface_hit(triangles,30.3,7.6,side)
        coordinates = [(27.5,2.8),(27.5,12.4),(33.1,12.4),(33.1,2.8)]
        if side>0:coordinates = [(y,15.2-z) for y,z in coordinates]
        vertices = []
        errors = []
        for y,z in coordinates:
            x = origin[0]-(normal[1]*(y-origin[1])+normal[2]*(z-origin[2]))/normal[0]
            actual,_ = _surface_hit(triangles,y,z,side)
            errors.append(abs(actual[0]-x))
            vertices.append(tuple(v+q*.018 for v,q in zip((x,y,z),normal)))
        assert max(errors)<.0002, ('Number rectangle crosses a facet',label,errors)
        # Native/viewer camera right is up cross forward: viewed from port,
        # right points aft (-Z), and viewed from starboard it points bowward
        # (+Z).  Reverse U on both outside faces; vertex winding stays outward.
        panels.append(dict(name=label,region='island',vertices_m=vertices,
                           uv=[(1,0),(0,0),(0,.5),(1,.5)],normal=normal,
                           support_point_m=origin,offset_m=.018,
                           support_error_m=max(errors),panel_width_m=9.6,panel_height_m=5.6,
                           glyph_width_m=9.6*820/1024,glyph_height_m=5.6*384/512))
    return panels


def _append_panels(obj):
    original = obj.read_text().split(MARKER, 1)[0].rstrip() + '\n'
    vcount = len(re.findall(r'^v ', original, re.M))
    uvcount = len(re.findall(r'^vt ', original, re.M))
    normal_count = len(re.findall(r'^vn ', original, re.M))
    panels = _number_panels(original)
    rows = [MARKER, 'o HullNumbers']
    rows += ['v ' + ' '.join(f'{n/UNIT:.9f}' for n in v)
             for panel in panels for v in panel['vertices_m']]
    # OBJ V is bottom-up; the top atlas half is the deck and the bottom half
    # is the island.  Both faces show upright, non-mirrored numerals.
    uvs = [uv for panel in panels for uv in panel['uv']]
    rows += [f'vt {u:.6f} {v:.6f}' for u,v in uvs]
    rows += ['vn '+' '.join(f'{n:.9f}' for n in panel['normal']) for panel in panels]
    rows += ['usemtl hullnumber', 's off']
    for index,panel in enumerate(panels):
        panel['triangle_indices'] = [index*2,index*2+1]
        for face in ((0,1,2),(0,2,3)):
            rows.append('f ' + ' '.join(f'{vcount+index*4+i+1}/{uvcount+index*4+i+1}/{normal_count+index+1}' for i in face))
    obj.write_text(original + '\n'.join(rows) + '\n')
    return {'schema':2,'native_submodel':'HullNumbers','atlas_width':1024,'atlas_height':1024,
            'regions':{'deck':{'pixel_bounds':[0,0,1024,512],'background':'#394953'},
                       'island':{'pixel_bounds':[0,512,1024,1024],'background':'#9aacb3'}},
            'paint_color':'#dfebea','outline_color':'#253843','panels':panels,
            'source_obj_without_number_panels_sha256':hashlib.sha256(original.encode()).hexdigest()}


def apply_class_list(package):
    package = Path(package)
    vessels = package / 'vessels'
    archive = package / ARCHIVE
    # These are reference files outside the game's loaded vessels directory.
    # Existing missions using the three retired IDs must be re-placed from the
    # consolidated class, or the user can restore the verified previous build.
    for ship_id, _, _ in ROSTER:
        for suffix in ('.ini', '_variants.ini'):
            source = vessels / f'{ship_id}{suffix}'
            target = archive / 'vessels' / (source.name+'.reference')
            if source.is_file() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        for suffix in ('.obj', '.mtl'):
            source = package / 'ships' / ship_id / f'{ship_id}{suffix}'
            target = archive / 'ships' / ship_id / source.name
            if source.is_file() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    for ship_id, _, _ in ROSTER[1:]:
        for suffix in ('.ini', '_variants.ini'):
            (vessels / f'{ship_id}{suffix}').unlink(missing_ok=True)

    folder = package / ATLAS_FOLDER
    number_report = _append_panels(folder / f'{CANONICAL}.obj')
    mtl = folder / f'{CANONICAL}.mtl'
    text = mtl.read_text().split('\nnewmtl hullnumber\n', 1)[0].rstrip()
    mtl.write_text(text + '\n\nnewmtl hullnumber\nKd 1 1 1\nKa 0.15 0.15 0.15\nKs 0.1 0.1 0.1\nNs 20\nmap_Kd hullnumber_91.png\n')
    number_report['variants'] = [_number_atlas(folder,number) for _,_,number in ROSTER]
    number_report['obj_sha256'] = hashlib.sha256((folder/f'{CANONICAL}.obj').read_bytes()).hexdigest()
    (package/'number-panels.json').write_text(json.dumps(number_report,indent=2)+'\n')
    write_ini(folder / 'hullnumber_mat.ini', '[Shader]\nPath=Marmoset/Bumped Specular IBL\n\n[Textures]\n'
              f'_MainTex={ATLAS_FOLDER}hullnumber_91.png\n_SpecTex={ATLAS_FOLDER}specular.png\n_BumpMap={ATLAS_FOLDER}normal.png\n')

    path = vessels / f'{CANONICAL}.ini'
    cfg = read_ini(path)
    if 'HullNumbers' not in cfg['Submodels'].values():
        main = [int(k.split('_')[1]) for k in cfg['Submodels'] if re.fullmatch(r'Main_\d+', k)]
        key = 'Main_' + str(max(main, default=0)+1)
        text = path.read_text(encoding='utf-8-sig').replace('\r\n','\n')
        text = re.sub(r'(\[Submodels\]\n)', r'\g<1>'+key+'=HullNumbers\n', text, count=1)
        text = text.rstrip() + '\n\n[HullNumbers]\nMesh=HullNumbers\nMaterial=hullnumber_mat.ini\n'
        write_ini(path, text)

    shared = f'ResourcesFlagFolder=ships/materials/textures/\nFlagTexture=flag_australia\nNation=Australia\nServiceDate=2025|2055\nResourcesHullnumberFolder={ATLAS_FOLDER}\n'
    variants = '[General]\nNationFlagReference=Flag1\nHullnumberReference=HullNumbers\nNumberOfVariants=4\n\n'
    variants += '[Default]\n'+shared+'HullnumberTexture=hullnumber_91.png\n\n'
    names = [f'[{CANONICAL}]', 'Type=CVN,Aircraft Carrier', 'Default=Australis-class,Australis-class']
    for index, (_, name, number) in enumerate(ROSTER, 1):
        variants += f'[Variant{index}]\n'+shared+f'HullnumberTexture=hullnumber_{number}.png\n\n'
        names.append(f'Variant{index}=HMSCS {name} {number},{name} {number}')
    names.append('DefaultDescription=Australis-class carrier; four named ships with native hull-number variants. Experimental waterjet and lift-lighting build; in-game testing remains pending.')
    write_ini(vessels / f'{CANONICAL}_variants.ini', variants)
    write_ini(package / 'language_en/vessel_names.ini', '\n'.join(names)+'\n')
    return validate_class_list(package)


def validate_class_list(package):
    package = Path(package)
    vessels = package / 'vessels'
    active = sorted(p.name for p in vessels.glob('*.ini') if not p.name.endswith('_variants.ini'))
    assert active == [CANONICAL+'.ini'], ('Expected one active class definition', active)
    variants = read_ini(vessels / f'{CANONICAL}_variants.ini')
    assert variants['General']['NumberOfVariants'] == '4'
    assert variants['General']['HullnumberReference'] == 'HullNumbers'
    assert set(variants.sections()) == {'General','Default',*(f'Variant{i}' for i in range(1,5))}
    names = read_ini(package / 'language_en/vessel_names.ini')
    assert names.sections() == [CANONICAL]
    assert names[CANONICAL]['Default'] == 'Australis-class,Australis-class'
    cfg = read_ini(vessels / f'{CANONICAL}.ini')
    assert list(cfg['Submodels'].values()).count('HullNumbers') == 1
    assert cfg['HullNumbers']['Mesh'] == 'HullNumbers'
    folder = package / ATLAS_FOLDER
    material = read_ini(folder / cfg['HullNumbers']['Material'])
    assert material['Shader']['Path'] == 'Marmoset/Bumped Specular IBL'
    for resource in material['Textures'].values():
        assert (package/resource).is_file(), resource
    for index, (_, name, number) in enumerate(ROSTER, 1):
        section = variants[f'Variant{index}']
        assert names[CANONICAL][f'Variant{index}'] == f'HMSCS {name} {number},{name} {number}'
        assert section['Nation'] == 'Australia' and section['ServiceDate'] == '2025|2055'
        path = package / section['ResourcesHullnumberFolder'] / section['HullnumberTexture']
        data = path.read_bytes()
        assert data[:8] == b'\x89PNG\r\n\x1a\n' and int.from_bytes(data[16:20],'big') == 1024 and int.from_bytes(data[20:24],'big') == 1024
    obj = folder / f'{CANONICAL}.obj'
    text = obj.read_text()
    assert text.count(MARKER) == 1 and text.count('\no HullNumbers\n') == 1
    suffix = text.split(MARKER,1)[1]
    vertices = [tuple(map(float,line.split()[1:4])) for line in text.splitlines() if line.startswith('v ')]
    uvs = [tuple(map(float,line.split()[1:3])) for line in text.splitlines() if line.startswith('vt ')]
    normals = [tuple(map(float,line.split()[1:4])) for line in text.splitlines() if line.startswith('vn ')]
    faces = [[tuple(map(int,part.split('/'))) for part in line.split()[1:]] for line in suffix.splitlines() if line.startswith('f ')]
    report = json.loads((package/'number-panels.json').read_text())
    panels = report['panels']
    assert report['schema']==2 and len(panels)==3
    assert [p['name'] for p in panels]==['BowDeckNumber','PortIslandNumber','StarboardIslandNumber']
    assert hashlib.sha256(obj.read_bytes()).hexdigest()==report['obj_sha256']
    assert len(faces)==2*len(panels) and all(len(face)==3 for face in faces)
    assert all(len(indices)==3 and 1<=indices[0]<=len(vertices) and 1<=indices[1]<=len(uvs)
               and 1<=indices[2]<=len(normals) for face in faces for indices in face)
    assert all(0<=u<=1 and 0<=v<=1 for u,v in uvs[-4*len(panels):])
    for variant in report['variants']:
        texture = folder/variant['texture']
        assert hashlib.sha256(texture.read_bytes()).hexdigest()==variant['sha256']
    for i, face in enumerate(faces):
        a,b,c=(vertices[indices[0]-1] for indices in face)
        ab=[b[j]-a[j] for j in range(3)];ac=[c[j]-a[j] for j in range(3)]
        normal=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
        expected = panels[i//2]['normal']
        assert all(math.dist(normals[indices[2]-1],expected)<1e-8 for indices in face)
        length = math.sqrt(sum(v*v for v in normal))
        assert sum(v*q for v,q in zip(normal,expected))/length>.999999, ('Wrong number-panel winding',i,normal)
    expected_vertices = [v for panel in panels for v in panel['vertices_m']]
    actual_vertices = [tuple(v*UNIT for v in p) for p in vertices[-len(expected_vertices):]]
    assert all(math.dist(a,b)<1e-6 for a,b in zip(actual_vertices,expected_vertices))
    assert panels[0]['panel_width_m']==10.8 and panels[0]['panel_height_m']==8.8
    assert all(p['support_error_m']<.0002 and p['offset_m']==.018 for p in panels[1:])
    # Increasing U maps to screen-right in outward native side views.
    assert panels[1]['vertices_m'][1][2]>panels[1]['vertices_m'][0][2]
    assert panels[2]['vertices_m'][1][2]<panels[2]['vertices_m'][0][2]
    assert panels[1]['uv'][1][0]<panels[1]['uv'][0][0]
    assert panels[2]['uv'][1][0]<panels[2]['uv'][0][0]
    return {'class':'Australis-class', 'definition':CANONICAL, 'native_variants':4,
            'number_panel_triangles':len(faces), 'number_panels':len(panels),
            'legacy_reference_folder':ARCHIVE}


if __name__ == '__main__':
    package = Path(__file__).resolve().parents[1] / 'game-mod/RAN-Carrier-Australis-2030'
    print(apply_class_list(package))

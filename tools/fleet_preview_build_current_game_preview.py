#!/usr/bin/env python3
"""Preview the shipped OBJ + INI hierarchy, rather than the authoring mesh."""
from pathlib import Path
import sys,configparser,math,json,hashlib,shutil
import numpy as np
ROOT=Path(__file__).resolve().parents[1];DESIGN=ROOT/'australis-2030'
sys.path[:0]=[str(ROOT),str(DESIGN)]
from generate_source_models import Mesh
from build import COLORS
import build_3d_viewer as viewer
from render_current_views import render_current_views
from enclosed_deck import BAYS
UNIT=217/3.161967
PACKAGE=ROOT/'game-mod/RAN-Carrier-Australis-2030'

def load_current_mesh(package=PACKAGE, ship_id="ran_cvn_australis_2030"):
    config=package/'vessels'/f'{ship_id}.ini'
    if not config.is_file():
        config=package/'vessels'/f'{ship_id}.ini.reference'
    cfg=configparser.ConfigParser(interpolation=None);cfg.optionxform=str;cfg.read(config,encoding='utf-8-sig')
    obj=package/'ships'/ship_id/f'{ship_id}.obj'
    verts=[];groups={};name=None
    for line in obj.read_text().splitlines():
        if line.startswith('o '):name=line[2:];groups[name]={'faces':[],'material':None}
        elif line.startswith('v '):verts.append([float(v)*UNIT for v in line.split()[1:]])
        elif line.startswith('usemtl '):groups[name]['material']=line.split()[1]
        elif line.startswith('f '):groups[name]['faces'].append([int(v.split('/')[0])-1 for v in line.split()[1:]])
    verts=np.array(verts)
    def vec(s):return np.array([float(v) for v in s.split(',')])
    def rotation(s):
        x,y,z=np.radians(vec(s));cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
        return np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])@np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    matrices={}
    def transform(n,chain=()):
        if n in matrices:return matrices[n]
        assert n not in chain,'Cyclic submodel hierarchy'
        m=np.eye(4)
        if n in cfg:
            s=cfg[n];m[:3,:3]=rotation(s.get('Rotation','0,0,0'));m[:3,3]=vec(s.get('Position','0,0,0'))*UNIT
            if s.get('Parent'):m=transform(s['Parent'],chain+(n,))@m
        matrices[n]=m;return m
    mesh=Mesh()
    for n,g in groups.items():
        if n.startswith('coll_'):continue
        used=sorted({i for f in g['faces'] for i in f});lookup={i:j for j,i in enumerate(used)}
        m=transform(n);v=verts[used]@m[:3,:3].T+m[:3,3]
        mesh.parts.append((n,v,[[lookup[i] for i in f] for f in g['faces']],g['material']))
    return mesh,obj,config

def main():
    mesh,obj,config=load_current_mesh()
    for b in BAYS:
        kind,index=b.key.rsplit('_',1)
        if kind in ('CIWS','Mk46'):
            for part in ('Mount','Gun'):viewer.MOTIONS[f'{kind}_{part}_{index}']=('y',b.roof+.08-b.y if b.stroke else 0)
    # The game package has stowed laser hatches only; no invented raised overlay.
    viewer.TEMPLATE=viewer.TEMPLATE.replace('</style>','#deploy,#laserStatus{display:none}\n</style>')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Actual design-model views, not in-game screenshots.','Current game-package OBJ/INI hierarchy, not in-game screenshots. Stock runtime flag omitted.')
    revision=viewer.model_revision(mesh,COLORS)
    folder=DESIGN/'current-game-preview';(folder/'viewer').mkdir(parents=True,exist_ok=True);(folder/'model').mkdir(exist_ok=True)
    photos=render_current_views(mesh,COLORS,folder/'previews',revision)
    out=folder/'viewer'/f'australis_current_game_{revision}.html'
    viewer.build_viewer(mesh,COLORS,out,photos=photos)
    manifest={'revision':revision,'origin':'Current installable carrier OBJ and INI hierarchy','obj_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'ini_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),'visible_parts':len(mesh.parts),'triangles':sum(1 for _ in mesh.triangles()),'omitted':['stock runtime flag','collision-only mesh'],'viewer':out.name}
    (folder/'model/game-preview-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
    shutil.copy2(out,DESIGN/'viewer/australis_2030_3d.html')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()

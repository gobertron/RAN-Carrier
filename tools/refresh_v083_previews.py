#!/usr/bin/env python3
"""Refresh the v0.8.3 presentation from exported game meshes, without rebuilding release files."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'australis-2030'),str(ROOT)]
from fleet_preview_build_current_game_preview import load_current_mesh,PACKAGE
import fleet_preview_build_3d_viewer as viewer
import render_current_views as renderer
from build import COLORS
from enclosed_deck import BAYS
RELEASE='0.8.3-stock-catalogue-fix'
GEOMETRY_RELEASE='0.8.2-lift-lighting'
DESIGN=ROOT/'australis-2030';PREVIEWS=DESIGN/'previews';VIEWERS=DESIGN/'viewer'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    fleet=[]
    for key,name in [('australis','HMSCS Australis 91'),('southern_cross','HMSCS Southern Cross 92'),('federation','HMSCS Federation 93'),('commonwealth','HMSCS Commonwealth 94')]:
        ship_id=f'ran_cvn_{key}_2030'
        mesh,obj,ini=load_current_mesh(PACKAGE,ship_id)
        fleet.append({'id':ship_id,'name':name,'mesh':mesh,'obj_sha256':sha(obj),'ini_sha256':sha(ini)})
    mesh=fleet[0]['mesh'];revision=viewer.model_revision(mesh,COLORS)
    for bay in BAYS:
        kind,index=bay.key.rsplit('_',1)
        if kind in ('CIWS','Mk46'):
            for part in ('Mount','Gun'):viewer.MOTIONS[f'{kind}_{part}_{index}']=('y',bay.roof+.08-bay.y if bay.stroke else 0)
    viewer.TEMPLATE=viewer.TEMPLATE.replace('v0.8.2 LIFT LIGHTING','v0.8.3 CURRENT FLEET')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Australis 2030 — current model photos and 3D','Australis fleet v0.8.3 — current model photos and 3D')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('<h1>Australis 2030</h1>','<h1>HMSCS Australis 91</h1>')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('</style>','#deploy,#laserStatus{display:none}\n</style>')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Actual design-model views, not in-game screenshots.','Actual exported fleet meshes for v0.8.3; geometry and controller carried unchanged from v0.8.2. Runtime lighting is not simulated. These are model views, not gameplay screenshots.')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Original model sources and installers are included in the numbered release package.','Eight waterjets: four steering units and four fixed boosters. Standard 20 kn; Full/Flank 30 kn. Lift lamps are shown in the separate cutaway illustration; game appearance remains untested.')
    renderer.CAPTION='v0.8.3 current fleet · eight waterjets · 3 catapults · 4 lifts · 3 helipads'
    photos=renderer.render_current_views(mesh,COLORS,PREVIEWS,revision)
    for key,title,az,el in [('waterjets','Stern waterjets',-90,-4),('underwater','Underwater hull',-55,-23)]:
        path=PREVIEWS/f'australis_2030_current_{key}.png'
        renderer._render(list(mesh.triangles()),COLORS,title,az,el,revision,path)
        photos.append({'id':key,'title':title,'caption':renderer.CAPTION,'path':path})
    out=VIEWERS/'Australis-v0.8.3-Fleet-3D.html'
    viewer.build_viewer(mesh,COLORS,out,photos=photos,fleet=fleet)
    shutil.copy2(out,VIEWERS/'australis_2030_3d.html')
    shutil.copy2(photos[0]['path'],PREVIEWS/'Australis-v0.8.3-Full-Ship.png')
    for source,target in [('starboard','perspective'),('port_waist','port_waist'),('bow','bow')]:
        shutil.copy2(PREVIEWS/f'australis_2030_current_{source}.png',PREVIEWS/f'australis_2030_{target}.png')
    manifest_path=DESIGN/'model/presentation-manifest.json'
    manifest=json.loads(manifest_path.read_text())
    manifest.update({'version':RELEASE,'geometry_controller_release':GEOMETRY_RELEASE,'source':'Actual exported Sea Power OBJ and INI transforms','geometry_changed':False,'viewer':'../viewer/'+out.name,'rendered_lighting':'Studio surface shading only; no Unity runtime lighting simulation','omitted':['stock runtime flag','collision-only mesh']})
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    (PREVIEWS/'Australis-v0.8.3-Render-Provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Check executable JavaScript with a temporary file, no repository output.
    import tempfile
    for attrs,script in re.findall(r'<script([^>]*)>(.*?)</script>',out.read_text(),re.S):
        if 'application/json' in attrs:json.loads(script);continue
        with tempfile.NamedTemporaryFile(mode='w',suffix='.js') as test:
            test.write(script);test.flush();subprocess.run(['node','--check',test.name],check=True)
    print(json.dumps({'viewer':str(out),'revision':revision,'fleet':[{'name':s['name'],'parts':len(s['mesh'].parts),'triangles':sum(1 for _ in s['mesh'].triangles())} for s in fleet],'photos':len(photos)},indent=2))

if __name__=='__main__':main()

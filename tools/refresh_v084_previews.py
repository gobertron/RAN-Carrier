#!/usr/bin/env python3
"""Build the compact fleet design viewer from preserved numbered geometry.

The v0.8.4 game uses one native class mesh and variant number textures. This
viewer preserves the numbered fleet design appearance from the preceding
exported meshes; its studio views are not runtime or Mission Editor captures.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'australis-2030'), str(ROOT)]
from fleet_preview_build_current_game_preview import load_current_mesh, PACKAGE
import fleet_preview_build_3d_viewer as viewer
import render_current_views as renderer
from build import COLORS
from enclosed_deck import BAYS

DESIGN = ROOT/'australis-2030'
PREVIEWS = DESIGN/'previews'
VIEWERS = DESIGN/'viewer'
REFERENCE = PACKAGE/'compatibility-reference/v0.8.3'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    fleet = []
    for key, name in [('australis', 'HMSCS Australis 91'), ('southern_cross', 'HMSCS Southern Cross 92'),
                      ('federation', 'HMSCS Federation 93'), ('commonwealth', 'HMSCS Commonwealth 94')]:
        ship_id = f'ran_cvn_{key}_2030'
        mesh, obj, ini = load_current_mesh(REFERENCE, ship_id)
        fleet.append({'id': ship_id, 'name': name, 'mesh': mesh,
                      'obj_sha256': sha(obj), 'ini_sha256': sha(ini)})
    mesh = fleet[0]['mesh']
    revision = viewer.model_revision(mesh, COLORS)
    # Preserve the archived lower-stop coordinates in the compact payload.
    # Both the gallery and initial WebGL state pose only the four platforms
    # 10.202 m higher, flush with the flight deck; shaft walls stay fixed.
    idle_mesh = type(mesh)()
    for name, vertices, faces, material in mesh.parts:
        vertices = vertices.copy()
        if re.fullmatch(r'LiftPlatform[1-4]', name):
            vertices[:, 1] += 10.202
        idle_mesh.parts.append((name, vertices, faces, material))
    for bay in BAYS:
        kind, index = bay.key.rsplit('_', 1)
        if kind in ('CIWS', 'Mk46'):
            for part in ('Mount', 'Gun'):
                viewer.MOTIONS[f'{kind}_{part}_{index}'] = ('y', bay.roof+.08-bay.y if bay.stroke else 0)
    viewer.TEMPLATE = viewer.TEMPLATE.replace('v0.8.2 LIFT LIGHTING', 'v0.8.4 CLASS LIST')
    viewer.TEMPLATE = viewer.TEMPLATE.replace('Australis 2030 — current model photos and 3D',
                                             'Australis-class v0.8.4 — fleet design views')
    viewer.TEMPLATE = viewer.TEMPLATE.replace('<h1>Australis 2030</h1>', '<h1>HMSCS Australis 91</h1>')
    viewer.TEMPLATE = viewer.TEMPLATE.replace('</style>', '#deploy,#laserStatus{display:none}\n</style>')
    viewer.TEMPLATE = viewer.TEMPLATE.replace('let liftTarget = 0, liftProgress = 0;',
                                             'let liftTarget = 1, liftProgress = 1;')
    viewer.TEMPLATE = viewer.TEMPLATE.replace('id="moveLifts">Raise all four lifts',
                                             'id="moveLifts">Lower all four lifts')
    viewer.TEMPLATE = viewer.TEMPLATE.replace(
        'Two bow + one port-waist catapult. Four lifts and three helipads. Aircraft support: fixed-wing carrier aircraft, VTOL/STOL and helicopters.',
        'Two bow + one port-waist catapult. Four lifts start at flight-deck level. '
        'Three dedicated helicopter-only pads; fixed-wing carrier aircraft use the catapults.')
    viewer.TEMPLATE = viewer.TEMPLATE.replace('Actual design-model views, not in-game screenshots.',
        'Numbered fleet design geometry, preserved from the v0.8.3 exported meshes. '
        'The v0.8.4 game uses one Australis-class mesh with native hull-number textures. '
        'These are design views; runtime number textures and lighting are not simulated.')
    viewer.TEMPLATE = viewer.TEMPLATE.replace('Original model sources and installers are included in the numbered release package.',
        'All four ships now appear directly under Australis-class in the native class definition. '
        'Eight waterjets; Standard 20 kn, Full/Flank 30 kn. '
        'The complete PNG renders remain separately available in the project previews folder.')
    renderer.CAPTION = 'v0.8.4 idle flight deck · lifts UP · 3 catapults · 3 helicopter-only pads'
    photos = renderer.render_current_views(idle_mesh, COLORS, PREVIEWS, revision)
    for key, title, azimuth, elevation in [('waterjets', 'Stern waterjets', -90, -4),
                                         ('underwater', 'Underwater hull', -55, -23)]:
        path = PREVIEWS/f'australis_2030_current_{key}.png'
        renderer._render(list(idle_mesh.triangles()), COLORS, title, azimuth, elevation, revision, path)
        photos.append({'id': key, 'title': title,
                       'caption': renderer.CAPTION, 'path': path})
    for photo in photos:
        photo['caption'] = ('Idle flight-deck pose: lifts UP. Numbered fleet design geometry; '
                            'native v0.8.4 number textures are not rendered here.')
    out = VIEWERS/'Australis-v0.8.4-Fleet-3D.html'
    viewer.build_viewer(mesh, COLORS, out, photos=photos, fleet=fleet)
    if out.stat().st_size > 1_000_000:
        raise ValueError('Fleet viewer exceeds the compact publication size limit')
    shutil.copy2(out, VIEWERS/'australis_2030_3d.html')
    shutil.copy2(photos[0]['path'], PREVIEWS/'Australis-v0.8.4-Full-Ship.png')
    shutil.copy2(PREVIEWS/'Australis-v0.8.3-Lift-Cutaway.png', PREVIEWS/'Australis-v0.8.4-Lift-Cutaway.png')
    for source, target in [('starboard', 'perspective'), ('port_waist', 'port_waist'), ('bow', 'bow')]:
        shutil.copy2(PREVIEWS/f'australis_2030_current_{source}.png', PREVIEWS/f'australis_2030_{target}.png')
    manifest_path = DESIGN/'model/presentation-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest.update({'version': '0.8.4-class-list-fix', 'source': 'Preserved v0.8.3 numbered fleet OBJ and INI transforms',
        'native_class': 'Australis-class; four native variants sharing one mesh with native hull-number textures',
        'runtime_number_textures_simulated': False, 'viewer': '../viewer/'+out.name,
        'default_lift_pose': 'All four platforms UP; tops at 22.002 m, flush with flight deck',
        'lift_pose_offset_m': 10.202,
        'mesh_payload_pose': 'Archived lower-stop coordinates; viewer applies the initial upper-stop offset',
        'gallery_pose': 'Only LiftPlatform1..4 translated upward 10.202 m; shaft walls unchanged',
        'helicopter_pads': 'Three dedicated helicopter-only pads',
        'rendered_lighting': 'Studio surface shading only; no Unity runtime lighting simulation',
        'storage': 'Shared geometry aggregates; exact float32 bytes retained for each fleet choice',
        'gallery': '1600-pixel WebP display copies; current PNGs use the idle upper pose; versioned v0.8.3 PNGs unchanged'})
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    (PREVIEWS/'Australis-v0.8.4-Render-Provenance.json').write_text(json.dumps(manifest, indent=2)+'\n')
    for attrs, script in re.findall(r'<script([^>]*)>(.*?)</script>', out.read_text(), re.S):
        if 'application/json' in attrs:
            json.loads(script)
            continue
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js') as test:
            test.write(script)
            test.flush()
            subprocess.run(['node', '--check', test.name], check=True)
    print(json.dumps({'viewer': str(out), 'bytes': out.stat().st_size, 'fleet': len(fleet), 'photos': len(photos)}, indent=2))


if __name__ == '__main__':
    main()

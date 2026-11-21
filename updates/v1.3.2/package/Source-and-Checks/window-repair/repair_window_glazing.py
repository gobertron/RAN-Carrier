#!/usr/bin/env python3
"""Preserve Australis pane geometry while repairing UVs and glazing material."""
from collections import defaultdict
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile

BASELINE_SHA = 'df050f9f730242db5045afad7aa24540c3db22eb13af0b1b01a2b3c21cfbde65'
FITTINGS = ('FullBatch_glass', 'FullBatch_ICCS_Bubble_Lift__glass')
OBJ_NAME = 'ran_cvn_australis_2030.obj'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic(path, data):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        f.write(data)
    tmp.replace(path)


def is_window(name):
    return name.startswith('NavalWindow_') and name.endswith('_Glass')


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def read_obj(text):
    tables = {'v': [], 'vt': [], 'vn': []}
    raw_tables = {key: [] for key in tables}
    obj = material = ''
    windows = defaultdict(list)
    geometry = hashlib.sha256()
    nonwindow = hashlib.sha256()
    counts = defaultdict(int)
    for line_number, raw in enumerate(text.splitlines(), 1):
        a = raw.split()
        if not a:
            continue
        if a[0] in tables:
            values = tuple(map(float, a[1:]))
            assert all(map(math.isfinite, values)), line_number
            tables[a[0]].append(values)
            raw_tables[a[0]].append(raw)
        elif a[0] == 'o':
            obj = a[1]
        elif a[0] == 'usemtl':
            material = a[1]
        elif a[0] == 'f':
            assert len(a) == 4
            face = [tuple(map(int, t.split('/'))) for t in a[1:]]
            for token in face:
                assert len(token) == 3
                for k, i in zip(('v', 'vt', 'vn'), token):
                    assert 1 <= i <= len(tables[k]), (line_number, k, i)
            geometry.update((obj+'\0'+material+'\0'+' '.join(f'{x[0]}//{x[2]}' for x in face)+'\n').encode())
            counts[obj] += 1
            if is_window(obj):
                windows[obj].append(face)
            else:
                # Values, not table indices, define the non-window UV mapping.
                nonwindow.update((obj+'\0'+material+'\0'+str([
                    (t[0], tables['vt'][t[1]-1], t[2]) for t in face])+'\n').encode())
    determinants = []
    for faces in windows.values():
        for face in faces:
            u = [tables['vt'][t[1]-1] for t in face]
            d = (u[1][0]-u[0][0])*(u[2][1]-u[0][1])-(u[1][1]-u[0][1])*(u[2][0]-u[0][0])
            determinants.append(abs(d))
    return {'tables': tables, 'raw_tables': raw_tables, 'windows': windows,
            'geometry_sha256': geometry.hexdigest(), 'nonwindow_uv_sha256': nonwindow.hexdigest(),
            'face_counts': dict(counts), 'window_triangle_count': len(determinants),
            'degenerate_uv_triangles': sum(v < 1e-14 for v in determinants),
            'minimum_uv_determinant': min(determinants)}


def project(points):
    edges = [[points[j][i]-points[0][i] for i in range(3)] for j in (1, 2)]
    normal = cross(*edges)
    assert sum(x*x for x in normal) > 1e-24
    drop = max(range(3), key=lambda i: abs(normal[i]))
    axes = [i for i in range(3) if i != drop]
    spans = [(min(p[i] for p in points), max(p[i] for p in points)) for i in axes]
    assert all(hi > lo for lo, hi in spans)
    uv = [tuple(0.125+0.75*(p[i]-lo)/(hi-lo) for i, (lo, hi) in zip(axes, spans)) for p in points]
    d = (uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-(uv[1][1]-uv[0][1])*(uv[2][0]-uv[0][0])
    assert math.isfinite(d) and abs(d) > 1e-10
    return uv


def section(text, name):
    pattern = r'(?ms)^\['+re.escape(name)+r'\]\s*\n.*?(?=^\[|\Z)'
    matches = list(re.finditer(pattern, text))
    assert len(matches) == 1, name
    return matches[0]


def repair(payload):
    folder = payload / 'ships/ran_cvn_australis_2030'
    path = folder / OBJ_NAME
    original = path.read_bytes()
    assert sha(original) == BASELINE_SHA, 'Expected delivered v1.3.1 model'
    text = original.decode()
    before = read_obj(text)
    assert len(before['windows']) == 66
    assert before['window_triangle_count'] == 3928
    assert before['degenerate_uv_triangles'] == 244
    # Put the repaired pane UVs first, so their global source indices also stay
    # below UInt16. Existing UV values are moved intact and remapped semantically.
    projected = []
    for faces in before['windows'].values():
        for face in faces:
            projected.extend(project([before['tables']['v'][t[0]-1] for t in face]))
    offset = len(projected)
    assert offset == 11784
    added = [f'vt {u:.12f} {v:.12f}\n' for u, v in projected]
    out, obj, inserted, window_index = [], '', False, 1
    for raw in text.splitlines(keepends=True):
        a = raw.split()
        if a and a[0] == 'vt' and not inserted:
            out.append('# Australis window UV and glazing repair\n')
            out.extend(added)
            inserted = True
        if a and a[0] == 'o':
            obj = a[1]
        elif a and a[0] == 'f':
            tokens = [tuple(map(int, t.split('/'))) for t in a[1:]]
            if is_window(obj):
                raw = 'f '+' '.join(f'{t[0]}/{window_index+i}/{t[2]}' for i, t in enumerate(tokens))+'\n'
                window_index += 3
            else:
                raw = 'f '+' '.join(f'{t[0]}/{t[1]+offset}/{t[2]}' for t in tokens)+'\n'
        out.append(raw)
    assert inserted and window_index == offset+1
    repaired = ''.join(out)
    after = read_obj(repaired)
    assert before['geometry_sha256'] == after['geometry_sha256']
    assert before['nonwindow_uv_sha256'] == after['nonwindow_uv_sha256']
    assert before['raw_tables']['v'] == after['raw_tables']['v']
    assert before['raw_tables']['vn'] == after['raw_tables']['vn']
    assert before['raw_tables']['vt'] == after['raw_tables']['vt'][offset:]
    assert before['face_counts'] == after['face_counts']
    assert max(after['face_counts'].values())*3 <= 60000
    assert after['degenerate_uv_triangles'] == 0
    mat = folder / 'glass_mat.ini'
    original_material = mat.read_bytes()
    simplified = '\n'.join(line for line in original_material.decode().splitlines()
                           if not line.startswith(('_BumpMap=', '_SpecTex=')))+'\n'
    assert 'Path=Marmoset/Bumped Specular IBL' in simplified
    assert '_MainTex=ships/ran_cvn_australis_2030/glass.png' in simplified
    vessel_path = payload / 'vessels/ran_cvn_australis_2030.ini'
    original_vessel = vessel_path.read_text()
    vessel = original_vessel
    for name in FITTINGS:
        block = section(vessel, name)
        updated = block[0].replace('Material=glass_mat.ini', 'Material=glass_fittings_mat.ini')
        assert updated != block[0]
        vessel = vessel[:block.start()]+updated+vessel[block.end():]
    for name in before['windows']:
        assert 'Material=glass_mat.ini' in section(vessel, name)[0]
    assert vessel.count('Material=glass_fittings_mat.ini') == 2
    assert vessel.count('Material=glass_mat.ini') == 66
    atomic(path, repaired.encode())
    atomic(folder / 'glass_fittings_mat.ini', original_material)
    atomic(mat, simplified.encode())
    atomic(vessel_path, vessel.encode())
    return {
        'schema': 1, 'repair': 'Window-only UV and glazing material repair',
        'before_obj_sha256': sha(original), 'after_obj_sha256': sha(path.read_bytes()),
        'window_groups_repaired': 66, 'window_triangle_count': 3928,
        'degenerate_uv_triangles_before': 244, 'degenerate_uv_triangles_after': 0,
        'minimum_abs_uv_determinant_after': after['minimum_uv_determinant'],
        'new_uv_entries': offset, 'window_global_uv_index_range': [1, offset],
        'positions_preserved': True, 'normals_preserved': True,
        'triangle_position_indices_preserved': True, 'triangle_normal_indices_preserved': True,
        'all_obj_material_assignments_and_object_names_preserved': True,
        'nonwindow_uv_semantics_preserved': True, 'original_uv_values_preserved': True,
        'previous_mesh_batches_within_60000_expanded_corners': True,
        'before_material_sha256': sha(original_material),
        'after_material_sha256': sha(mat.read_bytes()),
        'fittings_material_sha256': sha((folder / 'glass_fittings_mat.ini').read_bytes()),
        'window_material_shader': 'Marmoset/Bumped Specular IBL',
        'removed_window_material_bindings': ['_BumpMap', '_SpecTex'],
        'window_main_texture_and_opaque_alpha_preserved': True,
        'nonwindow_glass_material_preserved_as': 'glass_fittings_mat.ini',
        'nonwindow_glass_submodels': list(FITTINGS),
        'window_material_reference_count': 66, 'fittings_material_reference_count': 2,
        'controller_and_glow_names_unchanged': True,
        'before_vessel_sha256': sha(original_vessel.encode()), 'after_vessel_sha256': sha(vessel.encode()),
        'diagnosis': 'Degenerate UVs confirmed; relationship to persistent strip requires runtime retest',
        'native_windows_tested': False, 'live_game_tested': False,
    }


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--payload', required=True, type=Path)
    ap.add_argument('--report', type=Path, default=Path('WINDOW-REPAIR-REPORT.json'))
    args = ap.parse_args()
    report = repair(args.payload)
    atomic(args.report, (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps(report, indent=2))

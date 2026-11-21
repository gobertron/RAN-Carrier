#!/usr/bin/env python3
"""Split Australis OBJ batches at conservative Unity UInt16 index limits.

This changes only OBJ object boundaries and the native vessel's submodel
registrations. Position/UV/normal tables and the complete face/material multiset
are preserved exactly. The original mesh name is retained for the first chunk, so
all existing controller, damage, flag and animation references remain valid.

Usage: python repair_mesh_batches.py --payload PATH [--report REPORT.json]
This is a conservative importer compatibility repair, not an in-game test.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile

MAX_CORNERS = 60_000
OBJ_REL = Path('ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj')
VESSEL_REL = Path('vessels/ran_cvn_australis_2030.ini')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic(path: Path, data: bytes) -> None:
    # Several source and regression copies may share an inode. Never modify it.
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        temp = Path(f.name)
        f.write(data)
    temp.replace(path)


def parse(text: str) -> dict:
    counts = Counter()
    tables = {'v': [], 'vt': [], 'vn': []}
    objects = {}
    obj = None
    material = ''
    ordered_faces = hashlib.sha256()
    face_material_records = []
    ordered_tables = hashlib.sha256()
    for line_number, raw in enumerate(text.splitlines(), 1):
        fields = raw.split()
        if not fields:
            continue
        kind = fields[0]
        counts[kind] += 1
        if kind in tables:
            nums = tuple(map(float, fields[1:]))
            assert all(map(math.isfinite, nums)), (line_number, 'Non-finite coordinate')
            tables[kind].append(nums)
            ordered_tables.update((raw + '\n').encode())
        elif kind == 'o':
            obj = ' '.join(fields[1:])
            assert obj not in objects, ('Duplicate object name', obj)
            objects[obj] = {'faces': 0, 'corners': 0, 'keys': set(), 'positions': set()}
        elif kind == 'usemtl':
            material = fields[1]
        elif kind == 'f':
            assert obj, 'Faces must belong to a named OBJ object'
            assert len(fields) == 4, (line_number, 'Only pre-triangulated faces accepted')
            group = objects[obj]
            group['faces'] += 1
            group['corners'] += 3
            group['keys'].update(fields[1:])
            for token in fields[1:]:
                indices = token.split('/')
                assert len(indices) == 3 and all(indices), (line_number, token)
                for i, table in zip(map(int, indices), ('v', 'vt', 'vn')):
                    assert 1 <= i <= len(tables[table]), (line_number, table, i)
                group['positions'].add(int(indices[0]))
            ordered_faces.update((material + '\0' + raw + '\n').encode())
            face_material_records.append(material + '\0' + raw + '\n')
        elif kind in ('l', 'p'):
            raise AssertionError(('Unexpected line/point primitive', line_number))
    stats = {name: {
        'faces': x['faces'], 'expanded_corners': x['corners'],
        'unique_vertex_uv_normal_tuples': len(x['keys']),
        'unique_positions': len(x['positions']),
        'bounds': [[min(tables['v'][k-1][i] for k in x['positions']),
                    max(tables['v'][k-1][i] for k in x['positions'])]
                   for i in range(3)] if x['positions'] else None,
    } for name, x in objects.items()}
    return {'counts': dict(counts), 'objects': stats,
            'bounds': [[min(p[i] for p in tables['v']), max(p[i] for p in tables['v'])]
                       for i in range(3)],
            'face_material_sha256': ordered_faces.hexdigest(),
            'face_material_multiset_sha256': digest(''.join(sorted(face_material_records)).encode()),
            'coordinate_tables_sha256': ordered_tables.hexdigest()}


def section(text: str, name: str) -> tuple[int, int, str]:
    headers = list(re.finditer(r'^\[([^\]\r\n]+)\][ \t]*$', text, re.M))
    matches = [i for i, h in enumerate(headers) if h[1] == name]
    assert len(matches) == 1, ('Expected unique INI section', name)
    i = matches[0]
    start, end = headers[i].start(), headers[i + 1].start() if i + 1 < len(headers) else len(text)
    return start, end, text[start:end]


def repair(payload: Path) -> dict:
    obj_path, vessel_path = payload / OBJ_REL, payload / VESSEL_REL
    source = obj_path.read_bytes()
    text = source.decode('utf-8')
    before = parse(text)
    # Re-running a completed repair validates it without generating new names.
    oversized = {name for name, stats in before['objects'].items()
                 if stats['expanded_corners'] > MAX_CORNERS}
    # The game may use the ResourcesMesh root's bounds for selection or scale.
    # Keep Hull's exact extrema in its first chunk, rather than relying on a
    # union of child mesh bounds. Move at most six original triangles up front;
    # no vertex, UV, normal, winding, material, triangle or multiplicity changes.
    if 'Hull' in oversized:
        vertices = [tuple(map(float, line.split()[1:4])) for line in text.splitlines()
                    if line.startswith('v ')]
        start = text.index('o Hull\n')
        end = text.find('\no ', start + len('o Hull\n'))
        end = end + 1 if end >= 0 else len(text)
        raw = text[start:end].splitlines(keepends=True)
        face_lines = [i for i, line in enumerate(raw) if line.startswith('f ')]
        assert all(line.startswith(('o ', 'usemtl ', 's ', 'f ')) for line in raw)
        face_positions = {i: [int(token.split('/')[0]) - 1 for token in raw[i].split()[1:]]
                          for i in face_lines}
        all_positions = {k for positions in face_positions.values() for k in positions}
        extremes = {fn(all_positions, key=lambda k: vertices[k][axis])
                    for axis in range(3) for fn in (min, max)}
        seeds = sorted({min(i for i in face_lines if k in face_positions[i]) for k in extremes})
        ordered = [raw[i] for i in seeds] + [raw[i] for i in face_lines if i not in seeds]
        header = ''.join(line for line in raw if not line.startswith('f '))
        text = text[:start] + header + ''.join(ordered) + text[end:]
    out = []
    additions = []
    current, material, smoothing, corners, part = '', '', 'off', 0, 1
    for raw in text.splitlines(keepends=True):
        fields = raw.split()
        if fields:
            if fields[0] == 'o':
                current, corners, part = ' '.join(fields[1:]), 0, 1
            elif fields[0] == 'usemtl':
                material = fields[1]
            elif fields[0] == 's':
                smoothing = fields[1]
            elif fields[0] == 'f':
                if corners + 3 > MAX_CORNERS:
                    assert current in oversized
                    part += 1
                    name = f'{current}__Chunk{part:02d}'
                    out.extend([f'o {name}\n', f'usemtl {material}\n', f's {smoothing}\n'])
                    additions.append({'source': current, 'name': name, 'material': material})
                    corners = 0
                corners += 3
        out.append(raw)
    repaired = ''.join(out)
    after = parse(repaired)
    assert before['face_material_multiset_sha256'] == after['face_material_multiset_sha256']
    assert before['coordinate_tables_sha256'] == after['coordinate_tables_sha256']
    assert before['bounds'] == after['bounds']
    assert before['objects']['Hull']['bounds'] == after['objects']['Hull']['bounds']
    assert before['counts']['f'] == after['counts']['f']
    assert max(x['expanded_corners'] for x in after['objects'].values()) <= MAX_CORNERS
    assert max(x['unique_vertex_uv_normal_tuples'] for x in after['objects'].values()) <= MAX_CORNERS
    vessel_source = vessel_path.read_text()
    vessel = vessel_source
    start, end, submodels = section(vessel, 'Submodels')
    assert not any(x['name'] in vessel for x in additions)
    appended = ''.join(f'MeshRepair_{i:04d}={x["name"]}\n' for i, x in enumerate(additions, 1))
    vessel = vessel[:start] + submodels.rstrip() + '\n' + appended + '\n' + vessel[end:]
    for x in additions:
        if x['source'] == 'Hull':
            _, _, model = section(vessel_source, 'Models')
            mat = re.search(r'^ResourcesMaterial=(.+)$', model, re.M)[1]
            body = f'Mesh={x["name"]}\nMaterial={mat}\n'
        else:
            _, _, original = section(vessel_source, x['source'])
            body = original.split('\n', 1)[1]
            body = re.sub(r'^Mesh=.+$', 'Mesh=' + x['name'], body, flags=re.M)
            assert not re.search(r'^(Parent|Position|Rotation|Scale)=', body, re.M), (
                'Repair only statically batched meshes', x['source'])
        vessel = vessel.rstrip() + '\n\n[' + x['name'] + ']\n' + body.strip() + '\n'
    # Preserve all existing names and every material/parent setting on old parts.
    assert set(before['objects']).issubset(after['objects'])
    _, _, submodels = section(vessel, 'Submodels')
    for x in additions:
        assert re.search(r'^MeshRepair_[0-9]+=' + re.escape(x['name']) + '$', submodels, re.M)
        _, _, part_section = section(vessel, x['name'])
        assert f'Mesh={x["name"]}\n' in part_section
        material_file = re.search(r'^Material=(.+)$', part_section, re.M)[1]
        assert (obj_path.parent / material_file).is_file(), material_file
    if additions:
        atomic(obj_path, repaired.encode())
        atomic(vessel_path, vessel.encode())
    return {
        'schema': 1, 'repair': 'Conservative UInt16-compatible OBJ batching',
        'max_expanded_face_corners_per_mesh': MAX_CORNERS,
        'before_obj_sha256': digest(source), 'after_obj_sha256': digest(obj_path.read_bytes()),
        'before': before, 'after': after, 'added_static_meshes': additions,
        'all_faces_and_material_assignments_preserved': True,
        'all_position_uv_normal_tables_preserved': True,
        'original_mesh_names_preserved': True,
        'ship_bounds_unchanged': True,
        'root_hull_bounds_unchanged': True,
        'root_hull_extremal_triangles_retained_in_first_chunk': True,
        'existing_moving_part_names_and_transforms_preserved': True,
        'indices_finite_and_in_range': True,
        'root_cause_status': 'Oversized batch demonstrated; importer overflow remains a likely explanation until a live game retest',
        'nixie_decoy_cables': 'Two native 579m cables intentionally retained',
        'live_game_tested': False,
    }


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--payload', required=True, type=Path)
    ap.add_argument('--report', type=Path, default=Path('MODEL-REPAIR-REPORT.json'))
    args = ap.parse_args()
    report = repair(args.payload)
    atomic(args.report, (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({k: report[k] for k in ('before_obj_sha256', 'after_obj_sha256',
                                          'added_static_meshes', 'live_game_tested')}, indent=2))
